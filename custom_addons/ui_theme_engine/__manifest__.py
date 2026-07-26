{
    "name": "Premium UI Theme",
    "summary": "Premium backend theme for Odoo 18: skin switch (Classic/Premium), "
    "Light/Dark themes, redesigned shell and views.",
    "description": """
Premium UI Theme
================

A complete backend re-skin of Odoo 18. Installing this module installs the whole
theme: design tokens, component library, app shell (sidebar, navbar, dashboard)
and redesigned views.

* **Non destructive** — the native Classic skin stays available. Every user can
  switch back from the user menu at any time (*Skin: Classic / Premium*).
* **Light & Dark** — Premium ships its own token-driven Light/Dark themes,
  toggled instantly from the user menu.
* **No business logic touched** — styling, tokens and additive OWL components
  only.

Installing this module pulls in *UI Brand Tokens* and *UI Premium Shell*, and
activates the Premium skin for all internal users.
""",
    "version": "18.0.1.0.0",
    "category": "Themes/Backend",
    "author": "Vittorio Aiello",
    "license": "LGPL-3",
    "depends": ["web", "ui_brand_tokens", "ui_premium_shell"],
    # Installing the theme must actually apply the theme: switch existing
    # internal users over to the Premium skin (new users get it via the field
    # default on res.users).
    "post_init_hook": "post_init_hook",
    "images": ["static/description/banner.png"],
    "data": [
        "data/ir_config_parameter.xml",
        "views/webclient_bootstrap.xml",
        "views/login.xml",
    ],
    "assets": {
        # Skin-switch user-menu item: shared by both skins so Classic can
        # reach the switch. Registers a menu item only (no CSS, no core patch).
        "web.assets_backend": [
            "ui_theme_engine/static/src/skin_switch/skin_switch_item.js",
        ],
        # Frontend (pre-auth) bundle: Premium tokens + login styles for the
        # login pilot. Palette/tokens emit inert --pui-* custom properties;
        # login styles are scoped under .pui-login. No $o-* core map here, so
        # the rest of the frontend (portal/website) stays Classic.
        "web.assets_frontend": [
            "ui_brand_tokens/static/src/scss/pui_palette.scss",
            "ui_brand_tokens/static/src/scss/pui_tokens.premium.scss",
            "ui_theme_engine/static/src/login/login.premium.scss",
        ],
        # Premium skin bundle. Mirrors the native dark-mode pattern
        # (web.assets_web_dark = include web.assets_web + *.dark.scss):
        # rebuild the full web bundle, prepend the palette + $o-* overrides
        # before core primary_variables, then append Premium tokens and SCSS.
        "ui_theme_engine.assets_web_premium": [
            ("include", "web.assets_web"),
            (
                "before",
                "web/static/src/scss/primary_variables.scss",
                "ui_brand_tokens/static/src/scss/pui_palette.scss",
            ),
            (
                "before",
                "web/static/src/scss/primary_variables.scss",
                "ui_brand_tokens/static/src/scss/pui_core_map.premium.scss",
            ),
            "ui_brand_tokens/static/src/scss/pui_tokens.premium.scss",
            "ui_theme_engine/static/src/scss/engine.premium.scss",
            # Premium-only user-menu entry: instant Light/Dark theme toggle
            # (flips <html data-pui-theme>, persists async). Premium bundle only,
            # so it never shows in Classic where the theme has no effect.
            "ui_theme_engine/static/src/theme_switch/theme_switch_item.js",
            # Component library: restyles shared Bootstrap/Odoo primitives via
            # --pui-* so every button/input/dropdown/dialog/badge/card/toast in
            # the Premium skin is coherent. Loads after tokens, after core.
            "ui_premium_shell/static/src/components/buttons.premium.scss",
            "ui_premium_shell/static/src/components/forms.premium.scss",
            "ui_premium_shell/static/src/components/dropdown.premium.scss",
            "ui_premium_shell/static/src/components/dialog.premium.scss",
            "ui_premium_shell/static/src/components/badge.premium.scss",
            "ui_premium_shell/static/src/components/card.premium.scss",
            "ui_premium_shell/static/src/components/notification.premium.scss",
            "ui_premium_shell/static/src/components/empty_state.premium.scss",
            "ui_premium_shell/static/src/components/wysiwyg.premium.scss",
            # Motion system: reusable keyframes + subtle entrances + the
            # prefers-reduced-motion accessibility guard.
            "ui_premium_shell/static/src/scss/motion.premium.scss",
            "ui_premium_shell/static/src/scss/shell.premium.scss",
            # Navbar: additive centered command-palette search launcher (systray
            # item) + top-bar restyle. Native navbar/systray left fully intact.
            "ui_premium_shell/static/src/navbar/nav_search.js",
            "ui_premium_shell/static/src/navbar/nav_search.xml",
            "ui_premium_shell/static/src/navbar/navbar_path.js",
            "ui_premium_shell/static/src/navbar/navbar_path.xml",
            "ui_premium_shell/static/src/navbar/navbar.premium.scss",
            # Premium App Sidebar (new structural component). JS + OWL template
            # + styles, all Premium-only so registering it in main_components is
            # automatically skin-gated (Classic never loads it).
            "ui_premium_shell/static/src/sidebar/sidebar.js",
            "ui_premium_shell/static/src/sidebar/sidebar.xml",
            "ui_premium_shell/static/src/sidebar/sidebar.scss",
            # Premium Dashboard (client action home screen).
            "ui_premium_shell/static/src/dashboard/dashboard.js",
            "ui_premium_shell/static/src/dashboard/dashboard.xml",
            "ui_premium_shell/static/src/dashboard/dashboard.scss",
            # View redesigns (token-driven, no DOM changes).
            "ui_premium_shell/static/src/views/control_panel.premium.scss",
            "ui_premium_shell/static/src/views/form.premium.scss",
            "ui_premium_shell/static/src/views/list.premium.scss",
            "ui_premium_shell/static/src/views/kanban.premium.scss",
            "ui_premium_shell/static/src/views/calendar.premium.scss",
            "ui_premium_shell/static/src/views/chatter.premium.scss",
            "ui_premium_shell/static/src/views/settings.premium.scss",
        ],
    },
    "installable": True,
    # Entry point of the theme: listed under Apps so it can be found and
    # installed from the UI. The two support modules (tokens, shell) stay
    # application=False and come in as dependencies.
    "application": True,
}
