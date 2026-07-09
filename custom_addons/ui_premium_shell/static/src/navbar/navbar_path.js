/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

// Premium only (this file ships in the Premium bundle). The app brand already
// anchors the dedicated path row (navbar_path.xml), so a top-level section that
// merely repeats the app name — e.g. Contacts > "Contacts", where both land on
// the app's default action — is a duplicate. Drop it so each place shows once.
patch(NavBar.prototype, {
    get currentAppSections() {
        const sections = super.currentAppSections;
        const app = this.currentApp;
        if (!app) {
            return sections;
        }
        return sections.filter((section) => section.name !== app.name);
    },
    // Preserve the native dummy setter (Enterprise/Website patches assign to it).
    set currentAppSections(_) {},
});
