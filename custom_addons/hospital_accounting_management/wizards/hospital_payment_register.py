# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class HospitalPaymentRegister(models.TransientModel):
    _name = 'hospital.payment.register'
    _description = 'Hospital Payment Register'

    invoice_id = fields.Many2one('account.move', string='Invoice', required=True, domain=[('move_type', '=', 'out_invoice')])
    patient_id = fields.Many2one('res.partner', string='Patient', related='invoice_id.hospital_patient_id', readonly=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('cash', 'bank'))])
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')

    def action_register_payment(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(_('Payment amount must be positive.'))
        if self.invoice_id.state == 'draft':
            self.invoice_id.action_post()
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=self.invoice_id.ids
        ).create({
            'amount': self.amount,
            'journal_id': self.journal_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication or self.invoice_id.name or self.invoice_id.ref,
        })
        payments = wizard._create_payments()
        payments.write({
            'hospital_patient_id': (self.invoice_id.hospital_patient_id or self.invoice_id.partner_id).id,
            'hospital_outpatient_id': self.invoice_id.hospital_outpatient_id.id,
            'hospital_inpatient_id': self.invoice_id.hospital_inpatient_id.id,
            'hospital_payment_type': 'regular',
        })
        if len(payments) == 1:
            return {
                'name': _('Hospital Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'res_id': payments.id,
            }
        return {'type': 'ir.actions.act_window_close'}
