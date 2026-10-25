from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolExamResult(models.Model):
    _name = 'school.exam.result'
    _description = 'Student Exam Result'
    _rec_name = 'student_id'
    _order = 'exam_id, roll_number'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    exam_id = fields.Many2one('school.exam', string="Exam", required=True, ondelete='cascade')
    student_id = fields.Many2one('school.student', string="Student", required=True, ondelete='cascade')

    roll_number = fields.Integer(string="Roll No.", related='student_id.roll_number', store=True, readonly=True)
    class_id = fields.Many2one('student.class', string="Class", related='exam_id.class_id', store=True, readonly=True)
    subject_id = fields.Many2one('school.subject', string="Subject", related='exam_id.subject_id', store=True, readonly=True)
    exam_state = fields.Selection(related='exam_id.state', string="Exam Status", store=True, readonly=True)

    total_marks = fields.Float(string="Total Marks", related='exam_id.total_marks', readonly=True)
    passing_marks = fields.Float(string="Passing Marks", related='exam_id.passing_marks', readonly=True)

    is_absent = fields.Boolean(string="Absent")
    marks_obtained = fields.Float(string="Marks Obtained")
    percentage = fields.Float(string="Percentage", compute='_compute_percentage', store=True)
    grade = fields.Char(string="Grade", compute='_compute_grade', store=True)
    result_status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('absent', 'Absent'),
    ], string="Result", compute='_compute_grade', store=True)

    remarks = fields.Char(string="Remarks")

    _sql_constraints = [
        ('exam_student_unique', 'unique(exam_id, student_id)',
         'A student can only have one result line per exam.'),
    ]

    @api.depends('marks_obtained', 'total_marks', 'is_absent')
    def _compute_percentage(self):
        for rec in self:
            if rec.is_absent or not rec.total_marks:
                rec.percentage = 0.0
            else:
                rec.percentage = (rec.marks_obtained / rec.total_marks) * 100.0

    @api.depends('percentage', 'is_absent', 'marks_obtained', 'passing_marks')
    def _compute_grade(self):
        grade_scale = self.env['school.exam.grade'].search([], order='sequence asc')
        for rec in self:
            if rec.is_absent:
                rec.grade = 'AB'
                rec.result_status = 'absent'
                continue

            matched = grade_scale.filtered(
                lambda g: g.min_percentage <= rec.percentage <= g.max_percentage
            )
            if matched:
                rec.grade = matched[0].name
                rec.result_status = 'pass' if matched[0].is_pass else 'fail'
            else:
                # Fallback if no grading scale is configured: use passing marks directly.
                rec.grade = '-'
                rec.result_status = 'pass' if rec.marks_obtained >= rec.passing_marks else 'fail'

    @api.constrains('marks_obtained', 'total_marks', 'is_absent')
    def _check_marks_obtained(self):
        for rec in self:
            if rec.is_absent:
                continue
            if rec.marks_obtained < 0:
                raise ValidationError("Marks obtained cannot be negative.")
            if rec.marks_obtained > rec.total_marks:
                raise ValidationError(
                    "Marks obtained (%.2f) cannot exceed the total marks (%.2f) for %s." % (
                        rec.marks_obtained, rec.total_marks, rec.student_id.name)
                )

    @api.onchange('is_absent')
    def _onchange_is_absent(self):
        if self.is_absent:
            self.marks_obtained = 0.0