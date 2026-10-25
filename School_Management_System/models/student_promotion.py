from odoo import fields, models
from odoo.exceptions import UserError


class StudentPromotion(models.TransientModel):
    _name = 'student.promotion'
    _description = 'Promote Students'

    source_class_id = fields.Many2one(
        'student.class', string='Source Class', required=True,
    )
    target_class_id = fields.Many2one(
        'student.class', string='Target Class', required=True,
    )
    target_academic_year_id = fields.Many2one(
        'school.academic.year', string='Target Academic Year', required=True,
    )
    student_ids = fields.Many2many(
        'school.student', string='Students', required=True,
        domain="[('class_id', '=', source_class_id)]",
    )

    def action_promote(self):
        self.ensure_one()
        if self.source_class_id == self.target_class_id:
            raise UserError('The source and target classes must be different.')
        if any(student.class_id != self.source_class_id for student in self.student_ids):
            raise UserError('All selected students must belong to the source class.')
        if (
            self.target_class_id.academic_year_id
            and self.target_class_id.academic_year_id != self.target_academic_year_id
        ):
            raise UserError('The target class does not belong to the target academic year.')
        for student in self.student_ids:
            old_class = student.class_id.display_name
            student.write({
                'class_id': self.target_class_id.id,
            })
            if student.admission_id:
                student.admission_id.class_id = self.target_class_id
            student.message_post(body=(
                'Student promoted from %s to %s for academic year %s.'
                % (old_class, self.target_class_id.display_name,
                   self.target_academic_year_id.display_name)
            ))
        return {'type': 'ir.actions.act_window_close'}
