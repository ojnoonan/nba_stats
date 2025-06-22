# Quick AI Agent Prompts for NBA Stats Project

## 🚀 **READY-TO-USE PROMPTS**

### **1. Standard Continuation Prompt**
```
You are working on the NBA Stats application. Please:

1. Check current checklist status: `python3 ai_checklist.py status`
2. Review ready items: `python3 app/mcp/checklist_cli.py list --ready`
3. Choose the highest priority ready item
4. Update status to "In Progress" before starting
5. Implement the improvement
6. Reference checklist ID in commits
7. Mark as "Completed" when done
8. Show final status and suggest next items

Follow the workflow in AI_AGENT_CHECKLIST_INTEGRATION.md. Focus on Critical/High priority items first.
```

### **2. Quick Security Focus Prompt**
```
NBA Stats project work needed. Check `python3 ai_checklist.py status` first, then work on the next ready security-related item (AUTH-*, SEC-*, PROD-*). Follow checklist workflow: update status → implement → mark complete → suggest next.
```

### **3. Next Item Prompt**
```
Continue NBA Stats improvements. Run checklist status check, pick next highest priority ready item, follow complete workflow from AI_AGENT_CHECKLIST_INTEGRATION.md. Update checklist before/during/after work.
```

### **4. Specific Focus Prompt**
```
NBA Stats project: Focus on [CATEGORY] improvements. Check status with `python3 ai_checklist.py status`, find ready items in that category, implement highest priority one following full checklist workflow.
```

---

## 🎯 **CURRENT PROJECT FOCUS**

Based on latest status, prioritize these ready items:
1. **PROD-001** - Remove hardcoded secrets (Critical, Ready) 🔥
2. **SEC-001** - Add input validation (High, Ready) 🔴  
3. **SEC-002** - SQL injection protection (High, Ready) 🔴
4. **ERR-001** - Error handling (High, Ready) 🔴

---

## 📋 **DYNAMIC PROMPT GENERATOR**

For current status-based prompts, run:
```bash
python3 generate_ai_prompt.py
```

This generates a prompt with live project status, ready items, and high priority items automatically included.

---

## 💡 **USAGE TIPS**

- Use the dynamic generator for most current info
- Use quick prompts for rapid iteration
- Always emphasize the checklist workflow
- Remind about commit message references
- Focus on Critical → High → Medium priority order
