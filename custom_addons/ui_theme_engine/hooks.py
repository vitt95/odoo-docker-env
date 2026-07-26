from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    """Activate the Premium skin on install.

    `res.users.pui_skin` defaults to 'premium', which covers users created
    after the install. Users that already existed keep whatever the column
    default wrote at column-creation time, and on an upgrade from an older
    version of this module they are still on 'classic'. Flip every internal
    user explicitly so that installing the theme means the theme is on.

    Portal / public users (share = True) are skipped: they never reach the
    backend web client, and the login screen has its own instance-level
    setting (`pui.login_skin`).
    """
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    internal_users = env["res.users"].with_context(active_test=False).search(
        [("share", "=", False)]
    )
    internal_users.write({"pui_skin": "premium"})
