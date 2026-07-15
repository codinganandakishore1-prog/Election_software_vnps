"""Global theme styles injected into every page."""

from nicegui import ui

from app.theme.colors import (
    ACCENT,
    BACKGROUND,
    BORDER,
    DARK_BACKGROUND,
    DARK_BORDER,
    DARK_SURFACE,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
    DANGER,
    PRIMARY,
    SECONDARY,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)

_THEME_INJECTED = False


def inject_theme() -> None:
    """Add fonts, CSS variables, and base styles once per process."""
    global _THEME_INJECTED
    if _THEME_INJECTED:
        return
    _THEME_INJECTED = True

    ui.add_head_html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
        """,
        shared=True,
    )

    ui.add_css(
        f"""
        :root {{
            --emp-primary: {PRIMARY};
            --emp-secondary: {SECONDARY};
            --emp-accent: {ACCENT};
            --emp-warning: {WARNING};
            --emp-danger: {DANGER};
            --emp-bg: {BACKGROUND};
            --emp-surface: {SURFACE};
            --emp-text: {TEXT_PRIMARY};
            --emp-text-muted: {TEXT_SECONDARY};
            --emp-border: {BORDER};
            --emp-sidebar-width: 260px;
            --emp-header-height: 64px;
            --emp-radius: 12px;
            --emp-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
            --emp-shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.08);
            --q-primary: {PRIMARY};
        }}

        body.body--dark {{
            --emp-bg: {DARK_BACKGROUND};
            --emp-surface: {DARK_SURFACE};
            --emp-text: {DARK_TEXT_PRIMARY};
            --emp-text-muted: {DARK_TEXT_SECONDARY};
            --emp-border: {DARK_BORDER};
        }}

        body {{
            font-family: 'Inter', 'Roboto', 'Open Sans', system-ui, sans-serif !important;
            background-color: var(--emp-bg) !important;
            color: var(--emp-text) !important;
        }}

        .emp-shell {{
            min-height: 100vh;
            background-color: var(--emp-bg);
        }}

        .emp-header {{
            background: var(--emp-surface) !important;
            border-bottom: 1px solid var(--emp-border);
            box-shadow: var(--emp-shadow);
            height: var(--emp-header-height);
        }}

        .emp-sidebar {{
            background: linear-gradient(180deg, {SECONDARY} 0%, #152a45 70%, #c45a1a 100%) !important;
            color: #fff !important;
        }}

        .emp-school-logo {{
            object-fit: contain;
            border-radius: 8px;
            background: #fff;
        }}

        .emp-school-logo-header {{
            width: 36px;
            height: 36px;
        }}

        .emp-school-logo-sidebar {{
            width: 44px;
            height: 44px;
        }}

        .emp-school-logo-login {{
            width: 96px;
            height: 96px;
            border-radius: 16px;
            box-shadow: var(--emp-shadow);
        }}

        .text-primary {{
            color: var(--emp-primary) !important;
        }}

        .bg-primary {{
            background-color: var(--emp-primary) !important;
        }}

        .emp-sidebar .q-item {{
            color: rgba(255, 255, 255, 0.85);
            border-radius: 8px;
            margin: 2px 8px;
        }}

        .emp-sidebar .q-item--active,
        .emp-sidebar .q-item:hover {{
            background: rgba(255, 255, 255, 0.12) !important;
            color: #fff !important;
        }}

        .emp-main {{
            padding: 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }}

        @media (max-width: 1023px) {{
            .emp-main {{
                padding: 1rem;
            }}
        }}

        .emp-card {{
            background: var(--emp-surface);
            border: 1px solid var(--emp-border);
            border-radius: var(--emp-radius);
            box-shadow: var(--emp-shadow);
        }}

        .emp-stat-card {{
            background: var(--emp-surface);
            border: 1px solid var(--emp-border);
            border-radius: var(--emp-radius);
            padding: 1.25rem;
            box-shadow: var(--emp-shadow);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}

        .emp-stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--emp-shadow-lg);
        }}

        .emp-stat-label {{
            color: var(--emp-text-muted);
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .emp-stat-value {{
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.2;
            margin-top: 0.25rem;
        }}

        .emp-badge-live {{
            background: {ACCENT};
            color: #fff;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.04em;
        }}

        .emp-login-page {{
            min-height: 100vh;
            background: linear-gradient(135deg, {SECONDARY} 0%, {PRIMARY} 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }}

        .emp-login-card {{
            background: var(--emp-surface);
            border-radius: 16px;
            box-shadow: var(--emp-shadow-lg);
            width: 100%;
            max-width: 420px;
            padding: 2rem;
        }}

        .emp-placeholder {{
            background: var(--emp-surface);
            border: 1px dashed var(--emp-border);
            border-radius: var(--emp-radius);
            padding: 3rem 2rem;
            text-align: center;
            color: var(--emp-text-muted);
        }}

        .emp-activity-item {{
            border-left: 3px solid var(--emp-primary);
            padding-left: 1rem;
            margin-bottom: 1rem;
        }}

        .emp-page-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--emp-text);
        }}

        .emp-page-subtitle {{
            color: var(--emp-text-muted);
            font-size: 0.95rem;
        }}
        """,
        shared=True,
    )


def apply_saved_theme() -> None:
    """Restore dark/light preference from user storage."""
    from nicegui import app

    dark = app.storage.user.get("dark_mode", False)
    if dark:
        ui.dark_mode().enable()
    else:
        ui.dark_mode().disable()
