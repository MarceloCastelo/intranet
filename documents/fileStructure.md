portal-corporativo/
├── app/
│   ├── __init__.py
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # Flask routes
│   ├── templates/           # Jinja2 templates
│   ├── static/
│   │   ├── css/
│   │   │   ├── input.css    # Tailwind source
│   │   │   └── output.css   # Compiled Tailwind
│   │   ├── js/
│   │   └── images/
│   ├── forms/               # WTForms
│   ├── utils/               # Helpers
│   └── services/            # Business logic
├── database/
│   └── schema.sql           # MySQL schema
├── nginx/
│   └── nginx.conf           # Nginx configuration
├── uploads/                 # User uploaded files
├── logs/                    # Application logs
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
├── tailwind.config.js
├── package.json
└── README.md