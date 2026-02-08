PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Problem statements and rubric metadata
CREATE TABLE IF NOT EXISTS problems (
    id TEXT PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (
        difficulty IN ('apprentice', 'sorcerer', 'archmage')
    ),
    focus_tags TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(focus_tags)),
    constraints TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(constraints)),
    estimated_time_minutes INTEGER NOT NULL DEFAULT 30 CHECK (estimated_time_minutes > 0),
    phase_time_minutes TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(phase_time_minutes)),
    rubric_hints TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(rubric_hints)),
    rubric_definition TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(rubric_definition)),
    sample_solution_outline TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- User submissions and their artifact metadata
CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    problem_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('received', 'transcribing', 'grading', 'complete', 'failed')
    ),
    phase_times TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(phase_times)),
    phases TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(phases)),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_submissions_problem ON submissions(problem_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);

-- Final grading payloads emitted by the agent pipeline
CREATE TABLE IF NOT EXISTS grading_results (
    submission_id TEXT PRIMARY KEY,
    overall_score REAL NOT NULL CHECK (overall_score BETWEEN 0 AND 10),
    verdict TEXT NOT NULL CHECK (
        verdict IN (
            'strong_no_hire',
            'lean_no_hire',
            'no_decision',
            'lean_hire',
            'hire',
            'strong_hire'
        )
    ),
    verdict_display TEXT NOT NULL,
    dimensions TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(dimensions)),
    top_improvements TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(top_improvements)),
    phase_observations TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(phase_observations)),
    raw_report TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions (id) ON DELETE CASCADE
);
