# School data seed

Run the seed script from the `school-erp` repository root. In PowerShell, pipe
the file contents because `<` is not input redirection:

```powershell
Get-Content -Raw scripts\seed_school_data.py |
    docker exec -i first_project-odoo-1 odoo shell -d school_management_db
```

The `School_Management_System` module must already be installed in
`school_management_db`.
The container name can be checked with `docker ps`; for this project it is
`first_project-odoo-1`.
The script is idempotent and commits only after all classes, subjects, teachers,
admissions, and exams have been created successfully.
