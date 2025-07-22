#!/usr/bin/env python3
"""
Enhanced verification script with detailed queries
Provides comprehensive analysis of imported data
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase  # noqa: E402

from src.utils.config import get_neo4j_config  # noqa: E402


def run_enhanced_verification():
    """Run comprehensive verification with detailed breakdown"""

    # Get Neo4j configuration
    neo4j_config = get_neo4j_config()
    uri = neo4j_config.get("uri")
    username = neo4j_config.get("username", "neo4j")
    password = neo4j_config.get("password")

    if not all([uri, password]):
        print("❌ Neo4j configuration missing")
        return

    # Type assertion since we've verified values are not None
    assert uri is not None and password is not None
    driver = GraphDatabase.driver(uri, auth=(username, password))

    try:
        with driver.session() as session:
            print("🔍 Enhanced Verification of Investic Tech Space Data")
            print("=" * 70)

            # 1. Overall node counts
            print("\n📊 Overall Node Counts:")
            node_count_query = """
            MATCH (n)
            WHERE (n.id = 'investic_team' OR n.id = '90161158278' OR 
                   n.id IN ['901602625750', '901606939084'] OR
                   n.list_id IN ['901602625750', '901606939084'] OR
                   n.space_id = '90161158278')
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
            """

            result = session.run(node_count_query)
            total_nodes = 0
            for record in result:
                count = record["count"]
                total_nodes += count
                print(f"   {record['node_type']}: {count}")
            print(f"   TOTAL NODES: {total_nodes}")

            # 2. Team and Space structure
            print("\n🏢 Team and Space Structure:")
            structure_query = """
            MATCH (t:Team {id: 'investic_team'})-[:HAS_SPACE]->(s:Space)
            RETURN t.name as team_name, s.name as space_name, s.id as space_id
            """

            result = session.run(structure_query)
            for record in result:
                print(f"   Team: {record['team_name']}")
                print(f"   Space: {record['space_name']} (ID: {record['space_id']})")

            # 3. Detailed Lists Analysis
            print("\n📝 Lists Analysis:")
            lists_query = """
            MATCH (s:Space)-[:CONTAINS_LIST]->(l:List)
            WHERE s.id = '90161158278'
            RETURN l.id as list_id, l.name as list_name, l.task_count as stated_count
            ORDER BY l.name
            """

            result = session.run(lists_query)
            list_data = []
            for record in result:
                list_id = record["list_id"]
                list_name = record["list_name"]
                stated_count = record["stated_count"]

                # Count actual tasks
                actual_count_query = """
                MATCH (l:List {id: $list_id})-[:CONTAINS_TASK]->(t:Task)
                RETURN count(t) as actual_count
                """
                actual_result = session.run(actual_count_query, list_id=list_id)
                actual_record = actual_result.single()
                assert actual_record is not None, f"No result found for list {list_id}"
                actual_count = actual_record["actual_count"]

                list_data.append(
                    {
                        "id": list_id,
                        "name": list_name,
                        "stated": stated_count,
                        "actual": actual_count,
                    }
                )

                print(f"   📋 {list_name} (ID: {list_id})")
                print(f"      Stated task count: {stated_count}")
                print(f"      Actual task count: {actual_count}")
                print(
                    f"      Status: {'✅ Match' if stated_count == actual_count else '⚠️ Mismatch'}"
                )

            # 4. Users with detailed assignments
            print("\n👥 Users and Assignments:")
            users_query = """
            MATCH (u:User)
            WHERE u.id IS NOT NULL
            RETURN u.id as user_id, u.username as username, u.email as email, u.initials as initials
            ORDER BY u.username
            """

            result = session.run(users_query)
            user_assignments = []

            for record in result:
                user_id = record["user_id"]
                username = record["username"]
                initials = record["initials"]

                # Count assignments per list
                assignments_query = """
                MATCH (u:User {id: $user_id})-[:ASSIGNED_TO]->(t:Task)
                WHERE t.list_id IN ['901602625750', '901606939084']
                RETURN t.list_id as list_id, count(t) as task_count
                ORDER BY list_id
                """

                assignments_result = session.run(assignments_query, user_id=user_id)

                get_shit_done_tasks = 0
                padtai_tasks = 0
                total_tasks = 0

                for assign_record in assignments_result:
                    list_id = assign_record["list_id"]
                    count = assign_record["task_count"]
                    total_tasks += count

                    if list_id == "901602625750":  # Get Shit Done
                        get_shit_done_tasks = count
                    elif list_id == "901606939084":  # PADTAI
                        padtai_tasks = count

                user_assignments.append(
                    {
                        "username": username,
                        "initials": initials,
                        "get_shit_done": get_shit_done_tasks,
                        "padtai": padtai_tasks,
                        "total": total_tasks,
                    }
                )

                print(f"   👤 {username} ({initials})")
                print(f"      Get Shit Done: {get_shit_done_tasks} tasks")
                print(f"      PADTAI: {padtai_tasks} tasks")
                print(f"      Total: {total_tasks} tasks")

            # 5. Task status breakdown per list
            print("\n📋 Task Status Breakdown:")

            for list_info in list_data:
                list_id = list_info["id"]
                list_name = list_info["name"]

                print(f"\n   📝 {list_name}:")

                status_query = """
                MATCH (t:Task)
                WHERE t.list_id = $list_id
                RETURN t.status as status, count(t) as count
                ORDER BY count DESC
                """

                status_result = session.run(status_query, list_id=list_id)

                for status_record in status_result:
                    status = status_record["status"] or "No Status"
                    count = status_record["count"]
                    print(f"      {status}: {count} tasks")

            # 6. Priority distribution per list
            print("\n⭐ Priority Distribution:")

            for list_info in list_data:
                list_id = list_info["id"]
                list_name = list_info["name"]

                print(f"\n   📝 {list_name}:")

                priority_query = """
                MATCH (t:Task)
                WHERE t.list_id = $list_id
                RETURN t.priority as priority, count(t) as count
                ORDER BY count DESC
                """

                priority_result = session.run(priority_query, list_id=list_id)

                for priority_record in priority_result:
                    priority = priority_record["priority"] or "No Priority"
                    count = priority_record["count"]
                    print(f"      {priority}: {count} tasks")

            # 7. Relationship verification
            print("\n🔗 Relationship Verification:")
            relationships_query = """
            MATCH ()-[r]->()
            WHERE (startNode(r).id = 'investic_team' OR startNode(r).id = '90161158278' OR 
                   startNode(r).id IN ['901602625750', '901606939084'] OR
                   startNode(r).list_id IN ['901602625750', '901606939084'] OR
                   startNode(r).space_id = '90161158278' OR
                   endNode(r).id = 'investic_team' OR endNode(r).id = '90161158278' OR 
                   endNode(r).id IN ['901602625750', '901606939084'] OR
                   endNode(r).list_id IN ['901602625750', '901606939084'] OR
                   endNode(r).space_id = '90161158278')
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """

            result = session.run(relationships_query)
            total_relationships = 0
            for record in result:
                count = record["count"]
                total_relationships += count
                print(f"   {record['relationship_type']}: {count}")
            print(f"   TOTAL RELATIONSHIPS: {total_relationships}")

            # 8. Data quality summary
            print("\n✅ Data Quality Summary:")
            print("=" * 40)

            # Check for any issues
            issues = []

            for list_info in list_data:
                if list_info["stated"] != list_info["actual"]:
                    issues.append(
                        f"List {list_info['name']}: stated count ({list_info['stated']}) != actual count ({list_info['actual']})"
                    )

            total_assignments = sum(user["total"] for user in user_assignments)

            print(f"   📊 Total Users: {len(user_assignments)}")
            print(
                f"   📊 Total Tasks: {sum(list_info['actual'] for list_info in list_data)}"
            )
            print(f"   📊 Total Assignments: {total_assignments}")
            print(
                f"   📊 Data Integrity: {'✅ Excellent' if not issues else '⚠️ Minor Issues'}"
            )

            if issues:
                print("\n   ⚠️ Issues Found:")
                for issue in issues:
                    print(f"      - {issue}")

            # 9. Top contributors summary
            print("\n🏆 Top Contributors:")
            sorted_users = sorted(
                user_assignments, key=lambda x: x["total"], reverse=True
            )

            for i, user in enumerate(sorted_users[:5], 1):
                print(f"   {i}. {user['username']}: {user['total']} total tasks")
                print(
                    f"      └─ Get Shit Done: {user['get_shit_done']}, PADTAI: {user['padtai']}"
                )

            print("\n✅ Enhanced verification completed successfully!")

    except Exception as e:
        print(f"❌ Enhanced verification failed: {e}")
        raise

    finally:
        driver.close()


if __name__ == "__main__":
    run_enhanced_verification()
