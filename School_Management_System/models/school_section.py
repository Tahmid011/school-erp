from odoo import api, models, fields

class SchoolSection(models.Model):
    _name = 'school.section'
    _description = 'School Section'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    name = fields.Char(string="Section", required=True)