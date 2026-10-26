from odoo.tests import TransactionCase, tagged


@tagged('school_security', '-at_install', 'post_install')
class TestSchoolSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        teacher_group = cls.env.ref(
            'School_Management_System.group_school_teacher'
        )
        parent_group = cls.env.ref(
            'School_Management_System.group_school_parent'
        )
        cls.teacher_user = cls._create_user('teacher.one', teacher_group)
        cls.other_teacher_user = cls._create_user(
            'teacher.two', teacher_group
        )
        cls.parent_user = cls._create_user('parent.one', parent_group)

        cls.section = cls.env['school.section'].create({'name': 'A'})
        cls.other_section = cls.env['school.section'].create({'name': 'B'})
        cls.teacher = cls._create_teacher('Teacher One', cls.teacher_user)
        cls.other_teacher = cls._create_teacher(
            'Teacher Two', cls.other_teacher_user
        )
        cls.first_class = cls.env['student.class'].create({
            'name': 'Class 1',
            'section_id': cls.section.id,
            'total_seat': 20,
            'class_teacher_id': cls.teacher.id,
        })
        cls.other_class = cls.env['student.class'].create({
            'name': 'Class 2',
            'section_id': cls.other_section.id,
            'total_seat': 20,
            'class_teacher_id': cls.other_teacher.id,
        })
        cls.env['school.subject'].create({
            'name': 'Mathematics',
            'class_id': cls.first_class.id,
            'teacher_id': cls.teacher.id,
        })
        cls.env['school.subject'].create({
            'name': 'Science',
            'class_id': cls.other_class.id,
            'teacher_id': cls.other_teacher.id,
        })

        cls.first_student = cls._create_student(
            'Student One', cls.first_class
        )
        cls.other_student = cls._create_student(
            'Student Two', cls.other_class
        )
        cls.env['school.guardian.relation'].create({
            'student_id': cls.first_student.id,
            'partner_id': cls.parent_user.partner_id.id,
            'relation': 'mother',
            'can_view_portal': True,
        })
        other_parent_partner = cls.env['res.partner'].create({
            'name': 'Other Parent',
        })
        cls.env['school.guardian.relation'].create({
            'student_id': cls.other_student.id,
            'partner_id': other_parent_partner.id,
            'relation': 'father',
            'can_view_portal': True,
        })

    @classmethod
    def _create_user(cls, login, group):
        return cls.env['res.users'].create({
            'name': login,
            'login': login,
            'email': '%s@example.com' % login,
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                group.id,
            ])],
        })

    @classmethod
    def _create_teacher(cls, name, user):
        employee = cls.env['hr.employee'].create({
            'name': name,
            'user_id': user.id,
        })
        return cls.env['school.teacher'].create({
            'name': name,
            'hr_employee_id': employee.id,
            'contact_number': '01234567890',
            'degree': 'B.Ed.',
            'experience': 5,
        })

    @classmethod
    def _create_student(cls, name, student_class):
        partner = cls.env['res.partner'].create({'name': name})
        return cls.env['school.student'].create({
            'name': name,
            'partner_id': partner.id,
            'class_id': student_class.id,
        })

    def test_teacher_cannot_see_another_teachers_students(self):
        visible_students = self.env['school.student'].with_user(
            self.teacher_user
        ).search([])
        self.assertIn(self.first_student, visible_students)
        self.assertNotIn(self.other_student, visible_students)

    def test_parent_cannot_see_another_child(self):
        visible_students = self.env['school.student'].with_user(
            self.parent_user
        ).search([])
        self.assertIn(self.first_student, visible_students)
        self.assertNotIn(self.other_student, visible_students)
