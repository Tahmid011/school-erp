from odoo import api, models, fields

class SchoolSubject(models.Model):
    _name = 'school.subject'
    _description = 'School Subject'
    _rec_name = 'name'

    subject_code = fields.Char(string="Subject Code", default='New', readonly=True)
    section_id = fields.Many2one('student.class', string="Section", required=True)
    name = fields.Char(string="Subject Name", required=True)
    teacher_id = fields.Many2one('school.teacher', string="Teacher")

    @api.model_create_multi
    def create(self, vals_list):    
        for vals in vals_list:
            if vals.get('subject_code', 'New') == 'New':
                vals['subject_code'] = self.env['ir.sequence'].next_by_code('school.subject') or 'New'
        return super().create(vals_list)
    



