# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HospitalAccountingDashboard(models.Model):
    _name = 'hospital.accounting.dashboard'
    _description = 'Hospital Accounting Dashboard'

    name = fields.Char(default='Hospital Accounting Dashboard', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id')

    today_revenue = fields.Monetary(string='Today Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    monthly_revenue = fields.Monetary(string='Monthly Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    total_revenue = fields.Monetary(string='Total Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    outstanding_receivables = fields.Monetary(string='Outstanding Receivables', currency_field='currency_id', compute='_compute_dashboard_metrics')
    insurance_receivables = fields.Monetary(string='Insurance Receivables', currency_field='currency_id', compute='_compute_dashboard_metrics')
    payments_collected = fields.Monetary(string='Payments Collected', currency_field='currency_id', compute='_compute_dashboard_metrics')
    advance_collected = fields.Monetary(string='Advance Collected', currency_field='currency_id', compute='_compute_dashboard_metrics')
    refunds_paid = fields.Monetary(string='Refunds Paid', currency_field='currency_id', compute='_compute_dashboard_metrics')
    net_advance_balance = fields.Monetary(string='Net Advance Balance', currency_field='currency_id', compute='_compute_dashboard_metrics')

    opd_revenue = fields.Monetary(string='OPD Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    ipd_revenue = fields.Monetary(string='IPD Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    laboratory_revenue = fields.Monetary(string='Lab Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    pharmacy_revenue = fields.Monetary(string='Pharmacy Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    radiology_revenue = fields.Monetary(string='Radiology Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    surgery_revenue = fields.Monetary(string='Surgery Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')
    other_revenue = fields.Monetary(string='Other Revenue', currency_field='currency_id', compute='_compute_dashboard_metrics')

    invoice_count = fields.Integer(string='Hospital Invoices', compute='_compute_dashboard_metrics')
    posted_invoice_count = fields.Integer(string='Posted Invoices', compute='_compute_dashboard_metrics')
    draft_invoice_count = fields.Integer(string='Draft Invoices', compute='_compute_dashboard_metrics')
    paid_invoices = fields.Integer(string='Paid Invoices', compute='_compute_dashboard_metrics')
    unpaid_invoices = fields.Integer(string='Unpaid / Partial', compute='_compute_dashboard_metrics')
    overdue_invoices = fields.Integer(string='Overdue Invoices', compute='_compute_dashboard_metrics')
    insurance_invoice_count = fields.Integer(string='Insurance Invoices', compute='_compute_dashboard_metrics')
    payment_count = fields.Integer(string='Hospital Payments', compute='_compute_dashboard_metrics')

    @api.model
    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return today.replace(day=1)

    @api.model
    def _period_domain(self, date_field):
        self.ensure_one()
        date_from = self.date_from or self._default_date_from()
        date_to = self.date_to or fields.Date.context_today(self)
        domain = []
        if date_from:
            domain.append((date_field, '>=', date_from))
        if date_to:
            domain.append((date_field, '<=', date_to))
        return domain

    @api.depends_context('company')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = self.env.company.currency_id

    @api.depends('date_from', 'date_to')
    def _compute_dashboard_metrics(self):
        AccountMove = self.env['account.move'].sudo()
        AccountPayment = self.env['account.payment'].sudo()
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        accessible_company_ids = self.env.companies.ids or [self.env.company.id]

        metric_fields = [
            'today_revenue', 'monthly_revenue', 'total_revenue', 'outstanding_receivables', 'insurance_receivables',
            'payments_collected', 'advance_collected', 'refunds_paid', 'net_advance_balance', 'opd_revenue',
            'ipd_revenue', 'laboratory_revenue', 'pharmacy_revenue', 'radiology_revenue', 'surgery_revenue',
            'other_revenue', 'invoice_count', 'posted_invoice_count', 'draft_invoice_count', 'paid_invoices',
            'unpaid_invoices', 'overdue_invoices', 'insurance_invoice_count', 'payment_count',
        ]
        for record in self:
            for field_name in metric_fields:
                record[field_name] = 0

            invoice_base_domain = [
                ('move_type', '=', 'out_invoice'),
                ('hospital_invoice_type', '!=', False),
                ('company_id', 'in', accessible_company_ids),
            ]
            period_domain = record._period_domain('invoice_date')
            period_invoices = AccountMove.search(invoice_base_domain + period_domain)
            posted_period_invoices = period_invoices.filtered(lambda move: move.state == 'posted')
            today_invoices = posted_period_invoices.filtered(lambda move: move.invoice_date == today)
            monthly_invoices = posted_period_invoices.filtered(
                lambda move: move.invoice_date and month_start <= move.invoice_date <= today
            )
            outstanding = posted_period_invoices.filtered(lambda move: move.payment_state in ('not_paid', 'partial'))
            overdue = outstanding.filtered(lambda move: move.invoice_date_due and move.invoice_date_due < today)
            insurance_invoices = posted_period_invoices.filtered('insurance_provider_id')

            record.invoice_count = len(period_invoices)
            record.posted_invoice_count = len(posted_period_invoices)
            record.draft_invoice_count = len(period_invoices.filtered(lambda move: move.state == 'draft'))
            record.paid_invoices = len(posted_period_invoices.filtered(lambda move: move.payment_state == 'paid'))
            record.unpaid_invoices = len(outstanding)
            record.overdue_invoices = len(overdue)
            record.insurance_invoice_count = len(insurance_invoices)
            record.today_revenue = sum(today_invoices.mapped('amount_total'))
            record.monthly_revenue = sum(monthly_invoices.mapped('amount_total'))
            record.total_revenue = sum(posted_period_invoices.mapped('amount_total'))
            record.outstanding_receivables = sum(outstanding.mapped('amount_residual'))
            record.insurance_receivables = sum(insurance_invoices.mapped('amount_residual'))

            for department, field_name in {
                'opd': 'opd_revenue',
                'ipd': 'ipd_revenue',
                'laboratory': 'laboratory_revenue',
                'pharmacy': 'pharmacy_revenue',
                'radiology': 'radiology_revenue',
                'surgery': 'surgery_revenue',
                'other': 'other_revenue',
            }.items():
                record[field_name] = sum(
                    posted_period_invoices.filtered(lambda move, dept=department: move.hospital_department == dept).mapped('amount_total')
                )

            payment_domain = [
                ('hospital_payment_type', '!=', False),
                ('state', 'not in', ('draft', 'canceled', 'rejected')),
                ('company_id', 'in', accessible_company_ids),
            ] + record._period_domain('date')
            payments = AccountPayment.search(payment_domain)
            inbound_payments = payments.filtered(lambda payment: payment.payment_type == 'inbound')
            advance_payments = inbound_payments.filtered(lambda payment: payment.hospital_payment_type == 'advance')
            refunds = payments.filtered(lambda payment: payment.payment_type == 'outbound' and payment.hospital_payment_type == 'refund')
            record.payment_count = len(payments)
            record.payments_collected = sum(inbound_payments.mapped('amount'))
            record.advance_collected = sum(advance_payments.mapped('amount'))
            record.refunds_paid = sum(refunds.mapped('amount'))
            record.net_advance_balance = record.advance_collected - record.refunds_paid

    @api.model
    def get_dashboard_data(self, date_from=False, date_to=False):
        dashboard = self.env.ref('hospital_accounting_management.hospital_accounting_dashboard_main', raise_if_not_found=False)
        if not dashboard:
            dashboard = self.search([], limit=1)
        if dashboard:
            if date_from:
                dashboard.date_from = date_from
            if date_to:
                dashboard.date_to = date_to
            dashboard._compute_dashboard_metrics()
            return {
                'today_revenue': dashboard.today_revenue,
                'monthly_revenue': dashboard.monthly_revenue,
                'outstanding_receivables': dashboard.outstanding_receivables,
                'insurance_receivables': dashboard.insurance_receivables,
                'paid_invoices': dashboard.paid_invoices,
                'unpaid_invoices': dashboard.unpaid_invoices,
                'overdue_invoices': dashboard.overdue_invoices,
                'total_revenue': dashboard.total_revenue,
                'payments_collected': dashboard.payments_collected,
                'advance_collected': dashboard.advance_collected,
                'refunds_paid': dashboard.refunds_paid,
            }
        return {}

    def action_refresh_dashboard(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _action_open_invoices(self, name, extra_domain=None):
        self.ensure_one()
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('hospital_invoice_type', '!=', False),
            ('company_id', 'in', self.env.companies.ids or [self.env.company.id]),
        ] + self._period_domain('invoice_date')
        if extra_domain:
            domain += extra_domain
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'default_move_type': 'out_invoice'},
        }

    def action_open_hospital_invoices(self):
        return self._action_open_invoices(_('Hospital Invoices'))

    def action_open_outstanding_invoices(self):
        return self._action_open_invoices(_('Outstanding Hospital Invoices'), [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))])

    def action_open_overdue_invoices(self):
        today = fields.Date.context_today(self)
        return self._action_open_invoices(_('Overdue Hospital Invoices'), [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')), ('invoice_date_due', '<', today)])

    def action_open_insurance_invoices(self):
        return self._action_open_invoices(_('Insurance Receivables'), [('state', '=', 'posted'), ('insurance_provider_id', '!=', False)])

    def action_open_hospital_payments(self):
        self.ensure_one()
        domain = [
            ('hospital_payment_type', '!=', False),
            ('company_id', 'in', self.env.companies.ids or [self.env.company.id]),
        ] + self._period_domain('date')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hospital Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': domain,
        }
