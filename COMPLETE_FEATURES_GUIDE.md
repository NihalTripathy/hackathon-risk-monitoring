# Complete Features Guide
## Understanding Every Feature: Webhooks, Notifications, Simulations, and More

**Purpose**: This guide explains every feature in the Risk Monitoring system in simple, beginner-friendly language with real-world examples.

**Target Audience**: PMOs, project managers, team members, and anyone who needs to understand how the system works.

---

## Table of Contents

1. [What-If Simulation Feature](#what-if-simulation)
2. [Use This Option Feature](#use-this-option)
3. [Webhooks Feature](#webhooks)
4. [Notifications Feature](#notifications)
5. [Portfolio Management Feature](#portfolio)
6. [Feedback System Feature](#feedback)
7. [Onboarding Feature](#onboarding)
8. [Audit Log Feature](#audit-log)
9. [Re-Analyze Feature](#re-analyze)
10. [Forensic Intelligence Feature](#forensic-intelligence)
11. [Mitigation Ranking Feature](#mitigation-ranking)
12. [How All Features Work Together](#features-together)

---

## What-If Simulation Feature {#what-if-simulation}

### What Is It?

**Simple Explanation**:
Think of a "What-If Simulation" like a flight simulator for your project. You can test different scenarios without actually changing your real project. It's like asking "What if I do this?" and getting an instant answer.

**Real-World Analogy**:
Imagine you're planning a road trip. Before you leave, you use Google Maps to test different routes:
- Route A: 4 hours, tolls
- Route B: 5 hours, no tolls
- Route C: 3.5 hours, heavy traffic

You can test all three without actually driving. That's what What-If Simulation does for your project.

---

### How It Works

#### Step 1: Identify a Problem

**Example**:
- Activity "Implementation Sign-off" is at high risk
- Current duration: 10 days
- Project is behind schedule

#### Step 2: Open What-If Simulator

**Where to Find It**:
- Go to Activity Details page
- Scroll to "What-If Simulator" section

**What You See**:
- **Simulation Type**: Choose "Duration Reduction" or "Risk Mitigation"
- **New Duration (days)**: Input field to type a new duration
- **Run Simulation** button

#### Step 3: Enter Your "What-If" Scenario

**Example Scenarios**:

**Scenario A: Reduce Duration**
- **Simulation Type**: "Duration Reduction"
- **New Duration**: Type "8" (reduce from 10 days to 8 days)
- Click "Run Simulation"

**Scenario B: Reduce Risk**
- **Simulation Type**: "Risk Mitigation"
- **Reduce Risk**: Check the box
- Click "Run Simulation"

**Scenario C: Add Resources**
- **Simulation Type**: "Duration Reduction"
- **New Duration**: Type "7" (faster with more people)
- Click "Run Simulation"

#### Step 4: View Results

**What You Get**:
- **Original Forecast**: What happens if you do nothing
- **New Forecast**: What happens with your change
- **Improvement**: How many days you'll save
- **Risk Score Impact**: How risk changes

**Example Results**:
```
Original Forecast:
- P50: 18 days
- P80: 21 days
- Risk Score: 49.4%

New Forecast (after reducing duration to 8 days):
- P50: 17 days (saved 1 day)
- P80: 20 days (saved 1 day)
- Risk Score: 45.0% (reduced by 4.4%)

Improvement:
- P50 Improvement: 1 day
- P80 Improvement: 1 day
- Risk Score Improvement: 4.4 points
```

---

### Why It's Useful for PMO

**1. Test Before Committing**
- **Problem**: PMOs often make changes without knowing the impact
- **Solution**: Test changes in simulation first
- **Benefit**: Make informed decisions

**Real-World Example**:
**Before Simulation**: PMO decides to add 2 developers to speed up a task. Cost: $20,000. Result: Saves 0.5 days (not worth it!)

**With Simulation**: PMO tests adding 2 developers first. Sees it only saves 0.5 days. Decides not to do it. Saves $20,000!

**2. Compare Multiple Options**
- **Problem**: Multiple solutions, which is best?
- **Solution**: Test all options and compare
- **Benefit**: Choose the best option

**Real-World Example**:
**Option 1**: Reduce duration by 10% → Saves 1 day, costs 5% more
**Option 2**: Reduce duration by 20% → Saves 2 days, costs 10% more
**Option 3**: Add 1 FTE → Saves 1.5 days, costs 8% more

**Simulation Results**: Option 3 is best (best balance of time saved vs. cost)

**3. Quantify Impact**
- **Problem**: Hard to explain benefits to leadership
- **Solution**: Simulation provides exact numbers
- **Benefit**: Clear, data-driven communication

**Real-World Example**:
**PMO to Leadership**: "If we reduce this task by 2 days, we'll save 1 day on overall project (P80 confidence) and reduce risk by 4.4 points. Cost: 5% increase."

**Leadership**: "Approved! The numbers are clear."

---

### Technical Details

#### How the Simulation Works

**Behind the Scenes**:

1. **Load Project Data**
   - System loads all activities
   - Builds digital twin (graph structure)
   - Gets current forecasts

2. **Apply Your Change**
   - Creates a copy of the project
   - Modifies the specific activity (duration, risk, or FTE)
   - Rebuilds the digital twin with changes

3. **Run Monte Carlo Simulation**
   - Runs 2,000 simulations (virtual project runs)
   - Each simulation has slight variations
   - Calculates probabilities

4. **Calculate Results**
   - Compares new forecast to original
   - Calculates improvements
   - Updates risk scores

5. **Return Results**
   - Sends data back to UI
   - UI displays in user-friendly format

**Time to Complete**: Usually 1-3 seconds

---

### API Endpoint

**Endpoint**: `POST /api/projects/{project_id}/simulate`

**Request Body**:
```json
{
  "activity_id": "20",
  "new_duration": 8.0,
  "reduce_risk": false,
  "new_fte": null
}
```

**Response**: See [UI_AND_API_COMPLETE_EXPLANATION.md](./UI_AND_API_COMPLETE_EXPLANATION.md) for detailed API response breakdown.

---

### Best Practices for PMO

1. **Test Multiple Scenarios**: Don't just test one option - test 3-5 options
2. **Compare Results**: Look at both time saved AND cost impact
3. **Use P80 for Planning**: P80 is more reliable than P50
4. **Consider Risk Score**: Time isn't everything - risk reduction matters too
5. **Document Decisions**: Save simulation results for future reference

---

## Use This Option Feature {#use-this-option}

### What Is It?

**Simple Explanation**:
After the system recommends mitigation options, you can click "Use This Option →" to automatically apply that recommendation to your simulation. It's like a "Quick Apply" button.

**Real-World Analogy**:
Like Amazon's "Buy Now" button - instead of adding to cart and going through checkout, you click one button and it's done.

---

### How It Works

#### Step 1: View Recommended Options

**Where to Find It**:
- Go to Activity Details page
- Scroll to "Recommended Mitigation Options" section

**What You See**:
- List of ranked options (Option #1, #2, #3, etc.)
- Each option shows:
  - Description (e.g., "Reduce duration by 10%")
  - P50/P80 Improvement
  - Cost Impact
  - **"Use This Option →"** button

#### Step 2: Review an Option

**Example Option**:
```
Option #1: Reduce Duration by 10% (crashing)
- P50 Improvement: 2.0 days
- P80 Improvement: 1.5 days
- Cost Impact: 105% (5% increase)
- FTE Days: 0.0
```

**PMO Decision**: "This looks good - saves 1.5 days at P80, only 5% cost increase."

#### Step 3: Click "Use This Option →"

**What Happens**:
1. System automatically fills in the "What-If Simulator" with this option's parameters
2. Scrolls to the simulator section
3. Pre-fills "New Duration" field (if duration reduction)
4. Pre-selects "Risk Mitigation" (if risk reduction)
5. **Ready to run** - just click "Run Simulation"

**Visual Flow**:
```
[Recommended Options Section]
  ↓
[Click "Use This Option →"]
  ↓
[What-If Simulator Section]
  - Fields automatically filled
  - Ready to simulate
  ↓
[Click "Run Simulation"]
  ↓
[See Results]
```

---

### Why It's Useful for PMO

**1. Saves Time**
- **Without**: Manually type duration, select options, configure
- **With**: One click, everything is set up
- **Time Saved**: 30-60 seconds per option

**2. Reduces Errors**
- **Without**: Might type wrong number, select wrong option
- **With**: System uses exact recommended values
- **Benefit**: No mistakes

**3. Easy Comparison**
- **Without**: Hard to remember what you tested
- **With**: Can quickly test multiple options
- **Benefit**: Better decision-making

**Real-World Example**:
**PMO Workflow**:
1. See Option #1: "Reduce by 10%" → Click "Use This Option" → Run → See results
2. See Option #2: "Reduce by 20%" → Click "Use This Option" → Run → See results
3. Compare: Option #2 saves more time but costs more
4. Decision: Choose Option #1 (better balance)

**Time**: 2 minutes to test 2 options vs. 5 minutes manually

---

### Technical Implementation

**Frontend Code Flow**:

```typescript
// When "Use This Option" is clicked
onClick={() => {
  if (option.type === 'reduce_duration') {
    setNewDuration(option.parameters.new_duration.toString())
    setSimulationType('duration')
  } else if (option.type === 'reduce_risk') {
    setReduceRisk(true)
    setSimulationType('risk')
  }
  // Scroll to simulator
  document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth' })
}}
```

**What This Does**:
1. Checks the option type
2. Sets the appropriate fields in the simulator
3. Scrolls to the simulator section
4. User can immediately run the simulation

---

### Best Practices for PMO

1. **Test Top 3 Options**: Usually the top 3 are the best - test them all
2. **Compare Results**: After testing, compare improvements and costs
3. **Consider Context**: Best option might depend on budget, timeline, resources
4. **Document**: Save which option you chose and why

---

## Webhooks Feature {#webhooks}

### What Is a Webhook?

**Simple Explanation**:
A webhook is like a "phone call" from our system to another system (like Slack, Teams, or Jira). When something important happens (like a high-risk alert), our system automatically calls the other system and tells it what happened.

**Real-World Analogy**:
Like a doorbell that rings when someone arrives. When a high-risk activity is detected, our system "rings the bell" (sends a webhook) to Slack/Teams/Jira, and they show you a notification.

---

### How Webhooks Work

#### The Flow

```
1. High-Risk Activity Detected
   ↓
2. System Checks Webhook Configurations
   ↓
3. For Each Enabled Webhook:
   - Check if it applies (project, threshold)
   - Format the message (Slack/Teams/Jira format)
   - Send HTTP POST request
   ↓
4. External System Receives Webhook
   ↓
5. External System Shows Notification
   (Slack channel, Teams channel, Jira ticket)
```

---

### Setting Up Webhooks

#### Step 1: Get Webhook URL

**For Slack**:
1. Go to Slack → Your Workspace → Apps → Incoming Webhooks
2. Create new webhook
3. Copy the webhook URL (looks like: `https://hooks.slack.com/services/...`)

**For Microsoft Teams**:
1. Go to Teams → Your Channel → Connectors
2. Add "Incoming Webhook"
3. Copy the webhook URL

**For Jira**:
1. Go to Jira → Project Settings → Webhooks
2. Create webhook
3. Copy the webhook URL

#### Step 2: Configure in Our System

**API Endpoint**: `POST /api/webhooks`

**Request Body**:
```json
{
  "name": "Slack Risk Alerts",
  "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "webhook_type": "slack",
  "project_id": null,  // null = all projects
  "triggers": {
    "risk_alert": true,
    "daily_digest": false,
    "anomaly": true
  },
  "risk_threshold": 70.0,
  "secret_key": "optional-secret-for-security"
}
```

**Fields Explained**:

**`name`**: Friendly name (e.g., "Slack Risk Alerts")
- **Why**: Helps you identify this webhook later
- **Example**: "Team Channel - High Risks"

**`webhook_url`**: The URL from Step 1
- **Why**: This is where we send the notification
- **Example**: `https://hooks.slack.com/services/ABC123/XYZ789`

**`webhook_type`**: Type of system (slack, teams, jira, generic)
- **Why**: Different systems need different message formats
- **Options**: `slack`, `teams`, `jira`, `generic`

**`project_id`**: Which project(s) to monitor
- **null**: All projects
- **Specific ID**: Only this project
- **Why**: You might want different webhooks for different projects

**`triggers`**: What events trigger the webhook
- **`risk_alert`**: When high-risk activity detected
- **`daily_digest`**: Daily summary
- **`anomaly`**: When anomalies (zombie tasks, black holes) detected
- **Why**: Control what notifications you get

**`risk_threshold`**: Minimum risk score to trigger
- **70.0**: Only send for risk score >= 70
- **Why**: Avoid notification spam - only important risks

**`secret_key`**: Optional security key
- **Why**: Verifies the webhook came from our system
- **How**: System signs the message with this key

---

### Webhook Types Explained

#### 1. Slack Webhooks

**What You Get**:
- Message in Slack channel
- Color-coded by risk level (red = high, orange = medium, green = low)
- Activity details
- "View Details" button (links to our system)

**Example Message**:
```
🚨 Risk Alert: Implementation Sign-off

Activity: 20: Implementation Sign-off
Risk Score: 78.0/100
Project: 2a13cc29-76f3-4987-a5f6-bf42e29ea138
Explanation: Activity 20 at high risk (score 78): 211-day delay + critical path + low float.

[View Details Button]
```

**How It Helps PMO**:
- **Team Visibility**: Entire team sees alerts in Slack
- **Quick Action**: Click button to view details
- **Integration**: Works with existing Slack workflows

**Real-World Example**:
**Setup**: PMO configures webhook to #project-risks channel
**Trigger**: Activity with risk score 75 detected
**Result**: Alert appears in #project-risks channel
**Team Action**: Team lead sees it, clicks "View Details", takes action

---

#### 2. Microsoft Teams Webhooks

**What You Get**:
- Card in Teams channel
- Color-coded by risk level
- Activity details in structured format
- "View Details" button

**Example Message**:
```
🚨 Risk Alert: Implementation Sign-off

Activity ID: 20
Risk Score: 78.0/100
Project: 2a13cc29-76f3-4987-a5f6-bf42e29ea138
Explanation: Activity 20 at high risk (score 78): 211-day delay + critical path + low float.

[View Details Button]
```

**How It Helps PMO**:
- **Enterprise Integration**: Works with Microsoft ecosystem
- **Team Collaboration**: Teams can discuss in channel
- **Mobile Access**: Get alerts on Teams mobile app

**Real-World Example**:
**Setup**: PMO configures webhook to "Project Management" Teams channel
**Trigger**: High-risk activity detected
**Result**: Card appears in Teams channel
**Team Action**: PMO manager sees it on phone, escalates immediately

---

#### 3. Jira Webhooks

**What You Get**:
- New Jira issue created automatically
- Issue includes:
  - Summary: "Risk Alert: [Activity Name] - Risk Score: X"
  - Description: Full explanation and details
  - Priority: Set based on risk score
  - Labels: "risk-alert", "automated"
  - Link: Back to our system

**Example Issue**:
```
Issue Type: Task
Summary: Risk Alert: Implementation Sign-off - Risk Score: 78.0
Priority: Highest
Labels: risk-alert, automated

Description:
Activity ID: 20
Project: 2a13cc29-76f3-4987-a5f6-bf42e29ea138
Risk Score: 78.0/100

Explanation:
Activity 20 at high risk (score 78): 211-day delay + critical path + low float.

View Details: http://localhost:3000/projects/.../activities/20
```

**How It Helps PMO**:
- **Issue Tracking**: Automatically creates trackable issues
- **Workflow Integration**: Fits into existing Jira workflows
- **Assignment**: Can assign to team members
- **History**: Full audit trail in Jira

**Real-World Example**:
**Setup**: PMO configures webhook to create issues in "RISK" project
**Trigger**: High-risk activity detected
**Result**: Jira issue #RISK-123 created
**Team Action**: Issue assigned to project manager, tracked in sprint

---

#### 4. Generic Webhooks

**What You Get**:
- Custom JSON payload
- You define the format (using `payload_template`)
- Flexible for any system

**Example**:
```json
{
  "event_type": "risk_alert",
  "timestamp": 1234567890,
  "data": {
    "activity_id": "20",
    "activity_name": "Implementation Sign-off",
    "risk_score": 78.0,
    "project_id": "2a13cc29-76f3-4987-a5f6-bf42e29ea138",
    "explanation": "Activity 20 at high risk...",
    "action_url": "http://localhost:3000/..."
  }
}
```

**How It Helps PMO**:
- **Custom Integration**: Works with any system that accepts webhooks
- **Flexible Format**: Define your own message format
- **Enterprise Systems**: Integrate with custom dashboards, BI tools, etc.

**Real-World Example**:
**Setup**: PMO has custom dashboard that accepts webhooks
**Trigger**: High-risk activity detected
**Result**: Custom JSON sent to dashboard
**Dashboard**: Displays alert in custom format

---

### Webhook Triggers

#### 1. Risk Alert Trigger

**When It Fires**:
- High-risk activity detected (risk score >= threshold)
- During risk analysis (when project is analyzed)

**What Gets Sent**:
- Activity ID and name
- Risk score
- Explanation
- Project ID
- Link to view details

**Example**:
```
Activity: "Implementation Sign-off"
Risk Score: 78.0
Threshold: 70.0
→ Webhook Fires! ✅
```

**How It Helps PMO**:
- **Immediate Notification**: Know about risks as soon as they're detected
- **Proactive Management**: Act before problems become crises
- **Team Awareness**: Everyone sees alerts in real-time

---

#### 2. Anomaly Trigger

**When It Fires**:
- Zombie task detected
- Resource black hole detected

**What Gets Sent**:
- Anomaly type (zombie_task, black_hole)
- Activity/resource details
- Days overdue or utilization percentage
- Link to view details

**Example**:
```
Anomaly: Resource Black Hole
Resource: R010
Utilization: 175%
Period: 2026-04-06 to 2026-07-07
→ Webhook Fires! ✅
```

**How It Helps PMO**:
- **Early Warning**: Know about anomalies immediately
- **Resource Management**: Get alerts when resources are overloaded
- **Prevent Delays**: Fix problems before they cause delays

---

#### 3. Daily Digest Trigger

**When It Fires**:
- Once per day (configurable time)
- Summary of all risks across portfolio

**What Gets Sent**:
- Total projects
- High-risk activities count
- New risks today
- Portfolio risk score
- Link to portfolio dashboard

**Example**:
```
Daily Digest - January 15, 2026

Total Projects: 5
High Risk Activities: 12
New Risks Today: 3
Portfolio Risk Score: 45.2%

→ Webhook Fires! ✅
```

**How It Helps PMO**:
- **Portfolio Overview**: See big picture daily
- **Trend Tracking**: See if risks are increasing
- **Leadership Reporting**: Easy summary for executives

---

### Webhook Security

#### Secret Key (Optional)

**What It Is**:
- A password that signs webhook messages
- Proves the message came from our system

**How It Works**:
1. You provide a secret key when creating webhook
2. System signs each message with this key
3. Your system verifies the signature
4. If signature matches, message is authentic

**Why It's Important**:
- **Security**: Prevents fake webhooks
- **Trust**: Know messages are from our system
- **Best Practice**: Always use secret keys in production

**Example**:
```
Secret Key: "my-secret-key-12345"
Message: {...}
Signature: "sha256=abc123def456..."
```

Your system verifies: `signature matches secret key` → ✅ Authentic

---

### Managing Webhooks

#### List All Webhooks

**API Endpoint**: `GET /api/webhooks`

**Response**:
```json
[
  {
    "id": 1,
    "name": "Slack Risk Alerts",
    "webhook_url": "https://hooks.slack.com/...",
    "webhook_type": "slack",
    "project_id": null,
    "triggers": {"risk_alert": true, "anomaly": true},
    "risk_threshold": 70.0,
    "enabled": true,
    "last_triggered": "2026-01-15T10:30:00",
    "failure_count": 0
  }
]
```

**Fields Explained**:

**`enabled`**: Is this webhook active?
- **true**: Webhook is active and will fire
- **false**: Webhook is disabled (won't fire)

**`last_triggered`**: When was it last used?
- **Why**: Know if webhook is working
- **Example**: "2026-01-15T10:30:00" = Last fired today at 10:30 AM

**`failure_count`**: How many times did it fail?
- **0**: Never failed (good!)
- **> 0**: Some failures (check webhook URL)

---

#### Update Webhook

**API Endpoint**: `PUT /api/webhooks/{webhook_id}`

**Use Cases**:
- Change risk threshold
- Update webhook URL
- Enable/disable triggers
- Change project scope

**Example**:
```json
{
  "name": "Slack Risk Alerts",
  "webhook_url": "https://hooks.slack.com/services/NEW/URL",
  "risk_threshold": 80.0,  // Changed from 70.0
  "triggers": {
    "risk_alert": true,
    "anomaly": false  // Disabled anomaly alerts
  }
}
```

---

#### Delete Webhook

**API Endpoint**: `DELETE /api/webhooks/{webhook_id}`

**When to Use**:
- Webhook no longer needed
- Moving to different system
- Cleaning up old configurations

---

#### Test Webhook

**API Endpoint**: `POST /api/webhooks/{webhook_id}/test`

**What It Does**:
- Sends a test message to your webhook
- Verifies the webhook URL works
- Updates `last_triggered` if successful

**Test Message**:
```json
{
  "activity_id": "TEST-001",
  "activity_name": "Test Activity",
  "risk_score": 75.0,
  "explanation": "This is a test webhook from Schedule Risk Monitoring System",
  "project_id": "test-project"
}
```

**How It Helps PMO**:
- **Verify Setup**: Make sure webhook works before relying on it
- **Troubleshooting**: Test if webhook URL is correct
- **Confidence**: Know alerts will be received

---

### Webhook Best Practices for PMO

1. **Start with Test**: Always test webhook before using in production
2. **Set Appropriate Thresholds**: Don't set too low (spam) or too high (miss alerts)
3. **Use Secret Keys**: Always use secret keys for security
4. **Monitor Failure Count**: Check `failure_count` regularly
5. **Project-Specific Webhooks**: Create separate webhooks for critical projects
6. **Team Channels**: Send to team channels, not individual DMs (better visibility)

---

## Notifications Feature {#notifications}

### What Are Notifications?

**Simple Explanation**:
Notifications are emails sent automatically when important things happen in your projects. Like getting a text message when your package is delivered, but for project risks.

**Real-World Analogy**:
Like your phone's notification system:
- **Email Notifications**: Like getting an email alert
- **Threshold**: Like setting "only notify me for important emails"
- **Preferences**: Like choosing which apps can send notifications

---

### Types of Notifications

#### 1. Risk Alert Notifications

**When You Get Them**:
- High-risk activity detected (risk score >= your threshold)
- During project analysis

**What You Get**:
- Email with:
  - Subject: "🚨 High Risk Alert: [Activity Name] (Risk Score: X)"
  - Activity details
  - Risk explanation
  - Recommended mitigations
  - Link to view details

**Example Email**:
```
Subject: 🚨 High Risk Alert: Implementation Sign-off (Risk Score: 78.0)

Body:
Activity 20 (Implementation Sign-off) has a risk score of 78.0/100.

Risk Details:
- Activity ID: 20
- Activity Name: Implementation Sign-off
- Risk Score: 78.0/100
- Explanation: Activity 20 at high risk (score 78): 211-day delay + critical path + low float.

Recommended Actions:
1. Review and update the schedule
2. Monitor closely and have contingency plans
3. Ensure this activity completes on time

[View Details Button] → Links to activity page
```

**How It Helps PMO**:
- **Proactive Alerts**: Know about risks immediately
- **Actionable**: Includes recommendations
- **Easy Access**: Click button to view details
- **Documentation**: Email serves as record

**Real-World Example**:
**Scenario**: PMO is in a meeting, not looking at dashboard
**Trigger**: High-risk activity detected (score 78)
**Result**: Email arrives in PMO's inbox
**Action**: PMO sees email, opens link, takes immediate action
**Benefit**: Risk addressed within minutes, not days

---

#### 2. Daily Digest Notifications

**When You Get Them**:
- Once per day (configurable time)
- Summary of all projects

**What You Get**:
- Email with:
  - Portfolio summary
  - High-risk activities count
  - New risks today
  - Portfolio risk score
  - Link to portfolio dashboard

**Example Email**:
```
Subject: Daily Risk Digest: 12 High-Risk Activities

Body:
Your portfolio summary for January 15, 2026:

- Total Projects: 5
- High Risk Activities: 12
- New Risks Today: 3
- Portfolio Risk Score: 45.2%

Top Risks:
1. Implementation Sign-off (Score: 78.0)
2. System Test Cycle 2 (Score: 75.5)
3. Requirements Gathering (Score: 72.3)

[View Portfolio Dashboard Button]
```

**How It Helps PMO**:
- **Portfolio Overview**: See big picture daily
- **Trend Tracking**: See if risks are increasing
- **Leadership Reporting**: Easy summary for executives
- **Time-Saving**: Don't need to check each project individually

**Real-World Example**:
**Scenario**: PMO manages 10 projects
**Without Digest**: Must check each project dashboard (10 minutes)
**With Digest**: One email shows everything (30 seconds)
**Time Saved**: 9.5 minutes per day = 3.5 hours per month

---

#### 3. Weekly Summary Notifications

**When You Get Them**:
- Once per week (configurable day/time)
- Weekly trends and patterns

**What You Get**:
- Email with:
  - Week-over-week trends
  - Risk score changes
  - Completed mitigations
  - Upcoming milestones

**Example Email**:
```
Subject: Weekly Risk Summary - Week of January 15, 2026

Body:
Weekly Summary:

Projects Analyzed: 5
Total Activities: 250
High-Risk Activities: 12 (down from 15 last week) ✅

Trends:
- Risk Score Improved: 3 projects
- Risk Score Worsened: 1 project
- Risk Score Stable: 1 project

Mitigations Applied: 5
Average Improvement: 2.3 days saved

[View Portfolio Dashboard Button]
```

**How It Helps PMO**:
- **Trend Analysis**: See if things are getting better or worse
- **Performance Tracking**: Measure improvement over time
- **Strategic Planning**: Understand long-term patterns

---

### Notification Preferences

#### Setting Your Preferences

**API Endpoint**: `PUT /api/notifications/preferences`

**Request Body**:
```json
{
  "email_enabled": true,
  "email_risk_alerts": true,
  "email_daily_digest": false,
  "email_weekly_summary": true,
  "risk_alert_threshold": 70.0,
  "risk_digest_threshold": 50.0,
  "digest_frequency": "daily"
}
```

**Fields Explained**:

**`email_enabled`**: Master switch for all emails
- **true**: Receive emails
- **false**: No emails (webhooks still work)

**`email_risk_alerts`**: Get risk alert emails?
- **true**: Yes, send risk alerts
- **false**: No risk alert emails

**`email_daily_digest`**: Get daily digest?
- **true**: Yes, daily summary
- **false**: No daily digest

**`email_weekly_summary`**: Get weekly summary?
- **true**: Yes, weekly summary
- **false**: No weekly summary

**`risk_alert_threshold`**: Minimum risk score for alerts
- **70.0**: Only send for risk score >= 70
- **Why**: Avoid email spam

**`risk_digest_threshold`**: Minimum risk score for digest
- **50.0**: Include activities with risk score >= 50 in digest
- **Why**: Control what appears in summary

**`digest_frequency`**: How often to send digest
- **"daily"**: Every day
- **"weekly"**: Once per week
- **"never"**: Don't send digest

---

#### Project-Specific Preferences

**What It Is**:
- Different notification settings for different projects
- Some projects might need more alerts than others

**Example**:
```json
{
  "project_preferences": {
    "project-123": {
      "enabled": true,
      "threshold": 60.0  // Lower threshold for critical project
    },
    "project-456": {
      "enabled": false  // Disable alerts for this project
    }
  }
}
```

**How It Helps PMO**:
- **Critical Projects**: Lower threshold for important projects
- **Noise Reduction**: Disable alerts for low-priority projects
- **Flexibility**: Different rules for different projects

**Real-World Example**:
**Critical Project**: "Q1 Product Launch"
- Threshold: 60.0 (get alerts earlier)
- Daily Digest: Enabled

**Low-Priority Project**: "Internal Tool Update"
- Threshold: 80.0 (only critical alerts)
- Daily Digest: Disabled

---

### Email Configuration

#### SMTP Settings

**What You Need**:
- SMTP server address (e.g., smtp.gmail.com)
- SMTP port (usually 587 for TLS)
- Username and password
- From email address

**Environment Variables**:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@riskmonitor.com
SMTP_USE_TLS=true
```

**How It Works**:
1. System connects to SMTP server
2. Authenticates with username/password
3. Sends email
4. SMTP server delivers to recipient

**Security Note**:
- Use "App Password" for Gmail (not regular password)
- Use environment variables (never hardcode passwords)
- Use TLS encryption (secure connection)

---

### Testing Notifications

#### Test Email

**API Endpoint**: `POST /api/notifications/test`

**What It Does**:
- Sends a test email to your account
- Verifies SMTP configuration works
- Confirms you'll receive notifications

**Test Email Content**:
```
Subject: Test Notification - Schedule Risk Monitoring

Body:
This is a test notification from Schedule Risk Monitoring System.
If you received this, your email configuration is working correctly.

[Manage Notification Preferences Link]
```

**How It Helps PMO**:
- **Verify Setup**: Make sure emails work before relying on them
- **Troubleshooting**: Test if SMTP settings are correct
- **Confidence**: Know alerts will be received

---

### Notification Best Practices for PMO

1. **Set Appropriate Thresholds**: 
   - Too low (50): Too many emails (spam)
   - Too high (90): Miss important risks
   - Recommended: 70.0 (high-risk only)

2. **Use Daily Digest**: 
   - Get overview without checking dashboard
   - Saves time

3. **Project-Specific Settings**: 
   - Critical projects: Lower threshold
   - Low-priority: Higher threshold or disabled

4. **Test Regularly**: 
   - Test email configuration monthly
   - Verify you're receiving alerts

5. **Mobile Access**: 
   - Check email on phone
   - Get alerts even when away from desk

---

## Portfolio Management Feature {#portfolio}

### What Is Portfolio Management?

**Simple Explanation**:
Portfolio Management lets you see ALL your projects in one place. Instead of checking each project individually, you get a bird's-eye view of everything.

**Real-World Analogy**:
Like a stock portfolio dashboard:
- **Individual Stocks**: Like individual projects
- **Portfolio View**: See all stocks together
- **Portfolio Risk**: Overall risk across all stocks
- **Top Performers/Worst Performers**: Which projects are doing well/poorly

---

### Portfolio Features

#### 1. Portfolio Summary

**What You Get**:
- Total number of projects
- Total number of activities
- Portfolio risk score (aggregated)
- Projects at risk count
- Resource allocation summary

**API Endpoint**: `GET /api/portfolio/summary`

**Response Example**:
```json
{
  "total_projects": 5,
  "total_activities": 250,
  "portfolio_risk_score": 45.2,
  "high_risk_projects": 2,
  "high_risk_activities": 12,
  "projects_at_risk": [
    {
      "project_id": "project-123",
      "project_name": "Q1 Product Launch",
      "risk_score": 65.5,
      "high_risk_activities": 5
    }
  ],
  "resource_summary": {
    "total_resources": 15,
    "overloaded_resources": 3,
    "utilization_rate": 0.85
  }
}
```

**How It Helps PMO**:
- **Quick Overview**: See portfolio health at a glance
- **Identify Problems**: Spot high-risk projects immediately
- **Resource Planning**: See resource allocation across all projects
- **Leadership Reporting**: Easy summary for executives

**Real-World Example**:
**PMO Dashboard Shows**:
- 5 projects total
- 2 projects at high risk
- 12 high-risk activities across portfolio
- 3 resources overloaded

**PMO Action**: Focus on the 2 high-risk projects first, then address resource overload

---

#### 2. Portfolio Risks

**What You Get**:
- Top risks across ALL projects
- Ranked by risk score
- Shows which project each risk belongs to

**API Endpoint**: `GET /api/portfolio/risks?limit=20`

**Response Example**:
```json
{
  "total_risks": 50,
  "top_risks": [
    {
      "project_id": "project-123",
      "project_name": "Q1 Product Launch",
      "activity_id": "20",
      "activity_name": "Implementation Sign-off",
      "risk_score": 78.0,
      "risk_level": "high"
    },
    {
      "project_id": "project-456",
      "activity_id": "15",
      "activity_name": "System Test Cycle 2",
      "risk_score": 75.5,
      "risk_level": "high"
    }
  ]
}
```

**How It Helps PMO**:
- **Cross-Project Prioritization**: See which risks matter most across all projects
- **Resource Allocation**: Allocate resources to highest-risk items first
- **Strategic Planning**: Understand portfolio-wide risk patterns

**Real-World Example**:
**Top Portfolio Risks**:
1. Project A, Activity 20: Risk 78.0
2. Project B, Activity 15: Risk 75.5
3. Project A, Activity 25: Risk 72.3

**PMO Action**: Focus on Project A first (2 of top 3 risks), then Project B

---

#### 3. Cross-Project Dependencies

**What You Get**:
- Dependencies between projects
- Which projects depend on others
- Potential cascading delays

**API Endpoint**: `GET /api/portfolio/dependencies`

**Response Example**:
```json
{
  "cross_project_dependencies": [
    {
      "source_project": "project-123",
      "target_project": "project-456",
      "dependency_type": "finish-to-start",
      "risk_level": "medium"
    }
  ]
}
```

**How It Helps PMO**:
- **Cascade Prevention**: See if Project A delay will affect Project B
- **Coordination**: Coordinate between project teams
- **Risk Amplification**: Understand how risks spread across projects

**Real-World Example**:
**Dependency**: Project A (Infrastructure) must finish before Project B (Application) can start
**Risk**: If Project A is delayed, Project B is automatically delayed
**PMO Action**: Monitor Project A closely, have contingency plan for Project B

---

#### 4. Portfolio Resource Allocation

**What You Get**:
- Resource usage across all projects
- Overloaded resources (used in multiple projects)
- Resource conflicts

**API Endpoint**: `GET /api/portfolio/resources`

**Response Example**:
```json
{
  "total_resources": 15,
  "overloaded_resources": [
    {
      "resource_id": "R010",
      "utilization": 1.75,
      "projects": ["project-123", "project-456"],
      "conflict_period": "2026-04-06 to 2026-07-07"
    }
  ],
  "resource_allocation": {
    "by_project": {...},
    "by_resource": {...}
  }
}
```

**How It Helps PMO**:
- **Resource Planning**: See who's working on what
- **Conflict Detection**: Find resources assigned to multiple projects simultaneously
- **Capacity Management**: Understand overall resource capacity

**Real-World Example**:
**Resource R010** (Senior Developer):
- Assigned to Project A: 1.0 FTE
- Assigned to Project B: 0.75 FTE
- **Total**: 1.75 FTE (impossible!)
- **Conflict Period**: April 6 - July 7

**PMO Action**: Reassign R010 or adjust project timelines

---

### Portfolio Dashboard (UI)

**What You See**:
- Portfolio summary cards (total projects, risks, etc.)
- Top risks table (across all projects)
- Resource allocation chart
- Project health indicators

**How It Helps PMO**:
- **Visual Overview**: See everything at a glance
- **Quick Navigation**: Click to drill down into specific projects
- **Trend Analysis**: See if portfolio health is improving or worsening

---

## Feedback System Feature {#feedback}

### What Is the Feedback System?

**Simple Explanation**:
The feedback system lets you tell the system what's helpful and what's not. Like rating a restaurant or leaving a review, but for risk explanations, forecasts, and mitigations.

**Real-World Analogy**:
Like Amazon reviews:
- **Rating**: 1-5 stars
- **Feedback Text**: Written comments
- **Helpful/Not Helpful**: Thumbs up/down

---

### Types of Feedback

#### 1. Explanation Feedback

**When to Use**:
- After viewing a risk explanation
- If explanation was helpful or confusing

**What You Can Provide**:
- **Was Helpful**: Yes/No
- **Rating**: 1-5 stars
- **Feedback Text**: Written comments

**Example**:
```
Activity: Implementation Sign-off
Explanation: "Activity 20 at high risk (score 78): 211-day delay + critical path + low float."

Feedback:
- Was Helpful: Yes
- Rating: 5 stars
- Feedback Text: "Very clear explanation. The 211-day delay number was especially helpful."
```

**How It Helps PMO**:
- **System Improvement**: Helps system learn what explanations are helpful
- **Quality Assurance**: Identifies confusing explanations
- **User Experience**: Improves explanations over time

---

#### 2. Forecast Feedback

**When to Use**:
- After viewing forecasts (P50, P80, etc.)
- If forecast was accurate or not

**What You Can Provide**:
- **Was Accurate**: Yes/No
- **Rating**: 1-5 stars
- **Feedback Text**: Written comments

**Example**:
```
Forecast: P80 = 21 days
Actual Completion: 22 days

Feedback:
- Was Accurate: Yes (close enough)
- Rating: 4 stars
- Feedback Text: "Forecast was very close. P80 of 21 days, actual was 22 days. Good prediction!"
```

**How It Helps PMO**:
- **Forecast Accuracy**: System learns to improve predictions
- **Calibration**: Adjusts forecasts based on feedback
- **Trust Building**: Better forecasts = more trust in system

---

#### 3. Mitigation Feedback

**When to Use**:
- After applying a mitigation
- If mitigation worked as expected

**What You Can Provide**:
- **Was Effective**: Yes/No
- **Rating**: 1-5 stars
- **Feedback Text**: Written comments

**Example**:
```
Mitigation: Reduce duration by 10%
Predicted Improvement: 2 days saved
Actual Improvement: 1.5 days saved

Feedback:
- Was Effective: Yes
- Rating: 4 stars
- Feedback Text: "Mitigation worked, though improvement was slightly less than predicted. Still worth it."
```

**How It Helps PMO**:
- **Mitigation Accuracy**: System learns which mitigations work best
- **Recommendation Quality**: Improves future recommendations
- **ROI Understanding**: Better cost-benefit predictions

---

#### 4. General Feedback

**When to Use**:
- General comments about the system
- Feature requests
- Bug reports

**What You Can Provide**:
- **Feedback Type**: "general"
- **Rating**: 1-5 stars
- **Feedback Text**: Written comments

**Example**:
```
Feedback Type: General
Rating: 5 stars
Feedback Text: "Love the webhook integration! Would be great to add Discord support too."
```

**How It Helps PMO**:
- **Feature Requests**: Tell developers what features you want
- **Bug Reports**: Report problems
- **System Evolution**: Shape the system's future

---

### How to Submit Feedback

#### Via UI

**Where to Find It**:
- **Feedback Button**: Usually in bottom-right corner of pages
- **After Explanations**: "Was this helpful?" buttons
- **After Simulations**: "Rate this simulation" option

**Steps**:
1. Click "Feedback" button
2. Select feedback type
3. Rate (1-5 stars)
4. Write comments (optional)
5. Submit

---

#### Via API

**API Endpoint**: `POST /api/feedback`

**Request Body**:
```json
{
  "feedback_type": "explanation",
  "context_id": "20",
  "was_helpful": true,
  "rating": 5,
  "feedback_text": "Very clear explanation!",
  "page_url": "/projects/.../activities/20"
}
```

**Fields Explained**:

**`feedback_type`**: Type of feedback
- **Options**: `explanation`, `forecast`, `mitigation`, `general`

**`context_id`**: What this feedback is about
- **For explanations**: Activity ID
- **For forecasts**: Project ID
- **For mitigations**: Activity ID

**`was_helpful`**: Was it helpful?
- **true**: Yes, helpful
- **false**: No, not helpful

**`rating`**: 1-5 star rating
- **1**: Poor
- **5**: Excellent

**`feedback_text`**: Written comments
- **Optional**: But very helpful!

**`page_url`**: Where you were when giving feedback
- **Why**: Helps developers understand context

---

### How Feedback Helps Improve the System

**1. Machine Learning**:
- System learns which explanations are helpful
- Improves forecast accuracy based on feedback
- Better mitigation recommendations over time

**2. Quality Assurance**:
- Identifies confusing explanations
- Finds inaccurate forecasts
- Discovers ineffective mitigations

**3. Feature Development**:
- User requests shape new features
- Bug reports help fix issues
- Ratings show what's working

**Real-World Example**:
**Month 1**: Users rate explanations 3.5/5 stars
**Feedback**: "Explanations are too technical"
**System Update**: Explanations simplified, more plain language
**Month 3**: Users rate explanations 4.5/5 stars ✅

---

## Onboarding Feature {#onboarding}

### What Is Onboarding?

**Simple Explanation**:
Onboarding is like a guided tour of the system. When you first use the system, it shows you around and explains how everything works.

**Real-World Analogy**:
Like a video game tutorial:
- **First Level**: Shows you the basics
- **Tooltips**: Explains what each button does
- **Guided Steps**: Walks you through key features

---

### Onboarding Features

#### 1. Interactive Tour

**What It Is**:
- Step-by-step walkthrough of the system
- Highlights important features
- Explains how to use them

**Steps**:
1. **Welcome**: Introduction to the system
2. **Upload Project**: How to upload your first project
3. **View Dashboard**: Understanding the dashboard
4. **Check Risks**: How to view and understand risks
5. **Run Simulation**: How to use What-If Simulator
6. **Set Notifications**: How to configure alerts

**How It Helps PMO**:
- **Quick Learning**: Learn the system in 5-10 minutes
- **No Training Needed**: Self-service onboarding
- **Reduced Support**: Fewer questions to support team

---

#### 2. Tooltips and Help Text

**What It Is**:
- Small popup explanations when you hover over elements
- "?" icons that explain features
- Contextual help throughout the system

**Example**:
```
Hover over "P80 Forecast":
Tooltip: "P80 means there's an 80% chance your project will finish in this many days or less. This is a conservative, reliable estimate for planning."
```

**How It Helps PMO**:
- **Just-in-Time Learning**: Learn as you use
- **No Manual Reading**: Help appears when needed
- **Reduced Confusion**: Clear explanations for technical terms

---

#### 3. Progress Tracking

**What It Is**:
- Tracks which onboarding steps you've completed
- Shows your progress
- Suggests next steps

**Example**:
```
Onboarding Progress:
✅ Welcome
✅ Upload Project
✅ View Dashboard
⏳ Check Risks (Next Step)
⏳ Run Simulation
⏳ Set Notifications
```

**How It Helps PMO**:
- **Clear Path**: Know what to do next
- **Completion Tracking**: See what you've learned
- **No Overwhelm**: One step at a time

---

### Onboarding API

**API Endpoint**: `GET /api/onboarding/status`

**Response**:
```json
{
  "completed": true,
  "steps_completed": 6,
  "total_steps": 6,
  "last_completed": "2026-01-15T10:00:00"
}
```

**How It Helps**:
- **Resume Onboarding**: Continue where you left off
- **Skip Completed**: Don't show steps you've already done
- **Analytics**: Track onboarding completion rates

---

## Audit Log Feature {#audit-log}

### What Is the Audit Log?

**Simple Explanation**:
The Audit Log is like a security camera recording of everything that happens in your project. It shows who did what, when, and what changed.

**Real-World Analogy**:
Like a bank statement:
- **Every Transaction**: Recorded with date, time, amount
- **Who Made It**: Account holder
- **What Happened**: Deposit, withdrawal, etc.

---

### What Gets Logged

#### 1. Project Events

**Examples**:
- Project uploaded
- Project analyzed
- Project deleted
- Project updated

**Log Entry Example**:
```json
{
  "timestamp": "2026-01-15T10:30:00",
  "event": "project_uploaded",
  "user_id": 1,
  "details": {
    "project_id": "2a13cc29-76f3-4987-a5f6-bf42e29ea138",
    "activity_count": 50,
    "file_name": "project_plan.csv"
  }
}
```

---

#### 2. Risk Analysis Events

**Examples**:
- Risk scan performed
- Forecast generated
- Anomalies detected

**Log Entry Example**:
```json
{
  "timestamp": "2026-01-15T10:35:00",
  "event": "risk_scan",
  "user_id": 1,
  "details": {
    "project_id": "2a13cc29-76f3-4987-a5f6-bf42e29ea138",
    "risk_count": 50,
    "top_risk_score": 78.0
  }
}
```

---

#### 3. Simulation Events

**Examples**:
- Simulation run
- Mitigation applied
- Mitigation options generated

**Log Entry Example**:
```json
{
  "timestamp": "2026-01-15T10:40:00",
  "event": "simulation",
  "user_id": 1,
  "details": {
    "project_id": "2a13cc29-76f3-4987-a5f6-bf42e29ea138",
    "activity_id": "20",
    "mitigation_type": "duration_reduction",
    "improvement": {
      "p50_improvement": 1.0,
      "p80_improvement": 1.0
    }
  }
}
```

---

#### 4. Configuration Changes

**Examples**:
- Notification preferences changed
- Webhook added/updated/deleted
- User settings changed

**Log Entry Example**:
```json
{
  "timestamp": "2026-01-15T11:00:00",
  "event": "webhook_created",
  "user_id": 1,
  "details": {
    "webhook_id": 1,
    "webhook_name": "Slack Risk Alerts",
    "webhook_type": "slack"
  }
}
```

---

### Viewing Audit Log

#### Via UI

**Where to Find It**:
- Project page → "Audit Log" tab
- Shows all events for that project

**What You See**:
- List of events (newest first)
- Event type, timestamp, user
- Expandable details

**Example**:
```
📅 January 15, 2026, 10:40 AM
🔄 Simulation
User: john@company.com
Activity: Implementation Sign-off (20)
Mitigation: Duration Reduction
Improvement: 1.0 days (P80)
[View Details]
```

---

#### Via API

**API Endpoint**: `GET /api/projects/{project_id}/audit`

**Response**:
```json
{
  "total_events": 25,
  "events": [
    {
      "id": 1,
      "timestamp": "2026-01-15T10:40:00",
      "event": "simulation",
      "user_id": 1,
      "user_email": "john@company.com",
      "details": {...}
    }
  ]
}
```

---

### Why Audit Log Is Important

**1. Compliance**:
- **Requirement**: Many organizations require audit trails
- **Benefit**: Complete record of all actions
- **Use Case**: Regulatory compliance, security audits

**2. Troubleshooting**:
- **Problem**: Something went wrong, need to understand what happened
- **Solution**: Check audit log to see what changed
- **Use Case**: "Why did the forecast change?" → Check audit log

**3. Accountability**:
- **Problem**: Need to know who made changes
- **Solution**: Audit log shows user for each event
- **Use Case**: "Who deleted this project?" → Check audit log

**4. History**:
- **Problem**: Need to see how project evolved
- **Solution**: Audit log shows complete history
- **Use Case**: "When was this risk first detected?" → Check audit log

**Real-World Example**:
**Scenario**: Project forecast changed unexpectedly
**PMO Action**: Check audit log
**Found**: "Simulation run at 10:40 AM by user@company.com, mitigation applied"
**Result**: Understand why forecast changed, verify it was intentional

---

## Re-Analyze Feature {#re-analyze}

### What Is Re-Analyze?

**Simple Explanation**:
Re-Analyze tells the system to recalculate everything from scratch. Like refreshing a webpage, but for your entire project analysis.

**Real-World Analogy**:
Like recalculating a spreadsheet:
- **Original**: Formulas calculate based on old data
- **Re-Analyze**: Recalculates with new data
- **Result**: Updated numbers

---

### When to Use Re-Analyze

#### 1. After Updating Project Data

**Scenario**:
- You updated task durations in your project plan
- You want to see new forecasts

**Action**:
- Click "Re-Analyze" button
- System recalculates risks, forecasts, anomalies

**Result**:
- Updated risk scores
- New forecasts (P50, P80, etc.)
- Updated anomaly detection

---

#### 2. After Time Passes

**Scenario**:
- Last analysis was 1 week ago
- Some tasks have progressed
- You want current status

**Action**:
- Click "Re-Analyze"
- System uses current date for calculations

**Result**:
- Updated progress percentages
- New zombie task detection (tasks that should have started)
- Updated forecasts based on current state

---

#### 3. After Applying Mitigations

**Scenario**:
- You applied a mitigation (reduced duration, added resources)
- You want to see the new risk scores

**Action**:
- Click "Re-Analyze"
- System analyzes with new data

**Result**:
- Updated risk scores (should be lower)
- New forecasts (should be better)
- Updated recommendations

---

### How Re-Analyze Works

#### Step 1: Clear Cache

**What Happens**:
- System clears cached results
- Forces fresh calculation

**Why**:
- Ensures you get latest data
- Not using stale cached results

---

#### Step 2: Reload Data

**What Happens**:
- System loads latest project data from database
- Gets current activity statuses
- Gets current dates

**Why**:
- Uses most up-to-date information
- Accounts for any changes made

---

#### Step 3: Rebuild Digital Twin

**What Happens**:
- System rebuilds the project graph
- Recalculates dependencies
- Updates topology metrics

**Why**:
- Graph structure might have changed
- Dependencies might have been updated

---

#### Step 4: Re-run Analysis

**What Happens**:
- Forensic intelligence extraction
- Risk analysis
- Anomaly detection
- Forecasting

**Why**:
- Everything needs to be recalculated
- New data = new results

---

#### Step 5: Update Cache

**What Happens**:
- New results are cached
- Ready for fast retrieval

**Why**:
- Future requests are fast
- But you have fresh data

---

### Re-Analyze vs. Refresh

**Re-Analyze**:
- **What**: Recalculates everything from scratch
- **When**: After data changes, time passes, or applying mitigations
- **Time**: 1-3 seconds (full recalculation)

**Refresh**:
- **What**: Just reloads current data (no recalculation)
- **When**: To see if new data arrived
- **Time**: < 1 second (just data fetch)

**Simple Analogy**:
- **Re-Analyze**: Like recalculating a spreadsheet
- **Refresh**: Like refreshing a webpage

---

### Re-Analyze API

**API Endpoint**: `POST /api/projects/{project_id}/reanalyze`

**What It Does**:
- Clears cache
- Recalculates all metrics
- Returns updated results

**Response**:
```json
{
  "status": "success",
  "message": "Project re-analyzed successfully",
  "timestamp": "2026-01-15T10:45:00"
}
```

---

### Best Practices for PMO

1. **Re-Analyze After Changes**: Always re-analyze after updating project data
2. **Regular Re-Analysis**: Re-analyze weekly or after significant progress
3. **Before Important Decisions**: Re-analyze before making major decisions
4. **After Mitigations**: Re-analyze after applying mitigations to see impact

---

## Forensic Intelligence Feature {#forensic-intelligence}

### What Is Forensic Intelligence?

**Simple Explanation**:
Forensic Intelligence is like a detective investigating your project. It looks for hidden clues and patterns that regular analysis might miss. It uses AI and historical data to predict problems before they happen.

**Real-World Analogy**:
Like a forensic scientist at a crime scene:
- **Regular Analysis**: "There's a delay" (obvious)
- **Forensic Intelligence**: "Based on historical patterns, this delay will likely cause 3 more delays downstream" (insightful)

---

### Forensic Intelligence Components

#### 1. Drift Velocity Engine

**What It Does**:
- Compares current plan to original baseline
- Calculates how much plans have "drifted"
- Predicts future delays based on historical drift

**Example**:
```
Baseline: 10 days
Current Plan: 15 days
Drift: 50% (plans have increased by 50%)

Prediction: Future tasks will likely also drift 50%
```

**How It Helps PMO**:
- **Early Warning**: Know plans are drifting before it's too late
- **Realistic Forecasts**: Adjust forecasts based on drift patterns
- **Pattern Recognition**: Identify projects that consistently drift

**Real-World Example**:
**Activity**: "Requirements Gathering"
**Baseline**: 5 days
**Current Plan**: 8 days
**Drift**: 60%

**Forensic Intelligence**: "This activity has 60% historical drift. Similar activities in past projects also drifted 60%. Forecast: This will likely take 8 days, not 5 days."

---

#### 2. Skill Constraint Analyzer

**What It Does**:
- Analyzes resource skills across all activities
- Detects when skills are overbooked
- Identifies skill bottlenecks

**Example**:
```
Skill: "Python Developer"
Demand: 1.5 FTE (3 tasks need Python work)
Supply: 1.0 FTE (only 1 Python developer available)
Bottleneck: 150% overbooked
```

**How It Helps PMO**:
- **Resource Planning**: Know when to hire more people
- **Conflict Detection**: Find skill conflicts before they cause delays
- **Capacity Management**: Understand skill capacity across portfolio

**Real-World Example**:
**Skill**: "UI/UX Designer"
**Analysis**: 3 projects need UI/UX work simultaneously
**Bottleneck Detected**: Only 1 designer available
**Forensic Intelligence**: "UI/UX skill bottleneck detected. Tasks will likely be delayed by 2-3 weeks. Recommendation: Hire temporary designer or reschedule tasks."

---

#### 3. Cost Performance Index (CPI) Engine

**What It Does**:
- Compares planned cost to actual cost
- Calculates Cost Performance Index
- Predicts schedule problems from cost overruns

**Example**:
```
Planned Cost: $10,000
Actual Cost (so far): $12,000
CPI: 0.83 (spending more than planned)

Prediction: Cost overruns often precede schedule delays
```

**How It Helps PMO**:
- **Early Warning**: Cost problems often predict schedule problems
- **Budget Management**: Track cost performance
- **Risk Prediction**: Use CPI to predict delays

**Real-World Example**:
**Activity**: "Development Phase"
**CPI**: 0.85 (15% over budget)
**Forensic Intelligence**: "CPI of 0.85 indicates cost overrun. Historical data shows 80% of activities with CPI < 0.9 experience schedule delays. Forecast: This activity will likely be delayed by 10-15%."

---

#### 4. Topology Engine

**What It Does**:
- Analyzes project structure (how tasks connect)
- Identifies "bridge" activities (critical connection points)
- Calculates centrality metrics

**Example**:
```
Activity 11: Centrality = 0.251
Meaning: Activity 11 is on critical path 25% of the time

If Activity 11 is delayed → 25% chance of delaying entire project
```

**How It Helps PMO**:
- **Focus Areas**: Know which activities are most critical
- **Risk Amplification**: Understand which delays have biggest impact
- **Strategic Planning**: Focus resources on bridge activities

**Real-World Example**:
**Activity**: "Database Setup"
**Centrality**: 0.85 (very high)
**Forensic Intelligence**: "Database Setup is a critical bridge activity. 85% of simulations show it's on the critical path. Any delay here will likely delay the entire project. Recommendation: Add buffer time and extra resources."

---

#### 5. ML Risk Clustering

**What It Does**:
- Uses Machine Learning to find risk patterns
- Groups activities into risk clusters
- Predicts which activities are likely to have problems

**Example**:
```
Cluster 0: Low Risk (Stable Zone)
- Activities: 30
- Failure Probability: 5%

Cluster 1: Medium Risk (Watch Zone)
- Activities: 15
- Failure Probability: 15%

Cluster 2: High Risk (Burnout Zone)
- Activities: 5
- Failure Probability: 30%

Cluster 3: Very High Risk (Failure Zone)
- Activities: 0
- Failure Probability: 50%
```

**How It Helps PMO**:
- **Pattern Recognition**: AI finds patterns humans might miss
- **Predictive**: Identifies risks before they become problems
- **Prioritization**: Focus on high-risk clusters first

**Real-World Example**:
**Pattern Detected**: "Activities with 200+ day delays, 0 float, and resource overloads have 85% failure rate"
**Your Project**: 3 activities match this pattern
**Forensic Intelligence**: "High-Risk Cluster detected: 3 activities match failure pattern. Immediate action required."

---

### Forensic Intelligence in Forecasts

#### Standard vs. Forensic Forecast

**Standard Forecast**:
- Uses basic project data
- Simple risk calculations
- Like: "Based on your plan: 18 days"

**Forensic Forecast**:
- Uses forensic intelligence
- Accounts for drift, skills, topology, clusters
- Like: "Based on your plan PLUS all hidden factors: 21 days"

**Example**:
```
Standard Forecast:
P50: 18 days
P80: 21 days

Forensic Forecast:
P50: 18 days (same)
P80: 21 days (same)
P90: 22 days (new - shows worst case)
P95: 23 days (new - shows extreme worst case)

Why Different?
- Accounts for 50% historical drift
- Accounts for skill bottlenecks
- Accounts for high-risk clusters
- More realistic, conservative forecast
```

**How It Helps PMO**:
- **More Accurate**: Forensic considers real-world factors
- **Better Planning**: P90/P95 help plan for worst case
- **Risk Awareness**: Understand full range of possibilities

---

### Enabling Forensic Intelligence

#### Via UI

**Where to Find It**:
- Project Dashboard
- "Forecast Mode" toggle
- Select "Forensic" (instead of "Standard")

**What Happens**:
- System uses forensic intelligence for forecasts
- Shows additional metrics (P90, P95)
- Displays forensic insights

---

#### Via API

**API Endpoint**: `GET /api/projects/{project_id}/forecast/forensic`

**What It Does**:
- Runs forecast with forensic intelligence
- Returns enhanced forecasts
- Includes forensic metrics

**Response**:
```json
{
  "p50": 18,
  "p80": 21,
  "p90": 22,
  "p95": 23,
  "forensic_modulation_applied": true,
  "forensic_insights": {
    "drift_activities": 5,
    "skill_bottlenecks": 2,
    "bridge_nodes": 3,
    "high_risk_clusters": 12
  }
}
```

---

### Forensic Intelligence Best Practices for PMO

1. **Use for Critical Projects**: Enable forensic mode for important projects
2. **Review Insights**: Check forensic insights (drift, bottlenecks, clusters)
3. **Plan for P95**: Use P95 for worst-case planning
4. **Act on Insights**: Don't just view - take action on forensic findings

---

## Mitigation Ranking Feature {#mitigation-ranking}

### What Is Mitigation Ranking?

**Simple Explanation**:
When the system recommends ways to fix a problem, it ranks them from best to worst. Like a "Top 10" list, but for solutions to your project problems.

**Real-World Analogy**:
Like restaurant reviews sorted by rating:
- **#1 Restaurant**: Best rating (4.8 stars)
- **#2 Restaurant**: Second best (4.6 stars)
- **#3 Restaurant**: Third best (4.4 stars)

But for mitigations:
- **#1 Mitigation**: Best improvement vs. cost
- **#2 Mitigation**: Second best
- **#3 Mitigation**: Third best

---

### How Mitigation Ranking Works

#### Step 1: Generate Candidate Mitigations

**What the System Does**:
- Analyzes the risky activity
- Generates multiple mitigation options:
  - Reduce duration by 10%, 20%, 30%
  - Add 0.5, 1.0, 1.5 FTE
  - Reduce risk by 25%, 50%, 75%

**Example**:
```
Activity: Implementation Sign-off (10 days, high risk)

Generated Options:
1. Reduce duration by 10% (9 days)
2. Reduce duration by 20% (8 days)
3. Reduce duration by 30% (7 days)
4. Add 0.5 FTE
5. Add 1.0 FTE
6. Reduce risk by 50%
... (and more)
```

---

#### Step 2: Simulate Each Option

**What the System Does**:
- For each option, runs a simulation
- Calculates improvement (days saved)
- Calculates cost impact
- Calculates FTE impact

**Example**:
```
Option 1: Reduce by 10%
- P80 Improvement: 1.0 days
- Cost Impact: 105% (+5%)
- FTE Days: 0.0

Option 2: Reduce by 20%
- P80 Improvement: 2.0 days
- Cost Impact: 110% (+10%)
- FTE Days: 0.0

Option 3: Add 1.0 FTE
- P80 Improvement: 1.5 days
- Cost Impact: 108% (+8%)
- FTE Days: 10.0
```

---

#### Step 3: Calculate Utility Score

**What the System Does**:
- Calculates a "utility score" for each option
- Formula: `Utility = Improvement - Cost Penalty - FTE Penalty`
- Higher utility = better option

**Example Calculation**:
```
Option 1:
- Improvement: 1.0 days
- Cost Penalty: 0.05 (5% increase)
- FTE Penalty: 0.0
- Utility: 1.0 - (0.05 * 10) - 0.0 = 0.5

Option 2:
- Improvement: 2.0 days
- Cost Penalty: 0.10 (10% increase)
- FTE Penalty: 0.0
- Utility: 2.0 - (0.10 * 10) - 0.0 = 1.0

Option 3:
- Improvement: 1.5 days
- Cost Penalty: 0.08 (8% increase)
- FTE Penalty: 1.0 (10 FTE days)
- Utility: 1.5 - (0.08 * 10) - 1.0 = -0.3
```

**Ranking**:
1. Option 2 (Utility: 1.0) - Best!
2. Option 1 (Utility: 0.5)
3. Option 3 (Utility: -0.3) - Worst (negative utility!)

---

#### Step 4: Return Ranked List

**What You Get**:
- List of options, ranked by utility score
- Best option first (#1)
- Each option shows:
  - Description
  - P50/P80 Improvement
  - Cost Impact
  - FTE Days
  - Utility Score

**Example Response**:
```json
{
  "activity_id": "20",
  "total_options": 6,
  "ranked_mitigations": [
    {
      "rank": 1,
      "type": "reduce_duration",
      "description": "Reduce duration by 20% (crashing)",
      "utility_score": 1.0,
      "improvement": {
        "p50_improvement": 2.0,
        "p80_improvement": 2.0
      },
      "estimated_cost_multiplier": 1.10,
      "estimated_ftedays": 0.0
    },
    {
      "rank": 2,
      "type": "reduce_duration",
      "description": "Reduce duration by 10% (crashing)",
      "utility_score": 0.5,
      "improvement": {
        "p50_improvement": 1.0,
        "p80_improvement": 1.0
      },
      "estimated_cost_multiplier": 1.05,
      "estimated_ftedays": 0.0
    }
  ]
}
```

---

### Why Ranking Is Important

**1. Saves Time**:
- **Without Ranking**: PMO must test all options manually
- **With Ranking**: Best options shown first
- **Time Saved**: 10-15 minutes per activity

**2. Better Decisions**:
- **Without Ranking**: Might choose suboptimal option
- **With Ranking**: Best option is clear
- **Benefit**: Better outcomes

**3. Clear Communication**:
- **Without Ranking**: Hard to explain why one option is better
- **With Ranking**: "Option #1 has highest utility score"
- **Benefit**: Easy to justify decisions

**Real-World Example**:
**Scenario**: Activity at high risk, need to fix it
**Without Ranking**: PMO tests 6 options manually (30 minutes)
**With Ranking**: System shows top 3 options, PMO tests those (5 minutes)
**Time Saved**: 25 minutes
**Better Decision**: Focus on best options, not waste time on poor options

---

### Understanding Utility Score

**What It Means**:
- **Positive Score**: Good option (benefits outweigh costs)
- **Negative Score**: Poor option (costs outweigh benefits)
- **Higher Score**: Better option

**Factors**:
- **Improvement**: How many days saved (higher = better)
- **Cost Penalty**: How much cost increases (lower = better)
- **FTE Penalty**: How many FTE days needed (lower = better)

**Example**:
```
Option A: Utility = 2.0
- Saves 2 days
- Costs 5% more
- No FTE needed
→ Excellent option!

Option B: Utility = -0.5
- Saves 0.5 days
- Costs 15% more
- Needs 5 FTE days
→ Poor option (costs more than benefits)
```

---

### Mitigation Ranking API

**API Endpoint**: `GET /api/projects/{project_id}/mitigations/{activity_id}`

**Response**: See example above

**How It Helps**:
- **Programmatic Access**: Other systems can get ranked options
- **Integration**: Integrate with other tools
- **Automation**: Automatically apply top-ranked option

---

## How All Features Work Together {#features-together}

### Complete Workflow Example

**Scenario**: PMO manages a project with a high-risk activity

#### Step 1: Risk Detection
- **System**: Analyzes project, detects high-risk activity (score 78)
- **Feature**: Risk Analysis Pipeline
- **Result**: Activity flagged as high risk

#### Step 2: Early Warning
- **System**: Sends email notification
- **Feature**: Notifications
- **Result**: PMO receives email alert

#### Step 3: Webhook Integration
- **System**: Sends webhook to Slack
- **Feature**: Webhooks
- **Result**: Alert appears in Slack channel

#### Step 4: View Details
- **PMO**: Opens activity details page
- **Feature**: Activity Details, Risk Explanation
- **Result**: Sees explanation and recommendations

#### Step 5: Get Mitigation Options
- **PMO**: Views "Recommended Mitigation Options"
- **Feature**: Mitigation Ranking
- **Result**: Sees top 6 ranked options

#### Step 6: Test Options
- **PMO**: Clicks "Use This Option →" for Option #1
- **Feature**: Use This Option
- **Result**: Simulator pre-filled with Option #1 parameters

#### Step 7: Run Simulation
- **PMO**: Clicks "Run Simulation"
- **Feature**: What-If Simulation
- **Result**: Sees improvement: 2 days saved, 5% cost increase

#### Step 8: Apply Mitigation
- **PMO**: Decides Option #1 is good, applies it
- **Feature**: Mitigation Application
- **Result**: Project updated with new duration

#### Step 9: Re-Analyze
- **PMO**: Clicks "Re-Analyze"
- **Feature**: Re-Analyze
- **Result**: New risk score (lower), new forecasts (better)

#### Step 10: Track Changes
- **System**: Logs all actions in audit log
- **Feature**: Audit Log
- **Result**: Complete history of what happened

#### Step 11: Portfolio View
- **PMO**: Checks portfolio dashboard
- **Feature**: Portfolio Management
- **Result**: Sees how this project affects overall portfolio

#### Step 12: Provide Feedback
- **PMO**: Rates the mitigation recommendation
- **Feature**: Feedback System
- **Result**: System learns, improves future recommendations

---

### Feature Integration Matrix

| Feature | Integrates With | How |
|---------|----------------|-----|
| **Notifications** | Risk Analysis | Sends alerts when risks detected |
| **Webhooks** | Risk Analysis | Triggers webhooks for high risks |
| **What-If Simulation** | Mitigation Ranking | Tests ranked options |
| **Use This Option** | What-If Simulation | Pre-fills simulator |
| **Re-Analyze** | All Features | Recalculates after changes |
| **Audit Log** | All Features | Records all actions |
| **Portfolio** | All Projects | Aggregates data from all projects |
| **Feedback** | Explanations, Forecasts, Mitigations | Collects user input |

---

## Feature Comparison Table

| Feature | Purpose | When to Use | Time to Set Up |
|---------|---------|-------------|----------------|
| **What-If Simulation** | Test scenarios | Before making changes | Instant (no setup) |
| **Use This Option** | Quick apply | When you like a recommendation | Instant (no setup) |
| **Webhooks** | External notifications | Want alerts in Slack/Teams/Jira | 5 minutes |
| **Notifications** | Email alerts | Want email notifications | 2 minutes |
| **Portfolio Management** | Multi-project view | Managing multiple projects | Instant (no setup) |
| **Feedback** | Improve system | After using features | Instant (no setup) |
| **Onboarding** | Learn system | First time using system | 10 minutes |
| **Audit Log** | Track changes | Need compliance/history | Instant (automatic) |
| **Re-Analyze** | Refresh analysis | After changes or time passes | Instant (no setup) |
| **Forensic Intelligence** | Advanced predictions | Want more accurate forecasts | Instant (toggle on) |
| **Mitigation Ranking** | Best solutions | Need to fix a problem | Instant (automatic) |

---

## Best Practices Summary

### For What-If Simulation
1. Test multiple scenarios
2. Compare time saved vs. cost
3. Use P80 for planning
4. Consider risk score impact

### For Use This Option
1. Test top 3 options
2. Compare results
3. Consider context (budget, timeline)
4. Document your choice

### For Webhooks
1. Test webhook before relying on it
2. Set appropriate thresholds
3. Use secret keys for security
4. Monitor failure count

### For Notifications
1. Set threshold to 70.0 (high-risk only)
2. Enable daily digest
3. Use project-specific settings
4. Test email configuration

### For Portfolio Management
1. Check portfolio dashboard daily
2. Focus on high-risk projects first
3. Monitor resource allocation
4. Track cross-project dependencies

### For Feedback
1. Provide feedback regularly
2. Be specific in comments
3. Rate honestly
4. Suggest improvements

### For Re-Analyze
1. Re-analyze after changes
2. Re-analyze weekly
3. Re-analyze before decisions
4. Re-analyze after mitigations

---

## Conclusion

This system provides a comprehensive set of features that work together to solve the PMO's core problem: **automated early warning with actionable insights**.

**Key Features**:
- ✅ **What-If Simulation**: Test scenarios before committing
- ✅ **Use This Option**: Quick apply of recommendations
- ✅ **Webhooks**: Integrate with external systems
- ✅ **Notifications**: Proactive email alerts
- ✅ **Portfolio Management**: Multi-project overview
- ✅ **Feedback System**: Improve the system
- ✅ **Onboarding**: Learn the system quickly
- ✅ **Audit Log**: Complete history
- ✅ **Re-Analyze**: Fresh analysis on demand
- ✅ **Forensic Intelligence**: Advanced predictions
- ✅ **Mitigation Ranking**: Best solutions first

**Together, these features transform PMO from reactive firefighting to proactive risk management.**

---

**Document Version**: 1.0  
**Last Updated**: 2025  
**For Questions**: Refer to this guide or the main architecture document
