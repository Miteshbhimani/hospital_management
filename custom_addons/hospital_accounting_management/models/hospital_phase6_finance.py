# -*- coding: utf-8 -*-
"""Phase 6 executive finance snapshot for enterprise hospital reporting."""

from odoo import api, fields, models, _


class HospitalEnterpriseFinanceSnapshot(models.Model):
    _name = 'hospital.enterprise.finance.snapshot'
    _description = 'Hospital Enterprise Finance Snapshot'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'snapshot_date desc, id desc'

    name = fields.Char(default='New', readonly=True, copy=False, index=True)
    snapshot_date = fields.Date(default=fields.Date.context_today, required=True)
    branch_id = fields.Many2one('hospital.branch', string='Branch')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    invoice_count = fields.Integer(readonly=True)
    posted_invoice_count = fields.Integer(readonly=True)
    paid_invoice_count = fields.Integer(readonly=True)
    outstanding_invoice_count = fields.Integer(readonly=True)
    gross_revenue = fields.Monetary(currency_field='currency_id', readonly=True)
    paid_revenue = fields.Monetary(currency_field='currency_id', readonly=True)
    outstanding_amount = fields.Monetary(currency_field='currency_id', readonly=True)
    insurance_claim_count = fields.Integer(readonly=True)
    pending_claim_count = fields.Integer(readonly=True)
    settled_claim_count = fields.Integer(readonly=True)
    insurance_claim_amount = fields.Monetary(currency_field='currency_id', readonly=True)
    patient_payable_amount = fields.Monetary(currency_field='currency_id', readonly=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.enterprise.finance.snapshot') or _('New')
        return super().create(vals_list)

    def _get_branch_patient_ids(self, branch):
        if not branch:
            return []
        partner_model = self.env['res.partner']
        if 'primary_branch_id' not in partner_model._fields:
            return []
        return partner_model.search([('primary_branch_id', '=', branch.id)]).ids

    def action_compute_snapshot(self):
        for snapshot in self:
            domain = [('move_type', '=', 'out_invoice'), ('company_id', '=', snapshot.company_id.id)]
            linked_patients = snapshot._get_branch_patient_ids(snapshot.branch_id)
            if snapshot.branch_id:
                domain += ['|', ('hospital_patient_id', 'in', linked_patients), ('partner_id', 'in', linked_patients or [0])]
            invoices = self.env['account.move'].search(domain)
            posted = invoices.filtered(lambda move: move.state == 'posted')
            paid = posted.filtered(lambda move: move.payment_state in ('paid', 'in_payment'))
            outstanding = posted.filtered(lambda move: move.payment_state not in ('paid', 'in_payment'))
            claim_domain = []
            if snapshot.branch_id:
                claim_domain += [('patient_id', 'in', linked_patients or [0])]
            claims = self.env['hospital.insurance.claim'].search(claim_domain)
            snapshot.write({
                'invoice_count': len(invoices),
                'posted_invoice_count': len(posted),
                'paid_invoice_count': len(paid),
                'outstanding_invoice_count': len(outstanding),
                'gross_revenue': sum(posted.mapped('amount_total')),
                'paid_revenue': sum(paid.mapped('amount_total')),
                'outstanding_amount': sum(outstanding.mapped('amount_residual')),
                'insurance_claim_count': len(claims),
                'pending_claim_count': len(claims.filtered(lambda c: c.state not in ('settled', 'rejected', 'cancelled'))),
                'settled_claim_count': len(claims.filtered(lambda c: c.state == 'settled')),
                'insurance_claim_amount': sum(claims.mapped('insurance_payable_amount')) if claims else 0.0,
                'patient_payable_amount': sum(claims.mapped('patient_payable_amount')) if claims else 0.0,
            })
        return True
