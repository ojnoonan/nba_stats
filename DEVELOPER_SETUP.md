# NBA Stats - Developer Setup Guide

## Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Git**
- **Docker & Docker Compose** (optional, for containerized development)

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd nba_stats
```

### 2. Backend Setup

#### Virtual Environment
```bash
cd Application/backend
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Database Setup
```bash
# Create database
alembic upgrade head

# (Optional) Load sample data
python update_data.py
```

#### Run Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd Application/frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Development Tools Setup

#### Pre-commit Hooks
```bash
# From project root
pre-commit install
```

This will automatically run code formatting and linting before each commit.

## Detailed Setup

### Backend Development

#### Environment Variables
Create a `.env` file in the backend directory:
```env
# Database
DATABASE_URL=sqlite:///./nba_stats.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# NBA API (if using external data sources)
NBA_API_BASE_URL=https://stats.nba.com/stats
NBA_API_TIMEOUT=30
```

#### Database Management
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Revert to previous migration
alembic downgrade -1
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_teams.py

# Run tests in verbose mode
pytest -v
```

#### Code Quality Checks
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Run all checks
pre-commit run --all-files
```

### Frontend Development

#### Environment Variables
Create a `.env` file in the frontend directory:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=NBA Stats Dashboard
```

#### Development Commands
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format
```

#### Testing (Future)
```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## Docker Development (Alternative)

### Using Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services
```bash
# Backend only
docker-compose up backend

# Frontend only
docker-compose up frontend

# Database only
docker-compose up postgres
```

## IDE Configuration

### VS Code
Install recommended extensions:
1. Open the project in VS Code
2. When prompted, install recommended extensions
3. Or manually install from `.vscode/extensions.json`

Recommended extensions:
- Python (Microsoft)
- Black Formatter
- isort
- Flake8
- Prettier - Code formatter
- ESLint
- GitLens
- REST Client (for API testing)

### Settings
The project includes VS Code settings in `.vscode/settings.json` that will:
- Format code on save
- Enable linting
- Configure Python interpreter
- Set up debugging

## Project Structure

```
nba_stats/
├── Application/
│   ├── backend/           # FastAPI backend
│   │   ├── app/          # Application code
│   │   ├── tests/        # Test files
│   │   ├── alembic/      # Database migrations
│   │   └── requirements.txt
│   └── frontend/         # React frontend
│       ├── src/          # Source code
│       ├── public/       # Static assets
│       └── package.json
├── Documents/            # Project documentation
├── docker-compose.yml    # Docker configuration
└── README.md
```

## Common Issues & Solutions

### Backend Issues

**Import errors:**
```bash
# Ensure you're in the backend directory and virtual environment is activated
cd Application/backend
source env/bin/activate
pip install -e .
```

**Database connection errors:**
```bash
# Check database file exists
ls -la nba_stats.db

# Recreate database
rm nba_stats.db
alembic upgrade head
```

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Frontend Issues

**Node modules issues:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Port conflicts:**
```bash
# Vite will automatically find an available port
# Or specify a different port
npm run dev -- --port 3000
```

### Git Issues

**Pre-commit hooks failing:**
```bash
# Run formatting manually
cd Application/backend
black app/ tests/
isort app/ tests/

cd ../frontend
npm run format

# Try commit again
git commit -m "Your message"
```

## Testing the Setup

### Verify Backend
1. Visit `http://localhost:8000/docs`
2. Try the `/teams` endpoint
3. Check that you get a JSON response

### Verify Frontend
1. Visit `http://localhost:5173`
2. Navigate to different pages
3. Check that data loads from the API

### Run Tests
```bash
# Backend tests
cd Application/backend
pytest

# Should see all tests passing
```

## Next Steps

1. Read the [Coding Standards](CODING_STANDARDS.md)
2. Check the [Project Analysis Report](PROJECT_ANALYSIS_REPORT.md)
3. Review the API documentation at `/docs`
4. Explore the codebase structure
5. Try making a small change and see the pre-commit hooks in action

## Getting Help

- Check existing issues in the repository
- Review the project documentation
- Ask questions in team channels
- Refer to the FastAPI and React documentation for framework-specific questions
