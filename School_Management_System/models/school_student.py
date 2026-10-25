from odoo import api, models, fields

class SchoolStudent(models.Model):
    _name = 'school.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'School Student'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    name = fields.Char(string="Name", required=True)
    roll_number = fields.Integer(string="Roll Number")
    date_of_birth = fields.Date(string="Date of Birth")
    class_id = fields.Many2one('student.class', string="Class", tracking=True)
    section = fields.Char(
        related='class_id.section_id.name', string="Section", store=True, readonly=True,
    )
    parent_contact = fields.Char(string="Parent Contact")
    #section = fields.Char(string="Section")
    

    admission_id = fields.Many2one(
        'student.admission',
        string="Admission Record",
        readonly=True
    )

    exam_result_ids = fields.One2many('school.exam.result', 'student_id', string="Exam Results")
    exam_result_count = fields.Integer(string="Exam Count", compute='_compute_exam_result_count')

    @api.depends('exam_result_ids')
    def _compute_exam_result_count(self):
        for rec in self:
            rec.exam_result_count = len(rec.exam_result_ids)

    def action_view_exam_results(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Results - %s' % (self.name or ''),
            'res_model': 'school.exam.result',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
        }