from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StudentAdmission(models.Model):
    _name = 'student.admission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Student Admission'
    _rec_name = 'name'
    _order = 'entrance_test_score desc, application_number'

    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company,
        required=True, tracking=True,
    )
    application_number = fields.Char(
        string="Application Number", readonly=True, copy=False, index=True,
    )
    name = fields.Char(string="Name", required=True, tracking=True)
    date_of_birth = fields.Date(string="Date of Birth", required=True, tracking=True)
    applying_for_class_id = fields.Many2one(
        'student.class', string="Applying for Class", tracking=True,
    )
    class_id = fields.Many2one(
        'student.class', string="Admitted Class", tracking=True,
    )
    section = fields.Char(
        related='applying_for_class_id.section_id.name', string="Section",
        store=True, readonly=True,
    )
    previous_school = fields.Char(string="Previous School")
    father_name = fields.Char(string="Father Name")
    father_phone = fields.Char(string="Father Phone")
    father_email = fields.Char(string="Father Email")
    father_occupation = fields.Char(string="Father Occupation")
    mother_name = fields.Char(string="Mother Name")
    mother_phone = fields.Char(string="Mother Phone")
    mother_email = fields.Char(string="Mother Email")
    mother_occupation = fields.Char(string="Mother Occupation")
    parent_contact = fields.Char(string="Parent Contact", tracking=True)
    guardian_email = fields.Char(string="Guardian Email")
    address = fields.Text(string="Address")
    photo = fields.Image(string="Photo", max_width=1920, max_height=1920)
    document_ids = fields.One2many(
        'school.admission.document', 'admission_id', string="Documents",
        copy=False,
    )
    entrance_test_score = fields.Float(string="Entrance Test Score")
    reviewer_id = fields.Many2one(
        'res.users', string="Reviewer", tracking=True,
        default=lambda self: self.env.user,
    )
    roll_number = fields.Integer(string="Roll Number", tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
        ('admitted', 'Admitted'),
    ], default='draft', tracking=True, string="Status")

    student_id = fields.Many2one('school.student', string="Student Record", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault(
                'application_number',
                self.env['ir.sequence'].next_by_code('student.admission') or 'New',
            )
        return super().create(vals_list)

    def _send_notification(self, template_xmlid, message):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        for record in self:
            if template:
                template.send_mail(record.id, force_send=True)
            record.message_post(body=message, subtype_xmlid='mail.mt_note')

    def _required_documents_complete(self):
        self.ensure_one()
        required = self.document_ids.filtered('required')
        return all(document.attachment_id for document in required)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'
            if rec.reviewer_id:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=rec.reviewer_id.id,
                    summary='Review admission application',
                    note='Review application %s.' % rec.application_number,
                )
            rec._send_notification(
                'School_Management_System.mail_template_admission_received',
                'Application received and submitted for review.',
            )

    def action_under_review(self):
        self.write({'state': 'under review'})

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec._send_notification(
                'School_Management_System.mail_template_admission_approved',
                'Admission application approved.',
            )

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec._send_notification(
                'School_Management_System.mail_template_admission_rejected',
                'Admission application rejected.',
            )

    def action_waitlist(self):
        self.write({'state': 'waitlisted'})

    def action_admit(self):
        for rec in self:
            rec.ensure_one()
            if rec.student_id:
                continue
            target_class = rec.applying_for_class_id or rec.class_id
            if not target_class:
                raise ValidationError("Please select a class before admitting the student.")
            if not rec._required_documents_complete():
                raise ValidationError(
                    "All required admission documents must have an attachment."
                )
            target_class._get_next_roll_number()
            admitted_count = self.search_count([
                ('class_id', '=', target_class.id),
                ('state', '=', 'admitted'),
            ])
            if admitted_count >= target_class.total_seat:
                raise ValidationError("No available seats in the selected class.")

            student_partner = self.env['res.partner'].create({
                'name': rec.name,
                'street': rec.address,
                'image_1920': rec.photo,
                'company_id': rec.company_id.id,
            })
            student = self.env['school.student'].create({
                'name': rec.name,
                'date_of_birth': rec.date_of_birth,
                'roll_number': target_class._get_next_roll_number(),
                'admission_id': rec.id,
                'class_id': target_class.id,
                'partner_id': student_partner.id,
                'company_id': rec.company_id.id,
            })
            guardian_values = (
                ('father', rec.father_name, rec.father_phone, rec.father_email,
                 rec.father_occupation),
                ('mother', rec.mother_name, rec.mother_phone, rec.mother_email,
                 rec.mother_occupation),
            )
            created_guardian = False
            for relation, name, phone, email, occupation in guardian_values:
                if not name:
                    continue
                guardian = self.env['res.partner'].create({
                    'name': name,
                    'phone': phone,
                    'email': email,
                    'function': occupation,
                    'company_id': rec.company_id.id,
                })
                self.env['school.guardian.relation'].create({
                    'student_id': student.id,
                    'partner_id': guardian.id,
                    'relation': relation,
                    'is_primary': not created_guardian,
                    'is_fee_payer': not created_guardian,
                    'company_id': rec.company_id.id,
                })
                created_guardian = True
            if not created_guardian and rec.parent_contact:
                guardian = self.env['res.partner'].create({
                    'name': 'Guardian of %s' % rec.name,
                    'phone': rec.parent_contact,
                    'email': rec.guardian_email,
                    'company_id': rec.company_id.id,
                })
                self.env['school.guardian.relation'].create({
                    'student_id': student.id,
                    'partner_id': guardian.id,
                    'relation': 'guardian',
                    'is_primary': True,
                    'is_fee_payer': True,
                    'company_id': rec.company_id.id,
                })
            rec.write({
                'class_id': target_class.id,
                'roll_number': student.roll_number,
                'state': 'admitted',
                'student_id': student.id,
            })
            rec._send_notification(
                'School_Management_System.mail_template_admission_admitted',
                'Admission completed and student record created.',
            )


class SchoolAdmissionDocument(models.Model):
    _name = 'school.admission.document'
    _description = 'Admission Document'
    _rec_name = 'document_type'

    company_id = fields.Many2one(
        'res.company', related='admission_id.company_id', store=True, readonly=True,
    )
    admission_id = fields.Many2one(
        'student.admission', string="Admission", required=True, ondelete='cascade',
    )
    document_type = fields.Selection([
        ('birth_certificate', 'Birth Certificate'),
        ('previous_marksheet', 'Previous Marksheet'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    ], string="Type", required=True)
    required = fields.Boolean(string="Required")
    attachment_id = fields.Many2one(
        'ir.attachment', string="Attachment", required=False, ondelete='restrict',
    )
