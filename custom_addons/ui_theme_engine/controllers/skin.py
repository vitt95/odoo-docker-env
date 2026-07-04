from odoo import http
from odoo.http import request

VALID_SKINS = ("classic", "premium")


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
