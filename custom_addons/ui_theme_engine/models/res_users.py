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

    pui_theme = fields.Selection(
        selection=[
            ("light", "Light"),
            ("dark", "Dark"),
        ],
        string="UI Theme",
        default="light",
        required=True,
        help="Premium color theme. Light is the reference; Dark swaps only the "
        "semantic color tokens (same layout, spacing, components). No effect on "
        "the Classic skin.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["pui_skin", "pui_theme"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["pui_skin", "pui_theme"]
