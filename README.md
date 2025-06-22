# NBA Stats Application

A comprehensive NBA statistics tracking application with FastAPI backend and React frontend.

## 🤖 FOR AI AGENTS - MANDATORY CHECKLIST INTEGRATION

**⚠️ IMPORTANT**: This project uses a systematic improvement checklist. Before making ANY changes:

```bash
# Check current project status
python3 ai_checklist.py status

# Or use the full CLI
python3 app/mcp/checklist_cli.py stats
```

**See [AI_AGENT_CHECKLIST_INTEGRATION.md](AI_AGENT_CHECKLIST_INTEGRATION.md) for complete integration guide.**

---

## Quick Start

### Development Setup
```bash
# Backend
cd Application/backend
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Configure environment (IMPORTANT!)
cp .env.example .env
# Generate secure secret key:
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
# Add the generated key to your .env file

uvicorn app.main:app --reload --port 7778

# Frontend  
cd Application/frontend
npm install
npm run dev
```

### Production Deployment
```bash
# 1. Set secure environment variables
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export ENVIRONMENT=production

# 2. Deploy with Docker
docker-compose up -d
```

⚠️ **Security Warning**: Never use default secret keys in production! See [SECURITY.md](SECURITY.md) for details.

### Using the Checklist System
```bash
# Navigate to checklist tools
cd app/mcp

# Show project improvement status
python3 checklist_cli.py stats

# List high priority items
python3 checklist_cli.py list --high-priority

# Interactive AI agent workflow
python3 ../../ai_checklist.py
```

## 📋 Current Project Status

Run `python3 ai_checklist.py status` to see:
- Overall completion percentage
- High priority items needing attention
- Items ready to work on
- Blocked items and their dependencies

## 🎯 AI Agent Integration

### Before Starting Work:
1. ✅ Run `python3 ai_checklist.py status`
2. ✅ Check `python3 app/mcp/checklist_cli.py list --ready`
3. ✅ Update item status to "In Progress"

### While Working:
- 📝 Add progress notes to checklist items
- 🔗 Reference checklist IDs in commits (e.g., "AUTH-001: Added JWT")
- 🔄 Update status as work progresses

### After Completing:
- ✅ Mark items as "Completed"
- 🎯 Suggest next ready items
- 📊 Check how completion affects dependencies

## 🚨 Critical Items

Current critical priority items (run checklist for latest):
- Authentication system implementation
- Remove hardcoded secrets
- Add input validation
- Implement error handling

## Architecture

- **Backend**: FastAPI with SQLAlchemy
- **Frontend**: React with Vite
- **Database**: SQLite (development)
- **API**: NBA Stats API integration

## Key Features

- Team and player statistics
- Game schedules and results
- Real-time data updates
- Admin dashboard
- Search functionality

## Contributing

1. **Check the checklist first**: `python3 ai_checklist.py status`
2. **Find ready items**: `python3 app/mcp/checklist_cli.py list --ready`
3. **Update checklist**: Reference item IDs in commits
4. **Follow the improvement plan**: Prioritize Critical → High → Medium → Low

## VS Code Integration

Open the workspace file for integrated checklist tasks:
```bash
code nba-stats.code-workspace
```

Available tasks:
- **Checklist: Show Status** - View current project status
- **Checklist: High Priority Items** - See critical items
- **Checklist: Ready Items** - See what's ready to work on
- **Checklist: Interactive Update** - Update items interactively

## Documentation

- [Complete Improvement Checklist](IMPROVEMENT_CHECKLIST.md)
- [AI Agent Integration Guide](AI_AGENT_CHECKLIST_INTEGRATION.md)
- [Checklist Management Tools](app/mcp/README.md)

---

**🎯 The goal is systematic improvement guided by the checklist - ensuring all AI agents contribute to the same organized plan.**
