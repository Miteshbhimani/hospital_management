# -*- coding: utf-8 -*-
"""Central charge-capture model for HMS revenue cycle modernization."""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HospitalCharge(models.Model):
    """Department-neutral patient charge before Odoo Accounting invoicing."""
    _name = 'hms.charge'
    _description = 'Hospital Charge Capture'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'charge_date desc, id desc'

    name = fields.Char(string='Charge No.', required=True, readonly=True, copy=False, default='New')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])]
    )
    charge_date = fields.Date(string='Charge Date', default=fields.Date.context_today, required=True, tracking=True)
    department_area = fields.Selection([
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('lab', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('pharmacy', 'Pharmacy'),
        ('ot', 'Operation Theatre'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency'),
        ('package', 'Package'),
        ('other', 'Other'),
    ], string='Department Area', default='other', required=True, tracking=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor')
    product_id = fields.Many2one('product.product', string='Service / Product')
    description = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    amount_total = fields.Monetary(string='Amount', compute='_compute_amount_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, required=True)
    payer_type = fields.Selection([
        ('patient', 'Patient'),
        ('insurance', 'Insurance / TPA'),
        ('corporate', 'Corporate'),
    ], string='Payer Type', default='patient', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready to Invoice'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    source_model = fields.Char(string='Source Model', readonly=True)
    source_record_id = fields.Integer(string='Source Record ID', readonly=True)
    outpatient_id = fields.Many2one('hospital.outpatient', string='OPD Visit')
    inpatient_id = fields.Many2one('hospital.inpatient', string='IPD Admission')
    lab_test_id = fields.Many2one('patient.lab.test', string='Lab Test')
    emergency_id = fields.Many2one('hospital.emergency.case', string='Emergency Case')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    notes = fields.Text(string='Internal Notes')

    @api.depends('quantity', 'unit_price')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hms.charge') or 'New'
        return super().create(vals_list)

    def action_mark_ready(self):
        self.write({'state': 'ready'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def _prepare_invoice_line_vals(self):
        self.ensure_one()
        vals = {
            'name': self.description,
            'quantity': self.quantity,
            'price_unit': self.unit_price,
            'hospital_source_model': self.source_model or self._name,
            'hospital_source_id': self.source_record_id or self.id,
            'hospital_service_type': {
                'opd': 'consultation',
                'ipd': 'room',
                'lab': 'lab',
                'radiology': 'radiology',
                'pharmacy': 'medicine',
                'ot': 'surgery',
            }.get(self.department_area, 'other'),
        }
        if self.product_id:
            vals['product_id'] = self.product_id.id
        return vals


    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_('No invoice has been created for this charge yet.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'context': {'create': False},
        }

    def action_create_invoice(self):
        """Create a standard Odoo customer invoice from a charge."""
        service = self.env['hospital.accounting.service']
        for charge in self:
            if charge.state == 'cancelled':
                raise UserError(_('Cancelled charges cannot be invoiced.'))
            if charge.invoice_id:
                continue
            line_vals = charge._prepare_invoice_line_vals()
            invoice_line = service._prepare_invoice_line(
                product=charge.product_id,
                name=line_vals.get('name'),
                quantity=line_vals.get('quantity'),
                price_unit=line_vals.get('price_unit'),
                source_model=line_vals.get('hospital_source_model'),
                source_id=line_vals.get('hospital_source_id'),
                service_type=line_vals.get('hospital_service_type') or 'other',
            )
            invoice = service.create_customer_invoice(
                charge.patient_id,
                [invoice_line],
                origin=charge.name,
                ref=charge.name,
                invoice_date=fields.Date.context_today(charge),
                hospital_context={
                    'hospital_patient_id': charge.patient_id.id,
                    'hospital_outpatient_id': charge.outpatient_id.id,
                    'hospital_inpatient_id': charge.inpatient_id.id,
                    'hospital_lab_test_id': charge.lab_test_id.id,
                    'hospital_invoice_type': ({'opd': 'opd', 'ipd': 'ipd', 'lab': 'laboratory', 'pharmacy': 'pharmacy', 'radiology': 'radiology'}.get(charge.department_area) or 'other'),
                    'hospital_department': ({'opd': 'opd', 'ipd': 'ipd', 'lab': 'laboratory', 'pharmacy': 'pharmacy', 'radiology': 'radiology', 'ot': 'surgery'}.get(charge.department_area) or 'other'),
                    'hospital_doctor_id': charge.doctor_id.id,
                },
            )
            charge.write({'invoice_id': invoice.id, 'state': 'invoiced'})
        if len(self) == 1 and self.invoice_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': self.invoice_id.id,
            }
        return True
