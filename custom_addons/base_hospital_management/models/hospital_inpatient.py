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
import datetime
from odoo import api, fields, models


class HospitalInpatient(models.Model):
    """Class holding inpatient details"""
    _name = 'hospital.inpatient'
    _description = 'Inpatient'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    patient_id = fields.Many2one('res.partner', string="Patient",
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 required=True, help='Choose the patient')
    name = fields.Char(string="Sequence Number", store=True,
                       copy=False, readonly=True, index=True,
                       help='Sequence number of inpatient for uniquely '
                            'identifying',
                       default=lambda self: 'New')
    reason = fields.Text(
        string="Reason For Admission",
        help="Current reason for hospitalization of the patient")
    bed_id = fields.Many2one('hospital.bed', string='Bed',
                             help='Choose the bed')
    room_id = fields.Many2one('patient.room', string='Room',
                              help='Choose the room to which patient admitted'
                                   ' to')
    building_id = fields.Many2one(
        'hospital.building', related='room_id.building_id',
        string="Block", help='Name of the block')
    room_building_id = fields.Many2one(
        'hospital.building', related='room_id.building_id',
        string="Room Building",
        help='Name of the building to which room belongs to')
    ward_id = fields.Many2one('hospital.ward',
                              related='bed_id.ward_id',
                              string='Ward',
                              help='Ward to which the bed belongs to')
    type_admission = fields.Selection([('emergency',
                                        'Emergency Admission'),
                                       ('routine', 'Routine Admission')],
                                      string="Admission Type",
                                      help='The type of admission',
                                      required=True)
    attending_doctor_id = fields.Many2one('hr.employee',
                                          string="Attending Doctor",
                                          required=True,
                                          help='Name of attending doctor',
                                          domain=[
                                              ('job_id.name', '=', 'Doctor')])
    operating_doctor_id = fields.Many2one('hr.employee',
                                          string="Operating Doctor",
                                          help='Name of operating doctor',
                                          domain=[
                                              ('job_id.name', '=', 'Doctor')])
    hosp_date = fields.Date(string="Admission Date",
                            help='Date of hospitalisation',
                            default=fields.Date.today())
    discharge_date = fields.Date(string="Discharge Date",
                                 help='Date of discharge', copy=False)
    condition = fields.Text(
        string="Condition Before Hospitalization",
        help="The condition of the patient before he/she is admitted to"
             " the hospital")
    nursing_plan_ids = fields.One2many('nursing.plan',
                                       'admission_id',
                                       string='Nursing Plan',
                                       help='Nursing plan of the inpatient')
    active = fields.Boolean(string='Active', default=True,
                            help='True for active inpatients')
    doctor_round_ids = fields.One2many('doctor.round',
                                       'admission_id',
                                       string='Doctor Rounds',
                                       help='Doctor rounds of the patient')
    discharge_plan = fields.Text(string="Discharge Plan",
                                 help='Discharge plan of the inpatient')
    notes = fields.Text(string="Notes", help='Notes regarding the inpatient')
    bed_rent = fields.Monetary(string='Rent Per Day', related='bed_id.bed_rent',
                               help='Rent for the bed')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help='Currency in which rent is calculating',
                                  default=lambda self: self.env.user.company_id
                                  .currency_id.id)
    state = fields.Selection([('draft', 'Draft'),
                              ('reserve', 'Reserved'),
                              ('admit', 'Admitted'),
                              ('dis', 'Discharge')],
                             string='State', readonly=True,
                             help='State of inpatient',
                             default="draft")
    bed_rent_amount = fields.Monetary(string="Total Bed Rent",
                                      help='Total rent '
                                           'for stayed '
                                           'days',
                                      compute='_compute_bed_rent_amount',
                                      copy=False)
    admit_days = fields.Integer(string='Days',
                                help='Number of days the inpatient admitted',
                                compute='_compute_admit_days',
                                copy=False)
    bed_type = fields.Selection([('gatch', 'Gatch Bed'),
                                 ('electric', 'Electric'),
                                 ('stretcher', 'Stretcher'),
                                 ('low', 'Low Bed'),
                                 ('air', 'Low Air Loss'),
                                 ('circo', 'Circo Electric'),
                                 ('clinitron', 'Clinitron'),
                                 ], string="Bed Type",
                                help='Indicates the type of bed')
    is_ward = fields.Selection([('ward', 'Ward'), ('room', 'Room')],
                               string='Room/Ward',
                               help='Choose where the patient is admitted to')
    prescription_ids = fields.One2many('prescription.line',
                                       'inpatient_id',
                                       string='Prescription',
                                       help='Medical prescriptions of patient')
    enable_outpatient = fields.Boolean(string='Prescription History',
                                       help='If checked, the prescription '
                                            'history of the patient will be '
                                            'added')
    lab_test_ids = fields.One2many('patient.lab.test',
                                   'inpatient_id',
                                   string='Lab Test',
                                   help='Lab tests of the inpatient')
    test_count = fields.Integer(string='Test Created',
                                help='Number of tests of the inpatient',
                                compute='_compute_test_count')
    test_ids = fields.One2many('patient.lab.test',
                               'inpatient_id', string='Test Line',
                               help='Details of the lab test')
    surgery_ids = fields.One2many('inpatient.surgery',
                                  'inpatient_id',
                                  string='Surgery/Operation',
                                  help='Surgery details of the patient')
    room_rent = fields.Monetary(string='Rent per day', help='Rent for the room',
                                related='room_id.rent')
    room_rent_amount = fields.Monetary(string="Total Room Rent",
                                       compute='_compute_room_rent_amount',
                                       help='Total rent for the room',
                                       copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Sequence number generation"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hospital.inpatient') or 'New'
        return super().create(vals_list)

    @api.depends('test_ids')
    def _compute_test_count(self):
        """Method for computing test count"""
        self.test_count = self.env['lab.test.line'].sudo().search_count(
            [('id', 'in', self.test_ids.ids)])

    def _compute_admit_days(self):
        """Method for computing admit days"""
        if self.hosp_date:
            if self.discharge_date:
                self.admit_days = (self.discharge_date - self.hosp_date +
                                   datetime.timedelta(days=1)).days
            else:
                self.admit_days = (fields.date.today() - self.hosp_date +
                                   datetime.timedelta(days=1)).days

    @api.depends('hosp_date', 'discharge_date',
                 'admit_days', 'room_id')
    def _compute_room_rent_amount(self):
        """Method for computing room rent amount"""
        if self.hosp_date:
            if self.discharge_date:
                self.admit_days = (self.discharge_date - self.hosp_date +
                                   datetime.timedelta(days=1)).days
                self.room_rent_amount = self.room_id.rent * self.admit_days
            else:
                self.admit_days = (fields.date.today() - self.hosp_date +
                                   datetime.timedelta(days=1)).days
                self.room_rent_amount = self.room_id.rent * self.admit_days
        self.room_rent_amount = self.room_id.rent * self.admit_days

    @api.depends('hosp_date', 'discharge_date', 'room_rent_amount',
                 'admit_days')
    def _compute_bed_rent_amount(self):
        """Method for computing bed rent amount"""
        if self.hosp_date:
            if self.discharge_date:
                self.admit_days = (self.discharge_date - self.hosp_date +
                                   datetime.timedelta(days=1)).days
                self.bed_rent_amount = self.bed_id.bed_rent * self.admit_days
            else:
                self.admit_days = (fields.date.today() - self.hosp_date +
                                   datetime.timedelta(days=1)).days
                self.bed_rent_amount = self.bed_id.bed_rent * self.admit_days
        else:
            self.bed_rent_amount = self.bed_id.bed_rent

    @api.onchange('enable_outpatient')
    def _onchange_enable_outpatient(self):
        """Method for adding prescription lines of patient"""
        self.prescription_ids = False
        if self.enable_outpatient:
            outpatient_id = self.env['hospital.outpatient'].sudo().search(
                [('patient_id', '=', self.patient_id.id)])
            self.sudo().write({
                'prescription_ids': [(0, 0, {
                    'medicine_id': rec.medicine_id.id,
                    'quantity': rec.quantity,
                    'no_intakes': rec.no_intakes,
                    'note': rec.note,
                    'time': rec.time,
                }) for rec in outpatient_id.prescription_ids]
            })

    @api.onchange('bed_type')
    def _onchange_bed_type(self):
        """Method for filtering beds according to the bed type"""
        return {'domain': {
            'bed_id': [
                ('bed_type', '=', self.bed_type),
                ('state', '=', 'avail')
            ], 'room_id': [
                ('bed_type', '=', self.bed_type),
                ('state', '=', 'avail')
            ]}}

    def action_view_tests(self):
        """Returns all lab tests"""
        return {
            'name': 'Lab Tests',
            'res_model': 'patient.lab.test',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'domain': [('inpatient_id', '=', self.id)]
        }

    def action_create_lab_test(self):
        """Function for creating lab test"""
        return {
            'name': 'Create Lab Test',
            'res_model': 'lab.test.line',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.attending_doctor_id.id,
                'default_patient_type': 'inpatient',
                'default_ip_id': self.id
            }
        }

    def action_view_test(self):
        """View test details"""
        return {
            'name': 'Created Tests',
            'res_model': 'lab.test.line',
            'view_mode': 'list,form',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [
                ('patient_type', '=', 'inpatient'),
                ('ip_id', '=', self.id)
            ]
        }

    def action_reserve(self):
        """Method for inpatient reservation"""
        if self.bed_id:
            self.bed_id.state = 'not'
        if self.room_id:
            self.room_id.state = 'reserve'
        self.sudo().write({
            'state': "reserve"
        })

    def action_admit(self):
        """Method for patient admission"""
        if self.bed_id:
            self.bed_id.state = 'not'
        if self.room_id:
            self.room_id.state = 'not'
        self.sudo().write({
            'state': "admit"
        })

    def action_discharge(self):
        """Method for patient discharge"""
        if self.bed_id:
            self.bed_id.state = 'avail'
        if self.room_id:
            self.room_id.state = 'avail'
        self.sudo().write({
            'state': "dis"
        })
        self.active = False

    def create_new_in_patient(self, domain):
        """Create in-patient from receptionist dashboard"""
        if domain:
            patient = self.env['hospital.inpatient'].sudo().search(
                [('patient_id', '=', domain['patient_id'])])
            if patient:
                return 'Patient already exists'
            else:
                self.sudo().create({
                    'patient_id': domain['patient_id'],
                    'reason': domain['reason_of_admission'],
                    'type_admission': domain['admission_type'],
                    'attending_doctor_id': domain['attending_doctor_id'],
                })

    def fetch_inpatient(self, domain):
        """Returns inpatient details to display on the doctor's dashboard"""
        if domain:
            return self.env['hospital.inpatient'].sudo().search(
                ['|', '|', '|', '|', ('name', 'ilike', domain),
                 ('patient_id.name', 'ilike', domain),
                 ('hosp_date', 'ilike', domain),
                 ('discharge_date', 'ilike', domain),
                 ('state', 'ilike', domain)]).read(
                ['name', 'patient_id', 'ward_id', 'bed_id',
                 'hosp_date', 'discharge_date', 'type_admission',
                 'attending_doctor_id',
                 'state'])
        else:
            return self.env['hospital.inpatient'].sudo().search_read(
                fields=['name', 'patient_id', 'ward_id', 'bed_id', 'hosp_date',
                        'discharge_date', 'attending_doctor_id', 'state'])

    def action_print_prescription(self):
        """Method for printing prescription"""
        data = False
        p_list = []
        for rec in self.prescription_ids:
            p_list.append({
                'medicine': rec.medicine_id.name,
                'intake': rec.no_intakes,
                'time': rec.time.capitalize(),
                'quantity': rec.quantity,
                'note': rec.note.capitalize(),
            })
            data = {
                'datas': p_list,
                'date': fields.date.today(),
                'patient_name': self.patient_id.name,
                'doctor_name': self.attending_doctor_id.name,
            }
        return self.env.ref(
            'base_hospital_management.action_report_patient_prescription'). \
            report_action(self, data=data)

    @api.model
    def hospital_inpatient_list(self):
        """Returns list of inpatients to doctor's dashboard"""
        patient_list = []
        patients = self.sudo().search([])
        patient_type = {'emergency': 'Emergency Admission',
                        'routine': 'Routine Admission'}
        for rec in patients:
            patient_list.append({
                'id': rec.id,
                'name': rec.name,
                'patient_id': rec.patient_id.name,
                'bed_id': rec.bed_id.name,
                'ward_id': rec.ward_id.ward_no,
                'room_id': rec.room_id,
                'hosp_date': rec.hosp_date,
                'attending_doctor_id': rec.attending_doctor_id._origin.name,
                'admission_type': patient_type[rec.type_admission],
                'discharge_date': rec.discharge_date
            })
        return patient_list
