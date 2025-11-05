autobook/
├── Dockerfile  # Updated
├── docker-compose.yml  # Updated
├── requirements.txt  # Updated
├── manage.py  # Unchanged
├── autobook/
│   ├── __init__.py
│   ├── settings.py  # Updated for Channels
│   ├── urls.py  # Unchanged
│   ├── wsgi.py
│   ├── asgi.py  # Updated for Channels
│   ├── celery.py  # Unchanged
│   └── tasks.py  # Enhanced
├── organizer/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/  # Run `python manage.py makemigrations` after updates
│   ├── models.py  # Enhanced with Log model
│   ├── tests.py
│   ├── urls.py  # Updated
│   ├── views.py  # Enhanced with upload and Channels
│   ├── forms.py  # Updated for upload
│   ├── templates/
│   │   └── organizer/
│   │       ├── base.html  # Updated with JS for WS
│   │       ├── index.html  # Updated
│   │       └── results.html  # Updated with progress bar
│   └── utils.py  # Major enhancements
└── README.md  # Updated
