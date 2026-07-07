import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { session } from "@web/session";

/**
 * User-menu entry to switch the Premium color theme (Light <-> Dark).
 *
 * The switch is instant and reload-free: because every component reads only the
 * semantic --pui-* tokens, flipping <html data-pui-theme> swaps the whole theme
 * in one repaint. The preference is persisted asynchronously so it follows the
 * user on the next boot (where the bootstrap template stamps the attribute
 * server-side, avoiding any flash).
 *
 * Lives in the Premium bundle only, so it never appears in the Classic skin
 * (where the tokens — and therefore the theme — have no effect).
 */
const THEME_ATTR = "data-pui-theme";

function currentTheme() {
    return document.documentElement.getAttribute(THEME_ATTR) || session.pui_theme || "light";
}

function themeSwitchItem(env) {
    const isDark = currentTheme() === "dark";
    return {
        type: "item",
        id: "pui_theme_switch",
        description: isDark ? _t("Light mode") : _t("Dark mode"),
        callback: async () => {
            const next = currentTheme() === "dark" ? "light" : "dark";
            document.documentElement.setAttribute(THEME_ATTR, next);
            session.pui_theme = next;
            await env.services.orm.write("res.users", [user.userId], { pui_theme: next });
        },
        sequence: 30,
    };
}

registry.category("user_menuitems").add("pui_theme_switch", themeSwitchItem);
