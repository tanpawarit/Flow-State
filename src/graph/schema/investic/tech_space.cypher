// Investic Team - Tech Space Focused Graph Schema
// Includes only Get Shit Done and PADTAI lists from Tech space

// ============================================
// NODE DEFINITIONS
// ============================================

// Team Node - Investic specific
(:Team {
  id: "investic_team",
  name: "Investic",
  color: "#0066cc",
  avatar: string,
  created_at: datetime
})

// Space Node - Tech space only
(:Space {
  id: "space_investic_tech", 
  name: "Tech",
  color: "#00ff00",
  private: false,
  multiple_assignees: true,
  features: ["due_dates", "time_tracking", "tags", "priorities"]
})

// List Nodes - Only Get Shit Done and PADTAI
(:List {
  id: "901602625750",        // Real ClickUp ID for Get Shit Done
  name: "Get Shit Done",
  status: "active",
  color: "#ff6b6b",
  orderindex: 1,
  task_count: integer,
  space_id: "space_investic_tech"
})

(:List {
  id: "901606939084",        // Real ClickUp ID for PADTAI
  name: "PADTAI", 
  status: "active",
  color: "#4ecdc4",
  orderindex: 2,
  task_count: integer,
  space_id: "space_investic_tech"
})

// Task Node - Enhanced for Investic workflows
(:Task {
  id: string,                // ClickUp task ID
  name: string,              // Task title
  description: string,       // Task description
  text_content: string,      // Plain text content
  status: string,            // Current status
  priority: string,          // Task priority
  points: integer,           // Story points/effort estimation
  due_date: datetime,        // Deadline
  start_date: datetime,      // Start date
  date_created: datetime,    // Creation timestamp
  date_updated: datetime,    // Last update
  date_closed: datetime,     // Completion timestamp
  orderindex: integer,       // Task order in list
  url: string,               // ClickUp task URL
  time_estimate: integer,    // Estimated minutes
  time_spent: integer,       // Actual time tracked
  archived: boolean,         // Archive status
  list_id: string,           // Parent list ID
  space_id: string,          // Parent space ID
  custom_id: string          // Custom task identifier
})

// User Node - Investic team members
(:User {
  id: string,                // ClickUp user ID
  username: string,          // Username
  email: string,             // Email address
  color: string,             // User color in ClickUp
  initials: string,          // User initials
  profile_picture: string,   // Avatar URL
  role: string,              // Team role
  timezone: string,          // User timezone
  last_active: datetime      // Last activity timestamp
})

// Status Node - Task statuses
(:Status {
  id: string,
  status: string,            // TO DO, DEV-IN PROGRESS, REVIEW, COMPLETE
  type: string,              // open, closed, custom
  orderindex: integer,
  color: string
})

// Priority Node - Task priorities  
(:Priority {
  id: string,
  priority: string,          // urgent, high, normal, low
  color: string,
  orderindex: integer
})

// Tag Node - Task categorization
(:Tag {
  id: string,
  name: string,              // backtesting, frontend, api, etc.
  color: string,
  creator: string
})

// Sprint/Milestone Node - Time-boxed iterations
(:Sprint {
  id: string,
  name: string,
  start_date: datetime,
  end_date: datetime,
  goal: string,
  status: string             // planning, active, completed
})

// ============================================
// RELATIONSHIP DEFINITIONS  
// ============================================

// Organizational Hierarchy
(Team)-[:HAS_SPACE]->(Space)
(Space)-[:CONTAINS_LIST]->(List)
(List)-[:CONTAINS_TASK]->(Task)

// Task Assignment & Ownership
(User)-[:ASSIGNED_TO {
  assigned_at: datetime,
  assigned_by: string,
  role: string               // primary, secondary, reviewer
}]->(Task)

(User)-[:CREATED {
  created_at: datetime
}]->(Task)

(User)-[:WATCHING {
  since: datetime,
  notifications: boolean
}]->(Task)

// Task Dependencies & Hierarchy
(Task)-[:DEPENDS_ON {
  type: string,              // blocks, requires, related
  created_at: datetime,
  description: string
}]->(Task)

(Task)-[:SUBTASK_OF]->(Task)

(Task)-[:BLOCKS {
  impact_level: string,      // high, medium, low
  description: string
}]->(Task)

// Status & Metadata
(Task)-[:HAS_STATUS]->(Status)
(Task)-[:HAS_PRIORITY]->(Priority)
(Task)-[:TAGGED_WITH {
  tagged_at: datetime,
  tagged_by: string
}]->(Tag)

// Sprint Management
(Task)-[:IN_SPRINT]->(Sprint)
(Sprint)-[:FOR_LIST]->(List)

// Team & Access Management
(User)-[:MEMBER_OF {
  role: string,              // admin, member, guest
  joined_at: datetime,
  permissions: [string]
}]->(Team)

(User)-[:CAN_ACCESS {
  permission_level: string,  // view, edit, admin
  granted_at: datetime
}]->(List)

// Time Tracking
(User)-[:TRACKED_TIME {
  duration: integer,         // minutes
  start_time: datetime,
  end_time: datetime,
  description: string,
  billable: boolean,
  task_id: string
}]->(Task)

// Comments & Communication
(User)-[:COMMENTED_ON {
  comment_id: string,
  content: string,
  created_at: datetime,
  resolved: boolean
}]->(Task)

// ============================================
// TECH SPACE SPECIFIC ENHANCEMENTS
// ============================================

// Custom Fields for Tech workflows
(:CustomField {
  id: string,
  name: string,              // "Tech Stack", "Environment", "Review Type"
  type: string,              // text, dropdown, number, date
  options: [string],         // for dropdown fields
  required: boolean
})

(Task)-[:HAS_CUSTOM_FIELD {
  field_id: string,
  value: string,
  updated_at: datetime
}]->(CustomField)

// Code Review & QA specific relationships
(User)-[:REVIEWED {
  review_type: string,       // code, design, qa
  status: string,            // approved, changes_requested, rejected
  reviewed_at: datetime,
  comments: string
}]->(Task)

(Task)-[:REQUIRES_REVIEW {
  review_type: [string],     // ["code", "design", "qa"]
  required_reviewers: integer,
  created_at: datetime
}]->(User)

// Environment & Deployment tracking
(:Environment {
  id: string,
  name: string,              // dev, staging, production
  url: string,
  status: string             // active, maintenance, down
})

(Task)-[:DEPLOYED_TO {
  deployed_at: datetime,
  version: string,
  deployed_by: string,
  status: string             // success, failed, rollback
}]->(Environment)