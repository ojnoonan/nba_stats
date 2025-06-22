# AI Agent Prompt Template for NBA Stats Project

## 🤖 **MANDATORY CHECKLIST WORKFLOW PROMPT**

Copy and paste this prompt when asking an AI agent to work on the NBA Stats project:

---

## **PROMPT TEMPLATE:**

```
You are working on the NBA Stats application project. This project uses a systematic improvement checklist to ensure organized progress.

**MANDATORY FIRST STEPS:**

1. **Check current project status** by running:
   ```bash
   python3 ai_checklist.py status
   ```

2. **Review what items are ready to work on** by running:
   ```bash
   python3 app/mcp/checklist_cli.py list --ready
   ```

3. **Check high priority items** by running:
   ```bash
   python3 app/mcp/checklist_cli.py list --high-priority
   ```

**YOUR TASK:**
- Review the checklist status output
- Identify the next most appropriate item to work on (prioritize: Critical → High → Medium-High → Medium → Low)
- Choose an item that is "ready to work on" (no blocking dependencies)
- Update the item status to "In Progress" before starting
- Implement the improvement
- Update the item as "Completed" when done
- Suggest what should be worked on next

**WORKFLOW REQUIREMENTS:**
1. ✅ Start by running the status commands above
2. ✅ Choose ONE specific checklist item to work on
3. ✅ Update item status: `python3 app/mcp/checklist_cli.py update [ITEM-ID] --status "In Progress" --assign "AI Agent"`
4. ✅ Reference the checklist item ID in all commits (e.g., "AUTH-001: Implemented JWT authentication")
5. ✅ Add progress notes as you work: `python3 app/mcp/checklist_cli.py update [ITEM-ID] --notes "Progress update"`
6. ✅ Mark as completed: `python3 app/mcp/checklist_cli.py update [ITEM-ID] --status "Completed"`
7. ✅ Show final status and suggest next ready items

**FOCUS AREAS (in priority order):**
- 🔥 Critical: Authentication, Security, Production readiness
- 🔴 High: Error handling, Logging, Input validation
- 🟠 Medium-High: Database optimization, API caching
- 🟡 Medium: Testing, Documentation, Code quality

Please start by running the checklist status commands and then proceed with implementing ONE checklist item completely.
```

---

## **EXAMPLE USAGE:**

### For Continuing Work:
```
You are working on the NBA Stats application. Please:

1. Check the current checklist status using the commands in AI_AGENT_CHECKLIST_INTEGRATION.md
2. Continue with the next highest priority item that's ready to work on
3. Follow the complete workflow: status update → implementation → completion → next suggestion

Focus on Critical and High priority items first. Make sure to update the checklist as you work and reference item IDs in your commits.
```

### For Specific Areas:
```
You are working on the NBA Stats application. Please:

1. Run `python3 ai_checklist.py status` to see current progress
2. Focus on [SECURITY/DATABASE/API/TESTING] related improvements
3. Choose the highest priority ready item in that category
4. Follow the complete checklist workflow from start to finish

Use the checklist system to track your progress and ensure systematic improvement.
```

### For Quick Task:
```
Working on NBA Stats app - please check checklist status first with `python3 ai_checklist.py status`, then work on the next ready high-priority item. Follow the checklist workflow in AI_AGENT_CHECKLIST_INTEGRATION.md.
```

---

## **VERIFICATION COMMANDS**

After giving the prompt, verify the agent is following the checklist by asking them to show:

```bash
# Verify they checked status
python3 ai_checklist.py status

# Verify they updated an item
python3 app/mcp/checklist_cli.py get [ITEM-ID]

# Check overall progress
python3 app/mcp/checklist_cli.py stats
```

---

## **TIPS FOR EFFECTIVE PROMPTS:**

1. **Always include the mandatory first steps** - checking status and ready items
2. **Be specific about the workflow requirements** - update before starting, reference in commits, mark completed
3. **Emphasize priority order** - Critical → High → Medium → Low
4. **Request final status and next suggestions** - ensures continuity
5. **Reference the integration guide** - `AI_AGENT_CHECKLIST_INTEGRATION.md`

This ensures every AI agent will systematically work through your improvement checklist while maintaining proper tracking and progress visibility.
