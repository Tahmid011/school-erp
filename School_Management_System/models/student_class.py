from odoo import api, models, fields

class StudentClass(models.Model):
    _name = 'student.class'
    _description = 'Student Class'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    reference_code = fields.Char(string="Reference Code", default='New', readonly=True)
    name = fields.Char(string="Class Name", required=True)
    section_id = fields.Many2one(
        'school.section', string="Section", required=True, ondelete='restrict',
    )
    academic_year_id = fields.Many2one(
        'school.academic.year', string="Academic Year", ondelete='restrict',
    )
    class_teacher_id = fields.Many2one(
        'school.teacher', string="Class Teacher", ondelete='restrict',
    )
    subject_ids = fields.One2many(
        'school.subject', 'class_id', string="Subjects",
    )
    total_seat = fields.Integer(string="Total Seat", required=True)
    total_students = fields.Integer(string="Total Students", compute='_compute_total_students', store=True)
    available_seat = fields.Integer(string="Available Seat", compute='_compute_available_seat', store=True)

    student_ids = fields.One2many('student.admission', 'class_id', string="Students")

    exam_ids = fields.One2many('school.exam', 'class_id', string="Exams")  # adjust model/field names
    exam_count = fields.Integer(string="Exams", compute='_compute_exam_count')

    def _get_next_roll_number(self):
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM student_class WHERE id = %s FOR UPDATE",
            (self.id,),
        )
        self.env.cr.execute(
            """
                SELECT GREATEST(
                    COALESCE((SELECT MAX(roll_number)
                                FROM school_student
                               WHERE class_id = %s), 0),
                    COALESCE((SELECT MAX(roll_number)
                                FROM student_admission
                               WHERE class_id = %s), 0)
                ) + 1
            """,
            (self.id, self.id),
        )
        return self.env.cr.fetchone()[0]

    @api.depends('exam_ids')
    def _compute_exam_count(self):
        for rec in self:
            rec.exam_count = len(rec.exam_ids)

    def action_view_exams(self):
        self.ensure_one()
        return {
            'name': 'Exams',
            'type': 'ir.actions.act_window',
            'res_model': 'school.exam',  # adjust to your actual exam model's technical name
            'view_mode': 'tree,form',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
        }


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference_code', 'New') == 'New':
                vals['reference_code'] = self.env['ir.sequence'].next_by_code('student.class') or 'New'
        return super().create(vals_list)
    
    @api.depends('name', 'section_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"[{rec.section_id.name or ''}] {rec.name or ''}"
    
    @api.depends('total_seat', 'total_students')
    def _compute_available_seat(self):
        for rec in self:
            rec.available_seat = rec.total_seat - rec.total_students

    @api.depends('student_ids.state')
    def _compute_total_students(self):
        for rec in self:
            rec.total_students = len(rec.student_ids.filtered(lambda s: s.state == 'admitted'))
