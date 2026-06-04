# -*- coding: utf-8 -*-
"""Appointment and queue management."""
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HospitalAppointment(models.Model):
    """Doctor-wise appointment booking, queue and no-show tracking."""
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment and Queue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc, priority desc, token_number asc'

    name = fields.Char(string='Appointment No.', required=True, readonly=True, copy=False, default='New')
    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True, tracking=True,
        domain=[('patient_seq', 'not in', ['New', 'Employee', 'User'])]
    )
    doctor_id = fields.Many2one(
        'hr.employee', string='Doctor', tracking=True,
        domain=[('job_id.name', '=', 'Doctor')]
    )
    department_id = fields.Many2one('hr.department', string='Department')
    appointment_date = fields.Datetime(string='Appointment Date', required=True, default=fields.Datetime.now, tracking=True)
    source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('online', 'Online'),
        ('phone', 'Phone'),
        ('website', 'Website'),
        ('doctor_referral', 'Doctor Referral'),
        ('insurance_tpa', 'Insurance / TPA'),
        ('corporate', 'Corporate Tie-up'),
        ('camp', 'Health Camp'),
        ('teleconsultation', 'Teleconsultation'),
        ('emergency', 'Emergency'),
    ], string='Booking Source', default='walk_in', tracking=True)
    visit_type = fields.Selection([
        ('new', 'New Visit'),
        ('follow_up', 'Follow-up'),
        ('review', 'Report Review'),
        ('teleconsultation', 'Teleconsultation'),
        ('emergency', 'Emergency'),
    ], string='Visit Type', default='new', tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Priority'),
        ('2', 'Emergency')
    ], string='Queue Priority', default='0', tracking=True)
    token_number = fields.Integer(string='Token No.', copy=False, readonly=True)
    chief_complaint = fields.Text(string='Chief Complaint / Symptoms')
    notes = fields.Text(string='Internal Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('no_show', 'No-show'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    checked_in_at = fields.Datetime(string='Checked-in At', readonly=True)
    consultation_started_at = fields.Datetime(string='Consultation Started At', readonly=True)
    completed_at = fields.Datetime(string='Completed At', readonly=True)
    waiting_minutes = fields.Float(string='Waiting Minutes', compute='_compute_waiting_minutes', store=True)
    no_show_reason = fields.Char(string='No-show / Cancellation Reason')
    outpatient_id = fields.Many2one('hospital.outpatient', string='Related OPD')

    _sql_constraints = [
        ('hospital_appointment_name_unique', 'unique(name)', 'Appointment number must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or 'New'
            if not vals.get('token_number'):
                vals['token_number'] = self._next_token(vals.get('appointment_date'), vals.get('doctor_id'))
        return super().create(vals_list)

    @api.depends('checked_in_at', 'consultation_started_at')
    def _compute_waiting_minutes(self):
        for rec in self:
            if rec.checked_in_at and rec.consultation_started_at:
                delta = rec.consultation_started_at - rec.checked_in_at
                rec.waiting_minutes = delta.total_seconds() / 60.0
            else:
                rec.waiting_minutes = 0.0

    def _next_token(self, appointment_date=None, doctor_id=None):
        domain = []
        if appointment_date:
            date_value = fields.Datetime.to_datetime(appointment_date).date()
            start_dt = datetime.datetime.combine(date_value, datetime.time.min)
            end_dt = datetime.datetime.combine(date_value, datetime.time.max)
            domain += [
                ('appointment_date', '>=', fields.Datetime.to_string(start_dt)),
                ('appointment_date', '<=', fields.Datetime.to_string(end_dt)),
            ]
        if doctor_id:
            domain.append(('doctor_id', '=', doctor_id))
        last = self.search(domain, order='token_number desc', limit=1)
        return (last.token_number or 0) + 1

    def action_schedule(self):
        self.write({'state': 'scheduled'})

    def action_check_in(self):
        self.write({'state': 'checked_in', 'checked_in_at': fields.Datetime.now()})

    def action_start_consultation(self):
        self.write({'state': 'in_consultation', 'consultation_started_at': fields.Datetime.now()})

    def action_done(self):
        self.write({'state': 'done', 'completed_at': fields.Datetime.now()})

    def action_no_show(self):
        self.write({'state': 'no_show'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_opd(self):
        for appointment in self:
            if appointment.outpatient_id:
                continue
            if not appointment.doctor_id:
                raise ValidationError(_('Select a doctor before creating an OPD visit.'))
            allocation = self.env['doctor.allocation'].search([
                ('doctor_id', '=', appointment.doctor_id.id),
                ('date', '=', fields.Date.context_today(appointment)),
                ('state', '=', 'confirm'),
            ], limit=1)
            if not allocation:
                raise ValidationError(_('No confirmed doctor allocation found for today.'))
            appointment.outpatient_id = self.env['hospital.outpatient'].create({
                'patient_id': appointment.patient_id.id,
                'doctor_id': allocation.id,
                'op_date': fields.Date.context_today(appointment),
                'reason': appointment.chief_complaint,
            }).id
        return {
            'type': 'ir.actions.act_window',
            'name': _('OPD Visit'),
            'res_model': 'hospital.outpatient',
            'view_mode': 'form',
            'res_id': self.outpatient_id.id,
        }
