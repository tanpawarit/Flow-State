// Base Constraints and Indexes for Flow-State GraphRAG
// Ensures data integrity and query performance

// ============================================
// UNIQUENESS CONSTRAINTS
// ============================================

// Team constraints
CREATE CONSTRAINT team_id_unique IF NOT EXISTS
FOR (t:Team) REQUIRE t.id IS UNIQUE;

// Space constraints
CREATE CONSTRAINT space_id_unique IF NOT EXISTS
FOR (s:Space) REQUIRE s.id IS UNIQUE;

// List constraints
CREATE CONSTRAINT list_id_unique IF NOT EXISTS
FOR (l:List) REQUIRE l.id IS UNIQUE;

// Folder constraints
CREATE CONSTRAINT folder_id_unique IF NOT EXISTS
FOR (f:Folder) REQUIRE f.id IS UNIQUE;

// Task constraints
CREATE CONSTRAINT task_id_unique IF NOT EXISTS
FOR (t:Task) REQUIRE t.id IS UNIQUE;

// User constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT user_email_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS UNIQUE;

// Status constraints
CREATE CONSTRAINT status_id_unique IF NOT EXISTS
FOR (s:Status) REQUIRE s.id IS UNIQUE;

// Priority constraints
CREATE CONSTRAINT priority_id_unique IF NOT EXISTS
FOR (p:Priority) REQUIRE p.id IS UNIQUE;

// Tag constraints
CREATE CONSTRAINT tag_id_unique IF NOT EXISTS
FOR (t:Tag) REQUIRE t.id IS UNIQUE;

// Sprint constraints
CREATE CONSTRAINT sprint_id_unique IF NOT EXISTS
FOR (s:Sprint) REQUIRE s.id IS UNIQUE;

// Custom Field constraints
CREATE CONSTRAINT custom_field_id_unique IF NOT EXISTS
FOR (cf:CustomField) REQUIRE cf.id IS UNIQUE;

// Comment constraints
CREATE CONSTRAINT comment_id_unique IF NOT EXISTS
FOR (c:Comment) REQUIRE c.id IS UNIQUE;

// Environment constraints
CREATE CONSTRAINT environment_id_unique IF NOT EXISTS
FOR (e:Environment) REQUIRE e.id IS UNIQUE;

// ============================================
// PROPERTY EXISTENCE CONSTRAINTS
// ============================================

// Team required properties
CREATE CONSTRAINT team_name_exists IF NOT EXISTS
FOR (t:Team) REQUIRE t.name IS NOT NULL;

// Space required properties
CREATE CONSTRAINT space_name_exists IF NOT EXISTS
FOR (s:Space) REQUIRE s.name IS NOT NULL;

// List required properties
CREATE CONSTRAINT list_name_exists IF NOT EXISTS
FOR (l:List) REQUIRE l.name IS NOT NULL;

// Task required properties
CREATE CONSTRAINT task_name_exists IF NOT EXISTS
FOR (t:Task) REQUIRE t.name IS NOT NULL;

// User required properties
CREATE CONSTRAINT user_username_exists IF NOT EXISTS
FOR (u:User) REQUIRE u.username IS NOT NULL;

CREATE CONSTRAINT user_email_exists IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS NOT NULL;

// ============================================
// PERFORMANCE INDEXES
// ============================================

// Task indexes for common queries
CREATE INDEX task_status_index IF NOT EXISTS
FOR (t:Task) ON (t.status);

CREATE INDEX task_priority_index IF NOT EXISTS
FOR (t:Task) ON (t.priority);

CREATE INDEX task_due_date_index IF NOT EXISTS
FOR (t:Task) ON (t.due_date);

CREATE INDEX task_list_id_index IF NOT EXISTS
FOR (t:Task) ON (t.list_id);

CREATE INDEX task_space_id_index IF NOT EXISTS
FOR (t:Task) ON (t.space_id);

CREATE INDEX task_created_at_index IF NOT EXISTS
FOR (t:Task) ON (t.date_created);

CREATE INDEX task_updated_at_index IF NOT EXISTS
FOR (t:Task) ON (t.date_updated);

// User indexes
CREATE INDEX user_email_index IF NOT EXISTS
FOR (u:User) ON (u.email);

CREATE INDEX user_username_index IF NOT EXISTS
FOR (u:User) ON (u.username);

CREATE INDEX user_role_index IF NOT EXISTS
FOR (u:User) ON (u.role);

// List indexes
CREATE INDEX list_space_id_index IF NOT EXISTS
FOR (l:List) ON (l.space_id);

CREATE INDEX list_status_index IF NOT EXISTS
FOR (l:List) ON (l.status);

// Space indexes
CREATE INDEX space_name_index IF NOT EXISTS
FOR (s:Space) ON (s.name);

CREATE INDEX space_archived_index IF NOT EXISTS
FOR (s:Space) ON (s.archived);

// Status and Priority indexes
CREATE INDEX status_type_index IF NOT EXISTS
FOR (s:Status) ON (s.type);

CREATE INDEX priority_orderindex_index IF NOT EXISTS
FOR (p:Priority) ON (p.orderindex);

// Time-based indexes for analytics
CREATE INDEX task_date_created_range IF NOT EXISTS
FOR (t:Task) ON (t.date_created);

CREATE INDEX task_date_updated_range IF NOT EXISTS
FOR (t:Task) ON (t.date_updated);

CREATE INDEX task_date_closed_range IF NOT EXISTS
FOR (t:Task) ON (t.date_closed);

// Sprint indexes
CREATE INDEX sprint_status_index IF NOT EXISTS
FOR (s:Sprint) ON (s.status);

CREATE INDEX sprint_start_date_index IF NOT EXISTS
FOR (s:Sprint) ON (s.start_date);

CREATE INDEX sprint_end_date_index IF NOT EXISTS
FOR (s:Sprint) ON (s.end_date);

// Tag indexes
CREATE INDEX tag_name_index IF NOT EXISTS
FOR (t:Tag) ON (t.name);

// ============================================
// COMPOSITE INDEXES (for complex queries)
// ============================================

// Task composite indexes
CREATE INDEX task_list_status_composite IF NOT EXISTS
FOR (t:Task) ON (t.list_id, t.status);

CREATE INDEX task_space_status_composite IF NOT EXISTS
FOR (t:Task) ON (t.space_id, t.status);

CREATE INDEX task_priority_due_date_composite IF NOT EXISTS
FOR (t:Task) ON (t.priority, t.due_date);

// User assignment composite
CREATE INDEX user_team_role_composite IF NOT EXISTS
FOR (u:User) ON (u.team_id, u.role);

// ============================================
// FULL-TEXT SEARCH INDEXES
// ============================================

// Task content search
CREATE FULLTEXT INDEX task_content_search IF NOT EXISTS
FOR (t:Task) ON EACH [t.name, t.description, t.text_content];

// User search
CREATE FULLTEXT INDEX user_search IF NOT EXISTS
FOR (u:User) ON EACH [u.username, u.email];

// Comment search
CREATE FULLTEXT INDEX comment_search IF NOT EXISTS
FOR (c:Comment) ON EACH [c.content];

// Tag search
CREATE FULLTEXT INDEX tag_search IF NOT EXISTS
FOR (t:Tag) ON EACH [t.name];