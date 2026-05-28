-- Aegis Capital RE Wholesale Database Schema
-- Real data persistence replacing localStorage

CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Houston',
    state TEXT NOT NULL DEFAULT 'TX',
    zip TEXT,
    beds INTEGER,
    baths REAL,
    sqft INTEGER,
    condition TEXT CHECK(condition IN ('C1','C2','C3','C4','C5','C6')),
    year_built INTEGER,
    arv INTEGER NOT NULL,
    repair_estimate INTEGER DEFAULT 0,
    mao INTEGER,
    asking_price INTEGER,
    assignment_fee INTEGER,
    status TEXT NOT NULL DEFAULT 'lead' CHECK(status IN ('lead','analyzing','under_contract','closed','dead')),
    source TEXT,
    seller_name TEXT,
    seller_phone TEXT,
    seller_email TEXT,
    motivation TEXT,
    date_added DATE DEFAULT CURRENT_DATE,
    date_updated DATE DEFAULT CURRENT_DATE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT,
    phone TEXT,
    email TEXT,
    buy_box_min INTEGER,
    buy_box_max INTEGER,
    preferred_states TEXT,
    preferred_cities TEXT,
    property_types TEXT,
    min_beds INTEGER,
    max_rehab INTEGER,
    cash_buyer BOOLEAN DEFAULT 1,
    closing_time_days INTEGER,
    notes TEXT,
    date_added DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS deal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    event TEXT NOT NULL,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id)
);

CREATE INDEX IF NOT EXISTS idx_properties_arv ON properties(arv);
CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
CREATE INDEX IF NOT EXISTS idx_properties_date ON properties(date_added);
CREATE INDEX IF NOT EXISTS idx_buyers_range ON buyers(buy_box_min, buy_box_max);

-- View: Active deals around $400K ARV
CREATE VIEW IF NOT EXISTS deals_400k AS
SELECT *, 
    (arv * 0.70 - repair_estimate) as calculated_mao,
    (asking_price - (arv * 0.70 - repair_estimate)) as potential_profit
FROM properties
WHERE status IN ('lead','analyzing','under_contract')
    AND arv BETWEEN 350000 AND 450000;

-- View: Pipeline summary
CREATE VIEW IF NOT EXISTS pipeline_summary AS
SELECT 
    status,
    COUNT(*) as count,
    SUM(assignment_fee) as total_fees,
    AVG(arv) as avg_arv
FROM properties
WHERE status != 'dead'
GROUP BY status;
