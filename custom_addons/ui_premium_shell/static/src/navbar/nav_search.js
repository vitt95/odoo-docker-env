import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Premium navbar search launcher.
 *
 * A centered command-palette entry point, matching the reference's global
 * search bar. It is purely additive: it opens Odoo's OWN command palette
 * (the `command` service, same thing Ctrl+K triggers) — no navigation logic is
 * forked, nothing native is removed. Registered as a systray item so it lives
 * inside the untouched native navbar; Premium CSS then centers it on wide
 * screens and collapses it to an icon on small ones.
 *
 * Premium bundle only -> never present in the Classic skin.
 */
export class PuiNavSearch extends Component {
    static template = "ui_premium_shell.PuiNavSearch";
    static props = {};

    setup() {
        this.command = useService("command");
    }

    get label() {
        return _t("Search…");
    }

    open() {
        this.command.openMainPalette();
    }
}

registry.category("systray").add("pui_nav_search", { Component: PuiNavSearch }, { sequence: 1 });
