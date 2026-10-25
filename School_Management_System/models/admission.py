from odoo import api, models, fields
from odoo.exceptions import ValidationError

class StudentAdmission(models.Model):
    _name = 'student.admission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Student Admission'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True, tracking=True)
    date_of_birth = fields.Date(string="Date of Birth", required=True, tracking=True)
    class_id = fields.Many2one('student.class', string="Class", tracking=True)
    section = fields.Char(related='class_id.section', string="Section", store=True, readonly=True)
    parent_contact = fields.Char(string="Parent Contact", required=True, tracking=True)
    roll_number = fields.Integer(string="Roll Number", tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('admitted', 'Admitted')
    ], default='draft', tracking=True, string="Status")

    student_id = fields.Many2one('school.student', string="Student Record", readonly=True)

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'admitted':
            for rec in self:
                if not rec.student_id:
                    student = self.env['school.student'].create({
                        'name': rec.name,
                        'date_of_birth': rec.date_of_birth,
                        'parent_contact': rec.parent_contact,
                        'roll_number': rec.roll_number,
                        'admission_id': rec.id,
                        'class_id': rec.class_id.id
                    })
                    rec.student_id = student.id
        return res

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_under_review(self):
        for rec in self:
            rec.state = 'under review'
     
    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
    
    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def action_admit(self):
        for rec in self:
            if not rec.class_id:
                raise ValidationError("Please select a class before admitting the student.")
            if rec.class_id.available_seat <= 0:
                raise ValidationError("No available seats in the selected class.")
            rec.state = 'admitted'
