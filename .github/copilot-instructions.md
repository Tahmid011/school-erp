# Project rules
- Odoo 17 Community module "School Management System" (technical name School_Management_System). Python 3.10+, PostgreSQL.
- Reuse standard Odoo apps/models before creating anything: res.partner, res.users, hr.employee, hr_attendance, hr_holidays, account (Invoicing: account.move, account.payment, payment terms, products as fee heads), product, mail (threads, activities, templates), portal, website, calendar, ir.attachment, ir.sequence, ir.cron. Never build a custom ledger, journal, payment or invoice model.
- Only create new models for school-specific concepts. Extend standard models with _inherit instead of copying them.
- Use Odoo 17 view syntax (invisible="state != 'draft'", no attrs=), <tree> for list views.
- Every new model: ir.model.access.csv entries for every group, ir.rule where data must be restricted, company_id with multi-company rule, mail.thread where state/changes matter, sequences for codes.
- Never edit existing data XML ids; provide migration scripts (migrations/17.0.x.y/post-migration.py) when renaming or changing fields that already hold data.
- Keep code small and readable: one model per file, matching view file, update __manifest__.py data order correctly.
- After each task: list the files changed, the manifest changes, and a short manual test checklist.