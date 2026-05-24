-- Таблица узлов
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(45) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ресурсов
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    node_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица метрик
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица значений метрик
CREATE TABLE IF NOT EXISTS metric_values (
    id BIGSERIAL PRIMARY KEY,
    metric_id INTEGER REFERENCES metrics(id) ON DELETE CASCADE,
    value FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_metric_values_metric_time 
ON metric_values(metric_id, timestamp DESC);

-- Таблица агрегированных данных
CREATE TABLE IF NOT EXISTS aggregated_data (
    id BIGSERIAL PRIMARY KEY,
    metric_id INTEGER REFERENCES metrics(id) ON DELETE CASCADE,
    period VARCHAR(10) NOT NULL,
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    avg_value FLOAT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_aggregated_metric_period_time 
ON aggregated_data(metric_id, period, start_time DESC);