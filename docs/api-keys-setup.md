# 🔑 How to Get Slack & Jira API Keys

This guide provides detailed steps to obtain the API keys and tokens needed for PulseDev+ integrations.

## 🔵 Slack API Setup

### Option 1: Slack Bot Token (Recommended - Full Features)

#### Step 1: Create a Slack App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app details:
   - **App Name**: `PulseDev+ Bot`
   - **Development Slack Workspace**: Select your workspace
5. Click **"Create App"**

#### Step 2: Configure Bot Token Scopes
1. In your app dashboard, click **"OAuth & Permissions"** (left sidebar)
2. Scroll to **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
4. Add these scopes:
   ```
   chat:write          - Send messages as the bot
   chat:write.public   - Send messages to public channels
   channels:read       - View basic info about public channels
   groups:read         - View basic info about private channels
   users:read          - View people in workspace
   ```

#### Step 3: Install Bot to Workspace
1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   ```
   SLACK_BOT_TOKEN=xoxb-1234567890123-1234567890123-abcdefghijklmnopqrstuvwx
   ```

#### Step 4: Get Signing Secret
1. Go to **"Basic Information"** (left sidebar)
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**
   ```
   SLACK_SIGNING_SECRET=abcdefghijklmnopqrstuvwxyz123456
   ```

### Option 2: Incoming Webhooks (Simpler - Limited Features)

#### Step 1: Create Slack App (same as above)
Follow steps 1 from Option 1.

#### Step 2: Enable Incoming Webhooks
1. In app dashboard, click **"Incoming Webhooks"** (left sidebar)
2. Toggle **"Activate Incoming Webhooks"** to **ON**
3. Click **"Add New Webhook to Workspace"**
4. Select the channel for notifications (e.g., `#development`)
5. Click **"Allow"**
6. Copy the webhook URL:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T1234567890/B1234567890/abcdefghijklmnopqrstuvwx
   ```

### Step 3: Add Bot to Channels (Bot Token Only)
1. Go to your Slack workspace
2. In each channel where you want notifications:
   - Type: `/invite @PulseDev+ Bot`
   - Or go to channel → View channel details → Members → Add people

---

## 🔷 Jira API Setup

### Step 1: Get Your Jira Information
1. **Jira Base URL**: Your Jira instance URL
   - **Cloud**: `https://yourcompany.atlassian.net`
   - **Server**: `https://jira.yourcompany.com`
2. **Email**: The email address of your Jira account
3. **Project Key**: The key of your project (visible in project settings)

### Step 2: Create API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Enter a label: `PulseDev+ Integration`
4. Click **"Create"**
5. **IMPORTANT**: Copy the token immediately (you won't see it again!)
   ```
   JIRA_API_TOKEN=ATATT3xFfGF0abcdefghijklmnopqrstuvwxyzABCDEF123456
   ```

### Step 3: Test Your Credentials
You can test your Jira credentials using curl:

```bash
# Replace with your actual values
export JIRA_EMAIL="your-email@company.com"
export JIRA_TOKEN="your-api-token-here"
export JIRA_URL="https://yourcompany.atlassian.net"

# Test API access
curl -X GET \
  -H "Authorization: Basic $(echo -n $JIRA_EMAIL:$JIRA_TOKEN | base64)" \
  -H "Accept: application/json" \
  "$JIRA_URL/rest/api/3/myself"
```

If successful, you'll see your user information.

### Step 4: Find Your Project Key
1. Go to your Jira instance
2. Navigate to **Projects** → **View all projects**
3. Find your project and note the **Key** (usually 2-10 uppercase letters)
4. Or check the URL when viewing issues: `https://yourcompany.atlassian.net/browse/PROJ-123`
   - The project key is `PROJ`

---

## 📝 Complete .env Configuration

Here's what your `.env` file should look like with real values:

```bash
# Slack Integration (choose one option)

# Option 1: Bot Token (recommended)
SLACK_BOT_TOKEN=xoxb-1234567890123-1234567890123-abcdefghijklmnopqrstuvwx
SLACK_SIGNING_SECRET=abcdefghijklmnopqrstuvwxyz123456

# Option 2: Webhook (alternative)
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T1234567890/B1234567890/abcdefghijklmnopqrstuvwx

# Jira Integration
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=john.doe@company.com
JIRA_API_TOKEN=ATATT3xFfGF0abcdefghijklmnopqrstuvwxyzABCDEF123456
JIRA_PROJECT_KEY=DEV
```

---

## 🧪 Testing Your Setup

### Test Slack Integration

#### Using Bot Token:
```bash
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer xoxb-your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "#general",
    "text": "Hello from PulseDev+! 🚀",
    "username": "PulseDev+ Bot"
  }'
```

#### Using Webhook:
```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from PulseDev+! 🚀",
    "username": "PulseDev+ Bot",
    "icon_emoji": ":robot_face:"
  }'
```

### Test Jira Integration:
```bash
# List projects (should include your project)
curl -X GET \
  -H "Authorization: Basic $(echo -n your-email@company.com:your-api-token | base64)" \
  -H "Accept: application/json" \
  "https://yourcompany.atlassian.net/rest/api/3/project"
```

---

## 🔒 Security Best Practices

### 1. Protect Your Tokens
- ✅ Add `.env` to your `.gitignore` file
- ✅ Use environment variables in production
- ✅ Never commit tokens to version control
- ✅ Rotate tokens periodically

### 2. Principle of Least Privilege
- ✅ Only grant necessary Slack scopes
- ✅ Use dedicated service accounts for Jira
- ✅ Limit API token access to required projects

### 3. Environment Separation
```bash
# Development
JIRA_BASE_URL=https://yourcompany-dev.atlassian.net

# Production
JIRA_BASE_URL=https://yourcompany.atlassian.net
```

---

## 🚨 Troubleshooting

### Slack Issues

**❌ "Invalid token"**
- Check token starts with `xoxb-` (bot) or `xoxp-` (user)
- Verify token was copied completely
- Ensure app is installed to workspace

**❌ "Channel not found"**
- Add bot to the channel: `/invite @PulseDev+ Bot`
- Use channel ID instead of name: `C1234567890`
- Check channel name format: `#channel-name`

**❌ "Missing scope"**
- Add required scopes in OAuth & Permissions
- Reinstall app to workspace after adding scopes

### Jira Issues

**❌ "Authentication failed"**
- Verify email matches Jira account exactly
- Check API token was copied completely (no extra spaces)
- Ensure base64 encoding is correct

**❌ "Project not found"**
- Verify project key is correct (case-sensitive)
- Check you have access to the project
- Try browsing to project in web interface

**❌ "Field required"**
- Check project's issue type configuration
- Verify required fields for your project
- Some projects require custom fields

---

## 📞 Getting Help

### Slack API Documentation
- https://api.slack.com/web
- https://api.slack.com/messaging/webhooks

### Jira API Documentation  
- https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/

### PulseDev+ Integration Testing
Once you have your tokens configured, test the integrations in PulseDev+:

1. Go to `http://localhost:5173/#/teams`
2. Select a team → **Integrations** tab
3. Configure your tokens
4. Click **Test Integration** buttons

You should see notifications in Slack and be able to create test tickets in Jira! 🎉
