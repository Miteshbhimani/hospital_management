# -*- coding: utf-8 -*-
"""Phase 3 billing package and corporate billing extensions for OPD/IPD invoices."""

from odoo import _, models
from odoo.exceptions import UserError


class HospitalOutpatient(models.Model):
    _inherit = 'hospital.outpatient'

    def create_invoice(self):
        service = self.env['hospital.accounting.service']
        for record in self:
            if record.invoice_id and record.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for %s.') % record.display_name)
            if record.billing_package_id:
                lines = record.billing_package_id._prepare_invoice_lines()
                billing_mode = 'package'
            else:
                doctor = record.doctor_id.doctor_id
                product = doctor.consultation_product_id or self.env.ref(
                    'hospital_accounting_management.product_hospital_consultation',
                    raise_if_not_found=False,
                )
                lines = [service._prepare_invoice_line(
                    product=product,
                    name=_('Consultation fee - %s') % (doctor.name or ''),
                    quantity=1.0,
                    price_unit=doctor.consultancy_charge or (product.lst_price if product else 0.0),
                    source_model=record._name,
                    source_id=record.id,
                    service_type='consultation',
                )]
                billing_mode = 'cash'
            if record.corporate_contract_id:
                billing_mode = 'corporate'
            invoice_partner = record.corporate_contract_id.partner_id if record.corporate_contract_id and billing_mode == 'corporate' else record.patient_id
            invoice = service.create_customer_invoice(
                invoice_partner,
                lines,
                origin=record.op_reference,
                ref=record.op_reference,
                hospital_context={
                    'hospital_patient_id': record.patient_id.id,
                    'hospital_outpatient_id': record.id,
                    'hospital_invoice_type': 'opd',
                    'hospital_department': 'opd',
                    'hospital_doctor_id': record.doctor_id.doctor_id.id,
                    'corporate_contract_id': record.corporate_contract_id.id,
                    'hospital_package_id': record.billing_package_id.id,
                    'billing_mode': billing_mode,
                    'invoice_payment_term_id': record.corporate_contract_id.payment_term_id.id if record.corporate_contract_id.payment_term_id else False,
                },
            )
            if record.corporate_contract_id:
                invoice.action_approve_credit_billing()
            service.create_charge_capture_from_invoice(
                invoice,
                patient=record.patient_id,
                department_area='opd',
                doctor=record.doctor_id.doctor_id,
                outpatient=record,
                payer_type='corporate' if billing_mode == 'corporate' else 'patient',
            )
            record.write({'invoice_id': invoice.id, 'invoiced': True, 'state': 'invoice'})
        return True


class HospitalInpatient(models.Model):
    _inherit = 'hospital.inpatient'

    def _prepare_ipd_invoice_lines(self):
        self.ensure_one()
        if self.billing_package_id:
            return self.billing_package_id._prepare_invoice_lines()
        return super()._prepare_ipd_invoice_lines()

    def action_invoice(self):
        service = self.env['hospital.accounting.service']
        for record in self:
            if record.invoice_id and record.invoice_id.state != 'cancel':
                raise UserError(_('Invoice already exists for %s.') % record.name)
            billing_mode = 'package' if record.billing_package_id else 'cash'
            if record.corporate_contract_id:
                billing_mode = 'corporate'
            invoice_partner = record.corporate_contract_id.partner_id if record.corporate_contract_id and billing_mode == 'corporate' else record.patient_id
            invoice = service.create_customer_invoice(
                invoice_partner,
                record._prepare_ipd_invoice_lines(),
                origin=record.name,
                ref=record.name,
                hospital_context={
                    'hospital_patient_id': record.patient_id.id,
                    'hospital_inpatient_id': record.id,
                    'hospital_invoice_type': 'ipd',
                    'hospital_department': 'ipd',
                    'hospital_doctor_id': record.attending_doctor_id.id,
                    'corporate_contract_id': record.corporate_contract_id.id,
                    'hospital_package_id': record.billing_package_id.id,
                    'billing_mode': billing_mode,
                    'invoice_payment_term_id': record.corporate_contract_id.payment_term_id.id if record.corporate_contract_id.payment_term_id else False,
                },
            )
            if record.corporate_contract_id:
                invoice.action_approve_credit_billing()
            service.create_charge_capture_from_invoice(
                invoice,
                patient=record.patient_id,
                department_area='ipd',
                doctor=record.attending_doctor_id,
                inpatient=record,
                payer_type='corporate' if billing_mode == 'corporate' else 'patient',
            )
            record.write({'invoice_id': invoice.id, 'is_invoice': True, 'state': 'invoice'})
            record.test_ids.filtered(lambda item: not item.invoice_id).write({'invoice_id': invoice.id, 'invoiced': True})
        return self[:1].action_view_invoice()
