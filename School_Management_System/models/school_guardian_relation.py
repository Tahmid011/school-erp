from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolGuardianRelation(models.Model):
    _name = 'school.guardian.relation'
    _description = 'Student Guardian Relation'
    _rec_name = 'partner_id'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company,
        required=True,
    )
    student_id = fields.Many2one(
        'school.student', string="Student", required=True, ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner', string="Guardian", required=True, ondelete='restrict',
    )
    relation = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('other', 'Other'),
    ], required=True, default='guardian')
    is_primary = fields.Boolean(string="Primary Guardian")
    is_fee_payer = fields.Boolean(string="Fee Payer")
    can_view_portal = fields.Boolean(string="Can View Portal")

    @api.constrains('student_id', 'is_primary')
    def _check_single_primary(self):
        for relation in self.filtered('is_primary'):
            if self.search_count([
                ('student_id', '=', relation.student_id.id),
                ('is_primary', '=', True),
                ('id', '!=', relation.id),
            ]):
                raise ValidationError(
                    "A student can have only one primary guardian."
                )
