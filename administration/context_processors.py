def site_settings(request):
    """Context processor exposing dynamic site settings to all templates."""
    try:
        from administration.models import SiteSetting
        settings_dict = {s.key: s.value for s in SiteSetting.objects.all()}
    except Exception:
        settings_dict = {}

    defaults = {
        # Theme Presets & Branding
        "THEME_PRESET": "custom",
        "SITE_NAME": "Vinayaka",
        "SITE_SLOGAN": "Youth Committee",
        "HEADER_TITLE": "Vinayaka Chavithi",
        "HEADER_SUBTITLE": "Youth Committee Portal",
        "CURRENCY_SYMBOL": "₹",
        "FESTIVAL_YEAR": "2026",
        "SITE_LOGO_ICON": "bi-flower1",
        "SITE_LOGO_URL": "",

        # Global Typography & Google Fonts
        "BODY_FONT_FAMILY": "'Inter', sans-serif",
        "HEADING_FONT_FAMILY": "'Outfit', sans-serif",
        "BODY_FONT_SIZE": "0.925rem",
        "BODY_FONT_WEIGHT": "400",
        "HEADING_FONT_WEIGHT": "700",

        # Colors & Primary Theme
        "PRIMARY_COLOR": "#8b1e24",
        "PRIMARY_HOVER_BG": "#6c1419",
        "ACCENT_COLOR": "#f59e0b",
        "MAIN_BG": "#f8fafc",

        # Sidebar & Navigation
        "SIDEBAR_BG": "#0b0f19",
        "SIDEBAR_BRAND_BG": "#111827",
        "SIDEBAR_TEXT_COLOR": "#cbd5e1",
        "SIDEBAR_FONT_SIZE": "0.9rem",
        "SIDEBAR_FONT_WEIGHT": "500",
        "SIDEBAR_HOVER_BG": "rgba(255, 255, 255, 0.06)",
        "SIDEBAR_HOVER_TEXT_COLOR": "#ffffff",
        "SIDEBAR_ACTIVE_BG": "rgba(245, 158, 11, 0.14)",
        "SIDEBAR_ACTIVE_TEXT_COLOR": "#f59e0b",
        "SIDEBAR_ACTIVE_BORDER": "#f59e0b",
        "SIDEBAR_ICON_COLOR": "#94a3b8",

        # Topbar & Header
        "HEADER_BG": "#ffffff",
        "HEADER_TEXT_COLOR": "#0f172a",
        "HEADER_BORDER_COLOR": "#e2e8f0",
        "HEADER_FONT_SIZE": "1.25rem",
        "HEADER_FONT_WEIGHT": "700",

        # Containers & Layout
        "CONTAINER_MAX_WIDTH": "100%",
        "CONTAINER_PADDING": "1.5rem",

        # Cards & Div Containers
        "CARD_BG": "#ffffff",
        "CARD_HEADER_BG": "#ffffff",
        "CARD_HEADER_TEXT_COLOR": "#0f172a",
        "CARD_HEADER_FONT_SIZE": "1rem",
        "CARD_HEADER_FONT_WEIGHT": "600",
        "CARD_BORDER_COLOR": "#e2e8f0",
        "CARD_BORDER_RADIUS": "12px",
        "CARD_SHADOW": "0 4px 16px rgba(0, 0, 0, 0.03)",

        # Tables & Data Grids (th, tr, td)
        "TABLE_HEADER_BG": "#f8fafc",
        "TABLE_HEADER_TEXT_COLOR": "#475569",
        "TABLE_ROW_HOVER_BG": "#f1f5f9",
        "TABLE_BORDER_COLOR": "#e2e8f0",
        "TABLE_FONT_SIZE": "0.875rem",
        "TABLE_CELL_PADDING": "0.75rem 1rem",

        # Buttons & Interactive Actions
        "BTN_BORDER_RADIUS": "8px",
        "BTN_FONT_WEIGHT": "600",
        "BTN_HOVER_TRANSFORM": "translateY(-1px)",

        # Footer & Contact Info
        "FOOTER_BG": "#ffffff",
        "FOOTER_TEXT_COLOR": "#64748b",
        "FOOTER_LINK_COLOR": "#8b1e24",
        "CONTACT_PHONE": "+91 98765 43210",
        "CONTACT_EMAIL": "info@vinayakacommittee.org",
        "FOOTER_TEXT": "© 2026 Vinayaka Youth Committee. All Rights Reserved.",
        "FOOTER_URL": "https://vinayakacommittee.org",
        "FOOTER_URL_LABEL": "Visit Official Portal",
    }

    # Merge database settings over defaults
    merged_settings = {**defaults, **settings_dict}

    return {
        "site_settings": merged_settings,
        "SITE_NAME": merged_settings["SITE_NAME"],
        "SITE_SLOGAN": merged_settings["SITE_SLOGAN"],
        "CURRENCY_SYMBOL": merged_settings["CURRENCY_SYMBOL"],
    }
