# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    consultation_product_id = fields.Many2one('product.product', string='Consultation Product', domain=[('sale_ok', '=', True)])
    followup_product_id = fields.Many2one('product.product', string='Follow-up Product', domain=[('sale_ok', '=', True)])
