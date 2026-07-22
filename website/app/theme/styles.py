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
        <link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo+Black&family=Bebas+Neue&family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=Lato:wght@400;700&family=Libre+Baskerville:wght@400;700&family=Lora:wght@400;600;700&family=Merriweather:wght@400;700&family=Montserrat:wght@400;500;600;700&family=Nunito+Sans:wght@400;600;700&family=Nunito:wght@400;600;700&family=Open+Sans:wght@400;500;600;700&family=Oswald:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&family=PT+Serif:wght@400;700&family=Playfair+Display:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&family=Raleway:wght@400;500;600;700&family=Roboto:wght@400;500;700&family=Source+Sans+3:wght@400;500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
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
            color: var(--emp-text) !important;
            border-bottom: 1px solid var(--emp-border);
            box-shadow: var(--emp-shadow);
            height: var(--emp-header-height);
        }}

        .emp-header .text-grey-7 {{
            color: var(--emp-text-muted) !important;
        }}

        .emp-header .q-btn {{
            color: var(--emp-text) !important;
        }}

        .emp-sidebar {{
            background: linear-gradient(180deg, {SECONDARY} 0%, #152a45 70%, #c45a1a 100%) !important;
            color: #fff !important;
        }}

        .emp-sidebar.q-drawer,
        .emp-sidebar .q-drawer__content {{
            background: transparent !important;
            color: #fff !important;
        }}

        .emp-sidebar.q-drawer {{
            background: linear-gradient(180deg, {SECONDARY} 0%, #152a45 70%, #c45a1a 100%) !important;
        }}

        .emp-sidebar .q-drawer__content {{
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
            background: transparent !important;
        }}

        .emp-sidebar-inner {{
            display: flex;
            flex-direction: column;
            flex: 1 1 auto;
            height: 100%;
            min-height: 0;
            overflow: hidden;
            background: transparent;
        }}

        .emp-sidebar-nav {{
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 0.25rem 0.5rem 0.75rem;
        }}

        .emp-sidebar-nav::-webkit-scrollbar {{
            width: 6px;
        }}

        .emp-sidebar-nav::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.25);
            border-radius: 999px;
        }}

        .emp-sidebar-link {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            width: 100%;
            padding: 0.55rem 0.85rem;
            margin: 2px 0;
            border-radius: 8px;
            color: rgba(255, 255, 255, 0.88) !important;
            text-decoration: none !important;
            line-height: 1.25;
            transition: background 0.15s ease;
        }}

        .emp-sidebar-link:hover {{
            background: rgba(255, 255, 255, 0.12) !important;
            color: #fff !important;
        }}

        .emp-sidebar-link.is-active {{
            background: rgba(255, 255, 255, 0.16) !important;
            color: #fff !important;
            font-weight: 600;
        }}

        .emp-sidebar-link .material-icons {{
            flex: 0 0 auto;
            font-size: 1.15rem;
            opacity: 0.95;
        }}

        .emp-sidebar-link-label {{
            flex: 1 1 auto;
            min-width: 0;
            white-space: normal;
            word-break: break-word;
        }}

        .emp-sidebar-footer {{
            flex: 0 0 auto;
            border-top: 1px solid rgba(255, 255, 255, 0.15);
            padding: 0.85rem 1rem 1rem;
            background: transparent;
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

        .emp-font-option-selected {{
            background: color-mix(in srgb, var(--emp-primary) 14%, transparent) !important;
            color: var(--emp-primary) !important;
        }}

        .emp-font-preview {{
            color: var(--emp-text);
            line-height: 1.3;
        }}
        """,
        shared=True,
    )


def apply_saved_theme() -> None:
    """Restore dark/light preference from user storage (one dark_mode per page)."""
    from nicegui import app

    value = bool(app.storage.user.get("dark_mode", False))
    dark = ui.dark_mode(value)
    ui.context.client._emp_dark_mode = dark  # type: ignore[attr-defined]


def set_dark_mode(enabled: bool) -> None:
    """Apply dark mode immediately and persist the preference."""
    from nicegui import app

    app.storage.user["dark_mode"] = enabled
    dark = getattr(ui.context.client, "_emp_dark_mode", None)
    if dark is None:
        dark = ui.dark_mode(enabled)
        ui.context.client._emp_dark_mode = dark  # type: ignore[attr-defined]
    else:
        dark.value = enabled
