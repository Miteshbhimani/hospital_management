/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

export class DoctorDashboard extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.state = useState({
            loading: true,
            active: 'queue',
            kpis: {},
            patients: [],
            queue: [],
            vitals: [],
            surgeries: [],
            painScores: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            vitalsForm: {
                patient_id: '', temperature_c: '', pulse_rate: '', respiratory_rate: '',
                systolic_bp: '', diastolic_bp: '', spo2: '', height_cm: '', weight_kg: '',
                pain_score: '0', triage_category: 'green', notes: '',
            },
        });
        onWillStart(async () => await this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call('hospital.dashboard.service', 'get_doctor_dashboard', []);
        Object.assign(this.state, {
            kpis: data.kpis || {},
            patients: data.patients || [],
            queue: data.queue || [],
            vitals: data.vitals || [],
            surgeries: data.surgeries || [],
            loading: false,
        });
    }

    setActive(ev) { this.state.active = ev.currentTarget.dataset.section; }

    updateVitals(ev) {
        const field = ev.currentTarget.dataset.field;
        this.state.vitalsForm[field] = ev.currentTarget.value;
    }

    async saveVitals() {
        const form = this.state.vitalsForm;
        if (!form.patient_id) {
            this.notification.add(_t('Select a patient before saving vitals.'), { type: 'warning' });
            return;
        }
        const floatFields = ['temperature_c', 'height_cm', 'weight_kg'];
        const intFields = ['pulse_rate', 'respiratory_rate', 'systolic_bp', 'diastolic_bp', 'spo2'];
        const vals = {
            patient_id: parseInt(form.patient_id),
            pain_score: form.pain_score,
            triage_category: form.triage_category,
            notes: form.notes,
        };
        for (const field of floatFields) if (form[field] !== '') vals[field] = parseFloat(form[field]);
        for (const field of intFields) if (form[field] !== '') vals[field] = parseInt(form[field]);
        const id = await this.orm.call('hospital.vitals', 'create', [[vals]]);
        this.notification.add(_t('Vitals recorded.'), { type: 'success' });
        Object.assign(this.state.vitalsForm, {
            patient_id: '', temperature_c: '', pulse_rate: '', respiratory_rate: '',
            systolic_bp: '', diastolic_bp: '', spo2: '', height_cm: '', weight_kg: '',
            pain_score: '0', triage_category: 'green', notes: '',
        });
        await this.loadDashboard();
        this.openRecord('hospital.vitals', id, _t('Vitals'));
    }

    async appointmentAction(ev) {
        const id = parseInt(ev.currentTarget.dataset.id);
        const method = ev.currentTarget.dataset.method;
        if (!id || !method) return;
        await this.orm.call('hospital.appointment', method, [[id]]);
        this.notification.add(_t('Queue status updated.'), { type: 'success' });
        await this.loadDashboard();
    }

    async createOPD(ev) {
        const id = parseInt(ev.currentTarget.dataset.id);
        if (!id) return;
        try {
            await this.orm.call('hospital.appointment', 'action_create_opd', [[id]]);
            this.notification.add(_t('OPD visit created from appointment.'), { type: 'success' });
            await this.loadDashboard();
        } catch (error) {
            this.notification.add(error.message || _t('Unable to create OPD visit.'), { type: 'danger' });
        }
    }

    openModel(model, name, domain = []) {
        this.action.doAction({
            name, type: 'ir.actions.act_window', res_model: model, view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']], domain,
        });
    }

    openRecord(model, id, name) {
        if (!id) return;
        const resId = Array.isArray(id) ? id[0] : id;
        this.action.doAction({ name, type: 'ir.actions.act_window', res_model: model, res_id: resId, view_mode: 'form', views: [[false, 'form']] });
    }

    openPatients() { this.openModel('res.partner', _t('Patients'), [['patient_seq', 'not in', ['New', 'Employee', 'User']]]); }
    openConsultations() { this.openModel('hospital.outpatient', _t('OPD Consultations')); }
    openInpatients() { this.openModel('hospital.inpatient', _t('Inpatients')); }
    openSurgeries() { this.openModel('inpatient.surgery', _t('Surgeries')); }
    openAllocations() { this.openModel('doctor.allocation', _t('Shift Allocation')); }
    openAppointments() { this.openModel('hospital.appointment', _t('Appointments')); }
    openVitals() { this.openModel('hospital.vitals', _t('Vitals / EMR')); }
    openEmergency() { this.openModel('hospital.emergency.case', _t('Emergency Cases')); }

    openAppointment(ev) { ev.preventDefault && ev.preventDefault(); this.openRecord('hospital.appointment', parseInt(ev.currentTarget.dataset.id), _t('Appointment')); }
    openVital(ev) { this.openRecord('hospital.vitals', parseInt(ev.currentTarget.dataset.id), _t('Vitals')); }
    openSurgery(ev) { this.openRecord('inpatient.surgery', parseInt(ev.currentTarget.dataset.id), _t('Surgery')); }

    priorityLabel(value) { return ({ '0': _t('Normal'), '1': _t('Priority'), '2': _t('Emergency') })[value] || value || ''; }
    priorityClass(value) { return ({ '0': 'normal', '1': 'urgent', '2': 'emergency' })[value] || 'normal'; }

    formatM2O(value) { return Array.isArray(value) ? value[1] : (value || ''); }
    formatDate(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : ''; }
}

DoctorDashboard.template = 'DoctorDashboard';
registry.category('actions').add('doctor_dashboard_tags', DoctorDashboard);
