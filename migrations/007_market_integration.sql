-- Market Integration & Token Economics Schema
-- Implements the economic layer for ArxOS Building Whisperer

-- Contributions tracking table
CREATE TABLE IF NOT EXISTS contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contributor_id VARCHAR(255) NOT NULL,
    building_id VARCHAR(255) NOT NULL,
    object_id UUID,
    
    -- Contribution details
    contribution_type VARCHAR(50) NOT NULL,
    data_hash VARCHAR(255) NOT NULL, -- For verification
    metadata JSONB DEFAULT '{}',
    
    -- Verification
    verification_status VARCHAR(50) DEFAULT 'pending',
    quality_score DECIMAL(3,2) DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_contributions_contributor (contributor_id, timestamp DESC),
    INDEX idx_contributions_building (building_id, timestamp DESC),
    INDEX idx_contributions_verification (verification_status)
);

-- BILT Token registry
CREATE TABLE IF NOT EXISTS bilt_tokens (
    token_id VARCHAR(255) PRIMARY KEY, -- BILT-{building_id}
    building_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Token supply
    current_supply DECIMAL(20,8) NOT NULL DEFAULT 0,
    circulating_supply DECIMAL(20,8) NOT NULL DEFAULT 0,
    locked_supply DECIMAL(20,8) NOT NULL DEFAULT 0,
    
    -- Token data
    metadata JSONB NOT NULL DEFAULT '{}',
    market_data JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_tokens_building (building_id)
);

-- Token distributions (rewards)
CREATE TABLE IF NOT EXISTS token_distributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contributor_id VARCHAR(255) NOT NULL,
    building_id VARCHAR(255) NOT NULL,
    
    -- Distribution details
    amount DECIMAL(20,8) NOT NULL,
    distribution_type VARCHAR(50) NOT NULL,
    contribution_id UUID REFERENCES contributions(id),
    
    -- Timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_distributions_contributor (contributor_id, timestamp DESC),
    INDEX idx_distributions_building (building_id, timestamp DESC)
);

-- Contributor balances
CREATE TABLE IF NOT EXISTS contributor_balances (
    contributor_id VARCHAR(255) PRIMARY KEY,
    total_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    locked_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    available_balance DECIMAL(20,8) GENERATED ALWAYS AS (total_balance - locked_balance) STORED,
    
    -- Stats
    total_earned DECIMAL(20,8) NOT NULL DEFAULT 0,
    total_spent DECIMAL(20,8) NOT NULL DEFAULT 0,
    
    -- Timestamps
    first_contribution TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contributor profiles with reputation
CREATE TABLE IF NOT EXISTS contributor_profiles (
    contributor_id VARCHAR(255) PRIMARY KEY,
    display_name VARCHAR(255),
    
    -- Reputation metrics
    reputation_score DECIMAL(6,2) DEFAULT 0 CHECK (reputation_score >= 0 AND reputation_score <= 1000),
    trust_level VARCHAR(50) DEFAULT 'newcomer',
    
    -- Contribution stats
    total_contributions BIGINT DEFAULT 0,
    verified_contributions BIGINT DEFAULT 0,
    rejected_contributions BIGINT DEFAULT 0,
    
    -- Profile data
    specializations JSONB DEFAULT '[]',
    badges JSONB DEFAULT '[]',
    
    -- Timestamps
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_profiles_reputation (reputation_score DESC),
    INDEX idx_profiles_active (last_active DESC)
);

-- Market valuations cache
CREATE TABLE IF NOT EXISTS market_valuations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id VARCHAR(255) NOT NULL,
    
    -- Valuation components
    base_property_value DECIMAL(20,2) NOT NULL,
    rating_multiplier DECIMAL(5,3) NOT NULL,
    bilt_token_value DECIMAL(20,8) NOT NULL,
    total_market_value DECIMAL(20,2) NOT NULL,
    
    -- Market data
    price_per_token DECIMAL(20,8),
    market_cap DECIMAL(20,2),
    volume_24h DECIMAL(20,2),
    
    -- Timestamp
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_valuations_building (building_id, calculated_at DESC)
);

-- Reward calculations log
CREATE TABLE IF NOT EXISTS reward_calculations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contribution_id UUID REFERENCES contributions(id),
    
    -- Reward details
    base_reward DECIMAL(20,8) NOT NULL,
    quality_multiplier DECIMAL(5,3) NOT NULL,
    verification_multiplier DECIMAL(5,3) NOT NULL,
    final_reward DECIMAL(20,8) NOT NULL,
    
    -- Distribution
    distributed BOOLEAN DEFAULT FALSE,
    distributed_at TIMESTAMP,
    
    -- Timestamp
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_rewards_contribution (contribution_id),
    INDEX idx_rewards_distributed (distributed, calculated_at DESC)
);

-- Function to update contributor balance on distribution
CREATE OR REPLACE FUNCTION update_contributor_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert contributor balance
    INSERT INTO contributor_balances (
        contributor_id,
        total_balance,
        total_earned,
        first_contribution,
        last_updated
    ) VALUES (
        NEW.contributor_id,
        NEW.amount,
        NEW.amount,
        NEW.timestamp,
        NEW.timestamp
    ) ON CONFLICT (contributor_id) DO UPDATE SET
        total_balance = contributor_balances.total_balance + NEW.amount,
        total_earned = contributor_balances.total_earned + NEW.amount,
        last_updated = NEW.timestamp;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update balances on token distribution
CREATE TRIGGER update_balance_on_distribution
    AFTER INSERT ON token_distributions
    FOR EACH ROW
    EXECUTE FUNCTION update_contributor_balance();

-- Function to calculate contributor trust level
CREATE OR REPLACE FUNCTION calculate_trust_level(score DECIMAL)
RETURNS VARCHAR AS $$
BEGIN
    RETURN CASE
        WHEN score < 100 THEN 'newcomer'
        WHEN score < 300 THEN 'contributor'
        WHEN score < 600 THEN 'trusted'
        WHEN score < 900 THEN 'expert'
        ELSE 'master'
    END;
END;
$$ LANGUAGE plpgsql;

-- View for token market overview
CREATE OR REPLACE VIEW token_market_overview AS
SELECT 
    t.building_id,
    b.name as building_name,
    t.current_supply,
    t.circulating_supply,
    (t.metadata->>'current_rating')::VARCHAR as rating,
    (t.market_data->>'current_price')::DECIMAL as price_per_token,
    (t.market_data->>'market_cap')::DECIMAL as market_cap,
    (t.market_data->>'volume_24h')::DECIMAL as volume_24h,
    COUNT(DISTINCT td.contributor_id) as holder_count,
    t.last_updated
FROM bilt_tokens t
LEFT JOIN buildings b ON t.building_id = b.id::text
LEFT JOIN token_distributions td ON t.building_id = td.building_id
GROUP BY t.token_id, t.building_id, b.name, t.current_supply, 
         t.circulating_supply, t.metadata, t.market_data, t.last_updated
ORDER BY market_cap DESC;

-- View for contributor leaderboard
CREATE OR REPLACE VIEW contributor_leaderboard AS
SELECT 
    p.contributor_id,
    p.display_name,
    p.reputation_score,
    p.trust_level,
    p.total_contributions,
    p.verified_contributions,
    COALESCE(b.total_balance, 0) as token_balance,
    p.badges,
    p.joined_at,
    p.last_active
FROM contributor_profiles p
LEFT JOIN contributor_balances b ON p.contributor_id = b.contributor_id
ORDER BY p.reputation_score DESC, p.total_contributions DESC;

-- Index for fast contribution queries
CREATE INDEX idx_contributions_composite ON contributions(
    building_id, 
    contributor_id, 
    timestamp DESC
) WHERE verification_status != 'rejected';