# Premium UI Theme

Backend theme for Odoo 18 Community. A complete re-skin of the web client:
design tokens, component library, app shell (sidebar, navbar, dashboard) and
redesigned views. No business logic is modified.

## Install

The theme is one installable app. Copy the three modules into your addons path
and install **Premium UI Theme** (`ui_theme_engine`) — it pulls in the other two
as dependencies:

| Module             | Role                                                        |
| ------------------ | ----------------------------------------------------------- |
| `ui_theme_engine`  | Entry point: skin switch, asset bundles, login screen        |
| `ui_brand_tokens`  | Design tokens (`--pui-*` CSS variables, `$o-*` overrides)    |
| `ui_premium_shell` | Structural components + component/view styles (OWL + SCSS)   |

From the UI: *Apps* → update the app list → search **Premium UI Theme** →
*Install*.

From the CLI:

```bash
odoo-bin -c odoo.conf -d <db> -i ui_theme_engine --stop-after-init
```

Installing activates the Premium skin for all internal users (`post_init_hook`),
and new users get it from the `res.users.pui_skin` default.

## Using it

- **Skin** — user menu → *Skin: Classic / Premium*. Per user, stored on
  `res.users.pui_skin`, so it follows the user across devices. Classic is the
  untouched native Odoo interface.
- **Light / Dark** — user menu (Premium only). Stored on `res.users.pui_theme`,
  applied as `<html data-pui-theme="light|dark">` at render time, so there is no
  flash on first paint. Premium owns its theming and does not use Odoo's
  `web.assets_web_dark` bundle.
- **Login screen** — pre-auth, so there is no user preference to read. Set the
  system parameter `pui.login_skin` to `premium` or `classic`
  (*Settings → Technical → System Parameters*).

## Upgrading the styles

SCSS changes require an asset rebuild:

```bash
odoo-bin -c odoo.conf -d <db> -u ui_theme_engine --stop-after-init
```

## Uninstall

Uninstalling `ui_theme_engine` removes the skin fields, the bundle wiring and
the login override; the database returns to the stock Odoo interface.

## Compatibility

Odoo 18.0 Community. License LGPL-3.
