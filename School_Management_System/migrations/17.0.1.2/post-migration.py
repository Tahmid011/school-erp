from odoo import SUPERUSER_ID, api


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    student_model = env['school.student']
    partner_model = env['res.partner']
    guardian_model = env['school.guardian.relation']

    cr.execute(
        'SELECT id, name, company_id FROM school_student '
        'WHERE partner_id IS NULL'
    )
    for student_id, name, company_id in cr.fetchall():
        student = student_model.browse(student_id)
        student.partner_id = partner_model.create({
            'name': name or 'Student',
            'company_id': company_id or env.company.id,
        })

    if _column_exists(cr, 'school_student_parent_contact_backup', 'parent_contact'):
        cr.execute(
            """
            SELECT student_id, name, company_id, parent_contact
              FROM school_student_parent_contact_backup
            """
        )
        for student_id, name, company_id, parent_contact in cr.fetchall():
            student = student_model.browse(student_id)
            if guardian_model.search_count([
                ('student_id', '=', student_id),
                ('is_primary', '=', True),
            ]):
                continue
            guardian = partner_model.create({
                'name': 'Guardian of %s' % (name or 'Student'),
                'phone': parent_contact,
                'company_id': company_id or env.company.id,
            })
            guardian_model.create({
                'student_id': student.id,
                'partner_id': guardian.id,
                'relation': 'guardian',
                'is_primary': True,
                'is_fee_payer': True,
            })
        cr.execute('DROP TABLE school_student_parent_contact_backup')

    employee_model = env['hr.employee']
    cr.execute(
        'SELECT id, name, contact_number, company_id '
        'FROM school_teacher WHERE hr_employee_id IS NULL'
    )
    for teacher_id, name, contact_number, company_id in cr.fetchall():
        employee = employee_model.create({
            'name': name or 'Teacher',
            'work_phone': contact_number,
            'company_id': company_id or env.company.id,
        })
        cr.execute(
            'UPDATE school_teacher SET hr_employee_id = %s WHERE id = %s',
            (employee.id, teacher_id),
        )
