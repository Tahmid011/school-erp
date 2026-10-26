from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('school_foundation', '-at_install', 'post_install')
class TestRollNumber(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.section = cls.env['school.section'].create({'name': 'A'})
        cls.other_section = cls.env['school.section'].create({'name': 'B'})
        cls.student_class = cls.env['student.class'].create({
            'name': 'Class 1',
            'section_id': cls.section.id,
            'total_seat': 20,
        })
        cls.other_class = cls.env['student.class'].create({
            'name': 'Class 2',
            'section_id': cls.other_section.id,
            'total_seat': 20,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Parent'})

    def _student(self, name='Student', class_id=None, roll_number=0):
        return self.env['school.student'].create({
            'name': name,
            'partner_id': self.partner.id,
            'class_id': (class_id or self.student_class).id,
            'roll_number': roll_number,
        })

    def test_sequential_assignment_and_second_class(self):
        self.assertEqual(
            [self._student(name=str(index)).roll_number for index in range(3)],
            [1, 2, 3],
        )
        self.assertEqual(self._student(class_id=self.other_class).roll_number, 1)

    def test_manual_roll_is_kept(self):
        self.assertEqual(self._student(roll_number=9).roll_number, 9)

    def test_duplicate_roll_is_rejected(self):
        self._student(roll_number=4)
        with self.assertRaises(ValidationError):
            self._student(name='Duplicate', roll_number=4)

    def test_moving_assigns_next_and_does_not_reuse(self):
        first = self._student()
        second = self._student(name='Second')
        first.write({'class_id': self.other_class.id})
        self.assertEqual(first.roll_number, 1)
        second.unlink()
        third = self._student(name='Third')
        self.assertEqual(third.roll_number, 2)

    def test_deleted_middle_roll_is_not_reused(self):
        first = self._student()
        second = self._student(name='Second')
        second.unlink()
        third = self._student(name='Third')
        self.assertEqual(third.roll_number, 3)
        first.write({'roll_number': 10})
        fourth = self._student(name='Fourth')
        self.assertEqual(fourth.roll_number, 11)

    def test_admission_assigns_and_copies_roll(self):
        admission = self.env['student.admission'].create({
            'name': 'Admitted Student',
            'date_of_birth': '2010-01-01',
            'parent_contact': '01234567890',
            'class_id': self.student_class.id,
        })
        admission.action_admit()
        self.assertEqual(admission.roll_number, 1)
        self.assertEqual(admission.student_id.roll_number, 1)

    def test_admission_replaces_stale_roll_with_next_roll(self):
        existing = self._student()
        admission = self.env['student.admission'].create({
            'name': 'Stale Roll Student',
            'date_of_birth': '2010-01-01',
            'parent_contact': '01234567890',
            'class_id': self.student_class.id,
            'roll_number': 14,
        })
        admission.action_admit()
        self.assertEqual(existing.roll_number, 1)
        self.assertEqual(admission.roll_number, 2)
        self.assertEqual(admission.student_id.roll_number, 2)

    def test_admission_skips_existing_student_roll(self):
        self._student(roll_number=10)
        admission = self.env['student.admission'].create({
            'name': 'Existing Student Roll',
            'date_of_birth': '2010-01-01',
            'parent_contact': '01234567890',
            'class_id': self.student_class.id,
        })
        admission.action_admit()
        self.assertEqual(admission.roll_number, 11)
        self.assertEqual(admission.student_id.roll_number, 11)

    def test_non_admitted_student_does_not_affect_admission_roll(self):
        existing_admission = self.env['student.admission'].create({
            'name': 'Existing Student',
            'date_of_birth': '2010-01-01',
            'parent_contact': '01234567890',
            'class_id': self.student_class.id,
        })
        existing_admission.action_admit()
        admission = self.env['student.admission'].create({
            'name': 'Visible Student',
            'date_of_birth': '2010-01-01',
            'parent_contact': '01234567890',
            'class_id': self.student_class.id,
        })
        admission.action_admit()
        self.assertEqual(admission.roll_number, 2)
