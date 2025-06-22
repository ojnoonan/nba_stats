# NBA Stats Project - AI Agent Integration Guide

## 🤖 FOR AI AGENTS: MANDATORY CHECKLIST INTEGRATION

**CRITICAL**: Before making ANY changes to this NBA Stats project, you MUST:

1. **Check the improvement checklist** using: `python3 app/mcp/checklist_cli.py stats`
2. **Identify related checklist items** for your task
3. **Update checklist status** when starting work
4. **Reference checklist IDs** in commit messages and documentation

---

## Quick Checklist Commands

```bash
# Navigate to checklist directory
cd app/mcp

# Show current project status
python3 checklist_cli.py stats

# List high priority items
python3 checklist_cli.py list --high-priority

# List items ready to work on
python3 checklist_cli.py list --ready

# Get details of specific item
python3 checklist_cli.py get [ITEM-ID]

# Update item when starting work
python3 checklist_cli.py update [ITEM-ID] --status "In Progress" --assign "AI Agent"

# Add progress notes
python3 checklist_cli.py update [ITEM-ID] --notes "Your progress update"

# Mark as completed
python3 checklist_cli.py update [ITEM-ID] --status "Completed"
```

---

## 🎯 AI Agent Workflow

### BEFORE Starting Any Task:
1. Run `python3 app/mcp/checklist_cli.py stats` to see current project status
2. Run `python3 app/mcp/checklist_cli.py list --high-priority` to see critical items
3. Check if your task relates to any checklist items
4. If related, update the item status to "In Progress"

### WHILE Working:
- Add notes to relevant checklist items with your progress
- Reference checklist item IDs in git commits (e.g., "AUTH-001: Added JWT middleware")
- Consider impact on other checklist items

### AFTER Completing:
- Update checklist item status to "Completed"
- Add final notes about what was accomplished
- Suggest next related items that are now ready to work on

---

## 🔗 Checklist Item Categories & IDs

- **AUTH-*** = Authentication & Authorization
- **SEC-*** = Security 
- **PROD-*** = Production Environment
- **ERR-*** = Error Handling & Monitoring
- **DB-*** = Database Optimization
- **API-*** = API Performance & Caching
- **ARCH-*** = Architecture Improvements
- **TEST-*** = Testing Infrastructure
- **QUAL-*** = Code Quality & Standards
- **DOC-*** = Documentation
- **UX-*** = User Experience
- **FE-*** = Frontend Architecture
- **DEV-*** = DevOps & Deployment

---

## 🚨 Critical Items (Must Address First)

Current critical items that need immediate attention:
- AUTH-001: Authentication system (In Progress)
- AUTH-002: JWT for admin endpoints
- AUTH-003: Secure admin routes
- PROD-001: Remove hardcoded secrets
- SEC-001: Input validation
- SEC-002: SQL injection protection

---

## 📊 Integration Examples

### Example 1: Adding Input Validation
```bash
# Before starting
python3 app/mcp/checklist_cli.py get SEC-001
python3 app/mcp/checklist_cli.py update SEC-001 --status "In Progress" --assign "AI Agent"

# While working
python3 app/mcp/checklist_cli.py update SEC-001 --notes "Added Pydantic models for request validation"

# After completing
python3 app/mcp/checklist_cli.py update SEC-001 --status "Completed" --notes "All API endpoints now have input validation"
```

### Example 2: Database Optimization
```bash
# Check what's ready
python3 app/mcp/checklist_cli.py list --category "Database Optimization"
python3 app/mcp/checklist_cli.py update DB-001 --status "In Progress"
# ... do the work ...
python3 app/mcp/checklist_cli.py update DB-001 --status "Completed"
```

---

## 🔄 Mandatory Integration Points

1. **Always start by checking checklist status**
2. **Always update relevant items when making changes**
3. **Always reference checklist IDs in commits**
4. **Always suggest next ready items after completion**
5. **Always consider dependencies when planning work**

## 🤖 Ready-to-Use AI Agent Prompts

**For quick prompting, see:**
- `QUICK_AI_PROMPTS.md` - Copy-paste prompts for different scenarios
- `AI_AGENT_PROMPT_TEMPLATE.md` - Detailed prompt templates and examples
- `python3 generate_ai_prompt.py` - Generate prompts with current status

**Example quick prompt:**
```
NBA Stats project: Check `python3 ai_checklist.py status` first, then work on next highest priority ready item. Follow checklist workflow: update status → implement → mark complete → suggest next.
```

This ensures all AI agents contribute to the systematic improvement of the NBA Stats application while tracking progress and maintaining consistency.
