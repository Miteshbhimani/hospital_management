# -*- coding: utf-8 -*-
from odoo import fields, models


class LabTestResult(models.Model):
    _inherit = 'lab.test.result'

    tax_ids = fields.Many2many(
        'account.tax', string='Sales Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        help='Optional tax override for this completed test result.',
    )
