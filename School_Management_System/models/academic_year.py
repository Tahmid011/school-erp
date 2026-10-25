from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolAcademicYear(models.Model):
    _name = 'school.academic.year'
    _description = 'Academic Year'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company,
        index=True,
    )
    name = fields.Char(required=True, tracking=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    is_current = fields.Boolean(string='Current', tracking=True)
    state = fields.Selection(
        [('open', 'Open'), ('closed', 'Closed')],
        default='open', required=True, tracking=True,
    )
    term_ids = fields.One2many('school.term', 'academic_year_id', string='Terms')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_end < record.date_start:
                raise ValidationError('The academic year end date must be after its start date.')

    @api.constrains('is_current', 'company_id')
    def _check_one_current_per_company(self):
        for record in self.filtered('is_current'):
            other = self.search([
                ('id', '!=', record.id),
                ('company_id', '=', record.company_id.id),
                ('is_current', '=', True),
            ], limit=1)
            if other:
                raise ValidationError(
                    'Only one current academic year is allowed per company.'
                )


class SchoolTerm(models.Model):
    _name = 'school.term'
    _description = 'Academic Term'
    _order = 'academic_year_id, sequence, date_start, id'

    company_id = fields.Many2one(
        related='academic_year_id.company_id', store=True, index=True,
        readonly=True,
    )
    name = fields.Char(required=True)
    academic_year_id = fields.Many2one(
        'school.academic.year', required=True, ondelete='cascade',
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    sequence = fields.Integer(default=10)

    @api.constrains('date_start', 'date_end', 'academic_year_id')
    def _check_dates(self):
        for record in self:
            if record.date_end < record.date_start:
                raise ValidationError('The term end date must be after its start date.')
            if (
                record.academic_year_id
                and (
                    record.date_start < record.academic_year_id.date_start
                    or record.date_end > record.academic_year_id.date_end
                )
            ):
                raise ValidationError(
                    'A term must be within its academic year date range.'
                )
