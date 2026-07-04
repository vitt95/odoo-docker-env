from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    pui_skin = fields.Selection(
        selection=[
            ("classic", "Classic"),
            ("premium", "Premium"),
        ],
        string="UI Skin",
        default="classic",
        required=True,
        help="Active UI skin. Classic = standard Odoo UI. "
        "Premium = redesigned experience. Business logic is identical.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["pui_skin"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["pui_skin"]
