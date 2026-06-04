/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';
import { Component, onWillStart, useState } from '@odoo/owl';
import { _t } from '@web/core/l10n/translation';

export class PharmacyDashboard extends Component {
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');
        this.state = useState({
            loading: true,
            active: 'sale',
            kpis: {},
            currency: '',
            patients: [],
            medicines: [],
            low_stock: [],
            orders: [],
            saleForm: { patient_id: '', name: '', phone: '', email: '', dob: '' },
            orderLines: [],
            search: '',
        });
        onWillStart(async () => {
            await this.loadDashboard();
            this.addRow();
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call('hospital.dashboard.service', 'get_pharmacy_dashboard', []);
        Object.assign(this.state, {
            kpis: data.kpis || {},
            currency: data.currency || '',
            patients: data.patients || [],
            medicines: data.medicines || [],
            low_stock: data.low_stock || [],
            orders: data.orders || [],
            loading: false,
        });
    }

    setActive(ev) { this.state.active = ev.currentTarget.dataset.section; }

    updateForm(ev) {
        const field = ev.currentTarget.dataset.field;
        this.state.saleForm[field] = ev.currentTarget.value;
    }

    selectPatient(ev) {
        const patientId = parseInt(ev.currentTarget.value);
        this.state.saleForm.patient_id = ev.currentTarget.value;
        const patient = this.state.patients.find((item) => item.id === patientId);
        if (patient) {
            Object.assign(this.state.saleForm, {
                name: patient.name || '',
                phone: patient.phone || '',
                email: patient.email || '',
                dob: patient.date_of_birth || '',
            });
        }
    }

    updateSearch(ev) { this.state.search = ev.currentTarget.value; }

    addRow() {
        this.state.orderLines.push({ uid: Date.now() + Math.random(), product: '', qty: 1, price: 0, available: 0, sub_total: 0 });
    }

    removeLine(ev) {
        const uid = parseFloat(ev.currentTarget.dataset.uid);
        this.state.orderLines = this.state.orderLines.filter((line) => line.uid !== uid);
        if (!this.state.orderLines.length) this.addRow();
    }

    updateLine(ev) {
        const uid = parseFloat(ev.currentTarget.dataset.uid);
        const field = ev.currentTarget.dataset.field;
        const line = this.state.orderLines.find((item) => item.uid === uid);
        if (!line) return;
        line[field] = ev.currentTarget.value;
        if (field === 'product') {
            const product = this._medicineById(line.product);
            line.price = product ? Number(product.list_price || 0) : 0;
            line.available = product ? Number(product.qty_available || 0) : 0;
        }
        if (field === 'qty') line.qty = Number(line.qty || 0);
        line.sub_total = Number(line.qty || 0) * Number(line.price || 0);
    }

    async createSaleOrder() {
        if (!this.state.saleForm.name) {
            this.notification.add(_t('Patient/customer name is required.'), { type: 'warning' });
            return;
        }
        const products = this.state.orderLines
            .filter((line) => line.product && Number(line.qty) > 0)
            .map((line) => ({ product: parseInt(line.product), qty: Number(line.qty), price: Number(line.price || 0), sub_total: Number(line.sub_total || 0) }));
        if (!products.length) {
            this.notification.add(_t('Add at least one medicine line.'), { type: 'warning' });
            return;
        }
        const result = await this.orm.call('hospital.pharmacy', 'create_sale_order', [{
            name: this.state.saleForm.name,
            phone: this.state.saleForm.phone,
            email: this.state.saleForm.email,
            dob: this.state.saleForm.dob,
            products,
        }]);
        this.notification.add(_t('Sale order created: ') + result.invoice, { type: 'success' });
        Object.assign(this.state.saleForm, { patient_id: '', name: '', phone: '', email: '', dob: '' });
        this.state.orderLines = [];
        this.addRow();
        await this.loadDashboard();
        this.openRecord('sale.order', result.invoice_id, _t('Sale Order'));
    }

    get filteredMedicines() {
        const term = (this.state.search || '').toLowerCase();
        if (!term) return this.state.medicines.slice(0, 50);
        return this.state.medicines.filter((item) => (item.name || '').toLowerCase().includes(term)).slice(0, 50);
    }

    get orderTotal() {
        return this.state.orderLines.reduce((sum, line) => sum + Number(line.sub_total || 0), 0);
    }

    _medicineById(id) {
        return this.state.medicines.find((product) => product.id === parseInt(id));
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

    openMedicines() { this.openModel('product.template', _t('Medicines'), [['medicine_ok', '=', true]]); }
    openVaccines() { this.openModel('product.template', _t('Vaccines'), [['vaccine_ok', '=', true]]); }
    openLowStock() { this.openModel('product.template', _t('Low-stock Medicines'), [['medicine_ok', '=', true], ['qty_available', '<=', 5]]); }
    openOrders() { this.openModel('sale.order', _t('Pharmacy Sale Orders'), [['partner_id.patient_seq', 'not in', ['New', 'Employee', 'User']]]); }
    openOrder(ev) { this.openRecord('sale.order', parseInt(ev.currentTarget.dataset.id), _t('Sale Order')); }
    openProduct(ev) { this.openRecord('product.template', parseInt(ev.currentTarget.dataset.id), _t('Medicine')); }

    formatM2O(value) { return Array.isArray(value) ? value[1] : (value || ''); }
    formatDate(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : ''; }
    money(value) { return `${this.state.currency} ${Number(value || 0).toFixed(2)}`; }
}

PharmacyDashboard.template = 'PharmacyDashboard';
registry.category('actions').add('pharmacy_dashboard_tags', PharmacyDashboard);
