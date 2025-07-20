from neo4j import GraphDatabase


class FlowStateGraph:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_user_tasks(self, username):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {username: $username})-[:ASSIGNED_TO]->(t:Task)
                RETURN t.name as task_name, t.status as status, t.points as points
            """,
                username=username,
            )
            return [record for record in result]

    def create_task(
        self, task_id, name, status="DEV-IN PROGRESS", priority="Medium", points=1
    ):
        with self.driver.session() as session:
            session.run(
                """
                CREATE (t:Task {
                    id: $task_id,
                    name: $name,
                    status: $status,
                    priority: $priority,
                    points: $points,
                    created_at: datetime()
                })
            """,
                task_id=task_id,
                name=name,
                status=status,
                priority=priority,
                points=points,
            )

    def create_investic_workspace(self):
        with self.driver.session() as session:
            session.run("""
                CREATE 
                // Spaces for Investic team
                (lab:Space {id: "space_investic_lab", name: "Lab", color: "#0066ff", private: false}),
                (academy:Space {id: "space_investic_academy", name: "Academy", color: "#9900ff", private: false}),
                (tech:Space {id: "space_investic_tech", name: "Tech", color: "#00ff00", private: false}),
                
                // Lists in Tech Space (using real ClickUp IDs)
                (gsd:List {id: "901602625750", name: "Get Shit Done", status: "active", color: "#ff6b6b"}),
                (padtai:List {id: "901606939084", name: "PADTAI", status: "active", color: "#4ecdc4"}),
                (calendar:List {id: "901603254693", name: "calendar business", status: "active", color: "#45b7d1"}),
                
                // Common Statuses
                (complete:Status {id: "status_complete", status: "COMPLETE", type: "closed", color: "#00ff00", orderindex: 1}),
                (review:Status {id: "status_review", status: "REVIEW", type: "open", color: "#ff9900", orderindex: 2}),
                (dev:Status {id: "status_dev", status: "DEV-IN PROGRESS", type: "open", color: "#0066ff", orderindex: 3}),
                (todo:Status {id: "status_todo", status: "TO DO", type: "open", color: "#cccccc", orderindex: 4}),
                
                // Common Priorities
                (urgent:Priority {id: "priority_urgent", priority: "Urgent", color: "#ff0066", orderindex: 1}),
                (high:Priority {id: "priority_high", priority: "High", color: "#ff0000", orderindex: 2}),
                (medium:Priority {id: "priority_medium", priority: "Medium", color: "#ffaa00", orderindex: 3}),
                (low:Priority {id: "priority_low", priority: "Low", color: "#cccccc", orderindex: 4}),
                
                // Sample Users for Investic team
                (user1:User {id: "user_investic_1", username: "Alex", email: "alex@investic.com", initials: "AL"}),
                (user2:User {id: "user_investic_2", username: "Sarah", email: "sarah@investic.com", initials: "SA"}),
                (user3:User {id: "user_investic_3", username: "Mike", email: "mike@investic.com", initials: "MI"}),
                
                // Sample Tasks with name, assignee, and due date
                (task1:Task {
                    id: "task_investic_001",
                    name: "Setup Authentication System",
                    description: "Implement user login and registration",
                    status: "DEV-IN PROGRESS",
                    priority: "High",
                    points: 8,
                    due_date: datetime("2024-08-01T17:00:00"),
                    start_date: datetime("2024-07-15T09:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                (task2:Task {
                    id: "task_investic_002", 
                    name: "Database Schema Design",
                    description: "Design and implement core database structure",
                    status: "REVIEW",
                    priority: "Urgent", 
                    points: 5,
                    due_date: datetime("2024-07-25T12:00:00"),
                    start_date: datetime("2024-07-20T10:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                (task3:Task {
                    id: "task_investic_003",
                    name: "Frontend Dashboard UI",
                    description: "Create responsive dashboard interface",
                    status: "TO DO",
                    priority: "Medium",
                    points: 13,
                    due_date: datetime("2024-08-10T16:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                
                // Subtasks for Authentication System (task1)
                (subtask1:Task {
                    id: "task_investic_001_1",
                    name: "User Registration API",
                    description: "Create user registration endpoint",
                    status: "COMPLETE",
                    priority: "Urgent",
                    points: 3,
                    due_date: datetime("2024-07-28T15:00:00"),
                    start_date: datetime("2024-07-15T09:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                (subtask2:Task {
                    id: "task_investic_001_2", 
                    name: "Login Authentication",
                    description: "Implement JWT token authentication",
                    status: "DEV-IN PROGRESS",
                    priority: "High",
                    points: 5,
                    due_date: datetime("2024-07-30T17:00:00"),
                    start_date: datetime("2024-07-25T10:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                
                // Subtasks for Frontend Dashboard (task3)
                (subtask3:Task {
                    id: "task_investic_003_1",
                    name: "Dashboard Layout Design",
                    description: "Create wireframes and basic layout",
                    status: "TO DO", 
                    priority: "Medium",
                    points: 5,
                    due_date: datetime("2024-08-05T12:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                (subtask4:Task {
                    id: "task_investic_003_2",
                    name: "Data Visualization Components",
                    description: "Build charts and graphs components",
                    status: "TO DO",
                    priority: "Low", 
                    points: 8,
                    due_date: datetime("2024-08-08T16:00:00"),
                    created_at: datetime(),
                    updated_at: datetime()
                }),
                
                // Relationships: Lists belong to Tech space
                (gsd)-[:IN_SPACE]->(tech),
                (padtai)-[:IN_SPACE]->(tech),
                (calendar)-[:IN_SPACE]->(tech),
                
                // Task assignments (User assigned to Task)
                (user1)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(task1),
                (user2)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(task2),
                (user3)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(task3),
                
                // Subtask assignments (different assignees)
                (user2)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(subtask1), // Sarah
                (user3)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(subtask2), // Mike
                (user1)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(subtask3), // Alex
                (user2)-[:ASSIGNED_TO {assigned_at: datetime(), assigned_by: "PM"}]->(subtask4), // Sarah
                
                // Task belongs to Lists
                (task1)-[:BELONGS_TO]->(gsd),
                (task2)-[:BELONGS_TO]->(padtai), 
                (task3)-[:BELONGS_TO]->(gsd),
                
                // Task has status and priority
                (task1)-[:HAS_STATUS]->(dev),
                (task2)-[:HAS_STATUS]->(review),
                (task3)-[:HAS_STATUS]->(todo),
                (task1)-[:HAS_PRIORITY]->(high),
                (task2)-[:HAS_PRIORITY]->(urgent),
                (task3)-[:HAS_PRIORITY]->(medium),
                
                // Subtask relationships - SUBTASK_OF parent tasks
                (subtask1)-[:SUBTASK_OF]->(task1),
                (subtask2)-[:SUBTASK_OF]->(task1),
                (subtask3)-[:SUBTASK_OF]->(task3),
                (subtask4)-[:SUBTASK_OF]->(task3),
                
                // Subtasks have their own status and priority
                (subtask1)-[:HAS_STATUS]->(complete),  // User Registration API - COMPLETE
                (subtask2)-[:HAS_STATUS]->(dev),       // Login Authentication - DEV-IN PROGRESS
                (subtask3)-[:HAS_STATUS]->(todo),      // Dashboard Layout Design - TO DO
                (subtask4)-[:HAS_STATUS]->(todo),      // Data Visualization - TO DO
                (subtask1)-[:HAS_PRIORITY]->(urgent),  // User Registration API - Urgent
                (subtask2)-[:HAS_PRIORITY]->(high),    // Login Authentication - High
                (subtask3)-[:HAS_PRIORITY]->(medium),  // Dashboard Layout Design - Medium
                (subtask4)-[:HAS_PRIORITY]->(low)      // Data Visualization - Low
            """)

    def get_investic_structure(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Space)
                OPTIONAL MATCH (s)<-[:IN_SPACE]-(l:List)
                RETURN s.name as space_name, s.id as space_id, 
                       collect({name: l.name, id: l.id}) as lists
                ORDER BY s.name
            """)
            return [record for record in result]

    def get_workspace_stats(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Space)
                OPTIONAL MATCH (s)<-[:IN_SPACE]-(l:List)
                OPTIONAL MATCH (l)<-[:BELONGS_TO]-(t:Task)
                RETURN 
                    count(DISTINCT s) as spaces_count,
                    count(DISTINCT l) as lists_count, 
                    count(DISTINCT t) as tasks_count
            """)
            return result.single()

    def get_tasks_with_assignees(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Task)
                WHERE NOT (t)-[:SUBTASK_OF]->()  // Only parent tasks, not subtasks
                OPTIONAL MATCH (u:User)-[:ASSIGNED_TO]->(t)
                OPTIONAL MATCH (t)-[:HAS_STATUS]->(s:Status)
                OPTIONAL MATCH (t)-[:HAS_PRIORITY]->(p:Priority)
                RETURN 
                    t.name as task_name,
                    t.due_date as due_date,
                    u.username as assignee,
                    s.status as status,
                    p.priority as priority,
                    t.points as points
                ORDER BY t.due_date
            """)
            return [record for record in result]

    def get_task_hierarchy(self):
        """Get tasks with their subtasks"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (parent:Task)
                WHERE NOT (parent)-[:SUBTASK_OF]->()  // Only parent tasks
                OPTIONAL MATCH (u:User)-[:ASSIGNED_TO]->(parent)
                OPTIONAL MATCH (parent)-[:HAS_STATUS]->(s:Status)
                OPTIONAL MATCH (parent)-[:HAS_PRIORITY]->(p:Priority)
                OPTIONAL MATCH (subtask:Task)-[:SUBTASK_OF]->(parent)
                OPTIONAL MATCH (su:User)-[:ASSIGNED_TO]->(subtask)
                OPTIONAL MATCH (subtask)-[:HAS_STATUS]->(ss:Status)
                OPTIONAL MATCH (subtask)-[:HAS_PRIORITY]->(sp:Priority)
                RETURN 
                    parent.name as parent_name,
                    parent.due_date as parent_due_date,
                    u.username as parent_assignee,
                    s.status as parent_status,
                    p.priority as parent_priority,
                    collect({
                        name: subtask.name,
                        assignee: su.username,
                        due_date: subtask.due_date,
                        status: ss.status,
                        priority: sp.priority,
                        points: subtask.points
                    }) as subtasks
                ORDER BY parent.due_date
            """)
            return [record for record in result]

    def get_task_progress(self, parent_task_id):
        """Calculate progress of parent task based on subtasks"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (parent:Task {id: $parent_task_id})
                OPTIONAL MATCH (subtask:Task)-[:SUBTASK_OF]->(parent)
                OPTIONAL MATCH (subtask)-[:HAS_STATUS]->(s:Status)
                WITH parent, 
                     count(subtask) as total_subtasks,
                     count(CASE WHEN s.status = "COMPLETE" THEN 1 END) as completed_subtasks,
                     sum(subtask.points) as total_points,
                     sum(CASE WHEN s.status = "COMPLETE" THEN subtask.points ELSE 0 END) as completed_points
                RETURN 
                    parent.name as task_name,
                    total_subtasks,
                    completed_subtasks,
                    CASE 
                        WHEN total_subtasks > 0 THEN (completed_subtasks * 100 / total_subtasks)
                        ELSE 0 
                    END as progress_percentage,
                    total_points,
                    completed_points,
                    CASE 
                        WHEN total_points > 0 THEN (completed_points * 100 / total_points)
                        ELSE 0 
                    END as points_progress_percentage
            """,
                parent_task_id=parent_task_id,
            )
            return result.single()


# if __name__ == "__main__":
#     graph = FlowStateGraph()

#     # Create Investic workspace
#     graph.create_investic_workspace()
#     print("✅ Investic workspace created!")

#     # Display workspace structure
#     structure = graph.get_investic_structure()
#     print("\n📊 Workspace Structure:")
#     for record in structure:
#         space_name = record["space_name"]
#         lists = record["lists"]
#         print(f"🌌 Space: {space_name}")
#         if lists and lists[0]["name"]:  # Check if lists exist
#             for list_item in lists:
#                 print(f"   📝 List: {list_item['name']} (ID: {list_item['id']})")
#         else:
#             print("   (No lists)")

#     # Display stats
#     stats = graph.get_workspace_stats()
#     print(
#         f"\n📈 Stats: {stats['spaces_count']} spaces, {stats['lists_count']} lists, {stats['tasks_count']} tasks"
#     )

#     # Display task hierarchy with subtasks
#     hierarchy = graph.get_task_hierarchy()
#     print("\n📋 Task Hierarchy with Subtasks:")
#     for task in hierarchy:
#         parent_due = (
#             task["parent_due_date"].strftime("%Y-%m-%d %H:%M")
#             if task["parent_due_date"]
#             else "No due date"
#         )
#         parent_assignee = task["parent_assignee"] or "Unassigned"
#         print(f"\n🎯 {task['parent_name']}")
#         print(f"   👤 Assignee: {parent_assignee}")
#         print(f"   📅 Due: {parent_due}")
#         print(
#             f"   📊 Status: {task['parent_status']} | Priority: {task['parent_priority']}"
#         )

#         # Show subtasks if they exist
#         if task["subtasks"] and task["subtasks"][0]["name"]:
#             print("   📝 Subtasks:")
#             for subtask in task["subtasks"]:
#                 if subtask["name"]:  # Only show actual subtasks
#                     sub_due = (
#                         subtask["due_date"].strftime("%Y-%m-%d %H:%M")
#                         if subtask["due_date"]
#                         else "No due date"
#                     )
#                     sub_assignee = subtask["assignee"] or "Unassigned"
#                     print(f"      ├─ {subtask['name']}")
#                     print(f"      │  👤 {sub_assignee} | 📅 {sub_due}")
#                     print(
#                         f"      │  📊 {subtask['status']} | {subtask['priority']} | {subtask['points']} pts"
#                     )
#         else:
#             print("   📝 No subtasks")

#     # Show progress for tasks with subtasks
#     print("\n📈 Task Progress:")
#     for task_id in ["task_investic_001", "task_investic_003"]:
#         progress = graph.get_task_progress(task_id)
#         if progress and progress["total_subtasks"] > 0:
#             print(f"🎯 {progress['task_name']}")
#             print(
#                 f"   📊 Progress: {progress['completed_subtasks']}/{progress['total_subtasks']} subtasks ({progress['progress_percentage']:.1f}%)"
#             )
#             print(
#                 f"   🔢 Points: {progress['completed_points']}/{progress['total_points']} ({progress['points_progress_percentage']:.1f}%)"
#             )

#     graph.close()
