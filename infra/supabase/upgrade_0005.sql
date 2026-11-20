-- Existing OMS schema at 0004 only. Run as schema owner, before deploying 0005 code.
BEGIN;
SET LOCAL search_path TO oms;
DO $$ BEGIN IF (SELECT version_num FROM alembic_version) IS DISTINCT FROM '0004_invariants' THEN RAISE EXCEPTION 'Expected migration 0004_invariants'; END IF; END $$;


-- Running upgrade 0004_invariants -> 0005_personal_workspace

CREATE TABLE personal_profiles (
    user_id UUID NOT NULL, 
    details_encrypted TEXT, 
    goals_encrypted TEXT, 
    reviewer_id UUID, 
    member_id UUID, 
    version INTEGER NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (user_id), 
    FOREIGN KEY(user_id) REFERENCES app_users (id), 
    FOREIGN KEY(reviewer_id) REFERENCES app_users (id), 
    UNIQUE (member_id), 
    FOREIGN KEY(member_id) REFERENCES members (id)
);

CREATE TABLE personal_reports (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    month DATE NOT NULL, 
    content_encrypted TEXT NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    version INTEGER NOT NULL, 
    submitted_at TIMESTAMP WITH TIME ZONE, 
    reviewed_at TIMESTAMP WITH TIME ZONE, 
    reviewed_by UUID, 
    review_note_encrypted TEXT, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_personal_report_user_month UNIQUE (user_id, month), 
    FOREIGN KEY(user_id) REFERENCES app_users (id), 
    FOREIGN KEY(reviewed_by) REFERENCES app_users (id)
);

ALTER TABLE personal_profiles ENABLE ROW LEVEL SECURITY;

ALTER TABLE personal_reports ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='0005_personal_workspace' WHERE alembic_version.version_num = '0004_invariants';




GRANT SELECT, INSERT, UPDATE ON TABLE oms.personal_profiles TO oms_runtime;
CREATE POLICY oms_runtime_select ON oms.personal_profiles FOR SELECT TO oms_runtime USING (true);
CREATE POLICY oms_runtime_insert ON oms.personal_profiles FOR INSERT TO oms_runtime WITH CHECK (true);
CREATE POLICY oms_runtime_update ON oms.personal_profiles FOR UPDATE TO oms_runtime USING (true) WITH CHECK (true);
REVOKE ALL ON TABLE oms.personal_profiles FROM PUBLIC, anon, authenticated;

GRANT SELECT, INSERT, UPDATE ON TABLE oms.personal_reports TO oms_runtime;
CREATE POLICY oms_runtime_select ON oms.personal_reports FOR SELECT TO oms_runtime USING (true);
CREATE POLICY oms_runtime_insert ON oms.personal_reports FOR INSERT TO oms_runtime WITH CHECK (true);
CREATE POLICY oms_runtime_update ON oms.personal_reports FOR UPDATE TO oms_runtime USING (true) WITH CHECK (true);
REVOKE ALL ON TABLE oms.personal_reports FROM PUBLIC, anon, authenticated;
COMMIT;
SELECT version_num FROM oms.alembic_version;
