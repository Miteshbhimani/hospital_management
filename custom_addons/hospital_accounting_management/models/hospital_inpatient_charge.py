# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HospitalInpatientCharge(models.Model):
    """Billable IPD service line; this is a charge source, not a payment ledger."""

    _name = 'hospital.inpatient.charge'
    _description = 'Hospital Inpatient Charge'
    _order = 'date desc, id desc'

    inpatient_id = fields.Many2one(
        'hospital.inpatient', string='Inpatient Admission', required=True,
        ondelete='cascade', index=True,
    )
    date = fields.Date(string='Charge Date', default=fields.Date.context_today, required=True)
    name = fields.Char(string='Description', required=True)
    product_id = fields.Many2one(
        'product.product', string='Product/Service',
        domain=[('sale_ok', '=', True)],
    )
    service_type = fields.Selection([
        ('procedure', 'Procedure'),
        ('doctor_visit', 'Doctor Visit'),
        ('nursing', 'Nursing'),
        ('surgery', 'Surgery'),
        ('medicine', 'Medicine'),
        ('lab', 'Lab Test'),
        ('radiology', 'Radiology'),
        ('other', 'Other'),
    ], string='Service Type', default='other', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Monetary(string='Unit Price', currency_field='currency_id', required=True)
    tax_ids = fields.Many2many(
        'account.tax', string='Taxes',
        domain=[('type_tax_use', '=', 'sale')],
    )
    subtotal = fields.Monetary(
        string='Subtotal', currency_field='currency_id',
        compute='_compute_subtotal', store=True,
    )
    currency_id = fields.Many2one(
        related='inpatient_id.currency_id', string='Currency', readonly=True,
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for charge in self:
            charge.subtotal = charge.quantity * charge.price_unit
