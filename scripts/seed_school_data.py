"""Seed realistic school data through the Odoo shell.

Run from the repository root with:
    docker compose exec odoo odoo shell -d school_erp < scripts/seed_school_data.py

The target database must already have School_Management_System installed.
"""

import random
from datetime import date


rng = random.Random(42)
created = {
    'academic_years': 0,
    'terms': 0,
    'sections': 0,
    'classes': 0,
    'subjects': 0,
    'teachers': 0,
    'admissions': 0,
    'exams': 0,
    'results': 0,
}
skipped = {
    'academic_years': 0,
    'terms': 0,
    'sections': 0,
    'classes': 0,
    'subjects': 0,
    'teachers': 0,
    'admissions': 0,
    'exams': 0,
}
current_record = 'initial setup'


def get_or_create(model_name, domain, values, category, label):
    record = env[model_name].search(domain, limit=1)
    if record:
        skipped[category] += 1
        return record
    global current_record
    current_record = label
    record = env[model_name].create(values)
    created[category] += 1
    return record


def student_birth_date(grade):
    birth_year = 2026 - (grade + 5)
    return date(birth_year, rng.randint(1, 12), rng.randint(1, 28))


try:
    if not env['school.exam.grade'].search([], limit=1):
        raise RuntimeError(
            'No grading scale is installed; install School_Management_System first.'
        )

    company = env.company
    academic_year = get_or_create(
        'school.academic.year',
        [('name', '=', '2026-2027'), ('company_id', '=', company.id)],
        {
            'name': '2026-2027',
            'company_id': company.id,
            'date_start': date(2026, 1, 1),
            'date_end': date(2026, 12, 31),
            'is_current': True,
            'state': 'open',
        },
        'academic_years',
        'Academic Year 2026-2027',
    )
    term_data = (
        ('Term 1', date(2026, 1, 1), date(2026, 4, 30), 10),
        ('Term 2', date(2026, 5, 1), date(2026, 8, 31), 20),
        ('Term 3', date(2026, 9, 1), date(2026, 12, 31), 30),
    )
    for name, date_start, date_end, sequence in term_data:
        get_or_create(
            'school.term',
            [('name', '=', name), ('academic_year_id', '=', academic_year.id)],
            {
                'name': name,
                'academic_year_id': academic_year.id,
                'date_start': date_start,
                'date_end': date_end,
                'sequence': sequence,
            },
            'terms',
            '%s 2026-2027' % name,
        )

    section_records = {}
    for section in ('A', 'B'):
        section_records[section] = get_or_create(
            'school.section',
            [('name', '=', section), ('company_id', '=', company.id)],
            {'name': section, 'company_id': company.id},
            'sections',
            'Section %s' % section,
        )

    class_records = {}
    for grade in range(6, 10):
        for section in ('A', 'B'):
            label = 'Class %s-%s' % (grade, section)
            class_records[(grade, section)] = get_or_create(
                'student.class',
                [
                    ('name', '=', 'Class %s' % grade),
                    ('section_id', '=', section_records[section].id),
                    ('company_id', '=', company.id),
                ],
                {
                    'name': 'Class %s' % grade,
                    'section_id': section_records[section].id,
                    'academic_year_id': academic_year.id,
                    'company_id': company.id,
                    'total_seat': 30,
                },
                'classes',
                label,
            )
            if class_records[(grade, section)].academic_year_id != academic_year:
                current_record = 'Assigning academic year to %s' % label
                class_records[(grade, section)].write({
                    'academic_year_id': academic_year.id,
                })

    teacher_data = [
        ('Nusrat Jahan', '01711000001', 'M.Ed.', 9),
        ('Mahmudul Hasan', '01812000002', 'B.Ed.', 7),
        ('Farzana Akter', '01913000003', 'M.Sc. in Mathematics', 8),
        ('Tanvir Ahmed', '01614000004', 'M.Sc. in Physics', 6),
        ('Sabina Yasmin', '01515000005', 'M.A. in Bangla', 11),
        ('Rashed Karim', '01316000006', 'B.Sc. in ICT', 5),
    ]
    all_classes = env['student.class'].browse(
        [record.id for record in class_records.values()]
    )
    teachers = {}
    created_teacher_names = set()
    for name, contact, degree, experience in teacher_data:
        existing_teacher = env['school.teacher'].search([('name', '=', name)], limit=1)
        teachers[name] = get_or_create(
            'school.teacher',
            [('name', '=', name)],
            {
                'name': name,
                'contact_number': contact,
                'degree': degree,
                'experience': experience,
                'class_ids': [(6, 0, all_classes.ids)],
            },
            'teachers',
            'Teacher %s' % name,
        )
        if not existing_teacher:
            created_teacher_names.add(name)
        missing_class_ids = set(all_classes.ids) - set(teachers[name].class_ids.ids)
        if missing_class_ids:
            current_record = 'Assigning classes to Teacher %s' % name
            teachers[name].write({
                'class_ids': [(4, class_id) for class_id in missing_class_ids],
            })

    subject_names = [
        'Bangla',
        'English',
        'Mathematics',
        'Science',
        'Social Science',
        'ICT',
        'Religion',
        'Physical Education',
    ]
    subject_records = {}
    teacher_list = list(teachers.values())
    for class_index, ((grade, section), class_record) in enumerate(class_records.items()):
        for subject_index, subject_name in enumerate(subject_names):
            teacher = teacher_list[(class_index + subject_index) % len(teacher_list)]
            subject_records[(grade, section, subject_name)] = get_or_create(
                'school.subject',
                [
                    ('name', '=', subject_name),
                    ('class_id', '=', class_record.id),
                ],
                {
                    'name': subject_name,
                    'class_id': class_record.id,
                    'teacher_id': teacher.id,
                },
                'subjects',
                '%s %s-%s' % (subject_name, grade, section),
            )
    for class_index, ((grade, section), class_record) in enumerate(class_records.items()):
        class_teacher = teacher_list[class_index % len(teacher_list)]
        if class_record.class_teacher_id != class_teacher:
            current_record = 'Assigning class teacher to %s-%s' % (grade, section)
            class_record.write({'class_teacher_id': class_teacher.id})
    primary_subjects = {
        'Nusrat Jahan': 'Bangla',
        'Mahmudul Hasan': 'English',
        'Farzana Akter': 'Mathematics',
        'Tanvir Ahmed': 'Science',
        'Sabina Yasmin': 'Social Science',
        'Rashed Karim': 'ICT',
    }
    for teacher_name in created_teacher_names:
        primary_subject = env['school.subject'].search([
            ('name', '=', primary_subjects[teacher_name]),
            ('teacher_id', '=', teachers[teacher_name].id),
        ], limit=1)
        if primary_subject:
            current_record = 'Assigning subject to Teacher %s' % teacher_name
            teachers[teacher_name].write({'subject': primary_subject.id})

    first_names = [
        'Arafat', 'Ayesha', 'Badhon', 'Farhan', 'Jannat', 'Mehedi',
        'Mim', 'Nabil', 'Nafisa', 'Omar', 'Rafi', 'Sadia',
    ]
    last_names = [
        'Rahman', 'Hossain', 'Akter', 'Chowdhury', 'Islam', 'Khan',
        'Sultana', 'Ahmed', 'Karim', 'Miah', 'Das', 'Begum',
    ]
    for grade, section in class_records:
        class_record = class_records[(grade, section)]
        for student_index in range(1, 7):
            name = '%s %s' % (
                first_names[(grade + student_index + (section == 'B')) % len(first_names)],
                last_names[(grade * 2 + student_index) % len(last_names)],
            )
            parent_contact = '01%09d' % rng.randint(0, 999999999)
            admission = get_or_create(
                'student.admission',
                [('name', '=', name), ('class_id', '=', class_record.id)],
                {
                    'name': name,
                    'date_of_birth': student_birth_date(grade),
                    'parent_contact': parent_contact,
                    'class_id': class_record.id,
                },
                'admissions',
                'Admission %s (%s-%s)' % (name, grade, section),
            )
            if not admission.student_id and admission.state != 'admitted':
                current_record = 'Admission workflow for %s' % name
                admission.action_submit()
                admission.action_under_review()
                admission.action_approve()
                admission.action_admit()

    extra_admissions = (
        ('Rumana Sultana', 'draft'),
        ('Shakil Hossain', 'submitted'),
        ('Tanjim Ahmed', 'under review'),
    )
    class_record = class_records[(6, 'A')]
    for name, target_state in extra_admissions:
        admission = get_or_create(
            'student.admission',
            [('name', '=', name), ('class_id', '=', class_record.id)],
            {
                'name': name,
                'date_of_birth': student_birth_date(6),
                'parent_contact': '01%09d' % rng.randint(0, 999999999),
                'class_id': class_record.id,
            },
            'admissions',
            'Extra admission %s' % name,
        )
        if not admission.student_id and admission.state == 'draft' and target_state != 'draft':
            current_record = 'Admission workflow for %s' % name
            admission.action_submit()
            if target_state == 'under review':
                admission.action_under_review()

    exam_subjects = ('Bangla', 'English', 'Mathematics')
    for class_index, ((grade, section), class_record) in enumerate(class_records.items()):
        for subject_index, subject_name in enumerate(exam_subjects):
            subject = subject_records[(grade, section, subject_name)]
            exam_name = 'Midterm Exam 2026 - Class %s-%s - %s' % (
                grade,
                section,
                subject_name,
            )
            exam = get_or_create(
                'school.exam',
                [('name', '=', exam_name)],
                {
                    'name': exam_name,
                    'exam_type': 'midterm',
                    'subject_id': subject.id,
                    'exam_date': date(2026, 6, 15 + class_index),
                    'total_marks': 100.0,
                    'passing_marks': 40.0,
                    'note': 'Seeded Midterm examination data.',
                },
                'exams',
                exam_name,
            )
            if exam.state == 'draft':
                current_record = 'Starting %s' % exam_name
                exam.action_start()
                results = exam.result_ids.sorted(key=lambda result: result.roll_number)
                for result_index, result in enumerate(results):
                    if result_index == len(results) - 1:
                        result.write({
                            'is_absent': True,
                            'marks_obtained': 0.0,
                            'remarks': 'Absent',
                        })
                    else:
                        below_passing = (class_index + subject_index) % 4 == 0 and result_index == 1
                        marks = rng.randint(45, 95)
                        if below_passing:
                            marks = rng.randint(25, 39)
                        result.write({
                            'is_absent': False,
                            'marks_obtained': marks,
                            'remarks': 'Regular performance',
                        })
                    created['results'] += 1
                current_record = 'Publishing %s' % exam_name
                exam.action_publish()

    print('School seed completed successfully.')
    print('Created: %s' % ', '.join('%s=%s' % item for item in created.items()))
    print('Skipped: %s' % ', '.join('%s=%s' % item for item in skipped.items()))
except Exception as error:
    env.cr.rollback()
    print('School seed failed at %s: %s' % (current_record, error))
    raise

env.cr.commit()
