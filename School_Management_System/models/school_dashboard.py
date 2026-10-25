from odoo import api, fields, models


class SchoolDashboard(models.TransientModel):
    _name = 'school.dashboard'
    _description = 'School Dashboard'

    total_students = fields.Integer(string="Total Students")
    total_teachers = fields.Integer(string="Total Teachers")
    total_classes = fields.Integer(string="Total Classes")
    total_subjects = fields.Integer(string="Total Subjects")
    total_seats = fields.Integer(string="Total Seats")
    available_seats = fields.Integer(string="Available Seats")
    occupied_seats = fields.Integer(string="Occupied Seats")
    seat_usage_percent = fields.Float(string="Seat Usage")

    admission_draft = fields.Integer(string="Draft")
    admission_submitted = fields.Integer(string="Submitted")
    admission_under_review = fields.Integer(string="Under Review")
    admission_approved = fields.Integer(string="Approved")
    admission_rejected = fields.Integer(string="Rejected")
    admission_admitted = fields.Integer(string="Admitted")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update(self._compute_dashboard_values())
        return res

    def _compute_dashboard_values(self):
        student_class = self.env['student.class'].search([])

        total_seats = sum(student_class.mapped('total_seat'))
        available_seats = sum(student_class.mapped('available_seat'))
        occupied_seats = max(total_seats - available_seats, 0)

        values = {
            'total_students': self.env['school.student'].search_count([]),
            'total_teachers': self.env['school.teacher'].search_count([]),
            'total_classes': len(student_class),
            'total_subjects': self.env['school.subject'].search_count([]),
            'total_seats': total_seats,
            'available_seats': available_seats,
            'occupied_seats': occupied_seats,
            'seat_usage_percent': (occupied_seats / total_seats) if total_seats else 0,
            'admission_draft': self.env['student.admission'].search_count(
                [('state', '=', 'draft')]),
            'admission_submitted': self.env['student.admission'].search_count(
                [('state', '=', 'submitted')]),
            'admission_under_review': self.env['student.admission'].search_count(
                [('state', '=', 'under review')]),
            'admission_approved': self.env['student.admission'].search_count(
                [('state', '=', 'approved')]),
            'admission_rejected': self.env['student.admission'].search_count(
                [('state', '=', 'rejected')]),
            'admission_admitted': self.env['student.admission'].search_count(
                [('state', '=', 'admitted')]),
        }
        return values

    def action_refresh(self):
        self.ensure_one()
        self.write(self._compute_dashboard_values())
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'school.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_students(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Students',
            'res_model': 'school.student',
            'view_mode': 'tree,form',
        }

    def action_view_teachers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Teachers',
            'res_model': 'school.teacher',
            'view_mode': 'tree,form',
        }

    def action_view_classes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Classes',
            'res_model': 'student.class',
            'view_mode': 'tree',
        }

    def action_view_subjects(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subjects',
            'res_model': 'school.subject',
            'view_mode': 'tree,form',
        }

    def action_view_admission_draft(self):
        return self._action_view_admissions('draft', 'Draft Admissions')

    def action_view_admission_submitted(self):
        return self._action_view_admissions('submitted', 'Submitted Admissions')

    def action_view_admission_under_review(self):
        return self._action_view_admissions('under review', 'Admissions Under Review')

    def action_view_admission_approved(self):
        return self._action_view_admissions('approved', 'Approved Admissions')

    def action_view_admission_rejected(self):
        return self._action_view_admissions('rejected', 'Rejected Admissions')

    def action_view_admission_admitted(self):
        return self._action_view_admissions('admitted', 'Admitted Students')

    def _action_view_admissions(self, state, title):
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'student.admission',
            'view_mode': 'tree,form',
            'domain': [('state', '=', state)],
        }
