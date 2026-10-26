from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SchoolStudent(models.Model):
    _name = 'school.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'School Student'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company
    )
    name = fields.Char(string="Name", required=True)
    student_code = fields.Char(string="Student Code", readonly=True, copy=False)
    partner_id = fields.Many2one(
        'res.partner', string="Contact", required=True, ondelete='restrict',
    )
    phone = fields.Char(related='partner_id.phone', string="Phone", readonly=False)
    email = fields.Char(related='partner_id.email', string="Email", readonly=False)
    address = fields.Char(
        related='partner_id.contact_address', string="Address", readonly=True,
    )
    photo = fields.Image(related='partner_id.image_1920', string="Photo", readonly=False)
    roll_number = fields.Integer(string="Roll Number")
    date_of_birth = fields.Date(string="Date of Birth")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-'),
    ], string="Blood Group")
    class_id = fields.Many2one('student.class', string="Class", tracking=True)
    section = fields.Char(
        related='class_id.section_id.name', string="Section", store=True, readonly=True,
    )
    guardian_relation_ids = fields.One2many(
        'school.guardian.relation', 'student_id', string="Guardians",
    )
    guardian_count = fields.Integer(compute='_compute_guardian_count')
    parent_contact = fields.Char(
        string="Parent Contact", compute='_compute_parent_contact',
    )
    admission_id = fields.Many2one(
        'student.admission', string="Admission Record", readonly=True
    )
    exam_result_ids = fields.One2many('school.exam.result', 'student_id', string="Exam Results")
    exam_result_count = fields.Integer(string="Exam Count", compute='_compute_exam_result_count')

    @api.depends(
        'guardian_relation_ids.is_primary',
        'guardian_relation_ids.partner_id',
        'guardian_relation_ids.partner_id.phone',
        'guardian_relation_ids.partner_id.email',
    )
    def _compute_parent_contact(self):
        for rec in self:
            guardian = rec.guardian_relation_ids.filtered('is_primary')[:1].partner_id
            rec.parent_contact = (
                guardian.phone or guardian.email or guardian.name
                if guardian else False
            )

    @api.depends('guardian_relation_ids')
    def _compute_guardian_count(self):
        for rec in self:
            rec.guardian_count = len(rec.guardian_relation_ids)

    @api.depends('exam_result_ids')
    def _compute_exam_result_count(self):
        for rec in self:
            rec.exam_result_count = len(rec.exam_result_ids)

    @api.constrains('class_id', 'roll_number')
    def _check_roll_number_unique(self):
        for student in self.filtered(lambda rec: rec.class_id and rec.roll_number):
            duplicate = self.search_count([
                ('id', '!=', student.id),
                ('class_id', '=', student.class_id.id),
                ('roll_number', '=', student.roll_number),
            ])
            if duplicate:
                raise ValidationError(
                    "Roll number %s is already assigned in class %s."
                    % (student.roll_number, student.class_id.display_name)
                )

    @api.model_create_multi
    def create(self, vals_list):
        next_rolls = {}
        reserved_rolls = {}
        for vals in vals_list:
            if vals.get('class_id') and vals.get('roll_number'):
                reserved_rolls.setdefault(vals['class_id'], set()).add(
                    vals['roll_number']
                )
        for vals in vals_list:
            phone = vals.pop('phone', False)
            email = vals.pop('email', False)
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name') or 'Student',
                    'phone': phone,
                    'email': email,
                    'image_1920': vals.pop('photo', False),
                    'company_id': vals.get('company_id') or self.env.company.id,
                }
                vals['partner_id'] = self.env['res.partner'].create(partner_vals).id
            elif phone or email:
                self.env['res.partner'].browse(vals['partner_id']).write({
                    'phone': phone,
                    'email': email,
                })
            vals.setdefault(
                'student_code',
                self.env['ir.sequence'].next_by_code('school.student') or 'New',
            )
            if vals.get('class_id') and not vals.get('roll_number'):
                student_class = self.env['student.class'].browse(vals['class_id'])
                if student_class.id not in next_rolls:
                    next_rolls[student_class.id] = (
                        student_class._get_next_roll_number()
                    )
                while next_rolls[student_class.id] in reserved_rolls.get(
                    student_class.id, set()
                ):
                    next_rolls[student_class.id] += 1
                vals['roll_number'] = next_rolls[student_class.id]
                reserved_rolls.setdefault(student_class.id, set()).add(
                    vals['roll_number']
                )
                next_rolls[student_class.id] += 1
        return super().create(vals_list)

    @api.onchange('class_id')
    def _onchange_class_id_roll_number(self):
        if self.class_id and not self.roll_number and self.class_id.id:
            existing = self.search([
                ('class_id', '=', self.class_id.id),
            ], order='roll_number desc', limit=1)
            self.roll_number = (existing.roll_number or 0) + 1

    def action_open_contact(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Contact',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
        }

    def write(self, vals):
        class_change = 'class_id' in vals
        roll_number_given = 'roll_number' in vals
        old_values = {
            student.id: (
                student.class_id.display_name,
                student.roll_number,
            )
            for student in self
        } if class_change else {}
        if class_change and not roll_number_given and vals.get('class_id'):
            for student in self:
                vals_for_student = dict(vals)
                vals_for_student['roll_number'] = (
                    self.env['student.class'].browse(vals['class_id'])
                    ._get_next_roll_number()
                )
                student.write(vals_for_student)
            return True
        result = super().write(vals)
        partner_vals = {}
        if 'name' in vals:
            partner_vals['name'] = vals['name']
        if 'photo' in vals:
            partner_vals['image_1920'] = vals['photo']
        if partner_vals:
            self.mapped('partner_id').write(partner_vals)
        if class_change:
            for student in self:
                old_class, old_roll = old_values[student.id]
                student.message_post(body=(
                    'Class changed from %s (roll %s) to %s (roll %s).'
                    % (
                        old_class or 'Unassigned',
                        old_roll or 0,
                        student.class_id.display_name or 'Unassigned',
                        student.roll_number or 0,
                    )
                ))
        return result

    def action_view_guardians(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guardians',
            'res_model': 'school.guardian.relation',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_view_exam_results(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exam Results - %s' % (self.name or ''),
            'res_model': 'school.exam.result',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
        }
