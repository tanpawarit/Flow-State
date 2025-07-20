// Base Relationship Definitions for Flow-State GraphRAG
// Common relationships used across all team spaces

// ============================================
// ORGANIZATIONAL HIERARCHY
// ============================================

// Team structure
(Team)-[:HAS_SPACE {
  created_at: datetime
}]->(Space)

(Space)-[:CONTAINS_LIST {
  created_at: datetime
}]->(List)

(Space)-[:CONTAINS_FOLDER {
  created_at: datetime
}]->(Folder)

(Folder)-[:CONTAINS_LIST {
  created_at: datetime
}]->(List)

(List)-[:CONTAINS_TASK {
  created_at: datetime
}]->(Task)

// ============================================
// TASK ASSIGNMENT & OWNERSHIP
// ============================================

// User assignments
(User)-[:ASSIGNED_TO {
  assigned_at: datetime,
  assigned_by: string,
  role: string              // primary, secondary, reviewer
}]->(Task)

(User)-[:CREATED {
  created_at: datetime
}]->(Task)

(User)-[:WATCHING {
  since: datetime,
  notifications: boolean
}]->(Task)

(User)-[:OWNS {
  since: datetime
}]->(List)

// ============================================
// TASK DEPENDENCIES & HIERARCHY
// ============================================

// Task relationships
(Task)-[:DEPENDS_ON {
  type: string,             // blocks, requires, related
  created_at: datetime,
  description: string,
  impact_level: string      // high, medium, low
}]->(Task)

(Task)-[:SUBTASK_OF {
  created_at: datetime
}]->(Task)

(Task)-[:BLOCKS {
  impact_level: string,     // high, medium, low
  description: string,
  created_at: datetime
}]->(Task)

(Task)-[:RELATED_TO {
  relationship_type: string, // duplicate, similar, reference
  created_at: datetime,
  description: string
}]->(Task)

// ============================================
// STATUS & METADATA
// ============================================

// Task attributes
(Task)-[:HAS_STATUS {
  set_at: datetime,
  set_by: string
}]->(Status)

(Task)-[:HAS_PRIORITY {
  set_at: datetime,
  set_by: string
}]->(Priority)

(Task)-[:TAGGED_WITH {
  tagged_at: datetime,
  tagged_by: string
}]->(Tag)

(Task)-[:HAS_CUSTOM_FIELD {
  field_id: string,
  value: string,
  updated_at: datetime
}]->(CustomField)

// ============================================
// SPRINT & ITERATION MANAGEMENT
// ============================================

// Sprint relationships
(Task)-[:IN_SPRINT {
  added_at: datetime,
  points: integer
}]->(Sprint)

(Sprint)-[:FOR_SPACE {
  created_at: datetime
}]->(Space)

(Sprint)-[:FOR_LIST {
  created_at: datetime
}]->(List)

// ============================================
// TEAM & ACCESS MANAGEMENT
// ============================================

// Team membership
(User)-[:MEMBER_OF {
  role: string,             // admin, member, guest
  joined_at: datetime,
  permissions: [string]
}]->(Team)

(User)-[:MEMBER_OF {
  role: string,             // admin, member, guest
  joined_at: datetime,
  permissions: [string]
}]->(Space)

(User)-[:CAN_ACCESS {
  permission_level: string, // view, edit, admin
  granted_at: datetime,
  granted_by: string
}]->(List)

// ============================================
// TIME TRACKING & PRODUCTIVITY
// ============================================

// Time tracking
(User)-[:TRACKED_TIME {
  duration: integer,        // minutes
  start_time: datetime,
  end_time: datetime,
  description: string,
  billable: boolean,
  date: date
}]->(Task)

// Work sessions
(User)-[:WORKED_ON {
  start_time: datetime,
  end_time: datetime,
  focus_score: float,       // 0.0 - 1.0
  interruptions: integer
}]->(Task)

// ============================================
// COMMUNICATION & COLLABORATION
// ============================================

// Comments and discussions
(User)-[:COMMENTED_ON {
  comment_id: string,
  content: string,
  created_at: datetime,
  resolved: boolean,
  reply_to: string          // parent comment ID
}]->(Task)

(User)-[:MENTIONED_IN {
  comment_id: string,
  mentioned_at: datetime
}]->(Comment)

// Reviews and approvals
(User)-[:REVIEWED {
  review_type: string,      // code, design, qa, content
  status: string,           // approved, changes_requested, rejected
  reviewed_at: datetime,
  comments: string,
  score: integer            // 1-5 rating
}]->(Task)

(Task)-[:REQUIRES_REVIEW {
  review_type: [string],    // required review types
  required_reviewers: integer,
  created_at: datetime
}]->(User)

// ============================================
// WORKFLOW & AUTOMATION
// ============================================

// Status transitions
(Status)-[:TRANSITIONS_TO {
  created_at: datetime,
  automated: boolean,
  conditions: [string]
}]->(Status)

// Automation rules
(Task)-[:TRIGGERS_AUTOMATION {
  rule_id: string,
  triggered_at: datetime,
  action: string
}]->(Task)

// ============================================
// DEVELOPMENT & DEPLOYMENT
// ============================================

// Environment deployments
(Task)-[:DEPLOYED_TO {
  deployed_at: datetime,
  version: string,
  deployed_by: string,
  status: string,           // success, failed, rollback
  commit_hash: string
}]->(Environment)

// Code commits (if integrated with git)
(User)-[:COMMITTED {
  commit_hash: string,
  commit_message: string,
  committed_at: datetime,
  lines_added: integer,
  lines_removed: integer
}]->(Task)

// ============================================
// ANALYTICS & INSIGHTS
// ============================================

// Performance metrics
(Task)-[:HAS_METRIC {
  metric_name: string,
  value: float,
  measured_at: datetime,
  unit: string
}]->(Task)

// Bottleneck identification
(Task)-[:CREATES_BOTTLENECK {
  detected_at: datetime,
  severity: string,         // high, medium, low
  impact_tasks: [string],   // affected task IDs
  reason: string
}]->(Task)

// Learning and improvement
(User)-[:LEARNED_FROM {
  lesson: string,
  learned_at: datetime,
  category: string          // technical, process, communication
}]->(Task)