# -*- coding: utf-8 -*-
from odoo import fields, models


class HospitalBed(models.Model):
    _inherit = 'hospital.bed'

    product_id = fields.Many2one('product.product', string='Accounting Product', domain=[('sale_ok', '=', True)])
