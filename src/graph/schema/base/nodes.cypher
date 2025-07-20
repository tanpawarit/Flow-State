// Base Node Definitions for Flow-State GraphRAG
// Common nodes used across all team spaces

// Team Node - Root organization entity
(:Team {
  id: string,           // Unique team identifier
  name: string,         // Team name (e.g., "Investic")
  color: string,        // Team color theme
  avatar: string,       // Team avatar URL
  created_at: datetime, // Team creation timestamp
  updated_at: datetime  // Last update timestamp
})

// Space Node - Workspace/project space
(:Space {
  id: string,           // ClickUp space ID
  name: string,         // Space name (e.g., "Tech", "Lab", "Academy")
  color: string,        // Space color
  private: boolean,     // Private space flag
  avatar: string,       // Space avatar URL
  multiple_assignees: boolean, // Allow multiple assignees
  features: [string],   // Enabled features array
  archived: boolean,    // Archive status
  created_at: datetime,
  updated_at: datetime
})

// List Node - Task list/project container
(:List {
  id: string,           // ClickUp list ID
  name: string,         // List name
  orderindex: integer,  // Display order
  content: string,      // List description
  status: string,       // active, archived
  priority: integer,    // Default priority
  assignee: string,     // Default assignee ID
  due_date: datetime,   // List deadline
  start_date: datetime, // List start date
  color: string,        // List color
  avatar: string,       // List avatar
  task_count: integer,  // Number of tasks
  space_id: string,     // Parent space ID
  created_at: datetime,
  updated_at: datetime
})

// Folder Node - List grouping (optional)
(:Folder {
  id: string,           // ClickUp folder ID
  name: string,         // Folder name
  orderindex: integer,  // Display order
  override_statuses: boolean, // Custom status override
  hidden: boolean,      // Hidden folder flag
  space_id: string,     // Parent space ID
  task_count: integer,  // Total tasks in folder
  created_at: datetime,
  updated_at: datetime
})

// Task Node - Core work item
(:Task {
  id: string,           // ClickUp task ID
  name: string,         // Task title
  description: string,  // Task description
  text_content: string, // Plain text content
  status: string,       // Current status
  priority: string,     // Task priority
  points: integer,      // Story points/effort
  due_date: datetime,   // Task deadline
  start_date: datetime, // Task start date
  date_created: datetime, // Creation timestamp
  date_updated: datetime, // Last update
  date_closed: datetime,  // Completion timestamp
  date_done: datetime,    // Done timestamp
  orderindex: integer,    // Task order
  url: string,           // ClickUp task URL
  custom_id: string,     // Custom task ID
  time_estimate: integer, // Estimated minutes
  time_spent: integer,   // Actual time tracked
  archived: boolean,     // Archive status
  list_id: string,       // Parent list ID
  folder_id: string,     // Parent folder ID (optional)
  space_id: string,      // Parent space ID
  team_id: string,       // Parent team ID
  created_at: datetime,
  updated_at: datetime
})

// User Node - Team member
(:User {
  id: string,           // ClickUp user ID
  username: string,     // User display name
  email: string,        // User email
  color: string,        // User color theme
  initials: string,     // User initials
  profile_picture: string, // Avatar URL
  role: string,         // Team role (admin, member, guest)
  timezone: string,     // User timezone
  last_active: datetime, // Last activity timestamp
  created_at: datetime,
  updated_at: datetime
})

// Status Node - Task status definition
(:Status {
  id: string,           // Status ID
  status: string,       // Status name (TO DO, IN PROGRESS, COMPLETE, etc.)
  type: string,         // open, closed, custom
  orderindex: integer,  // Display order
  color: string,        // Status color
  created_at: datetime,
  updated_at: datetime
})

// Priority Node - Task priority definition
(:Priority {
  id: string,           // Priority ID
  priority: string,     // Priority name (urgent, high, normal, low)
  color: string,        // Priority color
  orderindex: integer,  // Display order
  created_at: datetime,
  updated_at: datetime
})

// Tag Node - Task categorization
(:Tag {
  id: string,           // Tag ID
  name: string,         // Tag name
  color: string,        // Tag color
  creator: string,      // Creator user ID
  created_at: datetime,
  updated_at: datetime
})

// Sprint Node - Time-boxed iteration
(:Sprint {
  id: string,           // Sprint ID
  name: string,         // Sprint name
  start_date: datetime, // Sprint start
  end_date: datetime,   // Sprint end
  goal: string,         // Sprint goal/objective
  status: string,       // planning, active, completed
  points_committed: integer, // Committed story points
  points_completed: integer, // Completed story points
  created_at: datetime,
  updated_at: datetime
})

// Custom Field Node - Dynamic field definitions
(:CustomField {
  id: string,           // Field ID
  name: string,         // Field name
  type: string,         // text, dropdown, number, date, etc.
  options: [string],    // Options for dropdown fields
  required: boolean,    // Required field flag
  created_at: datetime,
  updated_at: datetime
})

// Comment Node - Task discussions
(:Comment {
  id: string,           // Comment ID
  content: string,      // Comment text
  resolved: boolean,    // Resolution status
  date: datetime,       // Comment timestamp
  created_at: datetime,
  updated_at: datetime
})

// Environment Node - Deployment environments
(:Environment {
  id: string,           // Environment ID
  name: string,         // Environment name (dev, staging, prod)
  url: string,          // Environment URL
  status: string,       // active, maintenance, down
  created_at: datetime,
  updated_at: datetime
})