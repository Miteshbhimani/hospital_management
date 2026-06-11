# -*- coding: utf-8 -*-
"""Collect patient advance payments and process refunds."""

from odoo import _, fields, models
from odoo.exceptions import UserError


class HospitalAdvanceRefundWizard(models.TransientModel):
    _name = 'hospital.advance.refund.wizard'
    _description = 'Hospital Advance / Refund Wizard'

    operation_type = fields.Selection([
        ('advance', 'Collect Advance'),
        ('refund', 'Process Refund'),
    ], string='Operation', required=True, default='advance')
    patient_id = fields.Many2one('res.partner', string='Patient', required=True)
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Record')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', 'in', ('cash', 'bank'))])
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    memo = fields.Char(string='Memo')

    def action_create_payment(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_('Amount must be positive.'))
        inbound = self.operation_type == 'advance'
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound' if inbound else 'outbound',
            'partner_type': 'customer',
            'partner_id': self.patient_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'memo': self.memo or (_('Hospital Advance') if inbound else _('Hospital Refund')),
            'hospital_patient_id': self.patient_id.id,
            'hospital_outpatient_id': self.outpatient_id.id,
            'hospital_inpatient_id': self.inpatient_id.id,
            'hospital_payment_type': self.operation_type,
        })
        payment.action_post()
        return {
            'name': _('Hospital Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
        }
