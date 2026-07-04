import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

/**
 * Premium Dashboard — a new home screen (community Odoo has none).
 *
 * Registered as a client action ("pui_dashboard"), reachable from the sidebar
 * Home entry. It reuses the menu service for the app grid (no new navigation
 * logic) and shows only real data (user, company, apps) — no fabricated KPIs.
 * Widget slots are left as an honest empty state for later phases.
 *
 * Lives in the Premium bundle only, so its registration is skin-gated.
 */
export class PuiDashboard extends Component {
    static template = "ui_premium_shell.PuiDashboard";
    static props = ["*"];

    setup() {
        this.menuService = useService("menu");
        this.companyService = useService("company");
        this.user = user;
    }

    get apps() {
        return this.menuService.getApps();
    }

    get companyName() {
        return this.companyService.currentCompany?.name || "";
    }

    get greeting() {
        const h = new Date().getHours();
        if (h < 12) {
            return "Buongiorno";
        }
        if (h < 18) {
            return "Buon pomeriggio";
        }
        return "Buonasera";
    }

    get today() {
        const locale = (this.user.lang || "it_IT").replace("_", "-");
        try {
            return new Intl.DateTimeFormat(locale, {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric",
            }).format(new Date());
        } catch {
            return new Date().toDateString();
        }
    }

    appInitial(app) {
        return (app.name || "?").trim().charAt(0).toUpperCase();
    }

    openApp(app) {
        this.menuService.selectMenu(app);
    }
}

registry.category("actions").add("pui_dashboard", PuiDashboard);
