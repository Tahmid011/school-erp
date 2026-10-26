import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    changed = 0
    for student_class in env['student.class'].search([]):
        students = env['school.student'].search(
            [('class_id', '=', student_class.id)],
            order='id',
        )
        if students:
            ids = tuple(students.ids)
            cr.execute(
                """
                    UPDATE school_student
                       SET roll_number = roll_number + 1000000
                     WHERE id IN %s
                """,
                (ids,),
            )
        for roll_number, student in enumerate(students, start=1):
            if student.roll_number != roll_number:
                cr.execute(
                    "UPDATE school_student SET roll_number = %s WHERE id = %s",
                    (roll_number, student.id),
                )
                changed += 1
            if student.admission_id:
                cr.execute(
                    """
                        UPDATE student_admission
                           SET roll_number = %s
                         WHERE id = %s
                    """,
                    (roll_number, student.admission_id.id),
                )

    _logger.info('Roll number cleanup changed %s student records.', changed)
