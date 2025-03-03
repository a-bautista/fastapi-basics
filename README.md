## Project Structure

```
project_root/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Configuration settings
│   ├── dependencies.py     # Dependencies like DB session
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py         # DB connection setup
│   │   └── user.py         # User model
│   ├── schemas/            # Pydantic schemas
│   │   ├── __init__.py
│   │   └── user.py         # User schemas
│   ├── crud/               # Database operations
│   │   ├── __init__.py
│   │   ├── base.py         # Base CRUD operations
│   │   └── user.py         # User-specific operations
│   ├── api/                # API endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py   # API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── users.py # User endpoints
│   └── services/           # Business logic
│       ├── __init__.py
│       └── init_db.py      # Database initialization
├── .env                    # Environment variables
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Dockerfile for the API
└── requirements.txt        # Python dependencies
```

# How to run the application locally?

docker-compose up --build

# Version 0: abc52a9

Added basic configuration to run the application locally through a virtual environment in Python 3.11.9

# Version 0.1.0: 605f81a

Added configuration to run the application through Docker. 

# Version 0.2.0: 0ee0fba
