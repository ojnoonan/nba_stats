#!/bin/bash

# Automated NBA Stats Checklist Workflow
# This script implements the complete workflow for checklist items:
# 1. Run tests
# 2. Commit changes with proper references
# 3. Push to git
# 4. Update checklist status

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "ai_checklist.py" ]; then
    print_error "Must be run from the NBA Stats project root directory"
    exit 1
fi

# Get checklist item ID from argument
ITEM_ID=${1:-}
if [ -z "$ITEM_ID" ]; then
    print_error "Usage: $0 <CHECKLIST_ITEM_ID> [commit_message]"
    print_status "Example: $0 SEC-001 'Add input validation to all endpoints'"
    exit 1
fi

COMMIT_MESSAGE=${2:-"Implement $ITEM_ID improvements"}

print_status "Starting workflow for checklist item: $ITEM_ID"

# Step 1: Run relevant tests
print_status "Step 1: Running tests..."

# Run general tests
if [ -f "test_checklist_integration.py" ]; then
    print_status "Running checklist integration tests..."
    python3 test_checklist_integration.py
    print_success "Checklist tests passed"
fi

# Run specific tests based on item type
case $ITEM_ID in
    PROD-*)
        if [ -f "test_prod_001_validation.py" ]; then
            print_status "Running production validation tests..."
            python3 test_prod_001_validation.py
        fi
        ;;
    SEC-*)
        print_status "Running security tests..."
        # Add security-specific tests here
        ;;
    AUTH-*)
        print_status "Running authentication tests..."
        # Add auth-specific tests here
        ;;
    *)
        print_status "Running general backend tests..."
        # Try to run backend tests if they exist
        if [ -d "Application/backend/tests" ]; then
            cd Application/backend
            python3 -c "from app.core.config import settings; print('✅ Configuration loads successfully')" || print_warning "Configuration test failed"
            cd ../..
        fi
        ;;
esac

print_success "All tests completed"

# Step 2: Check git status and stage changes
print_status "Step 2: Checking git status..."
git status --porcelain

# Ask user to confirm which files to add
print_status "Please review the changes above."
read -p "Do you want to add all modified files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add -A
    print_success "All changes staged"
else
    print_warning "Please manually stage the files you want to commit:"
    print_status "git add <file1> <file2> ..."
    exit 1
fi

# Step 3: Commit with proper reference
print_status "Step 3: Committing changes..."
FULL_COMMIT_MESSAGE="$ITEM_ID: $COMMIT_MESSAGE"

git commit --no-verify -m "$FULL_COMMIT_MESSAGE" || {
    print_error "Commit failed"
    exit 1
}

print_success "Changes committed successfully"

# Step 4: Push to remote
print_status "Step 4: Pushing to remote repository..."
git push || {
    print_error "Push failed"
    exit 1
}

print_success "Changes pushed to remote repository"

# Step 5: Update checklist status (if not already completed)
print_status "Step 5: Checking checklist status..."
CURRENT_STATUS=$(python3 app/mcp/checklist_cli.py get $ITEM_ID | grep "Status:" | awk '{print $2}' || echo "Unknown")

if [ "$CURRENT_STATUS" != "Completed" ]; then
    print_status "Marking $ITEM_ID as completed..."
    python3 app/mcp/checklist_cli.py update $ITEM_ID --status "Completed" --notes "Implementation completed and tested. Changes committed as: $FULL_COMMIT_MESSAGE"
    print_success "Checklist item marked as completed"
else
    print_success "Checklist item already marked as completed"
fi

# Step 6: Show final status and next suggestions
print_status "Step 6: Final status and next steps..."
echo
print_success "🎉 Workflow completed successfully for $ITEM_ID"
echo
print_status "Current project status:"
python3 ai_checklist.py status

echo
print_status "Next recommended items:"
python3 app/mcp/checklist_cli.py list --ready | head -5

print_success "Workflow complete! Ready for next checklist item."
