# NOUN Student Admission Management System

An academic demonstration prototype built with Flask, SQLite, Jinja2 templates, and CSS. It demonstrates an applicant application workflow and an administrator review workspace.

> **Demonstration only:** This is not an official National Open University of Nigeria (NOUN) portal. Do not enter real personal information or rely on the prototype for admissions decisions.

## Features

### Applicant

- Register and sign in with an email address and password.
- View a dashboard with the applicant name, application reference, completion progress, and current status.
- Save personal details, academic qualifications, and programme/study-centre preferences in separate steps.
- Review and submit a completed application.
- Sign in later to track status and read submitted application details.
- Submitted applications are read-only in this prototype.

### Administrator

- Create an administrator account using the interactive command below; there is no built-in administrator password.
- Sign in through the separate staff sign-in page.
- View application totals and status counts.
- Search and filter submitted applications.
- Open an applicant record, record qualification verification notes, and change the status to Pending, Under Review, Approved, or Rejected.
- Download submitted records as a CSV file from the applications page.

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt`

## Run locally

From this directory:

```bash
python -m pip install -r requirements.txt
```

Set a session secret before starting. For Bash or Zsh:

```bash
export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python app.py
```

Open `http://127.0.0.1:5000`. The SQLite database is created automatically at `instance/admissions.sqlite3`. Set `ADMISSIONS_DB_PATH` to use a different SQLite file.

On Replit, provide `SESSION_SECRET` through the Secrets tool. The configured web preview starts the Flask app for you.

## Create an administrator

From the workspace root, run:

```bash
cd artifacts/noun-admission-management
python -m flask --app app create-admin
```

Enter the administrator's email and name, then choose and confirm a password of at least 10 characters when prompted. Password entry is hidden, and the password is hashed before storage. There is no default staff account or password. The command uses this application's SQLite database (`instance/admissions.sqlite3` by default); if `ADMISSIONS_DB_PATH` is set, it uses that database instead.

## Try the applicant and administrator flows

1. Open `/register` and create an applicant account using fictional information and a password of at least 10 characters.
2. On the dashboard, note the generated application reference.
3. Complete Personal Information, Academic Qualification, and Programme & Study Centre. Fields are validated and saved to SQLite.
4. Review the information and submit it. The status changes from Draft to Pending.
5. Sign out, create an administrator using the command above if you have not already, and sign in at `/admin/login`.
6. Search by the applicant's name, email, programme, or reference. Optionally filter by status.
7. Open the record, mark qualification verification, add verification/review notes, choose a status, and save.
8. Sign out and sign back in as the applicant to see the updated status and submitted details.
9. As an administrator, use the CSV download on the applications page to retrieve submitted records.

The application does not seed sample users or credentials. Create accounts using the steps above.

## Security notes

- Passwords are stored as Werkzeug password hashes, never as plain text.
- Forms use CSRF protection; database reads and writes use SQLAlchemy's parameterized ORM.
- Administrator views and CSV export require an authenticated administrator account.
- Registration only creates applicant-role accounts. Administrators are created with the protected interactive CLI command.
- SQLite data is stored in the ignored `instance/` directory by default; do not commit a database containing applicant records.

This is an academic prototype, not a production admissions platform. Use fictional records only.
