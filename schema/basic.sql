CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE agent_runs(
    run_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    input_text TEXT NOT NULL,
    input_format VARCHAR(50) NOT NULL DEFAULT 'raw_text',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    result TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE voice_ops_events (
    event_id TEXT PRIMARY KEY,
    run_id INT NOT NULL REFERENCES agent_runs(run_id),
    phase TEXT,
    module TEXT,
    pipeline_node TEXT,
    level TEXT,
    error_type TEXT,
    fingerprint TEXT,
    call_sid TEXT,
    room_id TEXT,
    agent_id TEXT,
    turn_id TEXT,
    provider TEXT,
    latency_ms INT,
    taxonomy_confidence FLOAT,
    message_redacted TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
