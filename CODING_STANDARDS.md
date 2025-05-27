# NBA Stats - Development Standards

## Code Formatting and Style

### Backend (Python)

We use the following tools to maintain consistent code quality:

- **Black**: Automatic code formatting
- **isort**: Import statement sorting
- **Flake8**: Linting and style checking

#### Code Style Guidelines

1. **Line Length**: Maximum 88 characters
2. **Imports**:
   - Use absolute imports when possible
   - Group imports: stdlib, third-party, first-party, local
   - Sort imports alphabetically within groups
3. **Naming Conventions**:
   - Functions and variables: `snake_case`
   - Classes: `PascalCase`
   - Constants: `UPPER_SNAKE_CASE`
   - Private methods/attributes: prefix with `_`
4. **Docstrings**: Use Google-style docstrings for all public functions and classes

#### Example:
```python
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.team import Team
from app.schemas.team import TeamCreate, TeamResponse


class TeamService:
    """Service for managing NBA team operations."""

    def __init__(self, db: Session):
        """Initialize the team service.

        Args:
            db: Database session instance
        """
        self.db = db

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID.

        Args:
            team_id: The team identifier

        Returns:
            Team instance if found, None otherwise

        Raises:
            HTTPException: If team not found
        """
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
```

### Frontend (React/JavaScript)

We use the following tools:

- **Prettier**: Automatic code formatting
- **ESLint**: Linting and error detection

#### Code Style Guidelines

1. **Components**: Use PascalCase for component names
2. **Files**: Use PascalCase for component files, camelCase for utilities
3. **Props**: Use camelCase for prop names
4. **Hooks**: Prefix custom hooks with `use`
5. **Constants**: Use UPPER_SNAKE_CASE for module-level constants

#### Example:
```javascript
import { useState, useEffect } from "react";
import { teamService } from "../services/api";

const TeamCard = ({ teamId, onTeamSelect }) => {
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTeam = async () => {
      try {
        const teamData = await teamService.getTeam(teamId);
        setTeam(teamData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTeam();
  }, [teamId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="team-card" onClick={() => onTeamSelect(team)}>
      <h3>{team.name}</h3>
      <p>{team.city}</p>
    </div>
  );
};

export default TeamCard;
```

## Git Workflow

### Branch Naming
- Features: `feature/description-of-feature`
- Bug fixes: `fix/description-of-fix`
- Hotfixes: `hotfix/critical-issue`
- Releases: `release/v1.0.0`

### Commit Messages
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add team statistics endpoint
fix(frontend): resolve loading state bug in player list
docs(readme): update installation instructions
```

## Testing Standards

### Backend Testing
- Use pytest for all tests
- Aim for >90% test coverage
- Test file naming: `test_*.py`
- Use fixtures for common test data
- Mock external dependencies

### Frontend Testing
- Use React Testing Library and Vitest
- Test user interactions, not implementation details
- Test file naming: `*.test.jsx`
- Use MSW for API mocking

## Pre-commit Hooks

The following checks run automatically before each commit:
- Code formatting (Black, Prettier)
- Import sorting (isort)
- Linting (Flake8, ESLint)
- Basic file checks (trailing whitespace, large files)

## Code Review Guidelines

### For Authors
1. Keep PRs small and focused
2. Write clear descriptions
3. Ensure all tests pass
4. Update documentation if needed

### For Reviewers
1. Check for code style and conventions
2. Verify test coverage
3. Look for potential bugs or edge cases
4. Suggest improvements for readability
5. Approve only when confident in the changes

## IDE Configuration

### VS Code
Recommended extensions:
- Python (Microsoft)
- Black Formatter
- isort
- Flake8
- Prettier
- ESLint
- GitLens

### Settings
Add to `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "python.linting.flake8Enabled": true,
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "python.sortImports.args": ["--profile", "black"],
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[jsx]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Environment Setup

### Backend
1. Use Python 3.12+
2. Create virtual environment: `python -m venv env`
3. Activate environment: `source env/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install -e ".[dev]"`

### Frontend
1. Use Node.js 18+
2. Install dependencies: `npm install`
3. Run development server: `npm run dev`

## Error Handling

### Backend
- Use appropriate HTTP status codes
- Return consistent error response format
- Log errors with sufficient context
- Handle database connection errors gracefully

### Frontend
- Implement error boundaries for React components
- Show user-friendly error messages
- Handle API errors gracefully
- Provide retry mechanisms where appropriate
