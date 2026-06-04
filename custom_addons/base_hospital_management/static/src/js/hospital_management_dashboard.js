/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

export class HospitalManagementDashboard extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.state = useState({
            loading: true,
            cards: {},
            ai: { latest: [] },
            disclaimer: _t('AI-generated, doctor/staff approval required'),
        });
        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call('hospital.ai.suggestion', 'get_hospital_ai_dashboard', []);
        this.state.cards = data.cards || {};
        this.state.ai = data.ai || { latest: [] };
        this.state.disclaimer = data.disclaimer || this.state.disclaimer;
        this.state.loading = false;
    }

    async generateSuggestions() {
        const result = await this.orm.call('hospital.ai.suggestion', 'generate_rule_based_suggestions', []);
        this.notification.add(_t('%s new reviewable suggestion(s) generated.').replace('%s', result.created || 0), {
            type: 'success',
        });
        await this.loadDashboard();
    }

    openModel(model, name, domain = []) {
        this.action.doAction({
            name,
            type: 'ir.actions.act_window',
            res_model: model,
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain,
        });
    }

    openPatients() {
        this.openModel('res.partner', _t('Patients'), [['patient_seq', 'not in', ['New', 'Employee', 'User']]]);
    }

    openAppointments() {
        this.openModel('hospital.appointment', _t('Appointments & Queue'));
    }

    openOPD() {
        this.openModel('hospital.outpatient', _t('OPD Visits'));
    }

    openIPD() {
        this.openModel('hospital.inpatient', _t('Admitted Patients'), [['state', '=', 'admit']]);
    }

    openBeds() {
        this.openModel('hospital.bed', _t('Beds'));
    }

    openLab() {
        this.openModel('patient.lab.test', _t('Pending Laboratory Tests'), [['state', 'in', ['draft', 'test']]]);
    }

    openLowStock() {
        this.openModel('product.template', _t('Low-stock Medicines'), [['medicine_ok', '=', true], ['qty_available', '<=', 5]]);
    }

    openEmergency() {
        this.openModel('hospital.emergency.case', _t('Active Emergency Cases'), [['state', 'in', ['draft', 'triaged', 'under_treatment']]]);
    }

    openAI() {
        this.openModel('hospital.ai.suggestion', _t('AI Suggestions'), [['state', 'in', ['draft', 'pending_review']]]);
    }

    openSuggestion(ev) {
        const recordId = parseInt(ev.currentTarget.dataset.id, 10);
        if (!recordId) {
            return;
        }
        this.action.doAction({
            name: _t('AI Suggestion'),
            type: 'ir.actions.act_window',
            res_model: 'hospital.ai.suggestion',
            res_id: recordId,
            view_mode: 'form',
            views: [[false, 'form']],
        });
    }
}

HospitalManagementDashboard.template = 'HospitalManagementDashboard';
registry.category('actions').add('hospital_management_dashboard_tags', HospitalManagementDashboard);
