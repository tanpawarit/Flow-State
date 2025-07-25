# -*- coding: utf-8 -*-
"""
Weekly Snapshot System for Historical Progress Tracking

Purpose: Create automated weekly snapshots of project progress for accurate historical data
Focus: Replace estimated progress calculations with real historical tracking
"""

import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.neo4j.client import Neo4jClient  # noqa: E402

logger = logging.getLogger(__name__)

# List IDs for target lists
PADTAI_LIST_ID = "901606939084"
GET_SHIT_DONE_LIST_ID = "901602625750"
TARGET_LISTS = [PADTAI_LIST_ID, GET_SHIT_DONE_LIST_ID]


class WeeklySnapshotManager:
    """Manages weekly progress snapshots for historical tracking."""

    def __init__(self):
        self.client = Neo4jClient()

    def create_weekly_snapshots(self) -> Dict[str, Any]:
        """
        Create weekly progress snapshots for all target lists.
        
        Returns:
            Dictionary with snapshot creation results
        """
        logger.info("🔄 Creating weekly progress snapshots...")
        
        results = {
            "snapshots_created": 0,
            "lists_processed": [],
            "timestamp": datetime.now(timezone.utc),
            "week_ending": self._get_week_ending_date(),
            "errors": []
        }
        
        for list_id in TARGET_LISTS:
            try:
                snapshot_result = self._create_list_snapshot(list_id)
                results["snapshots_created"] += 1
                results["lists_processed"].append({
                    "list_id": list_id,
                    "snapshot_id": snapshot_result["snapshot_id"],
                    "progress_data": snapshot_result["progress_data"]
                })
                logger.info(f"✅ Created snapshot for list {list_id}")
                
            except Exception as e:
                error_msg = f"Failed to create snapshot for list {list_id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        logger.info(f"📊 Created {results['snapshots_created']} weekly snapshots")
        return results

    def _create_list_snapshot(self, list_id: str) -> Dict[str, Any]:
        """Create a snapshot for a specific list."""
        week_ending = self._get_week_ending_date()
        snapshot_id = f"snapshot_{list_id}_{week_ending.strftime('%Y-%m-%d')}"
        
        # Get current list progress data
        query = """
        MATCH (l:List {id: $list_id})
        OPTIONAL MATCH (l)-[:CONTAINS_TASK]->(t:Task)
        
        WITH l, 
             count(t) as total_tasks,
             count(CASE WHEN toLower(t.status) IN ['complete', 'closed', 'done'] THEN 1 END) as completed_tasks,
             count(CASE WHEN 
                 (toLower(t.status) CONTAINS 'dev' AND NOT toLower(t.status) CONTAINS 'ready') OR 
                 toLower(t.status) CONTAINS 'review' 
             THEN 1 END) as in_progress_tasks
        
        // Create progress snapshot
        CREATE (ps:ProgressSnapshot {
            id: $snapshot_id,
            list_id: l.id,
            list_name: l.name,
            snapshot_date: date(),
            week_ending: $week_ending,
            total_tasks: total_tasks,
            completed_tasks: completed_tasks,
            in_progress_tasks: in_progress_tasks,
            progress_percentage: CASE WHEN total_tasks > 0 THEN completed_tasks * 100.0 / total_tasks ELSE 0 END,
            created_at: datetime(),
            snapshot_type: 'weekly'
        })
        
        // Create relationship
        CREATE (l)-[:HAD_PROGRESS_ON {
            date: date(),
            week_ending: $week_ending,
            snapshot_type: 'weekly'
        }]->(ps)
        
        RETURN ps {
            .id,
            .list_id,
            .list_name,
            .total_tasks,
            .completed_tasks,
            .in_progress_tasks,
            .progress_percentage,
            .week_ending
        } as snapshot_data
        """
        
        parameters = {
            "list_id": list_id,
            "snapshot_id": snapshot_id,
            "week_ending": week_ending
        }
        
        result = self.client.execute_read(query, parameters)
        
        if result:
            snapshot_data = result[0]["snapshot_data"]
            return {
                "snapshot_id": snapshot_id,
                "progress_data": snapshot_data
            }
        else:
            raise RuntimeError(f"Failed to create snapshot for list {list_id}")

    def get_historical_progress(self, list_id: str, weeks_back: int = 4) -> List[Dict[str, Any]]:
        """
        Get historical progress data for a list.
        
        Args:
            list_id: The list ID to get progress for
            weeks_back: Number of weeks of history to retrieve
            
        Returns:
            List of historical progress snapshots
        """
        query = """
        MATCH (ps:ProgressSnapshot)
        WHERE ps.list_id = $list_id 
          AND ps.snapshot_date >= date() - duration('P' + $weeks_back + 'W')
        RETURN ps {
            .id,
            .list_id,
            .list_name,
            .snapshot_date,
            .week_ending,
            .total_tasks,
            .completed_tasks,
            .in_progress_tasks,
            .progress_percentage,
            .created_at
        } as snapshot
        ORDER BY ps.snapshot_date DESC
        """
        
        parameters = {
            "list_id": list_id,
            "weeks_back": weeks_back
        }
        
        result = self.client.execute_read(query, parameters)
        return [record["snapshot"] for record in result]

    def get_progress_with_history(self, list_id: str) -> Dict[str, Any]:
        """
        Get current progress with previous week comparison using real historical data.
        
        Args:
            list_id: The list ID to get progress for
            
        Returns:
            Dictionary with current and historical progress data
        """
        query = """
        // Get current progress
        MATCH (l:List {id: $list_id})
        OPTIONAL MATCH (l)-[:CONTAINS_TASK]->(t:Task)
        
        WITH l,
             count(t) as current_total_tasks,
             count(CASE WHEN toLower(t.status) IN ['complete', 'closed', 'done'] THEN 1 END) as current_completed_tasks,
             count(CASE WHEN 
                 (toLower(t.status) CONTAINS 'dev' AND NOT toLower(t.status) CONTAINS 'ready') OR 
                 toLower(t.status) CONTAINS 'review' 
             THEN 1 END) as current_in_progress_tasks
        
        // Get previous week snapshot
        OPTIONAL MATCH (l)-[:HAD_PROGRESS_ON]->(ps:ProgressSnapshot)
        WHERE ps.snapshot_date >= date() - duration('P14D')
          AND ps.snapshot_date < date() - duration('P7D')
        
        WITH l, current_total_tasks, current_completed_tasks, current_in_progress_tasks, ps
        ORDER BY ps.snapshot_date DESC
        LIMIT 1
        
        WITH l, current_total_tasks, current_completed_tasks, current_in_progress_tasks,
             COALESCE(ps.progress_percentage, 0) as previous_progress,
             COALESCE(ps.completed_tasks, 0) as previous_completed_tasks
        
        RETURN {
            list_id: l.id,
            list_name: l.name,
            current_progress: CASE WHEN current_total_tasks > 0 THEN current_completed_tasks * 100.0 / current_total_tasks ELSE 0 END,
            previous_progress: previous_progress,
            progress_change: CASE WHEN current_total_tasks > 0 THEN current_completed_tasks * 100.0 / current_total_tasks ELSE 0 END - previous_progress,
            completed_tasks: current_completed_tasks,
            total_tasks: current_total_tasks,
            in_progress_tasks: current_in_progress_tasks,
            tasks_completed_this_week: current_completed_tasks - previous_completed_tasks
        } as progress_data
        """
        
        result = self.client.execute_read(query, {"list_id": list_id})
        
        if result:
            data = result[0]["progress_data"]
            # Round percentages for display
            data["current_progress"] = round(data["current_progress"], 1)
            data["previous_progress"] = round(data["previous_progress"], 1)
            data["progress_change"] = round(data["progress_change"], 1)
            return data
        else:
            # Fallback if no historical data exists
            return {
                "list_id": list_id,
                "list_name": "Unknown",
                "current_progress": 0,
                "previous_progress": 0,
                "progress_change": 0,
                "completed_tasks": 0,
                "total_tasks": 0,
                "in_progress_tasks": 0,
                "tasks_completed_this_week": 0
            }

    def get_velocity_metrics(self, list_id: str, weeks: int = 4) -> Dict[str, Any]:
        """
        Calculate team velocity metrics from historical snapshots.
        
        Args:
            list_id: The list ID to calculate velocity for
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with velocity statistics
        """
        query = """
        MATCH (ps:ProgressSnapshot)
        WHERE ps.list_id = $list_id 
          AND ps.snapshot_date >= date() - duration('P' + $weeks + 'W')
        
        WITH ps
        ORDER BY ps.snapshot_date ASC
        
        // Calculate week-over-week task completions
        WITH collect(ps) as snapshots
        
        UNWIND range(1, size(snapshots)-1) as i
        WITH snapshots[i-1] as prev_snapshot, snapshots[i] as curr_snapshot
        
        WITH (curr_snapshot.completed_tasks - prev_snapshot.completed_tasks) as tasks_completed_this_week
        WHERE tasks_completed_this_week >= 0
        
        RETURN {
            avg_velocity: avg(tasks_completed_this_week),
            max_velocity: max(tasks_completed_this_week),
            min_velocity: min(tasks_completed_this_week),
            total_weeks: count(tasks_completed_this_week),
            weekly_completions: collect(tasks_completed_this_week),
            velocity_trend: CASE 
                WHEN avg(tasks_completed_this_week) > 0 THEN 'positive'
                WHEN avg(tasks_completed_this_week) = 0 THEN 'stable' 
                ELSE 'negative'
            END
        } as velocity_data
        """
        
        result = self.client.execute_read(query, {"list_id": list_id, "weeks": weeks})
        
        if result and len(result) > 0:
            velocity_data = result[0]["velocity_data"]
            # Round velocity for display
            if velocity_data["avg_velocity"]:
                velocity_data["avg_velocity"] = round(velocity_data["avg_velocity"], 1)
            return velocity_data
        else:
            return {
                "avg_velocity": 0,
                "max_velocity": 0,
                "min_velocity": 0,
                "total_weeks": 0,
                "weekly_completions": [],
                "velocity_trend": "unknown"
            }

    def cleanup_old_snapshots(self, keep_weeks: int = 12) -> int:
        """
        Clean up old snapshots to prevent database bloat.
        
        Args:
            keep_weeks: Number of weeks of snapshots to retain
            
        Returns:
            Number of snapshots deleted
        """
        query = """
        MATCH (ps:ProgressSnapshot)
        WHERE ps.snapshot_date < date() - duration('P' + $keep_weeks + 'W')
        
        WITH ps
        DETACH DELETE ps
        RETURN count(ps) as deleted_count
        """
        
        # Use execute_read for queries returning data, even if they modify
        result = self.client.execute_read(query, {"keep_weeks": keep_weeks})
        deleted_count = result[0]["deleted_count"] if result else 0
        
        logger.info(f"🧹 Cleaned up {deleted_count} old snapshots (keeping {keep_weeks} weeks)")
        return deleted_count

    def _get_week_ending_date(self) -> datetime:
        """Get the date for the end of the current week (Sunday)."""
        today = datetime.now(timezone.utc)
        days_until_sunday = (6 - today.weekday()) % 7
        week_ending = today + timedelta(days=days_until_sunday)
        return week_ending.replace(hour=23, minute=59, second=59, microsecond=0)


def create_weekly_snapshots() -> Dict[str, Any]:
    """
    Convenience function to create weekly snapshots.
    Can be called from scripts or scheduled tasks.
    
    Returns:
        Dictionary with snapshot creation results
    """
    manager = WeeklySnapshotManager()
    return manager.create_weekly_snapshots()


def get_historical_progress_for_all_lists() -> Dict[str, Dict[str, Any]]:
    """
    Get historical progress data for all target lists.
    
    Returns:
        Dictionary mapping list IDs to their progress data
    """
    manager = WeeklySnapshotManager()
    progress_data = {}
    
    for list_id in TARGET_LISTS:
        progress_data[list_id] = manager.get_progress_with_history(list_id)
    
    return progress_data


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    try:
        # Create weekly snapshots
        results = create_weekly_snapshots()
        print("\n" + "=" * 50)
        print("📊 Weekly Snapshot Creation Results")
        print("=" * 50)
        print(f"Snapshots created: {results['snapshots_created']}")
        print(f"Week ending: {results['week_ending'].strftime('%Y-%m-%d')}")
        
        for list_data in results["lists_processed"]:
            progress = list_data["progress_data"]
            print(f"\n📋 {progress['list_name']} (ID: {progress['list_id']})")
            print(f"  Total tasks: {progress['total_tasks']}")
            print(f"  Completed: {progress['completed_tasks']}")
            print(f"  Progress: {progress['progress_percentage']:.1f}%")
        
        if results["errors"]:
            print(f"\n❌ Errors: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"  - {error}")
        
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Failed to create weekly snapshots: {e}")
        print(f"❌ Error: {e}")