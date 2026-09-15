-- Cross-department work graph used by the public collaboration console.
-- Apply through a reviewed database migration.

CREATE TABLE IF NOT EXISTS departments (
  department_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  department_code text UNIQUE NOT NULL,
  department_name text NOT NULL,
  mission text NOT NULL,
  service_tier text NOT NULL DEFAULT 'STANDARD',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stakeholder_profiles (
  stakeholder_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  stakeholder_type text NOT NULL CHECK (stakeholder_type IN ('ENGINEERING','PRODUCT','RISK','COMPLIANCE','FINANCE','OPERATIONS','EXECUTIVE','SHAREHOLDER','CUSTOMER_SUCCESS','DATA_SCIENCE')),
  display_name text NOT NULL,
  department_id uuid REFERENCES departments(department_id),
  objective_weights jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS work_items (
  work_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_key text UNIQUE NOT NULL,
  title text NOT NULL,
  description text NOT NULL,
  work_type text NOT NULL CHECK (work_type IN ('EPIC','STORY','TASK','BUG','INCIDENT','RISK','MODEL','DATA_CONTRACT')),
  status text NOT NULL DEFAULT 'BACKLOG' CHECK (status IN ('BACKLOG','READY','IN_PROGRESS','BLOCKED','REVIEW','DONE','CANCELLED')),
  priority text NOT NULL DEFAULT 'P2' CHECK (priority IN ('P0','P1','P2','P3','P4')),
  requester_department_id uuid REFERENCES departments(department_id),
  owner_department_id uuid REFERENCES departments(department_id),
  owner_name text,
  application_id text,
  pipeline_component text,
  source_ref text,
  due_at timestamptz,
  estimated_hours numeric(10,2),
  business_value numeric(12,4) NOT NULL DEFAULT 0,
  risk_reduction numeric(12,4) NOT NULL DEFAULT 0,
  urgency_score numeric(12,4) NOT NULL DEFAULT 0,
  effort_score numeric(12,4) NOT NULL DEFAULT 1,
  recommendation_score numeric(12,4) GENERATED ALWAYS AS ((business_value + risk_reduction + urgency_score) / GREATEST(effort_score, 0.25)) STORED,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_work_items_status_priority ON work_items(status, priority);
CREATE INDEX IF NOT EXISTS idx_work_items_owner_department ON work_items(owner_department_id, status);
CREATE INDEX IF NOT EXISTS idx_work_items_recommendation_score ON work_items(recommendation_score DESC);

CREATE TABLE IF NOT EXISTS work_item_dependencies (
  work_item_id uuid NOT NULL REFERENCES work_items(work_item_id) ON DELETE CASCADE,
  depends_on_work_item_id uuid NOT NULL REFERENCES work_items(work_item_id) ON DELETE CASCADE,
  dependency_type text NOT NULL DEFAULT 'BLOCKS' CHECK (dependency_type IN ('BLOCKS','RELATES_TO','DUPLICATES','REQUIRES_DATA_FROM')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(work_item_id, depends_on_work_item_id)
);

CREATE TABLE IF NOT EXISTS work_item_events (
  event_id bigserial PRIMARY KEY,
  work_item_id uuid NOT NULL REFERENCES work_items(work_item_id) ON DELETE CASCADE,
  event_type text NOT NULL,
  actor text NOT NULL,
  from_value text,
  to_value text,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS work_item_comments (
  comment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  work_item_id uuid NOT NULL REFERENCES work_items(work_item_id) ON DELETE CASCADE,
  author text NOT NULL,
  department_id uuid REFERENCES departments(department_id),
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS department_recommendations (
  recommendation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  department_id uuid REFERENCES departments(department_id),
  stakeholder_type text NOT NULL,
  recommendation_type text NOT NULL,
  title text NOT NULL,
  rationale text NOT NULL,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  confidence numeric(6,5) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  expected_value numeric(14,4) NOT NULL DEFAULT 0,
  work_item_id uuid REFERENCES work_items(work_item_id),
  status text NOT NULL DEFAULT 'PROPOSED' CHECK (status IN ('PROPOSED','ACCEPTED','REJECTED','IMPLEMENTED','EXPIRED')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_runs (
  agent_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id text NOT NULL,
  department_code text,
  objective text NOT NULL,
  input_context jsonb NOT NULL DEFAULT '{}'::jsonb,
  output jsonb NOT NULL DEFAULT '{}'::jsonb,
  confidence numeric(6,5),
  duration_ms bigint,
  status text NOT NULL DEFAULT 'SUCCEEDED',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW sem_work_queue AS
SELECT w.work_key, w.title, w.work_type, w.status, w.priority,
       rd.department_name AS requester_department,
       od.department_name AS owner_department,
       w.owner_name, w.pipeline_component, w.due_at, w.estimated_hours,
       w.business_value, w.risk_reduction, w.urgency_score, w.effort_score,
       w.recommendation_score, w.created_at, w.updated_at
FROM work_items w
LEFT JOIN departments rd ON rd.department_id = w.requester_department_id
LEFT JOIN departments od ON od.department_id = w.owner_department_id;

CREATE OR REPLACE VIEW sem_department_recommendations AS
SELECT d.department_code, d.department_name, r.stakeholder_type,
       r.recommendation_type, r.title, r.rationale, r.confidence,
       r.expected_value, r.status, w.work_key, r.created_at
FROM department_recommendations r
LEFT JOIN departments d ON d.department_id = r.department_id
LEFT JOIN work_items w ON w.work_item_id = r.work_item_id;
