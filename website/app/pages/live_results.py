"""Live results page with Regular/House sections and per-house breakdown."""

from __future__ import annotations

from typing import Any

from nicegui import app, ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.analytics_service import AnalyticsService
from app.theme import apply_saved_theme, inject_theme
from app.websocket.client import WebSocketClient
from app.websocket.page_session import WebSocketPageSession, safe_ui_update

ELECTION_TYPES = ("Regular", "House")


def register_live_results_routes() -> None:
    """Register the live results page."""

    @ui.page("/live-results")
    @require_auth
    async def live_results_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "election_type": "Regular",
            "selected_house_id": "",
            "regular": None,
            "houses": None,
            "ws_connected": False,
        }
        ui_refs: dict[str, Any] = {}
        ws_client: WebSocketClient | None = None
        ws_session = WebSocketPageSession()

        def _update_ws_indicator() -> None:
            ws_badge = ui_refs.get("ws_badge")
            if ws_badge is None:
                return
            if state["ws_connected"]:
                ws_badge.set_text("LIVE")
                ws_badge.props("color=positive")
            else:
                ws_badge.set_text("Reconnecting")
                ws_badge.props("color=warning")

        def _update_header() -> None:
            title = ui_refs.get("title")
            subtitle = ui_refs.get("subtitle")
            ws_badge = ui_refs.get("ws_badge")

            if state["election_type"] == "Regular":
                data = state.get("regular") or {}
                votes = data.get("total_votes", 0)
            else:
                data = state.get("houses") or {}
                houses = data.get("house_results") or []
                selected = state.get("selected_house_id") or ""
                if selected:
                    house = next((item for item in houses if item.get("house_id") == selected), None)
                    votes = (house or {}).get("vote_count", 0)
                else:
                    votes = data.get("total_votes", 0)

            election_name = data.get("election_name") or "Live Results"
            election_status = data.get("election_status") or "—"

            if title is not None:
                title.set_text(election_name)
            if subtitle is not None:
                scope = state["election_type"]
                if state["election_type"] == "House" and state.get("selected_house_id"):
                    houses = (state.get("houses") or {}).get("house_results") or []
                    house = next(
                        (item for item in houses if item.get("house_id") == state["selected_house_id"]),
                        None,
                    )
                    if house:
                        scope = house.get("house_name", "House")
                subtitle.set_text(f"{scope} · {election_status} · {votes:,} votes cast")

            _update_ws_indicator()

        def _render_position_block(position: dict[str, Any]) -> None:
            with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                ui.label(position.get("position_name", "Position")).classes("text-h6 text-weight-bold q-mb-sm")
                ui.label(f"{position.get('total_votes', 0):,} votes").classes("text-caption text-grey-7 q-mb-md")
                candidates = position.get("candidates") or []
                if not candidates:
                    ui.label("No votes yet.").classes("text-caption text-grey-6")
                    return
                for candidate in candidates:
                    with ui.row().classes("items-center q-gutter-sm q-mb-xs w-full"):
                        rank = candidate.get("rank")
                        rank_label = f"#{rank}" if rank else "—"
                        ui.label(rank_label).classes("text-caption text-grey-6 col-auto")
                        ui.label(candidate.get("candidate_name", "—")).classes("col-grow text-body2")
                        if candidate.get("is_winner"):
                            ui.badge("Winner", color="positive").props("outline")
                        ui.label(f"{candidate.get('vote_count', 0):,}").classes("text-body2 text-weight-medium")
                        ui.label(f"{candidate.get('percentage', 0)}%").classes("text-caption text-grey-7")
                        ui.linear_progress(
                            value=min(candidate.get("percentage", 0) / 100, 1.0),
                            show_value=False,
                        ).classes("col-12")

        def _sync_house_filter_options() -> None:
            house_filter = ui_refs.get("house_filter")
            if house_filter is None:
                return
            houses = (state.get("houses") or {}).get("house_results") or []
            options = {"": "All Houses"}
            for house in houses:
                house_id = house.get("house_id")
                if house_id:
                    options[house_id] = house.get("house_name") or house_id
            house_filter.options = options
            if state.get("selected_house_id") not in options:
                state["selected_house_id"] = ""
                house_filter.value = ""
            house_filter.update()

        def render_results() -> None:
            _update_header()
            house_row = ui_refs.get("house_filter_row")
            if house_row is not None:
                house_row.visible = state["election_type"] == "House"

            container = ui_refs.get("results_container")
            if container is None:
                return
            container.clear()

            with container:
                if state["election_type"] == "Regular":
                    data = state.get("regular") or {}
                    positions = data.get("positions") or []
                    if not positions:
                        with ui.element("div").classes("emp-placeholder w-full"):
                            ui.icon("live_tv", size="xl").classes("text-grey-5 q-mb-md")
                            ui.label("No regular election results yet").classes("text-h6 text-weight-medium")
                        return
                    for position in positions:
                        _render_position_block(position)
                    return

                data = state.get("houses") or {}
                houses = data.get("house_results") or []
                if not houses:
                    with ui.element("div").classes("emp-placeholder w-full"):
                        ui.icon("home", size="xl").classes("text-grey-5 q-mb-md")
                        ui.label("No house election results yet").classes("text-h6 text-weight-medium")
                    return

                selected = state.get("selected_house_id") or ""
                visible_houses = (
                    [house for house in houses if house.get("house_id") == selected]
                    if selected
                    else houses
                )

                for house in visible_houses:
                    with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                        with ui.row().classes("items-center justify-between q-mb-md w-full"):
                            ui.label(house.get("house_name", "House")).classes("text-h6 text-weight-bold")
                            ui.label(
                                f"{house.get('vote_count', 0):,} votes · {house.get('percentage', 0)}%"
                            ).classes("text-caption text-grey-7")

                        positions = house.get("positions") or []
                        if not positions:
                            ui.label("No positions with votes for this house yet.").classes(
                                "text-caption text-grey-6"
                            )
                            continue

                        for position in positions:
                            ui.label(position.get("position_name", "Position")).classes(
                                "text-subtitle1 text-weight-medium q-mt-sm q-mb-xs"
                            )
                            ui.label(f"{position.get('total_votes', 0):,} votes").classes(
                                "text-caption text-grey-7 q-mb-sm"
                            )
                            for candidate in position.get("candidates") or []:
                                with ui.row().classes("items-center q-gutter-sm q-mb-xs w-full"):
                                    rank = candidate.get("rank")
                                    ui.label(f"#{rank}" if rank else "—").classes(
                                        "text-caption text-grey-6 col-auto"
                                    )
                                    ui.label(candidate.get("candidate_name", "—")).classes(
                                        "col-grow text-body2"
                                    )
                                    if candidate.get("is_winner"):
                                        ui.badge("Winner", color="positive").props("outline")
                                    ui.label(f"{candidate.get('vote_count', 0):,}").classes(
                                        "text-body2 text-weight-medium"
                                    )
                                    ui.label(f"{candidate.get('percentage', 0)}%").classes(
                                        "text-caption text-grey-7"
                                    )
                                    ui.linear_progress(
                                        value=min(candidate.get("percentage", 0) / 100, 1.0),
                                        show_value=False,
                                    ).classes("col-12")

        async def refresh_data() -> None:
            regular = await AnalyticsService.get_regular()
            houses = await AnalyticsService.get_houses()
            if not ws_session.active:
                return
            state["regular"] = regular or {}
            state["houses"] = houses or {}
            safe_ui_update(_sync_house_filter_options)
            safe_ui_update(render_results)

        def on_live_update(_payload: dict[str, Any]) -> None:
            ui.timer(0, refresh_data, once=True)

        def on_ws_status(payload: dict[str, Any]) -> None:
            if payload.get("channel") == "live":
                state["ws_connected"] = bool(payload.get("connected"))
                _update_ws_indicator()

        async def connect_websocket() -> None:
            nonlocal ws_client
            ws_client = WebSocketClient(channel="live")
            ws_client.on("live_results_update", ws_session.bind(on_live_update))
            ws_session.subscribe("ws_status", on_ws_status)
            await ws_client.start()

        with admin_shell("/live-results") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui_refs["title"] = ui.label("Live Results").classes("emp-page-title")
                        ui_refs["subtitle"] = ui.label("Loading…").classes("emp-page-subtitle")
                    ui_refs["ws_badge"] = ui.badge("Connecting", color="grey")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md items-end"):
                    type_tabs = ui.toggle(list(ELECTION_TYPES), value=state["election_type"]).props(
                        "outline toggle-color=primary"
                    ).classes("col-12 col-md-3")

                    house_filter_row = ui.row().classes("col-12 col-md-4 items-end")
                    ui_refs["house_filter_row"] = house_filter_row
                    with house_filter_row:
                        house_filter = ui.select(
                            label="House",
                            options={"": "All Houses"},
                            value="",
                        ).props("outlined dense emit-value map-options").classes("w-full")
                        ui_refs["house_filter"] = house_filter
                    house_filter_row.visible = False

                ui_refs["results_container"] = ui.column().classes("w-full")

                def on_type_change() -> None:
                    state["election_type"] = type_tabs.value or "Regular"
                    render_results()

                def on_house_change() -> None:
                    state["selected_house_id"] = house_filter.value or ""
                    render_results()

                type_tabs.on("update:model-value", lambda: on_type_change())
                house_filter.on("update:model-value", lambda: on_house_change())

        await refresh_data()
        await connect_websocket()

        async def cleanup() -> None:
            ws_session.deactivate()
            if ws_client is not None:
                await ws_client.stop()

        app.on_disconnect(cleanup)
