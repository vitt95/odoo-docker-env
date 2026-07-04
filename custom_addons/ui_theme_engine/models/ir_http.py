from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        if res.get("uid"):
            # Exposed to the client so components (and the user-menu toggle)
            # know the active skin without an extra round-trip.
            res["pui_skin"] = self.env.user.pui_skin
        return res
