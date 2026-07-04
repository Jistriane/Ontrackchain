#!/usr/bin/env bash
# Quick setup script for Ontrackchain Governance CI/CD Integration
# Usage: ./setup-governance-cicd.sh

set -e

echo "🚀 Ontrackchain Governance CI/CD Setup"
echo "======================================"
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI not found. Please install gh: https://cli.github.com"
    echo "    After installation, run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "❌ Could not determine repository. Are you in a GitHub repo directory?"
    exit 1
fi

echo "📦 Repository: $REPO"
echo ""

# Step 1: Check workflows exist
echo "1️⃣  Checking GitHub Actions workflows..."
WORKFLOWS=(
    "governance-gate-check.yml"
    "governance-gate-refresh.yml"
    "governance-status-notify.yml"
)

for wf in "${WORKFLOWS[@]}"; do
    if [ -f ".github/workflows/$wf" ]; then
        echo "   ✅ $wf found"
    else
        echo "   ❌ $wf NOT FOUND"
        exit 1
    fi
done
echo ""

# Step 2: Ask for Slack webhook
echo "2️⃣  Configure Slack Webhook (Optional)"
echo "   This enables automatic Slack notifications."
read -p "   Do you have a Slack webhook URL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "   Enter Slack webhook URL: " SLACK_WEBHOOK
    
    # Add/update secret
    echo "   Adding secret SLACK_WEBHOOK_URL..."
    gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK" 2>/dev/null || {
        echo "   ⚠️  Could not set secret. You can do this manually:"
        echo "      Settings → Secrets and variables → Actions → New repository secret"
        echo "      Name: SLACK_WEBHOOK_URL"
        echo "      Value: $SLACK_WEBHOOK"
    }
    echo "   ✅ Secret configured"
else
    echo "   ⏭️  Skipping Slack setup (workflows will work without it)"
fi
echo ""

# Step 3: Verify workflows are discoverable
echo "3️⃣  Verifying workflows in GitHub..."
WF_COUNT=$(gh workflow list 2>/dev/null | grep -c governance || echo "0")
echo "   Found $WF_COUNT governance workflows"
echo ""

# Step 4: Summary
echo "✅ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Test governance-gate-check manually:"
echo "   gh workflow run governance-gate-check.yml"
echo ""
echo "2. Or visit GitHub UI:"
echo "   https://github.com/$REPO/actions"
echo ""
echo "3. Open a PR against main to test automatic validation"
echo ""
echo "4. (Optional) Configure branch protection:"
echo "   Settings → Branches → Add rule → main"
echo "   ✓ Require status checks to pass before merging"
echo "   ✓ Governance Gate"
echo ""
echo "📚 Documentation:"
echo "   .github/GOVERNANCE_CICD_SETUP.md"
echo ""
echo "💡 Workflows:"
echo "   - governance-gate-check.yml (PR validation + manual trigger)"
echo "   - governance-gate-refresh.yml (daily refresh at 08:00 UTC)"
echo "   - governance-status-notify.yml (daily notify at 09:00 UTC)"
echo ""
