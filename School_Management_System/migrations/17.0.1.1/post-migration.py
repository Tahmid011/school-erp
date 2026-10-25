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
    section_model = env['school.section']

    if (
        _column_exists(cr, 'student_class', 'section')
        and _column_exists(cr, 'student_class', 'section_id')
    ):
        cr.execute(
            "SELECT id, company_id, COALESCE(NULLIF(section, ''), 'General') "
            "FROM student_class WHERE section_id IS NULL"
        )
        for class_id, company_id, section_name in cr.fetchall():
            section = section_model.search([
                ('name', '=', section_name),
                ('company_id', '=', company_id),
            ], limit=1)
            if not section:
                section = section_model.create({
                    'name': section_name,
                    'company_id': company_id,
                })
            cr.execute(
                "UPDATE student_class SET section_id = %s WHERE id = %s",
                (section.id, class_id),
            )

    if (
        _column_exists(cr, 'school_subject', 'section_id')
        and _column_exists(cr, 'school_subject', 'class_id')
    ):
        cr.execute(
            "UPDATE school_subject SET class_id = section_id "
            "WHERE class_id IS NULL AND section_id IS NOT NULL"
        )
