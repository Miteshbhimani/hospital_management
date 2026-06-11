# -*- coding: utf-8 -*-
"""Hospital advance and refund payment tracking."""

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    hospital_patient_id = fields.Many2one('res.partner', string='Hospital Patient', index=True, copy=False)
    hospital_outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Record', copy=False, index=True)
    hospital_inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission', copy=False, index=True)
    hospital_payment_type = fields.Selection([
        ('advance', 'Advance'),
        ('refund', 'Refund'),
        ('regular', 'Regular Payment'),
    ], string='Hospital Payment Type', copy=False, index=True)
