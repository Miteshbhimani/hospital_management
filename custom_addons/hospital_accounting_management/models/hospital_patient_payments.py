# -*- coding: utf-8 -*-
"""Expose hospital advance/refund totals and actions on OPD/IPD records."""

from odoo import api, fields, models, _


class HospitalOutpatient(models.Model):
    _inherit = 'hospital.outpatient'

    hospital_payment_ids = fields.One2many('account.payment', 'hospital_outpatient_id', string='Hospital Payments')
    advance_amount = fields.Monetary(string='Advance Collected', compute='_compute_hospital_payment_totals', currency_field='currency_id')
    refund_amount = fields.Monetary(string='Refunded Amount', compute='_compute_hospital_payment_totals', currency_field='currency_id')

    @api.depends('hospital_payment_ids.amount', 'hospital_payment_ids.hospital_payment_type', 'hospital_payment_ids.state')
    def _compute_hospital_payment_totals(self):
        for record in self:
            posted = record.hospital_payment_ids.filtered(lambda payment: payment.state == 'posted')
            record.advance_amount = sum(posted.filtered(lambda payment: payment.hospital_payment_type == 'advance').mapped('amount'))
            record.refund_amount = sum(posted.filtered(lambda payment: payment.hospital_payment_type == 'refund').mapped('amount'))

    def action_collect_advance(self):
        self.ensure_one()
        return self._open_advance_refund_wizard('advance')

    def action_process_refund(self):
        self.ensure_one()
        return self._open_advance_refund_wizard('refund')

    def _open_advance_refund_wizard(self, operation):
        return {
            'name': _('Hospital Advance / Refund'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.advance.refund.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_operation_type': operation,
                'default_patient_id': self.patient_id.id,
                'default_outpatient_id': self.id,
            },
        }


class HospitalInpatient(models.Model):
    _inherit = 'hospital.inpatient'

    hospital_payment_ids = fields.One2many('account.payment', 'hospital_inpatient_id', string='Hospital Payments')
    advance_amount = fields.Monetary(string='Advance Collected', compute='_compute_hospital_payment_totals', currency_field='currency_id')
    refund_amount = fields.Monetary(string='Refunded Amount', compute='_compute_hospital_payment_totals', currency_field='currency_id')

    @api.depends('hospital_payment_ids.amount', 'hospital_payment_ids.hospital_payment_type', 'hospital_payment_ids.state')
    def _compute_hospital_payment_totals(self):
        for record in self:
            posted = record.hospital_payment_ids.filtered(lambda payment: payment.state == 'posted')
            record.advance_amount = sum(posted.filtered(lambda payment: payment.hospital_payment_type == 'advance').mapped('amount'))
            record.refund_amount = sum(posted.filtered(lambda payment: payment.hospital_payment_type == 'refund').mapped('amount'))

    def action_collect_advance(self):
        self.ensure_one()
        return self._open_advance_refund_wizard('advance')

    def action_process_refund(self):
        self.ensure_one()
        return self._open_advance_refund_wizard('refund')

    def _open_advance_refund_wizard(self, operation):
        return {
            'name': _('Hospital Advance / Refund'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.advance.refund.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_operation_type': operation,
                'default_patient_id': self.patient_id.id,
                'default_inpatient_id': self.id,
            },
        }
