# -*- coding: utf-8 -*-
"""Backend payloads for the OWL hospital role dashboards."""
from datetime import datetime, time, timedelta

from odoo import api, fields, models


class HospitalDashboardService(models.AbstractModel):
    """Small service layer used by OWL client actions.

    Keeping dashboard aggregation here avoids fragile browser-side counting,
    keeps domains consistent with Odoo security, and makes the old dashboards
    reusable as modern OWL screens.
    """
    _name = 'hospital.dashboard.service'
    _description = 'Hospital Dashboard Service'

    def _today_bounds(self):
        today = fields.Date.context_today(self)
        start = datetime.combine(today, time.min)
        end = start + timedelta(days=1)
        return today, fields.Datetime.to_string(start), fields.Datetime.to_string(end)

    def _patient_domain(self):
        return [('patient_seq', 'not in', ['New', 'Employee', 'User'])]

    def _doctor_domain_for_user(self):
        employees = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        return [('doctor_id', 'in', employees.ids)] if employees else []

    def _count(self, model_name, domain=None):
        return self.env[model_name].sudo().search_count(domain or [])

    def _search_read(self, model_name, domain=None, field_names=None, limit=10, order=None):
        return self.env[model_name].sudo().search_read(domain or [], field_names or [], limit=limit, order=order)

    def _doctors(self):
        return self._search_read(
            'hr.employee',
            [('job_id.name', '=', 'Doctor')],
            ['name', 'work_phone', 'user_id'],
            limit=200,
            order='name asc',
        )

    def _low_stock_medicines(self, limit=None):
        """Return medicine templates with low stock, safely sorted in Python.

        product.template.qty_available is a computed, non-stored inventory
        quantity. It can be read from the ORM, but it must not be used in an
        SQL ORDER BY clause. The dashboard therefore reads medicine records
        with a stored-field order, then filters and sorts the computed stock
        quantity after the ORM has populated it.
        """
        medicines = self.env['product.template'].sudo().search(
            [('medicine_ok', '=', True)],
            order='name asc',
        )
        low_stock = medicines.filtered(lambda product: product.qty_available <= 5)
        sorted_products = low_stock.sorted(lambda product: (product.qty_available, product.name or ''))
        if limit:
            sorted_products = sorted_products[:limit]
        return [{
            'id': product.id,
            'name': product.name,
            'list_price': product.list_price,
            'qty_available': product.qty_available,
            'medicine_brand_id': [product.medicine_brand_id.id, product.medicine_brand_id.display_name] if product.medicine_brand_id else False,
        } for product in sorted_products]

    def _patients(self, limit=200):
        return self._search_read(
            'res.partner',
            self._patient_domain(),
            ['name', 'patient_seq', 'phone', 'email', 'date_of_birth', 'gender', 'blood_group', 'rh_type'],
            limit=limit,
            order='name asc',
        )

    @api.model
    def get_reception_dashboard(self):
        today, start_dt, end_dt = self._today_bounds()
        appointment_today_domain = [
            ('appointment_date', '>=', start_dt),
            ('appointment_date', '<', end_dt),
            ('state', 'not in', ['cancelled']),
        ]
        queue_domain = [
            ('appointment_date', '>=', start_dt),
            ('appointment_date', '<', end_dt),
            ('state', 'in', ['draft', 'scheduled', 'checked_in', 'in_consultation']),
        ]
        return {
            'kpis': {
                'patients': self._count('res.partner', self._patient_domain()),
                'patients_today': self._count('res.partner', self._patient_domain() + [('create_date', '>=', start_dt), ('create_date', '<', end_dt)]),
                'appointments_today': self._count('hospital.appointment', appointment_today_domain),
                'queue_waiting': self._count('hospital.appointment', queue_domain),
                'opd_today': self._count('hospital.outpatient', [('op_date', '=', today), ('state', '!=', 'cancel')]),
                'ipd_admitted': self._count('hospital.inpatient', [('state', '=', 'admit')]),
                'available_beds': self._count('hospital.bed', [('state', '=', 'avail')]),
                'available_rooms': self._count('patient.room', [('state', '=', 'avail')]),
                'active_emergency': self._count('hospital.emergency.case', [('state', 'in', ['draft', 'triaged', 'under_treatment'])]),
            },
            'patients': self._patients(),
            'doctors': self._doctors(),
            'appointments': self._search_read(
                'hospital.appointment',
                queue_domain,
                ['name', 'patient_id', 'doctor_id', 'appointment_date', 'token_number', 'priority', 'visit_type', 'state', 'chief_complaint'],
                limit=20,
                order='priority desc, token_number asc, appointment_date asc',
            ),
            'rooms': self._search_read(
                'patient.room', [], ['name', 'building_id', 'floor_no', 'bed_type', 'rent', 'state'], limit=20, order='name asc'
            ),
            'wards': self._search_read(
                'hospital.ward', [], ['ward_no', 'building_id', 'floor_no', 'bed_count'], limit=20, order='ward_no asc'
            ),
        }

    @api.model
    def get_doctor_dashboard(self):
        today, start_dt, end_dt = self._today_bounds()
        doctor_domain = self._doctor_domain_for_user()
        appointment_today_domain = doctor_domain + [
            ('appointment_date', '>=', start_dt),
            ('appointment_date', '<', end_dt),
            ('state', 'not in', ['cancelled', 'done', 'no_show']),
        ]
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        surgery_domain = []
        if employee:
            surgery_domain.append(('doctor_id', '=', employee.id))
        return {
            'kpis': {
                'appointments_today': self._count('hospital.appointment', appointment_today_domain),
                'waiting': self._count('hospital.appointment', appointment_today_domain + [('state', 'in', ['draft', 'scheduled', 'checked_in'])]),
                'opd_today': self._count('hospital.outpatient', [('op_date', '=', today), ('state', '!=', 'cancel')]),
                'admitted': self._count('hospital.inpatient', [('state', '=', 'admit')]),
                'surgeries': self._count('inpatient.surgery', surgery_domain + [('state', 'in', ['draft', 'confirmed'])]),
                'abnormal_vitals': self._count('hospital.vitals', [('abnormal', '=', True), ('recorded_at', '>=', start_dt), ('recorded_at', '<', end_dt)]),
            },
            'patients': self._patients(),
            'queue': self._search_read(
                'hospital.appointment',
                appointment_today_domain,
                ['name', 'patient_id', 'doctor_id', 'appointment_date', 'token_number', 'priority', 'state', 'chief_complaint'],
                limit=20,
                order='priority desc, token_number asc, appointment_date asc',
            ),
            'vitals': self._search_read(
                'hospital.vitals',
                [('abnormal', '=', True)],
                ['name', 'patient_id', 'recorded_at', 'temperature_c', 'pulse_rate', 'systolic_bp', 'diastolic_bp', 'spo2', 'triage_category', 'abnormal_reason'],
                limit=10,
                order='recorded_at desc',
            ),
            'surgeries': self._search_read(
                'inpatient.surgery',
                surgery_domain,
                ['name', 'inpatient_id', 'doctor_id', 'planned_date', 'hours_to_take', 'state'],
                limit=10,
                order='planned_date asc',
            ),
        }

    @api.model
    def get_lab_dashboard(self):
        today, start_dt, end_dt = self._today_bounds()
        return {
            'kpis': {
                'new_requests': self._count('lab.test.line', [('state', '=', 'draft')]),
                'processing': self._count('patient.lab.test', [('state', '=', 'test')]),
                'draft_tests': self._count('patient.lab.test', [('state', '=', 'draft')]),
                'completed_today': self._count('patient.lab.test', [('state', '=', 'completed'), ('write_date', '>=', start_dt), ('write_date', '<', end_dt)]),
                'published_results': self._count('lab.test.result', [('attachment', '!=', False)]),
                'catalog_tests': self._count('lab.test', []),
            },
            'new_requests': self._search_read(
                'lab.test.line',
                [('state', '=', 'draft')],
                ['name', 'patient_id', 'doctor_id', 'date', 'patient_type', 'op_id', 'ip_id', 'test_ids', 'state'],
                limit=20,
                order='date asc, id asc',
            ),
            'in_process': self._search_read(
                'patient.lab.test',
                [('state', 'in', ['draft', 'test'])],
                ['test_id', 'patient_id', 'patient_type', 'date', 'total_price', 'state', 'lab_id'],
                limit=20,
                order='date asc, id asc',
            ),
            'published': self._search_read(
                'lab.test.result',
                [('attachment', '!=', False)],
                ['parent_id', 'patient_id', 'test_id', 'result', 'normal', 'uom_id'],
                limit=10,
                order='write_date desc',
            ),
        }

    @api.model
    def get_pharmacy_dashboard(self):
        today, start_dt, end_dt = self._today_bounds()
        orders_today = self.env['sale.order'].sudo().search([
            ('date_order', '>=', start_dt),
            ('date_order', '<', end_dt),
            ('partner_id.patient_seq', 'not in', ['New', 'Employee', 'User']),
        ])
        low_stock_medicines = self._low_stock_medicines()
        return {
            'kpis': {
                'medicines': self._count('product.template', [('medicine_ok', '=', True)]),
                'vaccines': self._count('product.template', [('vaccine_ok', '=', True)]),
                'low_stock': len(low_stock_medicines),
                'orders_today': len(orders_today),
                'sales_today': sum(orders_today.mapped('amount_total')),
                'pending_orders': self._count('sale.order', [('partner_id.patient_seq', 'not in', ['New', 'Employee', 'User']), ('state', 'in', ['draft', 'sent'])]),
            },
            'currency': self.env.company.currency_id.symbol or '',
            'patients': self._patients(),
            'medicines': self._search_read(
                'product.template',
                [('medicine_ok', '=', True)],
                ['name', 'list_price', 'qty_available', 'medicine_brand_id', 'uom_id'],
                limit=500,
                order='name asc',
            ),
            'low_stock': low_stock_medicines[:20],
            'orders': self._search_read(
                'sale.order',
                [('partner_id.patient_seq', 'not in', ['New', 'Employee', 'User'])],
                ['name', 'date_order', 'partner_id', 'amount_total', 'state'],
                limit=12,
                order='date_order desc',
            ),
        }
