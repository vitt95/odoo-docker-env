import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";

/**
 * User-menu entry to switch between the Classic and Premium skins.
 *
 * Lives in web.assets_backend (both skins) so the switch is reachable from
 * Classic — the single, deliberate functional addition to the Classic bundle.
 * It only registers a menu item; it adds no styles and patches no core.
 */
function skinSwitchItem(env) {
    const isPremium = session.pui_skin === "premium";
    return {
        type: "item",
        id: "pui_skin_switch",
        description: isPremium ? _t("Switch to Classic UI") : _t("Switch to Premium UI"),
        callback: () => {
            browser.location.href = "/pui/skin/toggle";
        },
        sequence: 35,
    };
}

registry.category("user_menuitems").add("pui_skin_switch", skinSwitchItem);
