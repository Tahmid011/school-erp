from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolExam(models.Model):
    _name = 'school.exam'
    _description = 'School Exam'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'exam_date desc'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    name = fields.Char(string="Exam Name", required=True, tracking=True,
                        help="E.g. 'Midterm Exam 2026' or 'Unit Test - Chapter 3'")
    exam_code = fields.Char(string="Exam Code", default='New', readonly=True, copy=False)

    exam_type = fields.Selection([
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('midterm', 'Midterm'),
        ('final', 'Final'),
        ('other', 'Other'),
    ], string="Exam Type", default='midterm', required=True, tracking=True)

    subject_id = fields.Many2one('school.subject', string="Subject", required=True, tracking=True)
    class_id = fields.Many2one(
        'student.class', string="Class", related='subject_id.class_id',
        store=True, readonly=True
    )
    # Derived from the subject so a teacher can only ever schedule exams for
    # subjects they are actually assigned to teach (see subject_id constraint below).
    teacher_id = fields.Many2one(
        'school.teacher', string="Teacher", related='subject_id.teacher_id',
        store=True, readonly=True, tracking=True
    )

    exam_date = fields.Date(string="Exam Date", required=True, tracking=True)
    total_marks = fields.Float(string="Total Marks", required=True, default=100.0, tracking=True)
    passing_marks = fields.Float(string="Passing Marks", required=True, default=40.0, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Marks Entry'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)

    note = fields.Text(string="Notes")

    result_ids = fields.One2many('school.exam.result', 'exam_id', string="Student Results")

    student_count = fields.Integer(string="Students", compute='_compute_stats')
    absent_count = fields.Integer(string="Absent", compute='_compute_stats')
    pass_count = fields.Integer(string="Passed", compute='_compute_stats')
    fail_count = fields.Integer(string="Failed", compute='_compute_stats')
    average_marks = fields.Float(string="Average Marks", compute='_compute_stats')
    highest_marks = fields.Float(string="Highest Marks", compute='_compute_stats')
    lowest_marks = fields.Float(string="Lowest Marks", compute='_compute_stats')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('exam_code', 'New') == 'New':
                vals['exam_code'] = self.env['ir.sequence'].next_by_code('school.exam') or 'New'
        return super().create(vals_list)

    @api.depends(
        'result_ids.marks_obtained', 'result_ids.is_absent', 'result_ids.result_status'
    )
    def _compute_stats(self):
        for rec in self:
            results = rec.result_ids
            present = results.filtered(lambda r: not r.is_absent)
            rec.student_count = len(results)
            rec.absent_count = len(results) - len(present)
            rec.pass_count = len(results.filtered(lambda r: r.result_status == 'pass'))
            rec.fail_count = len(results.filtered(lambda r: r.result_status == 'fail'))
            rec.average_marks = sum(present.mapped('marks_obtained')) / len(present) if present else 0.0
            rec.highest_marks = max(present.mapped('marks_obtained')) if present else 0.0
            rec.lowest_marks = min(present.mapped('marks_obtained')) if present else 0.0

    @api.constrains('subject_id')
    def _check_teacher_owns_subject(self):
        """A teacher (non-admin) may only create/keep exams for subjects assigned to them."""
        for rec in self:
            if self.env.user.has_group('School_Management_System.group_school_admin'):
                continue
            if not self.env.user.has_group('School_Management_System.group_school_teacher'):
                continue
            if rec.subject_id and rec.subject_id.teacher_id.user_id != self.env.user:
                raise ValidationError(
                    "You can only create or manage exams for subjects assigned to you."
                )

    @api.constrains('passing_marks', 'total_marks')
    def _check_passing_marks(self):
        for rec in self:
            if rec.total_marks <= 0:
                raise ValidationError("Total marks must be greater than zero.")
            if rec.passing_marks < 0 or rec.passing_marks > rec.total_marks:
                raise ValidationError("Passing marks must be between 0 and the total marks.")

    def action_start(self):
        """Move to 'Marks Entry' and auto-generate a result line for every student in the class."""
        for rec in self:
            if rec.state != 'draft':
                continue
            if not rec.class_id:
                raise ValidationError("The selected subject has no class/section assigned.")
            students = self.env['school.student'].search([('class_id', '=', rec.class_id.id)])
            existing_students = rec.result_ids.mapped('student_id')
            to_create = students - existing_students
            for student in to_create:
                self.env['school.exam.result'].create({
                    'exam_id': rec.id,
                    'student_id': student.id,
                })
            rec.state = 'in_progress'

    def action_publish(self):
        for rec in self:
            if not rec.result_ids:
                raise ValidationError(
                    "There are no students to publish results for. Click 'Start' first "
                    "to generate the student list."
                )
            rec.state = 'published'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_view_results(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Results - %s' % (self.name or ''),
            'res_model': 'school.exam.result',
            'view_mode': 'tree,form',
            'domain': [('exam_id', '=', self.id)],
            'context': {'default_exam_id': self.id},
        }

    def action_print_all_marksheets(self):
        """Generate one combined PDF containing every student's marksheet for this exam."""
        self.ensure_one()
        if not self.result_ids:
            raise ValidationError(
                "There are no students to print marksheets for. Click 'Start' first "
                "to generate the student list."
            )
        report = self.env.ref('School_Management_System.action_report_exam_marksheet')
        return report.report_action(self.result_ids)