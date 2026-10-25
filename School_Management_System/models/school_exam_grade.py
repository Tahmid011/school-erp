from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolExamGrade(models.Model):
    _name = 'school.exam.grade'
    _description = 'Exam Grading Scale'
    _order = 'sequence asc, min_percentage desc'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    name = fields.Char(string="Grade", required=True, help="Letter grade shown to teachers/students, e.g. A+, A, B, F")
    sequence = fields.Integer(string="Sequence", default=10)
    min_percentage = fields.Float(string="Min %", required=True)
    max_percentage = fields.Float(string="Max %", required=True)
    is_pass = fields.Boolean(string="Is Passing Grade", default=True)

    @api.constrains('min_percentage', 'max_percentage')
    def _check_range(self):
        for rec in self:
            if rec.min_percentage > rec.max_percentage:
                raise ValidationError(
                    "Minimum percentage cannot be greater than maximum percentage for grade '%s'." % rec.name)
            if rec.min_percentage < 0 or rec.max_percentage > 100:
                raise ValidationError(
                    "Percentage values must be between 0 and 100 for grade '%s'." % rec.name)