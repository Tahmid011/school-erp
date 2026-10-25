from odoo import api, models, fields

class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'School Teacher'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    employee_id = fields.Char(string="Employee ID", default='New', readonly=True)
    name = fields.Char(string="Name", required=True)
    contact_number = fields.Char(string="Contact Number", required=True)
    subject = fields.Many2one('school.subject', string="Subject")
    class_ids = fields.Many2many('student.class', string="Classes")
    degree = fields.Char(string="Degree", required=True)
    experience = fields.Integer(string="Experience (in years)", required=True)

    user_id = fields.Many2one(
        'res.users', string="Linked User",
        help="Login user linked to this teacher. Used to give this teacher "
             "access to only their own subjects/exams in the Exam module."
    )
    exam_ids = fields.One2many('school.exam', 'teacher_id', string="Exams")
    exam_count = fields.Integer(string="Exam Count", compute='_compute_exam_count')

    @api.depends('exam_ids')
    def _compute_exam_count(self):
        for rec in self:
            rec.exam_count = len(rec.exam_ids)

    def action_view_exams(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exams',
            'res_model': 'school.exam',
            'view_mode': 'tree,form',
            'domain': [('teacher_id', '=', self.id)],
        }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_id', 'New') == 'New':
                vals['employee_id'] = self.env['ir.sequence'].next_by_code('school.teacher') or 'New'
        return super().create(vals_list)