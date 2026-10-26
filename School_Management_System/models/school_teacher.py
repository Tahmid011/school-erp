from odoo import api, models, fields

class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'School Teacher'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    teacher_code = fields.Char(string="Teacher Code", default='New', readonly=True)
    hr_employee_id = fields.Many2one(
        'hr.employee', string="Employee", required=True, ondelete='restrict',
    )
    name = fields.Char(string="Name", required=True)
    contact_number = fields.Char(string="Contact Number", required=True)
    subject = fields.Many2one('school.subject', string="Subject")
    class_ids = fields.Many2many('student.class', string="Classes")
    degree = fields.Char(string="Degree", required=True)
    experience = fields.Integer(string="Experience (in years)", required=True)

    user_id = fields.Many2one(
        related='hr_employee_id.user_id', string="Linked User", readonly=True,
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
            if vals.get('teacher_code', 'New') == 'New':
                vals['teacher_code'] = self.env['ir.sequence'].next_by_code('school.teacher') or 'New'
            if not vals.get('hr_employee_id'):
                employee = self.env['hr.employee'].create({
                    'name': vals.get('name') or 'Teacher',
                    'work_phone': vals.get('contact_number'),
                    'company_id': vals.get('company_id') or self.env.company.id,
                })
                vals['hr_employee_id'] = employee.id
        return super().create(vals_list)

    def action_open_employee(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': self.hr_employee_id.id,
        }

    def write(self, vals):
        result = super().write(vals)
        employee_vals = {}
        if 'name' in vals:
            employee_vals['name'] = vals['name']
        if 'contact_number' in vals:
            employee_vals['work_phone'] = vals['contact_number']
        if employee_vals:
            self.mapped('hr_employee_id').write(employee_vals)
        return result