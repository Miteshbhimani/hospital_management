# -*- coding: utf-8 -*-
from odoo import fields, models


class LabTest(models.Model):
    _inherit = 'lab.test'

    tax_ids = fields.Many2many(
        'account.tax', string='Sales Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help='Taxes used when this test is invoiced.',
    )
    product_id = fields.Many2one(
        'product.product', string='Accounting Product',
        domain=[('sale_ok', '=', True)],
    )
    income_account_id = fields.Many2one(
        'account.account', string='Income Account',
        domain=[('deprecated', '=', False)],
    )
    service_type = fields.Selection([
        ('lab', 'Lab Test'),
        ('radiology', 'Radiology'),
        ('procedure', 'Procedure'),
        ('other', 'Other'),
    ], string='Accounting Service Type', default='lab')
