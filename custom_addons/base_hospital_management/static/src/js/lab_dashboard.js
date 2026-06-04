/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

export class LabDashBoard extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.state = useState({
            loading: true,
            active: 'requests',
            kpis: {},
            new_requests: [],
            in_process: [],
            published: [],
            requestDetail: false,
        });
        onWillStart(async () => await this.loadDashboard());
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call('hospital.dashboard.service', 'get_lab_dashboard', []);
        Object.assign(this.state, {
            kpis: data.kpis || {},
            new_requests: data.new_requests || [],
            in_process: data.in_process || [],
            published: data.published || [],
            loading: false,
        });
    }

    setActive(ev) { this.state.active = ev.currentTarget.dataset.section; }

    async previewRequest(ev) {
        const id = parseInt(ev.currentTarget.dataset.id);
        if (!id) return;
        this.state.requestDetail = await this.orm.call('lab.test.line', 'action_get_patient_data', [id]);
        this.state.active = 'preview';
    }

    async confirmRequest(ev) {
        const id = parseInt(ev.currentTarget.dataset.id || (this.state.requestDetail && this.state.requestDetail.id));
        if (!id) return;
        await this.orm.call('lab.test.line', 'create_lab_tests', [id]);
        this.notification.add(_t('Lab test request confirmed.'), { type: 'success' });
        this.state.requestDetail = false;
        this.state.active = 'requests';
        await this.loadDashboard();
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

    openRequests() { this.openModel('lab.test.line', _t('Lab Requests')); }
    openPatientTests() { this.openModel('patient.lab.test', _t('Patient Lab Tests')); }
    openResults() { this.openModel('lab.test.result', _t('Lab Results')); }
    openCatalog() { this.openModel('lab.test', _t('Lab Test Catalog')); }
    openRequest(ev) { ev.preventDefault && ev.preventDefault(); this.openRecord('lab.test.line', parseInt(ev.currentTarget.dataset.id), _t('Lab Request')); }
    openPatientTest(ev) { this.openRecord('patient.lab.test', parseInt(ev.currentTarget.dataset.id), _t('Patient Lab Test')); }
    openResult(ev) { this.openRecord('lab.test.result', parseInt(ev.currentTarget.dataset.id), _t('Lab Result')); }

    formatM2O(value) { return Array.isArray(value) ? value[1] : (value || ''); }
    formatMany(value) { return Array.isArray(value) ? value.length : 0; }
    formatDate(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : ''; }
}

LabDashBoard.template = 'LabDashboard';
registry.category('actions').add('lab_dashboard_tags', LabDashBoard);
