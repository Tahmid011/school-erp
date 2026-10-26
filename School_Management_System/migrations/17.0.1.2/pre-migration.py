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

    if _column_exists(cr, 'school_student', 'parent_contact'):
        cr.execute(
            """
            CREATE TABLE IF NOT EXISTS school_student_parent_contact_backup (
                student_id INTEGER PRIMARY KEY,
                name VARCHAR,
                company_id INTEGER,
                parent_contact VARCHAR
            )
            """
        )
        cr.execute(
            """
            INSERT INTO school_student_parent_contact_backup
                (student_id, name, company_id, parent_contact)
            SELECT id, name, company_id, parent_contact
              FROM school_student
             WHERE parent_contact IS NOT NULL AND parent_contact != ''
            ON CONFLICT (student_id) DO NOTHING
            """
        )

    if (
        _column_exists(cr, 'school_teacher', 'employee_id')
        and not _column_exists(cr, 'school_teacher', 'teacher_code')
    ):
        cr.execute(
            'ALTER TABLE school_teacher RENAME COLUMN employee_id TO teacher_code'
        )
