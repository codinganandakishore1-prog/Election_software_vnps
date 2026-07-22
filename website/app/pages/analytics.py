"""Analytics page with rankings, turnout, charts, and house statistics."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.election_service import ElectionService
from app.theme import apply_saved_theme, inject_theme

OVERVIEW_TAB = "Overview"
RANKINGS_TAB = "Rankings"
HOUSES_TAB = "Houses"
NODES_TAB = "Nodes"
TABS = (OVERVIEW_TAB, RANKINGS_TAB, HOUSES_TAB, NODES_TAB)

CHART_TYPES = [
    ("line", "Line"),
    ("bar", "Bar"),
    ("area", "Area"),
    ("pie", "Pie"),
    ("doughnut", "Doughnut"),
]

STATUS_PRIORITY = {"Live": 0, "Paused": 1, "Published": 2, "Closed": 3, "Draft": 4}


def _format_turnout(turnout: dict[str, Any] | None) -> str:
    if not turnout:
        return "—"
    percentage = turnout.get("turnout_percentage")
    if percentage is None:
        participants = turnout.get("estimated_participants", 0)
        return f"{participants:,} voters"
    return f"{percentage}%"


def _pick_default_election(elections: list[dict[str, Any]]) -> str:
    if not elections:
        return ""
    ordered = sorted(
        elections,
        key=lambda item: (
            STATUS_PRIORITY.get(item.get("status", "Draft"), 99),
            item.get("name") or item.get("election_name") or "",
        ),
    )
    return ordered[0]["id"]


def _build_series_chart(
    chart_type: str,
    labels: list[str],
    values: list[int | float],
    *,
    title: str,
) -> dict[str, Any]:
    safe_labels = [str(label) for label in labels]
    safe_values = [float(value or 0) for value in values]

    if not safe_labels or sum(safe_values) <= 0:
        return {
            "title": {"text": title, "left": "center", "top": 8, "textStyle": {"fontSize": 13}},
            "graphic": {
                "type": "text",
                "left": "center",
                "top": "middle",
                "style": {"text": "No chart data yet", "fill": "#9e9e9e", "fontSize": 14},
            },
            "xAxis": {"show": False},
            "yAxis": {"show": False},
            "series": [],
        }

    if chart_type in {"pie", "doughnut"}:
        return {
            "title": {"text": title, "left": "center", "top": 8, "textStyle": {"fontSize": 13}},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left", "top": 40},
            "series": [
                {
                    "name": title,
                    "type": "pie",
                    "radius": ["40%", "65%"] if chart_type == "doughnut" else "60%",
                    "center": ["60%", "55%"],
                    "data": [
                        {"name": label, "value": value}
                        for label, value in zip(safe_labels, safe_values)
                        if value > 0
                    ],
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.2)",
                        }
                    },
                }
            ],
        }

    series_type = "line" if chart_type in {"line", "area"} else "bar"
    series: dict[str, Any] = {
        "name": title,
        "type": series_type,
        "data": safe_values,
        "smooth": True,
    }
    if chart_type == "area":
        series["areaStyle"] = {"opacity": 0.3}

    return {
        "title": {"text": title, "left": "center", "top": 8, "textStyle": {"fontSize": 13}},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 48, "right": 24, "top": 48, "bottom": 48},
        "xAxis": {"type": "category", "data": safe_labels, "axisLabel": {"rotate": 30}},
        "yAxis": {"type": "value", "minInterval": 1},
        "series": [series],
    }


def _set_chart_options(chart: Any, options: dict[str, Any]) -> None:
    """Force a full chart redraw so type switches (line/bar/pie) always apply."""
    chart._props["options"] = options
    chart.update()
    try:
        chart.run_chart_method("clear")
        chart.run_chart_method("setOption", options, True)
    except Exception:
        # Client may not be ready yet on first paint; props update is enough then.
        pass


def register_analytics_routes() -> None:
    """Register the analytics page."""

    @ui.page("/analytics")
    @require_auth
    async def analytics_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {
            "overview": None,
            "chart_type": "bar",
            "election_id": "",
            "elections": [],
        }
        ui_refs: dict[str, Any] = {}

        def apply_overview(data: dict[str, Any]) -> None:
            state["overview"] = data
            summary = data.get("summary") or {}

            for key, value in {
                "election": summary.get("election_name", "—"),
                "status": summary.get("election_status", "—"),
                "votes": f"{summary.get('total_votes', 0):,}",
                "regular": f"{summary.get('regular_votes', 0):,}",
                "house": f"{summary.get('house_votes', 0):,}",
                "turnout": _format_turnout(summary.get("turnout")),
                "nodes": f"{summary.get('online_nodes', 0)} / {summary.get('total_nodes', 0)}",
            }.items():
                label = ui_refs.get(f"stat_{key}")
                if label is not None:
                    label.set_text(value)

            subtitle = ui_refs.get("subtitle")
            if subtitle is not None:
                subtitle.set_text(
                    f"{summary.get('election_status', '—')} · "
                    f"{summary.get('position_count', 0)} positions · "
                    f"{summary.get('candidate_count', 0)} candidates"
                )

            render_charts()
            render_rankings(data.get("regular_positions") or [])
            render_houses(data.get("house_results") or [])
            render_nodes(data.get("node_statistics") or [])

        def _candidate_vote_series(data: dict[str, Any]) -> tuple[list[str], list[float]]:
            entries: list[tuple[str, float]] = []

            for position in data.get("regular_positions") or []:
                position_name = position.get("position_name", "Position")
                for candidate in position.get("candidates") or []:
                    name = candidate.get("candidate_name", "—")
                    entries.append(
                        (f"{name} ({position_name})", float(candidate.get("vote_count") or 0))
                    )

            for house in data.get("house_results") or []:
                house_name = house.get("house_name", "House")
                for position in house.get("positions") or []:
                    position_name = position.get("position_name", "Position")
                    for candidate in position.get("candidates") or []:
                        name = candidate.get("candidate_name", "—")
                        entries.append(
                            (f"{name} ({house_name} · {position_name})", float(candidate.get("vote_count") or 0))
                        )

            entries.sort(key=lambda item: item[1], reverse=True)
            return [label for label, _ in entries], [value for _, value in entries]

        def _distribution_series(data: dict[str, Any]) -> tuple[str, list[str], list[float]]:
            house_results = data.get("house_results") or []
            house_labels = [house.get("house_name", "—") for house in house_results]
            house_values = [float(house.get("vote_count") or 0) for house in house_results]
            if sum(house_values) > 0:
                return "Votes Per House", house_labels, house_values

            # Regular elections often have no house votes — show top candidates instead.
            leaders = data.get("leading_candidates") or []
            if leaders:
                return (
                    "Leading Candidates",
                    [item.get("candidate_name", "—") for item in leaders],
                    [float(item.get("vote_count") or 0) for item in leaders],
                )

            positions = data.get("regular_positions") or []
            for position in positions:
                candidates = position.get("candidates") or []
                if candidates:
                    return (
                        f"{position.get('position_name', 'Position')} Votes",
                        [item.get("candidate_name", "—") for item in candidates],
                        [float(item.get("vote_count") or 0) for item in candidates],
                    )
            return "Vote Distribution", house_labels, house_values

        def render_charts() -> None:
            data = state.get("overview") or {}
            chart_type = state["chart_type"]

            candidate_labels, candidate_values = _candidate_vote_series(data)
            candidate_bar_chart = ui_refs.get("candidate_bar_chart")
            if candidate_bar_chart is not None:
                _set_chart_options(
                    candidate_bar_chart,
                    _build_series_chart(
                        "bar",
                        candidate_labels,
                        candidate_values,
                        title="Candidate Votes",
                    ),
                )
            candidate_pie_chart = ui_refs.get("candidate_pie_chart")
            if candidate_pie_chart is not None:
                _set_chart_options(
                    candidate_pie_chart,
                    _build_series_chart(
                        "pie",
                        candidate_labels,
                        candidate_values,
                        title="Vote Share by Candidate",
                    ),
                )

            timeline = data.get("timeline") or data.get("votes_per_minute") or []
            timeline_labels = [point.get("label") or point.get("minute", "") for point in timeline]
            timeline_values = [point.get("count", 0) for point in timeline]
            # Activity charts stay cartesian; pie/doughnut fall back to bar.
            activity_type = chart_type if chart_type in {"line", "bar", "area"} else "bar"
            timeline_chart = ui_refs.get("timeline_chart")
            if timeline_chart is not None:
                _set_chart_options(
                    timeline_chart,
                    _build_series_chart(
                        activity_type,
                        timeline_labels,
                        timeline_values,
                        title="Voting Activity",
                    ),
                )

            dist_title, dist_labels, dist_values = _distribution_series(data)
            dist_title_label = ui_refs.get("distribution_title")
            if dist_title_label is not None:
                dist_title_label.set_text(dist_title)

            house_chart = ui_refs.get("house_chart")
            if house_chart is not None:
                _set_chart_options(
                    house_chart,
                    _build_series_chart(
                        chart_type,
                        dist_labels,
                        dist_values,
                        title=dist_title,
                    ),
                )

            leaders_container = ui_refs.get("leaders_container")
            if leaders_container is not None:
                leaders_container.clear()
                with leaders_container:
                    leaders = data.get("leading_candidates") or []
                    if not leaders:
                        ui.label("No leading candidates yet.").classes("text-grey-6")
                    for leader in leaders:
                        with ui.element("div").classes("emp-card q-pa-sm q-mb-sm w-full"):
                            ui.label(leader.get("position_name", "Position")).classes(
                                "text-caption text-grey-7"
                            )
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(leader.get("candidate_name", "—")).classes(
                                    "text-body1 text-weight-medium"
                                )
                                ui.label(
                                    f"{leader.get('vote_count', 0):,} ({leader.get('percentage', 0)}%)"
                                ).classes("text-body2")
                            ui.label(f"Margin: {leader.get('margin', 0)}%").classes(
                                "text-caption text-grey-6"
                            )

        def render_rankings(positions: list[dict[str, Any]]) -> None:
            container = ui_refs.get("rankings_container")
            if container is None:
                return
            container.clear()
            with container:
                if not positions:
                    ui.label("No regular election results yet.").classes("text-grey-6")
                    return
                for position in positions:
                    with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                        ui.label(position.get("position_name", "Position")).classes(
                            "text-h6 text-weight-bold q-mb-xs"
                        )
                        ui.label(f"{position.get('total_votes', 0):,} votes").classes(
                            "text-caption text-grey-7 q-mb-md"
                        )
                        candidates = position.get("candidates") or []
                        if not candidates:
                            ui.label("No data available").classes("text-caption text-grey-6")
                            continue
                        columns = [
                            {"name": "rank", "label": "Rank", "field": "rank", "align": "left"},
                            {"name": "candidate", "label": "Candidate", "field": "candidate", "align": "left"},
                            {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                            {"name": "percentage", "label": "%", "field": "percentage", "align": "right"},
                            {"name": "winner", "label": "Winner", "field": "winner", "align": "center"},
                        ]
                        rows = [
                            {
                                "rank": candidate.get("rank", "—"),
                                "candidate": candidate.get("candidate_name", "—"),
                                "votes": f"{candidate.get('vote_count', 0):,}",
                                "percentage": f"{candidate.get('percentage', 0)}%",
                                "winner": "✓" if candidate.get("is_winner") else "",
                            }
                            for candidate in candidates
                        ]
                        ui.table(columns=columns, rows=rows, row_key="rank").props("flat dense").classes(
                            "w-full"
                        )

        def render_houses(house_results: list[dict[str, Any]]) -> None:
            container = ui_refs.get("houses_container")
            if container is None:
                return
            container.clear()
            with container:
                if not house_results:
                    ui.label("No house election results yet.").classes("text-grey-6")
                    return
                for house in house_results:
                    with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                        with ui.row().classes("items-center justify-between q-mb-sm w-full"):
                            ui.label(house.get("house_name", "House")).classes("text-h6 text-weight-bold")
                            ui.label(
                                f"{house.get('vote_count', 0):,} votes · {house.get('percentage', 0)}%"
                            ).classes("text-caption text-grey-7")
                        positions = house.get("positions") or []
                        if not positions:
                            ui.label("No positions for this house yet.").classes("text-caption text-grey-6")
                            continue
                        for position in positions:
                            ui.label(position.get("position_name", "Position")).classes(
                                "text-subtitle2 q-mt-sm"
                            )
                            for candidate in position.get("candidates") or []:
                                with ui.row().classes("items-center q-gutter-sm q-mb-xs w-full"):
                                    ui.label(f"#{candidate.get('rank', '—')}").classes(
                                        "text-caption text-grey-6 col-auto"
                                    )
                                    ui.label(candidate.get("candidate_name", "—")).classes(
                                        "col-grow text-body2"
                                    )
                                    ui.label(f"{candidate.get('vote_count', 0):,}").classes("text-body2")
                                    ui.label(f"{candidate.get('percentage', 0)}%").classes(
                                        "text-caption text-grey-7"
                                    )
                                    ui.linear_progress(
                                        value=min((candidate.get("percentage") or 0) / 100, 1.0),
                                        show_value=False,
                                    ).classes("col-12")

        def render_nodes(nodes: list[dict[str, Any]]) -> None:
            container = ui_refs.get("nodes_container")
            if container is None:
                return
            container.clear()
            with container:
                node_chart = ui_refs.get("node_chart")
                if node_chart is not None:
                    labels = [node.get("node_name", "—") for node in nodes[:12]]
                    values = [node.get("vote_count", 0) for node in nodes[:12]]
                    _set_chart_options(
                        node_chart,
                        _build_series_chart("bar", labels, values, title="Node Vote Contribution"),
                    )

                if not nodes:
                    ui.label("No node performance data yet.").classes("text-grey-6")
                    return

                columns = [
                    {"name": "node", "label": "Node", "field": "node", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "left"},
                    {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                    {"name": "share", "label": "Share", "field": "share", "align": "right"},
                    {"name": "status", "label": "Status", "field": "status", "align": "left"},
                    {"name": "rate", "label": "Votes/hr", "field": "rate", "align": "right"},
                ]
                rows = [
                    {
                        "node": node.get("node_name", "—"),
                        "type": node.get("house_name") or node.get("election_type", "—"),
                        "votes": f"{node.get('vote_count', 0):,}",
                        "share": f"{node.get('contribution_percentage', 0)}%",
                        "status": node.get("status", "—"),
                        "rate": "—" if node.get("votes_per_hour") is None else f"{node.get('votes_per_hour')}",
                    }
                    for node in nodes
                ]
                ui.table(columns=columns, rows=rows, row_key="node").props("flat dense").classes("w-full")

        def render_election_buttons() -> None:
            container = ui_refs.get("election_buttons")
            if container is None:
                return
            container.clear()
            with container:
                if not state["elections"]:
                    ui.label("No elections available.").classes("text-caption text-grey-6")
                    return
                for election in state["elections"]:
                    election_id = election["id"]
                    label = election.get("election_name") or election.get("name", "Election")
                    status = election.get("status", "")
                    button_label = f"{label} ({status})" if status else label
                    is_selected = election_id == state["election_id"]
                    props = "unelevated color=primary" if is_selected else "outline color=primary"

                    async def select_this(eid: str = election_id) -> None:
                        state["election_id"] = eid
                        render_election_buttons()
                        await refresh_data()

                    ui.button(
                        button_label,
                        on_click=lambda fn=select_this: ui.timer(0, fn, once=True),
                    ).props(props)

        def render_chart_type_buttons() -> None:
            container = ui_refs.get("chart_type_buttons")
            if container is None:
                return
            container.clear()
            with container:
                for value, label in CHART_TYPES:
                    is_selected = value == state["chart_type"]
                    props = "unelevated color=primary" if is_selected else "outline color=primary"

                    def select_type(selected: str = value) -> None:
                        state["chart_type"] = selected
                        render_chart_type_buttons()
                        if state.get("overview") is not None:
                            render_charts()
                        ui.notify(f"Chart type: {label}", type="info")

                    ui.button(label, on_click=select_type).props(props)

        async def refresh_data() -> None:
            success, message, data = await AnalyticsService.get_overview(
                state["election_id"] or None,
            )
            if success and data:
                apply_overview(data)
                return
            subtitle = ui_refs.get("subtitle")
            if subtitle is not None:
                subtitle.set_text(message or "Unable to load analytics")
            ui.notify(message or "Could not load analytics", type="negative")

        async def load_elections() -> None:
            success, message, elections = await ElectionService.list_elections()
            if not success:
                ui.notify(message or "Could not load elections", type="negative")
                render_election_buttons()
                render_chart_type_buttons()
                await refresh_data()
                return
            state["elections"] = elections
            valid_ids = {item["id"] for item in elections}
            if not state["election_id"] or state["election_id"] not in valid_ids:
                state["election_id"] = _pick_default_election(elections)
            render_election_buttons()
            render_chart_type_buttons()
            await refresh_data()

        with admin_shell("/analytics") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-md w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Analytics").classes("emp-page-title")
                        ui_refs["subtitle"] = ui.label("Loading…").classes("emp-page-subtitle")
                    ui.button(
                        "Refresh",
                        icon="refresh",
                        on_click=lambda: ui.timer(0, refresh_data, once=True),
                    ).props("outline")

                if not AuthService.has_backend_token():
                    ui.label(
                        "No backend API token in session. Connect to the API with valid credentials "
                        "to load analytics."
                    ).classes("text-warning text-caption q-mb-md")

                ui.label("Election").classes("text-caption text-grey-7 q-mb-xs")
                ui_refs["election_buttons"] = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

                ui.label("Chart type").classes("text-caption text-grey-7 q-mb-xs")
                ui_refs["chart_type_buttons"] = ui.row().classes("w-full q-gutter-sm q-mb-md flex-wrap")

                with ui.row().classes("w-full q-col-gutter-md q-mb-md"):
                    for key, label, icon, color in [
                        ("election", "Election", "event", "primary"),
                        ("status", "Status", "fiber_manual_record", "positive"),
                        ("votes", "Total Votes", "how_to_vote", "primary"),
                        ("regular", "Regular Votes", "how_to_vote", "info"),
                        ("house", "House Votes", "home", "info"),
                        ("turnout", "Turnout", "groups", "warning"),
                        ("nodes", "Nodes Online", "devices", "positive"),
                    ]:
                        with ui.column().classes("col-12 col-sm-6 col-md-4 col-lg-3"):
                            with ui.element("div").classes("emp-stat-card h-full"):
                                with ui.row().classes("items-center justify-between q-mb-sm"):
                                    ui.label(label).classes("emp-stat-label")
                                    ui.icon(icon, size="sm").classes(f"text-{color}")
                                ui_refs[f"stat_{key}"] = ui.label("—").classes("emp-stat-value")

                tabs = ui.tabs().classes("w-full")
                with tabs:
                    for tab_name in TABS:
                        ui.tab(tab_name)

                panels = ui.tab_panels(tabs, value=OVERVIEW_TAB).classes("w-full q-mt-md")
                with panels:
                    with ui.tab_panel(OVERVIEW_TAB):
                        with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                            ui.label("Candidate Votes").classes("text-weight-bold q-mb-sm")
                            with ui.row().classes("w-full q-col-gutter-md"):
                                with ui.column().classes("col-12 col-md-8"):
                                    ui_refs["candidate_bar_chart"] = ui.echart(
                                        {
                                            "xAxis": {"type": "category", "data": []},
                                            "yAxis": {"type": "value"},
                                            "series": [],
                                        }
                                    ).classes("w-full").style("height: 360px")
                                with ui.column().classes("col-12 col-md-4"):
                                    ui_refs["candidate_pie_chart"] = ui.echart(
                                        {
                                            "series": [{"type": "pie", "data": []}],
                                        }
                                    ).classes("w-full").style("height: 360px")

                        with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                            ui.label("Voting Activity").classes("text-weight-bold q-mb-sm")
                            ui_refs["timeline_chart"] = ui.echart(
                                {"xAxis": {"type": "category", "data": []}, "yAxis": {"type": "value"}, "series": []}
                            ).classes("w-full").style("height: 320px")

                        with ui.row().classes("w-full q-col-gutter-md"):
                            with ui.column().classes("col-12 col-md-4"):
                                with ui.element("div").classes("emp-card q-pa-md h-full"):
                                    ui.label("Current Leaders").classes("text-weight-bold q-mb-md")
                                    ui_refs["leaders_container"] = ui.column().classes("w-full")
                            with ui.column().classes("col-12 col-md-8"):
                                with ui.element("div").classes("emp-card q-pa-md h-full"):
                                    ui_refs["distribution_title"] = ui.label("Vote Distribution").classes(
                                        "text-weight-bold q-mb-sm"
                                    )
                                    ui_refs["house_chart"] = ui.echart(
                                        {
                                            "xAxis": {"type": "category", "data": []},
                                            "yAxis": {"type": "value"},
                                            "series": [],
                                        }
                                    ).classes("w-full").style("height: 320px")

                    with ui.tab_panel(RANKINGS_TAB):
                        ui_refs["rankings_container"] = ui.column().classes("w-full")

                    with ui.tab_panel(HOUSES_TAB):
                        ui_refs["houses_container"] = ui.column().classes("w-full")

                    with ui.tab_panel(NODES_TAB):
                        with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                            ui.label("Node Contribution").classes("text-weight-bold q-mb-md")
                            ui_refs["node_chart"] = ui.echart(
                                {"xAxis": {"type": "category", "data": []}, "yAxis": {"type": "value"}, "series": []}
                            ).classes("w-full").style("height: 280px")
                        ui_refs["nodes_container"] = ui.column().classes("w-full")

                ui.timer(10.0, refresh_data)

        await load_elections()
