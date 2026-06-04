/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class HospitalThemeActionCard extends Component {
    static template = "hospital_management_theme_owl.ActionCard";
    static props = {
        item: Object,
        onSelect: Function,
    };

    select() {
        if (this.props.onSelect) {
            this.props.onSelect(this.props.item);
        }
    }
}

export class HospitalThemeQuickPanel extends Component {
    static template = "hospital_management_theme_owl.QuickPanel";
    static components = { HospitalThemeActionCard };
    static props = {};

    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            open: false,
            compact: window.localStorage.getItem("hmo_quick_panel_compact") === "1",
        });
        this.quickActions = [
            { title: "Patients", subtitle: "Registration and EMR", icon: "fa fa-users", tone: "primary", action: "base_hospital_management.res_partner_action" },
            { title: "Appointments", subtitle: "Slots and queue", icon: "fa fa-calendar-check-o", tone: "info", action: "base_hospital_management.hospital_appointment_action" },
            { title: "OPD", subtitle: "Consultation visits", icon: "fa fa-stethoscope", tone: "success", action: "base_hospital_management.hospital_outpatient_action" },
            { title: "IPD", subtitle: "Admission workflow", icon: "fa fa-bed", tone: "warning", action: "base_hospital_management.hospital_inpatient_action" },
            { title: "Laboratory", subtitle: "Patient tests", icon: "fa fa-flask", tone: "primary", action: "base_hospital_management.patient_lab_test_action" },
            { title: "Pharmacy", subtitle: "Sales and inventory", icon: "fa fa-medkit", tone: "success", action: "base_hospital_management.hospital_pharmacy_action" },
            { title: "Emergency", subtitle: "Triage cases", icon: "fa fa-ambulance", tone: "danger", action: "base_hospital_management.hospital_emergency_case_action" },
            { title: "AI Log", subtitle: "Governance review", icon: "fa fa-shield", tone: "info", action: "base_hospital_management.hospital_ai_suggestion_action" },
        ];
    }

    toggleOpen() {
        this.state.open = !this.state.open;
    }

    toggleCompact() {
        this.state.compact = !this.state.compact;
        window.localStorage.setItem("hmo_quick_panel_compact", this.state.compact ? "1" : "0");
    }

    async openQuickAction(item) {
        try {
            await this.action.doAction(item.action);
            this.state.open = false;
        } catch (error) {
            console.warn("Hospital theme quick action failed", item.action, error);
            this.notification.add(`Could not open ${item.title}. Check access rights or whether the base action exists.`, {
                type: "warning",
            });
        }
    }
}

registry.category("main_components").add("hospital_management_theme_owl.quick_panel", {
    Component: HospitalThemeQuickPanel,
});
