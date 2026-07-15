"""Analytics page with rankings, turnout, charts, and house statistics."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from app.components.layout import admin_shell
from app.dependencies.auth import require_auth
from app.services.analytics_service import AnalyticsService
from app.theme import apply_saved_theme, inject_theme

OVERVIEW_TAB = "Overview"
RANKINGS_TAB = "Rankings"
HOUSES_TAB = "Houses"
NODES_TAB = "Nodes"
TABS = (OVERVIEW_TAB, RANKINGS_TAB, HOUSES_TAB, NODES_TAB)

CHART_TYPES = {
    "line": "Line",
    "bar": "Bar",
    "area": "Area",
    "pie": "Pie",
    "doughnut": "Doughnut",
}


def _format_turnout(turnout: dict[str, Any] | None) -> str:
    if not turnout:
        return "—"
    percentage = turnout.get("turnout_percentage")
    if percentage is None:
        participants = turnout.get("estimated_participants", 0)
        return f"{participants:,} voters"
    return f"{percentage}%"


def _build_series_chart(
  chart_type: str,
  labels: list[str],
  values: list[int | float],
  *,
  title: str,
) -> dict[str, Any]:
    if chart_type in {"pie", "doughnut"}:
        return {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [
                {
                    "type": "pie",
                    "radius": ["40%", "70%"] if chart_type == "doughnut" else "60%",
                    "data": [{"name": label, "value": value} for label, value in zip(labels, values)],
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

    series_type = "line" if chart_type == "line" else "bar"
    area_style = {} if chart_type != "area" else {}
    if chart_type == "area":
        series_type = "line"

    return {
        "title": {"text": title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": labels},
        "yAxis": {"type": "value"},
        "series": [
            {
                "type": series_type,
                "data": values,
                "smooth": True,
                "areaStyle": area_style if chart_type == "area" else None,
            }
        ],
    }


def register_analytics_routes() -> None:
    """Register the analytics page."""

    @ui.page("/analytics")
    @require_auth
    async def analytics_page() -> None:
        inject_theme()
        apply_saved_theme()

        state: dict[str, Any] = {"overview": None, "chart_type": "line"}
        ui_refs: dict[str, Any] = {}

        def apply_overview(data: dict[str, Any]) -> None:
            state["overview"] = data
            summary = data.get("summary", {})

            stat_values = {
                "election": summary.get("election_name", "—"),
                "status": summary.get("election_status", "—"),
                "votes": f"{summary.get('total_votes', 0):,}",
                "regular": f"{summary.get('regular_votes', 0):,}",
                "house": f"{summary.get('house_votes', 0):,}",
                "turnout": _format_turnout(summary.get("turnout")),
                "nodes": f"{summary.get('online_nodes', 0)} / {summary.get('total_nodes', 0)}",
            }
            for key, value in stat_values.items():
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

            _render_overview_charts(data)
            _render_rankings(data.get("regular_positions", []))
            _render_houses(data.get("house_results", []))
            _render_nodes(data.get("node_statistics", []))

        def _render_overview_charts(data: dict[str, Any]) -> None:
            timeline = data.get("timeline") or data.get("votes_per_minute", [])
            labels = [point.get("label") or point.get("minute", "") for point in timeline]
            values = [point.get("count", 0) for point in timeline]

            timeline_chart = ui_refs.get("timeline_chart")
            if timeline_chart is not None and labels:
                timeline_chart.options = _build_series_chart(
                    state["chart_type"] if state["chart_type"] not in {"pie", "doughnut"} else "line",
                    labels,
                    values,
                    title="Voting Activity",
                )
                timeline_chart.update()

            house_results = data.get("house_results", [])
            house_labels = [house.get("house_name", "—") for house in house_results]
            house_values = [house.get("vote_count", 0) for house in house_results]
            house_chart = ui_refs.get("house_chart")
            if house_chart is not None:
                chart_type = state["chart_type"] if state["chart_type"] in {"pie", "doughnut", "bar"} else "pie"
                house_chart.options = _build_series_chart(
                    chart_type,
                    house_labels,
                    house_values,
                    title="Votes Per House",
                )
                house_chart.update()

            leaders_container = ui_refs.get("leaders_container")
            if leaders_container is not None:
                leaders_container.clear()
                with leaders_container:
                    for leader in data.get("leading_candidates", []):
                        with ui.element("div").classes("emp-card q-pa-sm q-mb-sm w-full"):
                            ui.label(leader.get("position_name", "Position")).classes("text-caption text-grey-7")
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(leader.get("candidate_name", "—")).classes("text-body1 text-weight-medium")
                                ui.label(f"{leader.get('vote_count', 0):,} ({leader.get('percentage', 0)}%)").classes(
                                    "text-body2"
                                )
                            ui.label(f"Margin: {leader.get('margin', 0)}%").classes("text-caption text-grey-6")

        def _render_rankings(positions: list[dict[str, Any]]) -> None:
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
                        ui.label(position.get("position_name", "Position")).classes("text-h6 text-weight-bold q-mb-xs")
                        ui.label(f"{position.get('total_votes', 0):,} votes").classes("text-caption text-grey-7 q-mb-md")
                        columns = [
                            {"name": "rank", "label": "Rank", "field": "rank", "align": "left"},
                            {"name": "candidate", "label": "Candidate", "field": "candidate", "align": "left"},
                            {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                            {"name": "percentage", "label": "%", "field": "percentage", "align": "right"},
                            {"name": "winner", "label": "Winner", "field": "winner", "align": "center"},
                        ]
                        rows = []
                        for candidate in position.get("candidates", []):
                            rows.append(
                                {
                                    "rank": candidate.get("rank", "—"),
                                    "candidate": candidate.get("candidate_name", "—"),
                                    "votes": f"{candidate.get('vote_count', 0):,}",
                                    "percentage": f"{candidate.get('percentage', 0)}%",
                                    "winner": "✓" if candidate.get("is_winner") else "",
                                }
                            )
                        ui.table(columns=columns, rows=rows, row_key="rank").props("flat dense").classes("w-full")

        def _render_houses(house_results: list[dict[str, Any]]) -> None:
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
                        for position in house.get("positions", []):
                            ui.label(position.get("position_name", "Position")).classes("text-subtitle2 q-mt-sm")
                            for candidate in position.get("candidates", []):
                                with ui.row().classes("items-center q-gutter-sm q-mb-xs w-full"):
                                    ui.label(f"#{candidate.get('rank', '—')}").classes("text-caption text-grey-6 col-auto")
                                    ui.label(candidate.get("candidate_name", "—")).classes("col-grow text-body2")
                                    ui.label(f"{candidate.get('vote_count', 0):,}").classes("text-body2")
                                    ui.label(f"{candidate.get('percentage', 0)}%").classes("text-caption text-grey-7")
                                    ui.linear_progress(
                                        value=min(candidate.get("percentage", 0) / 100, 1.0),
                                        show_value=False,
                                    ).classes("col-12")

        def _render_nodes(nodes: list[dict[str, Any]]) -> None:
            container = ui_refs.get("nodes_container")
            if container is None:
                return
            container.clear()
            with container:
                if not nodes:
                    ui.label("No node performance data yet.").classes("text-grey-6")
                    return

                node_chart = ui_refs.get("node_chart")
                if node_chart is not None:
                    labels = [node.get("node_name", "—") for node in nodes[:12]]
                    values = [node.get("vote_count", 0) for node in nodes[:12]]
                    node_chart.options = _build_series_chart(
                        "bar",
                        labels,
                        values,
                        title="Node Vote Contribution",
                    )
                    node_chart.update()

                columns = [
                    {"name": "node", "label": "Node", "field": "node", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "left"},
                    {"name": "votes", "label": "Votes", "field": "votes", "align": "right"},
                    {"name": "share", "label": "Share", "field": "share", "align": "right"},
                    {"name": "status", "label": "Status", "field": "status", "align": "left"},
                    {"name": "rate", "label": "Votes/hr", "field": "rate", "align": "right"},
                ]
                rows = []
                for node in nodes:
                    rate = node.get("votes_per_hour")
                    rows.append(
                        {
                            "node": node.get("node_name", "—"),
                            "type": node.get("house_name") or node.get("election_type", "—"),
                            "votes": f"{node.get('vote_count', 0):,}",
                            "share": f"{node.get('contribution_percentage', 0)}%",
                            "status": node.get("status", "—"),
                            "rate": "—" if rate is None else f"{rate}",
                        }
                    )
                ui.table(columns=columns, rows=rows, row_key="node").props("flat dense").classes("w-full")

        async def on_chart_type_change(event) -> None:
            state["chart_type"] = event.value
            if state.get("overview"):
                apply_overview(state["overview"])

        async def refresh_data() -> None:
            data = await AnalyticsService.get_overview()
            if data:
                apply_overview(data)

        with admin_shell("/analytics") as content:
            with content:
                with ui.row().classes("items-center justify-between q-mb-lg w-full"):
                    with ui.column().classes("gap-0"):
                        ui.label("Analytics").classes("emp-page-title")
                        ui_refs["subtitle"] = ui.label("Loading…").classes("emp-page-subtitle")
                    with ui.row().classes("items-center q-gutter-sm"):
                        ui.select(
                            CHART_TYPES,
                            value="line",
                            label="Chart type",
                            on_change=on_chart_type_change,
                        ).props("outlined dense").classes("w-40")
                        ui.button("Refresh", icon="refresh", on_click=refresh_data).props("outline")

                stat_defs = [
                    ("election", "Election", "event", "primary"),
                    ("status", "Status", "fiber_manual_record", "positive"),
                    ("votes", "Total Votes", "how_to_vote", "primary"),
                    ("regular", "Regular Votes", "how_to_vote", "info"),
                    ("house", "House Votes", "home", "info"),
                    ("turnout", "Turnout", "groups", "warning"),
                    ("nodes", "Nodes Online", "devices", "positive"),
                ]
                with ui.row().classes("w-full q-col-gutter-md q-mb-md"):
                    for key, label, icon, color in stat_defs:
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
                        with ui.row().classes("w-full q-col-gutter-md"):
                            with ui.column().classes("col-12 col-lg-8"):
                                with ui.element("div").classes("emp-card q-pa-md"):
                                    ui.label("Voting Activity").classes("text-weight-bold q-mb-md")
                                    ui_refs["timeline_chart"] = ui.echart({}).classes("w-full").style("height: 320px")
                            with ui.column().classes("col-12 col-lg-4"):
                                with ui.element("div").classes("emp-card q-pa-md"):
                                    ui.label("Current Leaders").classes("text-weight-bold q-mb-md")
                                    ui_refs["leaders_container"] = ui.column().classes("w-full")
                        with ui.row().classes("w-full q-col-gutter-md q-mt-md"):
                            with ui.column().classes("col-12"):
                                with ui.element("div").classes("emp-card q-pa-md"):
                                    ui.label("House Vote Distribution").classes("text-weight-bold q-mb-md")
                                    ui_refs["house_chart"] = ui.echart({}).classes("w-full").style("height: 300px")

                    with ui.tab_panel(RANKINGS_TAB):
                        ui_refs["rankings_container"] = ui.column().classes("w-full")

                    with ui.tab_panel(HOUSES_TAB):
                        ui_refs["houses_container"] = ui.column().classes("w-full")

                    with ui.tab_panel(NODES_TAB):
                        with ui.element("div").classes("emp-card q-pa-md q-mb-md w-full"):
                            ui.label("Node Contribution").classes("text-weight-bold q-mb-md")
                            ui_refs["node_chart"] = ui.echart({}).classes("w-full").style("height: 280px")
                        ui_refs["nodes_container"] = ui.column().classes("w-full")

        await refresh_data()
