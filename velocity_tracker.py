# -*- coding: utf-8 -*-
"""
Velocity Tracking System for Team Performance Analytics

Purpose: Track team velocity and completion rates using historical data
Focus: Evidence-based velocity calculations for sprint planning and estimates
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from src.integrations.neo4j.client import Neo4jClient

logger = logging.getLogger(__name__)

# List IDs for target lists
PADTAI_LIST_ID = "901606939084"
GET_SHIT_DONE_LIST_ID = "901602625750"
TARGET_LISTS = [PADTAI_LIST_ID, GET_SHIT_DONE_LIST_ID]


class VelocityTracker:
    """Tracks and analyzes team velocity metrics."""

    def __init__(self):
        self.client = Neo4jClient()

    def get_completion_velocity(self, list_id: str, weeks: int = 4) -> Dict[str, Any]:
        """
        Calculate task completion velocity from historical data.

        Args:
            list_id: The list ID to analyze
            weeks: Number of weeks to analyze for velocity calculation

        Returns:
            Dictionary with velocity metrics
        """
        query = """
        // Get task completions from state history
        MATCH (h:TaskStateHistory)
        WHERE h.field_name = 'status'
          AND h.new_value IN ['complete', 'closed', 'done']
          AND h.changed_at >= datetime() - duration('P' + $weeks + 'W')
        
        // Get task details to filter by list
        MATCH (t:Task {id: h.task_id})
        WHERE t.list_id = $list_id
        
        // Group by week
        WITH h, t, 
             duration.between(date.truncate('week', h.changed_at.date), date.truncate('week', date())).weeks as weeks_ago
        
        WITH weeks_ago, count(h) as tasks_completed_that_week
        WHERE weeks_ago >= 0 AND weeks_ago < $weeks
        
        WITH collect({week: weeks_ago, completed: tasks_completed_that_week}) as weekly_data
        
        RETURN {
            weekly_completions: [item IN weekly_data | item.completed],
            avg_velocity: avg([item IN weekly_data | item.completed]),
            max_velocity: max([item IN weekly_data | item.completed]),
            min_velocity: min([item IN weekly_data | item.completed]),
            total_completed: sum([item IN weekly_data | item.completed]),
            weeks_analyzed: size(weekly_data),
            velocity_trend: CASE 
                WHEN size(weekly_data) >= 2 THEN
                    CASE WHEN weekly_data[-1].completed > weekly_data[0].completed THEN 'improving'
                         WHEN weekly_data[-1].completed < weekly_data[0].completed THEN 'declining'
                         ELSE 'stable'
                    END
                ELSE 'insufficient_data'
            END
        } as velocity_data
        """

        result = self.client.execute_read(query, {"list_id": list_id, "weeks": weeks})

        if result and len(result) > 0:
            velocity_data = result[0]["velocity_data"]

            # Round velocity metrics for display
            if velocity_data["avg_velocity"]:
                velocity_data["avg_velocity"] = round(velocity_data["avg_velocity"], 1)

            return velocity_data
        else:
            return {
                "weekly_completions": [],
                "avg_velocity": 0,
                "max_velocity": 0,
                "min_velocity": 0,
                "total_completed": 0,
                "weeks_analyzed": 0,
                "velocity_trend": "no_data",
            }

    def get_status_transition_velocity(
        self, list_id: str, from_status: str, to_status: str, weeks: int = 4
    ) -> Dict[str, Any]:
        """
        Calculate velocity for specific status transitions (e.g., dev -> review).

        Args:
            list_id: The list ID to analyze
            from_status: Source status
            to_status: Target status
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with transition velocity metrics
        """
        query = """
        MATCH (h:TaskStateHistory)
        WHERE h.field_name = 'status'
          AND toLower(h.old_value) CONTAINS toLower($from_status)
          AND toLower(h.new_value) CONTAINS toLower($to_status)
          AND h.changed_at >= datetime() - duration('P' + $weeks + 'W')
        
        // Get task details to filter by list
        MATCH (t:Task {id: h.task_id})
        WHERE t.list_id = $list_id
        
        // Group by week
        WITH h, t,
             duration.between(date.truncate('week', h.changed_at.date), date.truncate('week', date())).weeks as weeks_ago
        
        WITH weeks_ago, count(h) as transitions_that_week
        WHERE weeks_ago >= 0 AND weeks_ago < $weeks
        
        WITH collect({week: weeks_ago, transitions: transitions_that_week}) as weekly_data
        
        RETURN {
            weekly_transitions: [item IN weekly_data | item.transitions],
            avg_transition_velocity: avg([item IN weekly_data | item.transitions]),
            total_transitions: sum([item IN weekly_data | item.transitions]),
            weeks_analyzed: size(weekly_data)
        } as transition_data
        """

        parameters = {
            "list_id": list_id,
            "from_status": from_status,
            "to_status": to_status,
            "weeks": weeks,
        }

        result = self.client.execute_read(query, parameters)

        if result and len(result) > 0:
            transition_data = result[0]["transition_data"]

            if transition_data["avg_transition_velocity"]:
                transition_data["avg_transition_velocity"] = round(
                    transition_data["avg_transition_velocity"], 1
                )

            return transition_data
        else:
            return {
                "weekly_transitions": [],
                "avg_transition_velocity": 0,
                "total_transitions": 0,
                "weeks_analyzed": 0,
            }

    def get_user_velocity(self, user_id: str, weeks: int = 4) -> Dict[str, Any]:
        """
        Calculate individual user velocity metrics.

        Args:
            user_id: The user ID to analyze
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with user velocity metrics
        """
        query = """
        // Get task completions by user
        MATCH (h:TaskStateHistory)
        WHERE h.field_name = 'status'
          AND h.new_value IN ['complete', 'closed', 'done']
          AND h.changed_at >= datetime() - duration('P' + $weeks + 'W')
        
        // Get task and user assignment
        MATCH (t:Task {id: h.task_id})
        MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t)
        
        // Filter to target lists only
        WHERE t.list_id IN $target_lists
        
        // Group by week
        WITH h, t, u,
             duration.between(date.truncate('week', h.changed_at.date), date.truncate('week', date())).weeks as weeks_ago
        
        WITH weeks_ago, count(h) as tasks_completed_that_week
        WHERE weeks_ago >= 0 AND weeks_ago < $weeks
        
        WITH collect({week: weeks_ago, completed: tasks_completed_that_week}) as weekly_data
        
        RETURN {
            weekly_completions: [item IN weekly_data | item.completed],
            avg_velocity: avg([item IN weekly_data | item.completed]),
            total_completed: sum([item IN weekly_data | item.completed]),
            weeks_analyzed: size(weekly_data)
        } as user_velocity_data
        """

        parameters = {"user_id": user_id, "weeks": weeks, "target_lists": TARGET_LISTS}

        result = self.client.execute_read(query, parameters)

        if result and len(result) > 0:
            velocity_data = result[0]["user_velocity_data"]

            if velocity_data["avg_velocity"]:
                velocity_data["avg_velocity"] = round(velocity_data["avg_velocity"], 1)

            return velocity_data
        else:
            return {
                "weekly_completions": [],
                "avg_velocity": 0,
                "total_completed": 0,
                "weeks_analyzed": 0,
            }

    def get_team_velocity_ranking(self, weeks: int = 4) -> List[Dict[str, Any]]:
        """
        Get velocity ranking for all team members.

        Args:
            weeks: Number of weeks to analyze

        Returns:
            List of users ranked by velocity
        """
        query = """
        // Get all users with task assignments in target lists
        MATCH (u:User)-[:ASSIGNED_TO]->(t:Task)
        WHERE t.list_id IN $target_lists
        
        // Get their task completions
        OPTIONAL MATCH (h:TaskStateHistory)
        WHERE h.task_id = t.id
          AND h.field_name = 'status'
          AND h.new_value IN ['complete', 'closed', 'done']
          AND h.changed_at >= datetime() - duration('P' + $weeks + 'W')
        
        WITH u, count(DISTINCT h) as total_completed, count(DISTINCT t) as total_assigned
        WHERE total_assigned > 0
        
        WITH u, total_completed, total_assigned,
             (total_completed * 1.0 / $weeks) as avg_velocity,
             (total_completed * 1.0 / total_assigned) as completion_rate
        
        RETURN {
            user_id: u.id,
            username: u.username,
            total_completed: total_completed,
            total_assigned: total_assigned,
            avg_velocity: avg_velocity,
            completion_rate: completion_rate,
            velocity_score: avg_velocity * 0.7 + completion_rate * 0.3
        } as user_metrics
        ORDER BY user_metrics.velocity_score DESC
        """

        parameters = {"weeks": weeks, "target_lists": TARGET_LISTS}

        result = self.client.execute_read(query, parameters)

        ranked_users = []
        for record in result:
            user_metrics = record["user_metrics"]

            # Round metrics for display
            user_metrics["avg_velocity"] = round(user_metrics["avg_velocity"], 1)
            user_metrics["completion_rate"] = round(user_metrics["completion_rate"], 2)
            user_metrics["velocity_score"] = round(user_metrics["velocity_score"], 2)

            ranked_users.append(user_metrics)

        return ranked_users

    def predict_completion_date(
        self, list_id: str, target_completion_percentage: float = 100.0
    ) -> Dict[str, Any]:
        """
        Predict when a list will reach target completion percentage based on current velocity.

        Args:
            list_id: The list ID to analyze
            target_completion_percentage: Target completion percentage (default 100%)

        Returns:
            Dictionary with prediction data
        """
        # Get current progress
        current_query = """
        MATCH (l:List {id: $list_id})
        OPTIONAL MATCH (l)-[:CONTAINS_TASK]->(t:Task)
        
        WITH count(t) as total_tasks,
             count(CASE WHEN toLower(t.status) IN ['complete', 'closed', 'done'] THEN 1 END) as completed_tasks
        
        RETURN {
            total_tasks: total_tasks,
            completed_tasks: completed_tasks,
            current_percentage: CASE WHEN total_tasks > 0 THEN completed_tasks * 100.0 / total_tasks ELSE 0 END
        } as current_progress
        """

        current_result = self.client.execute_read(current_query, {"list_id": list_id})

        if not current_result:
            return {"error": "Unable to get current progress"}

        current_progress = current_result[0]["current_progress"]
        total_tasks = current_progress["total_tasks"]
        completed_tasks = current_progress["completed_tasks"]

        # Get velocity data
        velocity_data = self.get_completion_velocity(list_id, weeks=4)
        avg_velocity = velocity_data["avg_velocity"]

        if avg_velocity <= 0:
            return {
                "current_progress": current_progress,
                "prediction": "Unable to predict - insufficient velocity data",
                "estimated_completion_date": None,
                "weeks_remaining": None,
            }

        # Calculate remaining tasks needed
        target_completed_tasks = (target_completion_percentage / 100.0) * total_tasks
        remaining_tasks = target_completed_tasks - completed_tasks

        if remaining_tasks <= 0:
            return {
                "current_progress": current_progress,
                "prediction": f"Target {target_completion_percentage}% already achieved",
                "estimated_completion_date": datetime.now(timezone.utc),
                "weeks_remaining": 0,
            }

        # Calculate estimated weeks
        weeks_remaining = remaining_tasks / avg_velocity
        estimated_completion_date = datetime.now(timezone.utc) + timedelta(
            weeks=weeks_remaining
        )

        return {
            "current_progress": current_progress,
            "velocity_data": velocity_data,
            "remaining_tasks": int(remaining_tasks),
            "weeks_remaining": round(weeks_remaining, 1),
            "estimated_completion_date": estimated_completion_date,
            "prediction": f"Estimated {target_completion_percentage}% completion in {weeks_remaining:.1f} weeks",
        }

    def get_bottleneck_analysis(self, weeks: int = 4) -> Dict[str, Any]:
        """
        Analyze bottlenecks in the development process based on status transitions.

        Args:
            weeks: Number of weeks to analyze

        Returns:
            Dictionary with bottleneck analysis
        """
        # Analyze time spent in each status
        query = """
        MATCH (h1:TaskStateHistory)-[:HAS_HISTORY]-(t:Task)-[:HAS_HISTORY]-(h2:TaskStateHistory)
        WHERE t.list_id IN $target_lists
          AND h1.field_name = 'status' AND h2.field_name = 'status'
          AND h1.changed_at >= datetime() - duration('P' + $weeks + 'W')
          AND h2.changed_at > h1.changed_at
          AND h2.changed_at <= h1.changed_at + duration('P7D') // Within a week of each other
        
        WITH h1.new_value as status, 
             duration.between(h1.changed_at, h2.changed_at).days as days_in_status
        WHERE days_in_status >= 0 AND days_in_status <= 30 // Reasonable bounds
        
        WITH status, collect(days_in_status) as duration_list
        WHERE size(duration_list) > 0
        
        RETURN {
            status: status,
            avg_days: avg(duration_list),
            max_days: max(duration_list),
            min_days: min(duration_list),
            sample_size: size(duration_list)
        } as status_metrics
        ORDER BY status_metrics.avg_days DESC
        """

        result = self.client.execute_read(
            query, {"target_lists": TARGET_LISTS, "weeks": weeks}
        )

        status_analysis = []
        for record in result:
            metrics = record["status_metrics"]
            metrics["avg_days"] = round(metrics["avg_days"], 1)
            status_analysis.append(metrics)

        # Identify bottlenecks (statuses with high average time)
        bottlenecks = [
            s for s in status_analysis if s["avg_days"] > 3 and s["sample_size"] > 2
        ]

        return {
            "status_analysis": status_analysis,
            "bottlenecks": bottlenecks,
            "analysis_period_weeks": weeks,
            "recommendations": self._generate_bottleneck_recommendations(bottlenecks),
        }

    def _generate_bottleneck_recommendations(
        self, bottlenecks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on bottleneck analysis."""
        recommendations = []

        for bottleneck in bottlenecks:
            status = bottleneck["status"]
            avg_days = bottleneck["avg_days"]

            if "review" in status.lower():
                recommendations.append(
                    f"Review process bottleneck: Tasks spend {avg_days:.1f} days in {status}. Consider adding more reviewers or streamlining review criteria."
                )
            elif "dev" in status.lower():
                recommendations.append(
                    f"Development bottleneck: Tasks spend {avg_days:.1f} days in {status}. Consider breaking down tasks or providing development support."
                )
            else:
                recommendations.append(
                    f"Process bottleneck in {status}: {avg_days:.1f} days average. Investigate process improvements."
                )

        if not recommendations:
            recommendations.append(
                "No significant bottlenecks detected in the analysis period."
            )

        return recommendations


def get_velocity_summary() -> Dict[str, Any]:
    """
    Get a comprehensive velocity summary for all target lists.

    Returns:
        Dictionary with velocity summary data
    """
    tracker = VelocityTracker()

    summary = {
        "lists": {},
        "team_ranking": tracker.get_team_velocity_ranking(),
        "bottleneck_analysis": tracker.get_bottleneck_analysis(),
        "timestamp": datetime.now(timezone.utc),
    }

    for list_id in TARGET_LISTS:
        list_name = "PADTAI" if list_id == PADTAI_LIST_ID else "Get Shit Done"

        summary["lists"][list_id] = {
            "list_name": list_name,
            "completion_velocity": tracker.get_completion_velocity(list_id),
            "dev_to_review_velocity": tracker.get_status_transition_velocity(
                list_id, "dev", "review"
            ),
            "completion_prediction": tracker.predict_completion_date(list_id),
        }

    return summary


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Generate velocity summary
        summary = get_velocity_summary()
        print("\n" + "=" * 60)
        print("🚀 TEAM VELOCITY ANALYSIS")
        print("=" * 60)

        # List velocities
        for list_id, list_data in summary["lists"].items():
            print(f"\n📋 {list_data['list_name']}")
            print("-" * 40)

            completion_vel = list_data["completion_velocity"]
            print(
                f"Avg completion velocity: {completion_vel['avg_velocity']} tasks/week"
            )
            print(f"Velocity trend: {completion_vel['velocity_trend']}")

            prediction = list_data["completion_prediction"]
            if "weeks_remaining" in prediction:
                print(
                    f"Estimated 100% completion: {prediction['weeks_remaining']} weeks"
                )

        # Team ranking
        print("\n👥 TOP PERFORMERS (by velocity score)")
        print("-" * 40)
        for i, user in enumerate(summary["team_ranking"][:5], 1):
            print(
                f"{i}. {user['username']}: {user['velocity_score']} score ({user['avg_velocity']} tasks/week)"
            )

        # Bottlenecks
        bottlenecks = summary["bottleneck_analysis"]["bottlenecks"]
        if bottlenecks:
            print("\n⚠️  BOTTLENECKS DETECTED")
            print("-" * 40)
            for bottleneck in bottlenecks:
                print(
                    f"• {bottleneck['status']}: {bottleneck['avg_days']} days average"
                )

        print("=" * 60)

    except Exception as e:
        logger.error(f"Failed to generate velocity summary: {e}")
        print(f"❌ Error: {e}")
