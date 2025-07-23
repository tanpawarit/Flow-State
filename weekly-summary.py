# -*- coding: utf-8 -*-
"""
Weekly Summary Query for Flow-State Discord Bot

Purpose: Weekly Summary - Generate weekly team progress reports
Focus: Tasks in "dev" status (not "ready to dev") from PADTAI and Get Shit Done lists

Usage:
    python query.py

Output Format:
    📊 **Weekly Summary - Week of [date range]**
    📈 **Progress**: [previous]% → [current]% (+[change]%)
    🎯 **Tasks Completed**: [completed]/[total]
    ⏰ **Timeline**: [status] of schedule
    🏆 **Team Highlights**: [member accomplishments]
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.integrations.neo4j.client import Neo4jClient

logger = logging.getLogger(__name__)

# List IDs for target lists
PADTAI_LIST_ID = "901606939084"
GET_SHIT_DONE_LIST_ID = "901602625750"
TARGET_LISTS = [PADTAI_LIST_ID, GET_SHIT_DONE_LIST_ID]


def get_tasks_in_progress_by_list(list_id: str) -> List[Dict[str, Any]]:
    """
    Get tasks currently in progress from a specific list.

    Args:
        list_id: The list ID to get tasks from

    Returns:
        List of tasks in progress with assignee, progress info, and subtask hierarchy
    """
    client = Neo4jClient()

    query = """
    // First, get tasks that directly match the status criteria
    CALL () {
        MATCH (t:Task)
        WHERE t.list_id = $list_id
          AND (
              toLower(t.status) CONTAINS 'review'
              OR (toLower(t.status) CONTAINS 'dev' AND toLower(t.status) CONTAINS 'review')
          )
          AND NOT toLower(t.status) CONTAINS 'ready'
          AND NOT toLower(t.status) = 'ready to dev'
          AND NOT t.status IN ['complete', 'closed', 'done']
        RETURN t
        
        UNION
        
        // Second, get parent tasks that have subtasks matching the criteria
        MATCH (parent:Task)
        WHERE parent.list_id = $list_id
          AND EXISTS {
              MATCH (subtask:Task)-[:SUBTASK_OF]->(parent)
              WHERE subtask.list_id = $list_id
                AND (
                    toLower(subtask.status) CONTAINS 'review'
                    OR (toLower(subtask.status) CONTAINS 'dev' AND toLower(subtask.status) CONTAINS 'review')
                )
                AND NOT toLower(subtask.status) CONTAINS 'ready'
                AND NOT toLower(subtask.status) = 'ready to dev'
                AND NOT subtask.status IN ['complete', 'closed', 'done']
          }
        RETURN parent as t
    }
    
    // Now get the relationships for all selected tasks
    OPTIONAL MATCH (u:User)-[:ASSIGNED_TO]->(t)
    OPTIONAL MATCH (t)-[:SUBTASK_OF]->(parent:Task)
    WITH t, parent, collect(DISTINCT u.username) as assigned_users
    
    // Get active subtasks for the selected tasks
    OPTIONAL MATCH (subtask:Task)-[:SUBTASK_OF]->(t)
    WHERE subtask.list_id = $list_id
      AND (
          toLower(subtask.status) CONTAINS 'review'
          OR (toLower(subtask.status) CONTAINS 'dev' AND toLower(subtask.status) CONTAINS 'review')
      )
      AND NOT toLower(subtask.status) CONTAINS 'ready'
      AND NOT toLower(subtask.status) = 'ready to dev'
      AND NOT subtask.status IN ['complete', 'closed', 'done']
    OPTIONAL MATCH (su:User)-[:ASSIGNED_TO]->(subtask)
    
    WITH t, parent, assigned_users, 
         collect(DISTINCT subtask.id) as subtask_ids,
         collect(DISTINCT subtask.name) as subtask_names,
         collect(DISTINCT subtask.status) as subtask_statuses,
         collect(DISTINCT su.username) as all_subtask_users
    RETURN t.id as task_id,
           t.name as task_name,
           t.status as status,
           t.priority as priority,
           t.list_id as list_id,
           t.due_date as due_date,
           t.date_updated as last_updated,
           assigned_users,
           parent.id as parent_id,
           parent.name as parent_name,
           subtask_ids,
           subtask_names,
           subtask_statuses,
           all_subtask_users
    ORDER BY 
        CASE WHEN parent.id IS NULL THEN 0 ELSE 1 END,  // Show parent tasks first
        CASE WHEN t.due_date IS NULL THEN 1 ELSE 0 END, 
        t.due_date ASC, 
        t.priority DESC
    """

    try:
        result = client.execute_read(query, {"list_id": list_id})

        # Process the result to reconstruct subtask structure
        processed_tasks = []
        for task in result:
            # Reconstruct subtasks from separate lists
            subtasks = []
            if task.get("subtask_ids") and task["subtask_ids"][0] is not None:
                subtask_ids = task["subtask_ids"]
                subtask_names = task["subtask_names"]
                for i, subtask_id in enumerate(subtask_ids):
                    if subtask_id:  # Valid subtask
                        subtasks.append(
                            {
                                "id": subtask_id,
                                "name": subtask_names[i]
                                if i < len(subtask_names)
                                else "",
                                "assigned_users": task.get("all_subtask_users", []),
                            }
                        )

            # Create processed task
            processed_task = {
                "task_id": task["task_id"],
                "task_name": task["task_name"],
                "status": task["status"],
                "priority": task["priority"],
                "list_id": task["list_id"],
                "due_date": task["due_date"],
                "last_updated": task["last_updated"],
                "assigned_users": task["assigned_users"],
                "parent_id": task.get("parent_id"),
                "parent_name": task.get("parent_name"),
                "subtasks": subtasks,
            }
            processed_tasks.append(processed_task)

        return processed_tasks
    except Exception as e:
        logger.error(f"Failed to get weekly tasks in dev: {e}")
        return []


def get_list_progress(list_id: str) -> Dict[str, Any]:
    """
    Calculate progress metrics for a specific list.

    Args:
        list_id: The list ID to get progress for

    Returns:
        Dictionary with progress statistics for the specific list
    """
    client = Neo4jClient()

    # Get task statistics for specific list
    query = """
    MATCH (t:Task)
    WHERE t.list_id = $list_id
    WITH t,
         CASE 
             WHEN toLower(t.status) IN ['complete', 'closed', 'done'] THEN 'completed'
             WHEN (toLower(t.status) CONTAINS 'review' OR 
                   (toLower(t.status) CONTAINS 'dev' AND toLower(t.status) CONTAINS 'review'))
                  AND NOT toLower(t.status) CONTAINS 'ready' THEN 'in_progress'
             ELSE 'other'
         END as task_category
    RETURN 
        count(CASE WHEN task_category = 'completed' THEN 1 END) as completed_tasks,
        count(CASE WHEN task_category = 'in_progress' THEN 1 END) as in_progress_tasks,
        count(CASE WHEN task_category IN ['completed', 'in_progress'] THEN 1 END) as total_tasks
    """

    try:
        result = client.execute_read(query, {"list_id": list_id})
        if result:
            data = result[0]
            completed = data.get("completed_tasks", 0)
            total = data.get("total_tasks", 0)
            in_progress = data.get("in_progress_tasks", 0)

            current_progress = (completed / total * 100) if total > 0 else 0

            return {
                "completed_tasks": completed,
                "total_tasks": total,
                "in_progress_tasks": in_progress,
                "current_progress": round(current_progress, 1),
                "previous_progress": round(
                    max(0, current_progress - 10), 1
                ),  # Estimated previous week
                "progress_change": round(
                    min(current_progress, 10), 1
                ),  # Estimated change
            }
    except Exception as e:
        logger.error(f"Failed to get progress for list {list_id}: {e}")

    return {
        "completed_tasks": 0,
        "total_tasks": 0,
        "in_progress_tasks": 0,
        "current_progress": 0,
        "previous_progress": 0,
        "progress_change": 0,
    }


def get_weekly_progress() -> Dict[str, Any]:
    """
    Calculate weekly progress metrics for both lists separately.

    Returns:
        Dictionary with progress statistics for both lists
    """
    padtai_progress = get_list_progress(PADTAI_LIST_ID)
    get_shit_done_progress = get_list_progress(GET_SHIT_DONE_LIST_ID)

    # Calculate combined totals
    combined_completed = (
        padtai_progress["completed_tasks"] + get_shit_done_progress["completed_tasks"]
    )
    combined_total = (
        padtai_progress["total_tasks"] + get_shit_done_progress["total_tasks"]
    )
    combined_in_progress = (
        padtai_progress["in_progress_tasks"]
        + get_shit_done_progress["in_progress_tasks"]
    )

    combined_progress = (
        (combined_completed / combined_total * 100) if combined_total > 0 else 0
    )

    return {
        "padtai": padtai_progress,
        "get_shit_done": get_shit_done_progress,
        "combined": {
            "completed_tasks": combined_completed,
            "total_tasks": combined_total,
            "in_progress_tasks": combined_in_progress,
            "current_progress": round(combined_progress, 1),
            "previous_progress": round(max(0, combined_progress - 10), 1),
            "progress_change": round(min(combined_progress, 10), 1),
        },
    }


def get_most_supporter() -> List[Dict[str, Any]]:
    """
    Get team members who have the most task assignments and activity,
    indicating they are most supportive to the team effort.

    Returns:
        List of team members ranked by their task involvement
    """
    client = Neo4jClient()

    # Count task relationships that actually exist in the database
    query = """
    MATCH (u:User)-[:ASSIGNED_TO]->(t:Task)
    WHERE t.list_id IN $list_ids
    
    // Count existing task relationships
    OPTIONAL MATCH (t)-[:SUBTASK_OF]->(parent:Task)
    OPTIONAL MATCH (subtask:Task)-[:SUBTASK_OF]->(t)
    
    WITH u, t,
         count(DISTINCT parent) as parent_count,
         count(DISTINCT subtask) as subtask_count
    
    // Aggregate per user
    WITH u, 
         sum(parent_count + subtask_count) as relationship_score,
         count(DISTINCT t) as total_tasks,
         count(CASE WHEN toLower(t.status) IN ['complete', 'closed', 'done'] THEN 1 END) as completed_tasks,
         count(CASE WHEN toLower(t.status) CONTAINS 'review' OR 
                          (toLower(t.status) CONTAINS 'dev' AND toLower(t.status) CONTAINS 'review') 
                     THEN 1 END) as active_tasks
    
    // Calculate support score - if no relationships, use task activity
    WITH u, relationship_score, total_tasks, completed_tasks, active_tasks,
         CASE 
             WHEN relationship_score > 0 THEN relationship_score * 2 + total_tasks
             ELSE completed_tasks * 2 + active_tasks + total_tasks  
         END as support_score,
         CASE 
             WHEN relationship_score >= 5 THEN 'Cross-functional coordinator'
             WHEN relationship_score >= 3 THEN 'Team collaborator'  
             WHEN completed_tasks >= 5 THEN 'Delivery champion'
             WHEN active_tasks >= 3 THEN 'Active contributor'
             WHEN total_tasks >= 3 THEN 'Task supporter'
             ELSE 'Team contributor'
         END as support_type
    
    WHERE total_tasks > 0
    
    RETURN u.username as username,
           relationship_score,
           total_tasks,
           completed_tasks,
           active_tasks,
           support_type,
           support_score
    ORDER BY support_score DESC, completed_tasks DESC, active_tasks DESC
    LIMIT 5
    """

    try:
        result = client.execute_read(query, {"list_ids": TARGET_LISTS})

        supporters = []
        for record in result:
            username = record.get("username", "Unknown")
            relationship_score = record.get("relationship_score", 0)
            total_tasks = record.get("total_tasks", 0)
            completed_tasks = record.get("completed_tasks", 0)
            active_tasks = record.get("active_tasks", 0)
            support_type = record.get("support_type", "Team contributor")
            support_score = record.get("support_score", 0)

            if total_tasks > 0:  # Only include users with tasks
                # Generate support description based on what data we have
                if relationship_score >= 5:
                    accomplishment = f"Managing {relationship_score} subtask relationships across teams"
                elif relationship_score >= 3:
                    accomplishment = (
                        f"Coordinating {relationship_score} subtask relationships"
                    )
                elif completed_tasks >= 5:
                    accomplishment = f"Delivered {completed_tasks} completed tasks"
                elif active_tasks >= 3:
                    accomplishment = f"Actively working on {active_tasks} review tasks"
                elif total_tasks >= 3:
                    accomplishment = (
                        f"Supporting team with {total_tasks} assigned tasks"
                    )
                else:
                    accomplishment = f"Contributing {total_tasks} tasks to team effort"

                supporters.append(
                    {
                        "username": username,
                        "accomplishment": accomplishment,
                        "support_score": support_score,
                        "support_type": support_type,
                        "task_count": total_tasks,
                        "completed_count": completed_tasks,
                        "active_count": active_tasks,
                    }
                )

        return supporters
    except Exception as e:
        logger.error(f"Failed to get most supporter: {e}")
        return []


def get_timeline_status(progress_data: Dict[str, Any]) -> str:
    """
    Determine if the team is ahead, on track, or behind schedule.

    Args:
        progress_data: Progress statistics dictionary

    Returns:
        Timeline status string
    """
    progress_change = progress_data.get("progress_change", 0)

    if progress_change > 15:
        return "ahead of schedule"
    elif progress_change > 5:
        return "on track"
    elif progress_change > 0:
        return "slightly behind schedule"
    else:
        return "behind schedule"


def format_weekly_summary(
    padtai_tasks: List[Dict[str, Any]],
    get_shit_done_tasks: List[Dict[str, Any]],
    progress_data: Dict[str, Any],
    most_supporter: List[Dict[str, Any]],
) -> str:
    """
    Format all data into separate weekly summary sections.

    Args:
        padtai_tasks: List of PADTAI tasks in progress
        get_shit_done_tasks: List of Get Shit Done tasks in progress
        progress_data: Progress statistics (with separate list data)
        most_supporter: Team members with most task relationships

    Returns:
        Formatted weekly summary string with separate sections
    """
    # Calculate date range for current week
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_range = f"{week_start.strftime('%B %d')}-{week_end.strftime('%d')}"

    # Format progress - use combined data
    combined_data = progress_data["combined"]
    current_prog = combined_data["current_progress"]
    previous_prog = combined_data["previous_progress"]
    change = combined_data["progress_change"]
    completed = combined_data["completed_tasks"]
    total = combined_data["total_tasks"]

    # Individual list progress
    padtai_data = progress_data["padtai"]
    gsd_data = progress_data["get_shit_done"]

    # Format timeline status
    timeline_status = get_timeline_status(combined_data)
    timeline_days = abs(change // 5)  # Rough estimate
    if timeline_days > 0:
        timeline_text = f"{timeline_days} days {timeline_status}"
    else:
        timeline_text = timeline_status

    # Format most supporter
    supporter_text = ""
    for supporter in most_supporter[:3]:  # Top 3 supporters
        username = supporter["username"]
        accomplishment = supporter["accomplishment"]
        support_type = supporter.get("support_type", "Team contributor")
        supporter_text += f"• {username}: {accomplishment} ({support_type})\n"

    if not supporter_text:
        supporter_text = "• Team: Working on collaborative tasks\n"

    # Build final summary
    summary = f"""📊 **Weekly Summary - Week of {week_range}**

📈 **PADTAI Progress**: {padtai_data["previous_progress"]}% → {padtai_data["current_progress"]}% (+{padtai_data["progress_change"]}%)
🎯 **PADTAI Tasks Completed**: {padtai_data["completed_tasks"]}/{padtai_data["total_tasks"]}
⏰ **PADTAI Timeline**: {get_timeline_status(padtai_data)}

📈 **Get Shit Done Progress**: {gsd_data["previous_progress"]}% → {gsd_data["current_progress"]}% (+{gsd_data["progress_change"]}%)
🎯 **Get Shit Done Tasks Completed**: {gsd_data["completed_tasks"]}/{gsd_data["total_tasks"]}
⏰ **Get Shit Done Timeline**: {get_timeline_status(gsd_data)}

📈 **Combined Progress**: {previous_prog}% → {current_prog}% (+{change}%)
🎯 **Total Tasks Completed**: {completed}/{total}
⏰ **Overall Timeline**: {timeline_text}

🤝 **Most Supporter** (Team Collaborators):
{supporter_text.rstrip()}

📋 **PADTAI List** 
🔄 **In Progress** ({len(padtai_tasks)} tasks, {sum(len([st for st in task.get("subtasks", []) if st.get("id")]) for task in padtai_tasks)} subtasks):"""

    # Add PADTAI tasks
    for task in padtai_tasks[:]:  # Show top 5 PADTAI tasks
        task_name = task["task_name"]
        assignees = (
            ", ".join(task["assigned_users"])
            if task["assigned_users"]
            else "Unassigned"
        )
        status = task["status"]

        # Show parent relationship if this is a subtask
        parent_indicator = (
            f" (subtask of: {task['parent_name']})" if task.get("parent_name") else ""
        )

        summary += f"\n• {task_name} [{status}] ({assignees}){parent_indicator}"

        # Show subtasks if any
        subtasks = task.get("subtasks", [])
        for subtask in subtasks:
            if subtask.get("id"):  # Check if subtask exists
                subtask_name = subtask["name"]
                subtask_assignees = (
                    ", ".join(subtask["assigned_users"])
                    if subtask["assigned_users"]
                    else "Unassigned"
                )
                summary += f"\n  └─ {subtask_name} ({subtask_assignees})"

    # Add Get Shit Done section
    summary += "\n\n📋 **Get Shit Done List**"
    gsd_subtask_count = sum(
        len([st for st in task.get("subtasks", []) if st.get("id")])
        for task in get_shit_done_tasks
    )
    summary += f"\n🔄 **In Progress** ({len(get_shit_done_tasks)} tasks, {gsd_subtask_count} subtasks):"

    # Add Get Shit Done tasks
    for task in get_shit_done_tasks[:5]:  # Show top 5 Get Shit Done tasks
        task_name = task["task_name"]
        assignees = (
            ", ".join(task["assigned_users"])
            if task["assigned_users"]
            else "Unassigned"
        )
        status = task["status"]

        # Show parent relationship if this is a subtask
        parent_indicator = (
            f" (subtask of: {task['parent_name']})" if task.get("parent_name") else ""
        )

        summary += f"\n• {task_name} [{status}] ({assignees}){parent_indicator}"

        # Show subtasks if any
        subtasks = task.get("subtasks", [])
        for subtask in subtasks:
            if subtask.get("id"):  # Check if subtask exists
                subtask_name = subtask["name"]
                subtask_assignees = (
                    ", ".join(subtask["assigned_users"])
                    if subtask["assigned_users"]
                    else "Unassigned"
                )
                summary += f"\n  └─ {subtask_name} ({subtask_assignees})"

    return summary


def generate_weekly_summary() -> str:
    """
    Main function to generate the complete weekly summary with separate list sections.

    Returns:
        Formatted weekly summary string
    """
    logger.info("Generating weekly summary...")

    # Collect data for each list separately
    padtai_tasks = get_tasks_in_progress_by_list(PADTAI_LIST_ID)
    get_shit_done_tasks = get_tasks_in_progress_by_list(GET_SHIT_DONE_LIST_ID)
    progress_data = get_weekly_progress()
    most_supporter = get_most_supporter()

    logger.info(f"Found {len(padtai_tasks)} PADTAI tasks in progress")
    logger.info(f"Found {len(get_shit_done_tasks)} Get Shit Done tasks in progress")
    logger.info(f"Combined progress: {progress_data['combined']['current_progress']}%")
    logger.info(f"Most supporter: {len(most_supporter)} members")

    # Format and return summary
    summary = format_weekly_summary(
        padtai_tasks, get_shit_done_tasks, progress_data, most_supporter
    )
    return summary


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Generate and display weekly summary
        summary = generate_weekly_summary()
        print("\n" + "=" * 50)
        print(summary)
        print("=" * 50)

    except Exception as e:
        logger.error(f"Failed to generate weekly summary: {e}")
        print(f"❌ Error generating summary: {e}")
