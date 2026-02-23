# Project Overview

This project is a FastAPI-based web application that serves as a scalable starting point for building robust APIs. It follows a modular monolith architecture, with a clear separation of concerns between the presentation layer (API), business logic layer (services), and data access layer (CRUD).

**Main Technologies:**

*   **Backend:** Python with FastAPI
*   **Database:** PostgreSQL (interfaced with SQLAlchemy)
*   **Data Validation:** Pydantic
*   **Database Migrations:** Alembic
*   **Containerization:** Docker and Docker Compose

**Architecture:**

The project is structured as a layered monolith:

1.  **API Layer (`app/api`):** Handles HTTP requests and responses. It includes versioned endpoints for different resources like users and prompts.
2.  **CRUD Layer (`app/crud`):** Contains functions for Create, Read, Update, and Delete operations on the database models.
3.  **Models Layer (`app/models`):** Defines the SQLAlchemy database models.
4.  **Schemas Layer (`app/schemas`):** Defines the Pydantic schemas for data validation and serialization.
5.  **Services Layer (`app/services`):** Intended for business logic, though it currently only contains database initialization.

# Building and Running

The application is designed to be run with Docker Compose.

**To build and run the application:**

```bash
docker-compose up --build
```

This command will build the Docker image for the FastAPI application and start the necessary services, including the database.

**To run the application locally (without Docker):**

1.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the application using uvicorn:
    ```bash
    uvicorn main:app --reload
    ```

# Development Conventions

*   **Modular Structure:** The code is organized into modules based on features (e.g., `users`, `prompts`). Each feature has its own models, schemas, and CRUD operations.
*   **Dependency Injection:** FastAPI's dependency injection system is used to provide database sessions to the API endpoints.
*   **Database Migrations:** Alembic is used to manage database schema changes. Migrations are located in the `app/alembic/versions` directory.
*   **Testing:** While no tests are currently included, the project structure is set up to support unit and integration tests.
*   **API Versioning:** The API is versioned, with the first version located in `app/api/v1`.
