/** @odoo-module **/

import { whenReady } from "@odoo/owl";

const HOSPITAL_MODELS = [
    "hospital.appointment",
    "hospital.vitals",
    "hospital.consent",
    "hospital.emergency.case",
    "hospital.ai.suggestion",
    "hospital.inpatient",
    "hospital.insurance",
    "hospital.laboratory",
    "hospital.outpatient",
    "hospital.pharmacy",
    "hospital.vaccination",
    "hospital.ward",
    "hospital.bed",
    "hospital.building",
    "hospital.degree",
    "doctor.allocation",
    "doctor.slot",
    "doctor.specialization",
    "inpatient.surgery",
    "lab.test",
    "lab.test.line",
    "lab.test.result",
    "patient.lab.test",
    "patient.room",
    "blood.bank",
    "blood.donation",
    "medicine.brand",
    "room.facility",
    "contra.indication",
    "pharmacy.medicine",
];

function getDecodedHash() {
    try {
        return decodeURIComponent(window.location.hash || "");
    } catch (_error) {
        return window.location.hash || "";
    }
}

function hashContainsHospitalModel() {
    const hash = getDecodedHash();
    return HOSPITAL_MODELS.some((model) => hash.includes(`model=${model}`));
}

function hashLooksLikeHospitalPatientScreen() {
    const hash = getDecodedHash();
    return hash.includes("model=res.partner") && (
        hash.toLowerCase().includes("patient") ||
        document.querySelector("[name='patient_seq'], [name='patient_id'], .o_field_widget[name='patient_seq']")
    );
}

function navbarLooksHospital() {
    const brand = document.querySelector(".o_menu_brand, .o_navbar .o_menu_sections");
    return Boolean(brand && /hospital|patient|clinic/i.test(brand.textContent || ""));
}

function domContainsHospitalScreen() {
    return Boolean(document.querySelector([
        ".hm-dashboard",
        ".hm-role-dashboard",
        ".hm-reception-dashboard",
        ".hm-doctor-dashboard",
        ".hm-lab-dashboard",
        ".hm-pharmacy-dashboard",
        "[name='patient_seq']",
        "[name='appointment_date']",
        "[name='doctor_id'][data-tooltip*='Doctor']",
    ].join(",")));
}

function domContainsHospitalDashboard() {
    return Boolean(document.querySelector([
        ".hm-dashboard",
        ".hm-role-dashboard",
        ".hm-reception-dashboard",
        ".hm-doctor-dashboard",
        ".hm-lab-dashboard",
        ".hm-pharmacy-dashboard",
        ".hmo-dashboard-pulse",
    ].join(",")));
}

function updateHospitalThemeState() {
    const dashboardActive = domContainsHospitalDashboard();
    const active = hashContainsHospitalModel() || hashLooksLikeHospitalPatientScreen() || navbarLooksHospital() || domContainsHospitalScreen();
    document.body.classList.toggle("o_hmo_hospital_active", Boolean(active));
    document.body.classList.toggle("o_hmo_hospital_dashboard_active", Boolean(dashboardActive));
}

whenReady(() => {
    updateHospitalThemeState();
    window.addEventListener("hashchange", updateHospitalThemeState);

    const observer = new MutationObserver(updateHospitalThemeState);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "name"] });
});
