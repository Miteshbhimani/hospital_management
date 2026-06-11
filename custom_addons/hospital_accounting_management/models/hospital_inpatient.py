# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class HospitalInpatient(models.Model):
    _inherit = 'hospital.inpatient'

    state = fields.Selection(
        selection_add=[('invoice', 'Invoiced')],
        ondelete={'invoice': 'set default'},
    )
    invoice_id = fields.Many2one(
        'account.move', string='Invoice', copy=False,
        domain=[('move_type', '=', 'out_invoice')],
    )
    is_invoice = fields.Boolean(string='Is Invoiced', copy=False)
    charge_ids = fields.One2many(
        'hospital.inpatient.charge', 'inpatient_id', string='Billable Charges',
    )
    payment_state = fields.Selection(
        related='invoice_id.payment_state', string='Payment Status',
        store=True, readonly=True,
    )
    amount_total = fields.Monetary(
        related='invoice_id.amount_total', string='Invoice Total',
        currency_field='currency_id', readonly=True,
    )
    amount_residual = fields.Monetary(
        related='invoice_id.amount_residual', string='Outstanding',
        currency_field='currency_id', readonly=True,
    )

    def _prepare_ipd_invoice_lines(self):
        self.ensure_one()
        service = self.env['hospital.accounting.service']
        lines = []
        if self.bed_id and self.bed_rent_amount:
            product = self.bed_id.product_id or self.env.ref(
                'hospital_accounting_management.product_hospital_bed_rent',
                raise_if_not_found=False,
            )
            lines.append(service._prepare_invoice_line(
                product=product, name=_('Bed Rent'), quantity=max(self.admit_days, 1),
                price_unit=self.bed_rent or 0.0, source_model=self._name,
                source_id=self.id, service_type='room',
            ))
        if self.room_id and self.room_rent_amount:
            product = self.room_id.product_id or self.env.ref(
                'hospital_accounting_management.product_hospital_room_rent',
                raise_if_not_found=False,
            )
            lines.append(service._prepare_invoice_line(
                product=product, name=_('Room Rent'), quantity=max(self.admit_days, 1),
                price_unit=self.room_rent or 0.0, source_model=self._name,
                source_id=self.id, service_type='room',
            ))
        for charge in self.charge_ids:
            lines.append(service._prepare_invoice_line(
                product=charge.product_id, name=charge.name, quantity=charge.quantity,
                price_unit=charge.price_unit, taxes=charge.tax_ids,
                source_model=charge._name, source_id=charge.id,
                service_type=charge.service_type,
            ))
        for lab in self.test_ids.filtered(lambda item: not item.invoice_id):
            if lab.test_ids:
                for test in lab.test_ids:
                    lines.append(service._prepare_invoice_line(
                        product=test.product_id, name=test.name, quantity=1.0,
                        price_unit=test.price or 0.0, taxes=test.tax_ids,
                        source_model=lab._name, source_id=lab.id,
                        service_type=test.service_type or 'lab',
                    ))
            elif lab.total_price:
                lines.append(service._prepare_invoice_line(
                    name=lab.test_id.name, quantity=1.0, price_unit=lab.total_price,
                    source_model=lab._name, source_id=lab.id, service_type='lab',
                ))
        for prescription in self.prescription_ids:
            product = prescription.medicine_id.product_variant_id
            lines.append(service._prepare_invoice_line(
                product=product, name=prescription.medicine_id.name,
                quantity=prescription.quantity or 1.0,
                price_unit=product.lst_price,
                source_model=prescription._name, source_id=prescription.id,
                service_type='medicine',
            ))
        for surgery in self.surgery_ids:
            price = getattr(surgery, 'amount', 0.0) or getattr(surgery, 'price', 0.0) or 0.0
            if price:
                lines.append(service._prepare_invoice_line(
                    name=surgery.display_name, quantity=1.0, price_unit=price,
                    source_model=surgery._name, source_id=surgery.id,
                    service_type='surgery',
                ))
        return lines

    def action_invoice(self):
        service = self.env['hospital.accounting.service']
        for record in self:
            if record.invoice_id and record.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for %s.') % record.name)
            invoice = service.create_customer_invoice(
                record.patient_id,
                record._prepare_ipd_invoice_lines(),
                origin=record.name,
                ref=record.name,
                hospital_context={
                    'hospital_patient_id': record.patient_id.id,
                    'hospital_inpatient_id': record.id,
                    'hospital_invoice_type': 'ipd',
                    'hospital_department': 'ipd',
                    'hospital_doctor_id': record.attending_doctor_id.id,
                },
            )
            record.write({'invoice_id': invoice.id, 'is_invoice': True, 'state': 'invoice'})
            record.test_ids.filtered(lambda item: not item.invoice_id).write({
                'invoice_id': invoice.id, 'invoiced': True,
            })
        return self[:1].action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
            'context': {'create': False},
        }

    def action_register_hospital_payment(self):
        self.ensure_one()
        return {
            'name': _('Register Hospital Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_invoice_id': self.invoice_id.id},
        }
