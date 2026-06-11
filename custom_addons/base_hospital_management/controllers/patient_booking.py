# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, http
from odoo.http import request


class PatientBooking(http.Controller):
    """Secure patient self-booking controller."""

    def _portal_partner(self):
        if request.env.user._is_public():
            return False
        return request.env.user.partner_id

    @http.route('/patient_booking', type='http', auth='user', website=True)
    def patient_booking(self):
        """Render booking form for logged-in users only."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')
        values = {
            'user': request.env.user.name,
            'date': fields.Date.today(),
            'departments': [],
            'card': False,
            'attachment_id': False,
        }
        return request.render('base_hospital_management.patient_booking_form', values)

    @http.route('/patient_booking/success', type='http', auth='user', website=True, methods=['POST'])
    def patient_booking_submit(self, **kw):
        """Create a self-service OPD booking after validating user and doctor allocation."""
        partner = self._portal_partner()
        if not partner:
            return request.redirect('/web/login')

        doctor_allocation_id = kw.get('doctor-name')
        booking_date = kw.get('date')
        if not doctor_allocation_id or not booking_date:
            return request.redirect('/patient_booking')

        try:
            doctor_allocation_id = int(doctor_allocation_id)
        except (TypeError, ValueError):
            return request.not_found()

        allocation = request.env['doctor.allocation'].sudo().search([
            ('id', '=', doctor_allocation_id),
            ('date', '=', booking_date),
            ('state', '=', 'confirm'),
            ('slot_remaining', '>', 0),
        ], limit=1)
        if not allocation:
            return request.not_found()

        already_booked = request.env['hospital.outpatient'].sudo().search_count([
            ('patient_id', '=', partner.id),
            ('doctor_id', '=', allocation.id),
            ('op_date', '=', booking_date),
            ('state', '!=', 'cancel'),
        ])
        if already_booked:
            return request.redirect('/my/op')

        if partner.patient_seq in ['New', 'User', 'Employee']:
            partner.sudo().write({
                'patient_seq': request.env['ir.sequence'].sudo().next_by_code('patient.sequence') or 'New'
            })

        op = request.env['hospital.outpatient'].sudo().create({
            'patient_id': partner.id,
            'doctor_id': allocation.id,
            'op_date': booking_date,
            'reason': kw.get('reason') or '',
        })
        op.action_confirm()
        return request.redirect('/my/home')

    @http.route('/patient_booking/get_doctors', type='json', auth='user', website=True)
    def update_doctors(self, **kw):
        """Return valid doctor allocations for the selected date and optional department."""
        partner = self._portal_partner()
        if not partner:
            return {'doctors': [], 'departments': []}

        selected_date = kw.get('selected_date') or fields.Date.today()
        domain = [
            ('date', '=', selected_date),
            ('state', '=', 'confirm'),
            ('slot_remaining', '>', 0),
        ]
        department = kw.get('department')
        if department:
            try:
                domain.append(('doctor_id.department_id.id', '=', int(department)))
            except (TypeError, ValueError):
                return {'doctors': [], 'departments': []}

        departments = []
        department_ids = set()
        doctors = []
        allocations = request.env['doctor.allocation'].sudo().search(domain, order='name asc')
        for rec in allocations:
            if partner in rec.mapped('op_ids.patient_id'):
                continue
            doctors.append({'id': rec.id, 'name': rec.name})
            if rec.department_id and rec.department_id.id not in department_ids:
                departments.append({'id': rec.department_id.id, 'name': rec.department_id.name})
                department_ids.add(rec.department_id.id)
        return {'doctors': doctors, 'departments': departments}
