# Vinayaka Chavithi Youth Committee — Django UI

This ZIP contains a **UI-only Django project** based on the supplied design documentation.

## Included
- Responsive Bootstrap layout
- Login, registration and password-reset screens
- Dashboard
- Funds Received list + add form
- Expenses list + add form
- Reports screen and filters
- Committee Members list + add form
- Events list + add form
- Administration screens
- Audit Logs
- Sidebar navigation and mobile menu
- Placeholder charts/financial values

## Intentionally not included
- PostgreSQL connection
- Django models
- migrations
- authentication/backend logic
- CRUD persistence
- REST APIs
- real Chart.js data
- PDF/Excel generation
- file upload processing
- permissions/business rules

## Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Open:
http://127.0.0.1:8000/

The default route opens the UI login page. The login/register buttons are UI navigation only.
