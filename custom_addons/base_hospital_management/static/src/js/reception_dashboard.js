/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

class ReceptionDashBoard extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.state = useState({
            loading: true,
            active: 'patient',
            kpis: {},
            patients: [],
            doctors: [],
            appointments: [],
            rooms: [],
            wards: [],
            patientForm: {
                name: '', phone: '', email: '', date_of_birth: '', blood_group: 'a', rh_type: '+',
                gender: 'male', marital_status: 'unmarried', image_1920: false,
            },
            appointmentForm: {
                patient_id: '', doctor_id: '', appointment_date: this._defaultDateTime(), source: 'walk_in',
                visit_type: 'new', priority: '0', chief_complaint: '',
            },
            admissionForm: {
                patient_id: '', reason: '', type_admission: 'routine', attending_doctor_id: '',
            },
            emergencyForm: {
                patient_id: '', patient_name: '', triage_category: 'yellow', arrival_mode: 'walk_in',
                presenting_complaint: '', medico_legal_case: false,
            },
        });
        onWillStart(async () => await this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call('hospital.dashboard.service', 'get_reception_dashboard', []);
        Object.assign(this.state, {
            kpis: data.kpis || {},
            patients: data.patients || [],
            doctors: data.doctors || [],
            appointments: data.appointments || [],
            rooms: data.rooms || [],
            wards: data.wards || [],
            loading: false,
        });
    }

    setActive(ev) {
        this.state.active = ev.currentTarget.dataset.section;
    }

    updateForm(ev) {
        const { form, field } = ev.currentTarget.dataset;
        if (!form || !field) return;
        this.state[form][field] = ev.currentTarget.type === 'checkbox' ? ev.currentTarget.checked : ev.currentTarget.value;
    }

    async onPatientImageChange(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
            this.state.patientForm.image_1920 = String(reader.result).split(',')[1] || false;
        };
        reader.readAsDataURL(file);
    }

    async savePatient() {
        if (!this.state.patientForm.name || !this.state.patientForm.phone) {
            this.notification.add(_t('Patient name and phone are required.'), { type: 'warning' });
            return;
        }
        const vals = { ...this.state.patientForm };
        if (!vals.date_of_birth) delete vals.date_of_birth;
        if (!vals.image_1920) delete vals.image_1920;
        const patientId = await this.orm.call('res.partner', 'create', [[vals]]);
        this.notification.add(_t('Patient created successfully.'), { type: 'success' });
        this.state.appointmentForm.patient_id = patientId;
        this.state.admissionForm.patient_id = patientId;
        this.state.emergencyForm.patient_id = patientId;
        Object.assign(this.state.patientForm, {
            name: '', phone: '', email: '', date_of_birth: '', blood_group: 'a', rh_type: '+',
            gender: 'male', marital_status: 'unmarried', image_1920: false,
        });
        await this.loadDashboard();
    }

    async createAppointment() {
        const form = this.state.appointmentForm;
        if (!form.patient_id || !form.doctor_id || !form.appointment_date) {
            this.notification.add(_t('Patient, doctor and appointment date are required.'), { type: 'warning' });
            return;
        }
        const recordId = await this.orm.call('hospital.appointment', 'create', [[{
            patient_id: parseInt(form.patient_id),
            doctor_id: parseInt(form.doctor_id),
            appointment_date: this._toServerDateTime(form.appointment_date),
            source: form.source,
            visit_type: form.visit_type,
            priority: form.priority,
            state: 'scheduled',
            chief_complaint: form.chief_complaint,
        }]]);
        this.notification.add(_t('Appointment added to the queue.'), { type: 'success' });
        this.state.active = 'queue';
        await this.loadDashboard();
        this.openRecord('hospital.appointment', recordId, _t('Appointment'));
    }

    async createAdmission() {
        const form = this.state.admissionForm;
        if (!form.patient_id || !form.attending_doctor_id || !form.type_admission) {
            this.notification.add(_t('Patient, attending doctor and admission type are required.'), { type: 'warning' });
            return;
        }
        const recordId = await this.orm.call('hospital.inpatient', 'create', [[{
            patient_id: parseInt(form.patient_id),
            reason: form.reason,
            type_admission: form.type_admission,
            attending_doctor_id: parseInt(form.attending_doctor_id),
        }]]);
        this.notification.add(_t('Inpatient admission created.'), { type: 'success' });
        await this.loadDashboard();
        this.openRecord('hospital.inpatient', recordId, _t('Inpatient Admission'));
    }

    async createEmergency() {
        const form = this.state.emergencyForm;
        if (!form.patient_id && !form.patient_name) {
            this.notification.add(_t('Select a patient or enter an unregistered patient name.'), { type: 'warning' });
            return;
        }
        if (!form.presenting_complaint) {
            this.notification.add(_t('Presenting complaint is required for emergency triage.'), { type: 'warning' });
            return;
        }
        const vals = {
            patient_id: form.patient_id ? parseInt(form.patient_id) : false,
            patient_name: form.patient_name,
            triage_category: form.triage_category,
            arrival_mode: form.arrival_mode,
            presenting_complaint: form.presenting_complaint,
            medico_legal_case: Boolean(form.medico_legal_case),
        };
        const recordId = await this.orm.call('hospital.emergency.case', 'create', [[vals]]);
        this.notification.add(_t('Emergency triage case created.'), { type: 'success' });
        this.state.active = 'emergency';
        await this.loadDashboard();
        this.openRecord('hospital.emergency.case', recordId, _t('Emergency Triage'));
    }

    async checkIn(ev) {
        const id = parseInt(ev.currentTarget.dataset.id);
        await this.orm.call('hospital.appointment', 'action_check_in', [[id]]);
        this.notification.add(_t('Patient checked in.'), { type: 'success' });
        await this.loadDashboard();
    }

    openModel(model, name, domain = [], context = {}) {
        this.action.doAction({
            name, type: 'ir.actions.act_window', res_model: model, view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']], domain, context,
        });
    }

    openRecord(model, id, name) {
        if (!id) return;
        const resId = Array.isArray(id) ? id[0] : id;
        this.action.doAction({ name, type: 'ir.actions.act_window', res_model: model, res_id: resId, view_mode: 'form', views: [[false, 'form']] });
    }

    openPatients() { this.openModel('res.partner', _t('Patients'), [['patient_seq', 'not in', ['New', 'Employee', 'User']]]); }
    openAppointments() { this.openModel('hospital.appointment', _t('Appointment Queue')); }
    openOPD() { this.openModel('hospital.outpatient', _t('OPD Visits')); }
    openIPD() { this.openModel('hospital.inpatient', _t('Inpatients')); }
    openRooms() { this.openModel('patient.room', _t('Rooms')); }
    openWards() { this.openModel('hospital.ward', _t('Wards')); }
    openEmergency() { this.openModel('hospital.emergency.case', _t('Emergency Triage')); }

    openAppointment(ev) {
        ev.preventDefault && ev.preventDefault();
        this.openRecord('hospital.appointment', parseInt(ev.currentTarget.dataset.id), _t('Appointment'));
    }

    priorityLabel(value) { return ({ '0': _t('Normal'), '1': _t('Priority'), '2': _t('Emergency') })[value] || value || ''; }
    priorityClass(value) { return ({ '0': 'normal', '1': 'urgent', '2': 'emergency' })[value] || 'normal'; }

    formatM2O(value) { return Array.isArray(value) ? value[1] : (value || ''); }
    formatDate(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : ''; }

    _defaultDateTime() {
        const d = new Date();
        d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
        return d.toISOString().slice(0, 16);
    }

    _toServerDateTime(value) {
        return value ? value.replace('T', ' ') + ':00' : false;
    }
}

ReceptionDashBoard.template = 'ReceptionDashboard';
registry.category('actions').add('reception_dashboard_tags', ReceptionDashBoard);
