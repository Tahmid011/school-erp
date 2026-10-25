from odoo import api, models, fields

class SchoolSection(models.Model):
    _name = 'school.section'
    _description = 'School Section'

    name = fields.Char(string="Section", required=True)