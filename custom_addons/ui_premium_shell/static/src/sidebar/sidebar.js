import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

const COLLAPSE_KEY = "pui_sidebar_collapsed";

/**
 * Premium App Sidebar.
 *
 * A new structural component (community Odoo has no sidebar). It consumes the
 * existing menu service — it does not fork navigation logic — and navigates via
 * selectMenu, exactly like the navbar. The original navbar stays in the DOM
 * (its classes are a tour/JS contract); Premium SCSS only hides its redundant
 * apps menu and shifts the content.
 *
 * Loaded only in the Premium asset bundle, so registering it in main_components
 * is automatically skin-gated: Classic never loads this file.
 */
export class PuiSidebar extends Component {
    static template = "ui_premium_shell.PuiSidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.state = useState({
            collapsed: browser.localStorage.getItem(COLLAPSE_KEY) === "1",
        });
        // Re-render when the active app changes (keeps the highlight in sync).
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.render());
        onMounted(() => this._syncBodyClass());
        onWillUnmount(() => document.body.classList.remove("pui-has-sidebar", "pui-sidebar-collapsed"));
    }

    get apps() {
        return this.menuService.getApps();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    isActive(app) {
        const current = this.currentApp;
        return Boolean(current) && current.id === app.id;
    }

    appInitial(app) {
        return (app.name || "?").trim().charAt(0).toUpperCase();
    }

    onAppClick(app) {
        this.menuService.selectMenu(app);
    }

    openDashboard() {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "pui_dashboard",
            name: "Home",
        });
    }

    toggleCollapsed() {
        this.state.collapsed = !this.state.collapsed;
        browser.localStorage.setItem(COLLAPSE_KEY, this.state.collapsed ? "1" : "0");
        this._syncBodyClass();
    }

    _syncBodyClass() {
        // Drives the content offset in SCSS (padding-left on the web client body).
        document.body.classList.add("pui-has-sidebar");
        document.body.classList.toggle("pui-sidebar-collapsed", this.state.collapsed);
    }
}

registry.category("main_components").add("pui_sidebar", { Component: PuiSidebar });
