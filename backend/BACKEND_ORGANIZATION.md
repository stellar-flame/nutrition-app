# Backend Organization

This document describes the organized structure of the backend Python files.

## Database Layer (`database/` package)

### `database/connection.py`
- **Purpose**: Database configuration and connection management
- **Contents**:
  - SQLAlchemy engine setup with connection pooling
  - Session management (`SessionLocal`, `get_db()`)
  - Base class for ORM models
  - Database initialization (`init_db()`)

### `database/models.py`
- **Purpose**: SQLAlchemy ORM models (database schema)
- **Contents**:
  - `UserModel`: User profile and characteristics
  - `MealModel`: Meal entries with nutrition data
  - Relationships between models

### `database/schemas.py`
- **Purpose**: Pydantic models for API validation and serialization
- **Contents**:
  - Request/response models for all endpoints
  - Data validation and type checking
  - Separated from database models for clean API contracts

### `database/crud.py`
- **Purpose**: Database operations (Create, Read, Update, Delete)
- **Contents**:
  - Functions for user and meal data manipulation
  - Database query logic
  - Business logic for data operations

### `database/__init__.py`
- **Purpose**: Package initialization with convenient imports
- **Contents**:
  - Exports commonly used database components
  - Enables shorter import paths

## API Layer

### `api/` package
- **chat.py**: Meal analysis and LLM integration endpoints
- **auth.py**: User authentication endpoints
- **users.py**: User profile management endpoints  
- **meals.py**: Meal CRUD endpoints

## Application Layer

### `main.py`
- **Purpose**: FastAPI application setup and configuration
- **Contents**:
  - Application initialization
  - Route registration
  - Database initialization

## LLM Layer (`llm/` package)

### `llm/tools.py`
- **Purpose**: OpenAI function tool definitions

### `llm/helpers.py`  
- **Purpose**: LLM utility functions and response parsing

### `llm/prompts.py`
- **Purpose**: Centralized prompt templates

## Benefits of This Organization

1. **Separation of Concerns**: Database, API, and business logic are clearly separated
2. **Maintainability**: Each module has a single responsibility
3. **Testability**: Isolated components are easier to test
4. **Scalability**: Easy to extend without affecting other components
5. **Import Clarity**: Clear dependency relationships between modules

## Import Patterns

```python
# Database layer - Direct imports from package
from database import UserModel, MealModel, get_db, init_db
from database import ChatRequest, ChatResponse, UserProfile, MealCreate
from database import create_user_profile, get_meals

# Database layer - Explicit imports
from database.connection import get_db, init_db, Base
from database.models import UserModel, MealModel
from database.schemas import ChatRequest, ChatResponse, UserProfile, MealCreate
from database.crud import create_user_profile, get_user_profile

# LLM layer
from llm.tools import USDA_FUNCTION
from llm.helpers import create_openai_response
from llm.prompts import LOOKUP_PROMPT
```

## Migration Notes

All imports have been updated throughout the codebase to use the new structure. The schemas and crud modules have been moved into the `database/` package for better organization. You can now import database-related functionality either directly from the `database` package or from specific modules within it.
