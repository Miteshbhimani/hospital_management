# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalRadiologyRequest(models.Model):
    _name = 'hospital.radiology.request'
    _description = 'Hospital Radiology Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: 'New')
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, tracking=True, domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])])
    doctor_id = fields.Many2one('hr.employee', string='Requesting Doctor', tracking=True)
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Record')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    modality_id = fields.Many2one('hospital.radiology.modality', string='Modality')
    body_part = fields.Char(string='Body Part')
    reason = fields.Text(string='Reason for Request')
    estimated_price = fields.Float(string='Estimated Price')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.radiology.request') or 'New'
        return super().create(vals_list)

    def action_requested(self):
        self.state = 'requested'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_complete(self):
        self.state = 'completed'

    def action_cancel(self):
        self.state = 'cancelled'


class HospitalRadiologyModality(models.Model):
    _name = 'hospital.radiology.modality'
    _description = 'Radiology Modality'

    name = fields.Char(required=True)
    code = fields.Char()
    product_id = fields.Many2one('product.template', string='Service Product')
