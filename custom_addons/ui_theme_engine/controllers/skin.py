from odoo import http
from odoo.http import request

VALID_SKINS = ("classic", "premium")
VALID_THEMES = ("light", "dark")


class PuiSkin(http.Controller):
    """Switch the active skin by persisting the user's `pui_skin` preference.

    The preference (not a cookie) is the single source of truth: the inherited
    web.webclient_bootstrap template reads request.env.user.pui_skin at render
    time, so the choice follows the user across devices and sessions.
    """

    @http.route("/pui/skin/<string:skin>", type="http", auth="user")
    def set_skin(self, skin, redirect=None, **kw):
        user = request.env.user
        if not user._is_public():
            if skin == "toggle":
                skin = "classic" if user.pui_skin == "premium" else "premium"
            if skin in VALID_SKINS:
                user.sudo().pui_skin = skin
        return request.redirect(redirect or "/odoo")

    @http.route("/pui/theme/<string:theme>", type="http", auth="user")
    def set_theme(self, theme, redirect=None, **kw):
        """Switch the Premium color theme (light/dark).

        Persisted on res.users.pui_theme; the bootstrap template stamps it on
        <html data-pui-theme=...> at render time, so the swap is a pure token
        change (no component rebuild) and follows the user across sessions.
        """
        user = request.env.user
        if not user._is_public():
            if theme == "toggle":
                theme = "light" if user.pui_theme == "dark" else "dark"
            if theme in VALID_THEMES:
                user.sudo().pui_theme = theme
        return request.redirect(redirect or "/odoo")
