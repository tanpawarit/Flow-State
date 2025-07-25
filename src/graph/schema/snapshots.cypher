// Snapshot Schema for Flow-State GraphRAG
// Defines nodes and relationships for tracking historical progress snapshots

// ProgressSnapshot Node - Tracks weekly progress for lists
(:ProgressSnapshot {
  id: string,               // Unique snapshot ID (format: snapshot_<list_id>_<date>)
  snapshot_date: date,      // Date when snapshot was taken
  week_ending: date,        // End date of the week being tracked
  total_tasks: integer,     // Total number of tasks in the list
  completed_tasks: integer, // Number of completed tasks
  in_progress_tasks: integer, // Number of in-progress tasks
  progress_percentage: float, // Percentage of completion (0-100)
  created_at: datetime,     // When the snapshot was created
  updated_at: datetime      // When the snapshot was last updated
})

// Relationships
// List to ProgressSnapshot (one-to-many)
(List)-[:HAS_SNAPSHOT {
  created_at: datetime      // When the snapshot relationship was created
}]->(ProgressSnapshot)

// Indexes for faster lookups
CREATE INDEX progress_snapshot_id IF NOT EXISTS FOR (ps:ProgressSnapshot) ON (ps.id);
CREATE INDEX progress_snapshot_week_ending IF NOT EXISTS FOR (ps:ProgressSnapshot) ON (ps.week_ending);
CREATE INDEX progress_snapshot_list_id IF NOT EXISTS FOR (ps:ProgressSnapshot) ON (ps.list_id);

// Constraints to ensure data integrity
CREATE CONSTRAINT progress_snapshot_id_unique IF NOT EXISTS 
FOR (ps:ProgressSnapshot) REQUIRE ps.id IS UNIQUE;

// Optional: Materialized view for faster historical progress queries
// This can be implemented as a scheduled procedure in a production environment
