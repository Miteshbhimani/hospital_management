# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    hospital_staff_role = fields.Selection(
        selection=[
            ("doctor", "Doctor"),
            ("nurse", "Nurse"),
            ("receptionist", "Receptionist"),
            ("lab_technician", "Lab Technician"),
            ("pharmacist", "Pharmacist"),
            ("manager", "Hospital Manager"),
        ],
        string="Hospital Role",
        index=True,
        tracking=True,
        help="Hospital-specific role used to assign the correct Hospital Management security group.",
    )
    hospital_access_group_ids = fields.Many2many(
        "res.groups",
        string="Current Hospital Groups",
        compute="_compute_hospital_access_group_ids",
        help="Hospital Management groups currently assigned to the linked Odoo user.",
    )
    hospital_access_state = fields.Selection(
        selection=[
            ("no_user", "No User"),
            ("missing_role", "Missing Role"),
            ("to_sync", "To Sync"),
            ("synced", "Synced"),
        ],
        string="Access State",
        compute="_compute_hospital_access_state",
    )
    hospital_last_access_sync = fields.Datetime(
        string="Last Access Sync",
        readonly=True,
        copy=False,
    )

    _HOSPITAL_ROLE_GROUP_XMLIDS = {
        "doctor": "base_hospital_management.base_hospital_management_group_doctor",
        "nurse": "base_hospital_management.base_hospital_management_group_nurse",
        "receptionist": "base_hospital_management.base_hospital_management_group_receptionist",
        "lab_technician": "base_hospital_management.base_hospital_management_group_lab_assistant",
        "pharmacist": "base_hospital_management.base_hospital_management_group_pharmacist",
        "manager": "base_hospital_management.base_hospital_management_group_manager",
    }

    _HOSPITAL_ROLE_JOB_NAMES = {
        "doctor": "Doctor",
        "nurse": "Nurse",
        "receptionist": "Receptionist",
        "lab_technician": "Lab Technician",
        "pharmacist": "Pharmacist",
        "manager": "Hospital Manager",
    }

    def _hospital_group_records(self):
        groups = self.env["res.groups"].sudo()
        for xmlid in self._HOSPITAL_ROLE_GROUP_XMLIDS.values():
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                groups |= group
        return groups

    def _hospital_role_group(self, role):
        xmlid = self._HOSPITAL_ROLE_GROUP_XMLIDS.get(role)
        group = self.env.ref(xmlid, raise_if_not_found=False) if xmlid else False
        if not group:
            raise UserError(_("The security group for role %s was not found.") % (role or ""))
        return group

    def _ensure_hospital_job(self, role, company=None):
        job_name = self._HOSPITAL_ROLE_JOB_NAMES.get(role)
        if not job_name:
            return False
        company = company or self.env.company
        Job = self.env["hr.job"].sudo()
        job = Job.search([
            ("name", "=", job_name),
            "|", ("company_id", "=", False), ("company_id", "=", company.id),
        ], limit=1)
        if not job:
            job = Job.create({"name": job_name, "company_id": company.id})
        return job

    def _prepare_hospital_role_values(self, role):
        self.ensure_one()
        vals = {"doctor": role == "doctor"}
        job = self._ensure_hospital_job(role, self.company_id or self.env.company)
        if job:
            vals["job_id"] = job.id
            vals["job_title"] = job.name
        return vals

    def _require_hospital_access_manager(self):
        if self.env.is_superuser():
            return
        if self.env.user.has_group("base.group_system"):
            return
        if self.env.user.has_group("base_hospital_management.base_hospital_management_group_manager"):
            return
        raise AccessError(_("Only Hospital Managers or system administrators can manage hospital staff access."))

    @api.depends("user_id", "user_id.groups_id")
    def _compute_hospital_access_group_ids(self):
        hospital_groups = self._hospital_group_records()
        for employee in self:
            employee.hospital_access_group_ids = employee.user_id.groups_id & hospital_groups if employee.user_id else False

    @api.depends("user_id", "hospital_staff_role", "hospital_access_group_ids")
    def _compute_hospital_access_state(self):
        for employee in self:
            if not employee.user_id:
                employee.hospital_access_state = "no_user"
                continue
            if not employee.hospital_staff_role:
                employee.hospital_access_state = "missing_role"
                continue
            expected_group = employee._hospital_role_group(employee.hospital_staff_role)
            employee.hospital_access_state = "synced" if expected_group in employee.hospital_access_group_ids else "to_sync"

    @api.model_create_multi
    def create(self, vals_list):
        employees = self.env["hr.employee"]
        remaining_vals = []
        for vals in vals_list:
            role = vals.get("hospital_staff_role")
            if role:
                company = self.env["res.company"].browse(vals.get("company_id")) if vals.get("company_id") else self.env.company
                job = self._ensure_hospital_job(role, company)
                vals = dict(vals)
                vals["doctor"] = role == "doctor"
                if job:
                    vals.setdefault("job_id", job.id)
                    vals.setdefault("job_title", job.name)
            remaining_vals.append(vals)
        employees = super().create(remaining_vals)
        return employees

    def write(self, vals):
        if "hospital_staff_role" in vals and vals.get("hospital_staff_role"):
            result = True
            for employee in self:
                role_vals = employee._prepare_hospital_role_values(vals["hospital_staff_role"])
                merged_vals = dict(vals, **role_vals)
                result = super(HrEmployee, employee).write(merged_vals) and result
            return result
        return super().write(vals)

    def _sync_hospital_user_groups(self, user, role):
        self.ensure_one()
        role_group = self._hospital_role_group(role)
        internal_group = self.env.ref("base.group_user")
        # Keep existing hospital groups. Odoo access rights are additive, so one
        # user can correctly be both Manager and Nurse, Doctor and Pharmacist, etc.
        # The access-rights menus use actual group membership, not only the primary
        # employee role, so removing other hospital groups here would hide valid
        # multi-role users from their secondary role menus.
        user.sudo().write({"groups_id": [(4, internal_group.id), (4, role_group.id)]})
        return role_group

    def action_apply_hospital_access(self):
        self._require_hospital_access_manager()
        for employee in self:
            if not employee.hospital_staff_role:
                raise UserError(_("Please select a Hospital Role for %s.") % employee.name)
            if not employee.user_id:
                raise UserError(_("%s has no linked Odoo user. Use 'Create / Update User Access' first.") % employee.name)
            role_vals = employee._prepare_hospital_role_values(employee.hospital_staff_role)
            if role_vals:
                employee.sudo().write(role_vals)
            employee._sync_hospital_user_groups(employee.user_id, employee.hospital_staff_role)
            employee.sudo().write({"hospital_last_access_sync": fields.Datetime.now()})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Hospital access updated"),
                "message": _("The selected staff access rights were synchronized."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_open_hospital_access_wizard(self):
        self.ensure_one()
        self._require_hospital_access_manager()
        return {
            "name": _("Create / Update Hospital User Access"),
            "type": "ir.actions.act_window",
            "res_model": "hospital.staff.access.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_employee_id": self.id,
                "default_hospital_staff_role": self.hospital_staff_role,
                "default_login": self.work_email or (self.user_id.login if self.user_id else False),
                "default_user_id": self.user_id.id if self.user_id else False,
            },
        }

    def action_open_related_user(self):
        self.ensure_one()
        if not self.user_id:
            raise UserError(_("This staff member has no linked Odoo user."))
        return {
            "name": _("User"),
            "type": "ir.actions.act_window",
            "res_model": "res.users",
            "view_mode": "form",
            "res_id": self.user_id.id,
            "target": "current",
        }
