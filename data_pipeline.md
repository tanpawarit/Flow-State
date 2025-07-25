🚀 Historical Data Pipeline Setup

1. Weekly Snapshots (Manual/Scheduled)

# Create weekly snapshots manually
python src/graph/operations/weekly_snapshot.py

# Or add to cron for automation (every Sunday at 11:59 PM)
59 23 * * 0 cd /Users/pawarison/dev/Flow-State && python src/graph/operations/weekly_snapshot.py

2. Webhook Integration (Real-time)

Start webhook server:
# Start the webhook server to capture real-time changes
python -m src.webhooks.core.webhook_server

Configure ClickUp webhooks to point to your server:
- Endpoint: POST /webhooks/clickup
- Events: taskStatusUpdated, taskAssigneeUpdated, taskPriorityUpdated

3. Data Flow Pipeline

ClickUp Changes → Webhooks → TaskStateHistory nodes
    ↓
Weekly Snapshots → ProgressSnapshot nodes
    ↓
Historical Analysis → Velocity & Progress Reports

4. Using the System

Daily: Weekly Summary
python weekly-summary.py
# Now uses real historical data instead of fake +10%

Weekly: Velocity Analysis
python src/graph/operations/velocity_tracker.py
# Team velocity, bottlenecks, completion predictions

Monthly: Historical Trends
from src.graph.operations.weekly_snapshot import WeeklySnapshotManager
manager = WeeklySnapshotManager()

# Get 4 weeks of progress history
history = manager.get_historical_progress("901606939084", weeks_back=4)

📊 Available Analytics

Progress Tracking

- Real vs estimated progress: No more fake calculations
- Week-over-week comparison: Actual historical data
- Velocity-based predictions: Evidence-based completion dates

Team Performance

- Individual velocity: Tasks completed per week per person
- Team rankings: Performance-based scoring
- Bottleneck identification: Process improvement recommendations

Sprint Planning

- Completion predictions: Based on actual team velocity
- Resource allocation: Historical performance patterns
- Timeline estimates: Evidence-based planning
