-- Real-Time Chat Application PostgreSQL Schema
-- This schema handles user accounts, chatroom metadata, and permissions

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and profile data
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    public_key TEXT, -- RSA public key for E2E encryption
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Chatrooms table for chat room metadata
CREATE TABLE chatrooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_private BOOLEAN DEFAULT true,
    max_members INTEGER DEFAULT 100,
    encryption_enabled BOOLEAN DEFAULT true,
    auto_summary_enabled BOOLEAN DEFAULT true,
    summary_threshold INTEGER DEFAULT 50, -- Messages before auto-summary
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT name_length CHECK (LENGTH(name) >= 1),
    CONSTRAINT max_members_positive CHECK (max_members > 0),
    CONSTRAINT summary_threshold_positive CHECK (summary_threshold > 0)
);

-- Chatroom members table for user-chatroom relationships
CREATE TABLE chatroom_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chatroom_id UUID NOT NULL REFERENCES chatrooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_muted BOOLEAN DEFAULT false,
    
    -- Unique constraint to prevent duplicate memberships
    UNIQUE(chatroom_id, user_id),
    
    -- Role constraint
    CONSTRAINT valid_role CHECK (role IN ('owner', 'moderator', 'member'))
);

-- Invitations table for chatroom invitation links
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chatroom_id UUID NOT NULL REFERENCES chatrooms(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    invite_code VARCHAR(50) UNIQUE NOT NULL,
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT max_uses_positive CHECK (max_uses > 0),
    CONSTRAINT current_uses_non_negative CHECK (current_uses >= 0),
    CONSTRAINT uses_within_limit CHECK (current_uses <= max_uses)
);

-- User sessions table for JWT token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    device_info TEXT,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Chatroom settings table for additional configuration
CREATE TABLE chatroom_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chatroom_id UUID NOT NULL REFERENCES chatrooms(id) ON DELETE CASCADE UNIQUE,
    allow_file_uploads BOOLEAN DEFAULT true,
    max_file_size_mb INTEGER DEFAULT 10,
    allowed_file_types TEXT[] DEFAULT ARRAY['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],
    message_retention_days INTEGER DEFAULT 365,
    enable_typing_indicators BOOLEAN DEFAULT true,
    enable_read_receipts BOOLEAN DEFAULT true,
    enable_message_reactions BOOLEAN DEFAULT true,
    custom_theme JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT max_file_size_positive CHECK (max_file_size_mb > 0),
    CONSTRAINT retention_days_positive CHECK (message_retention_days > 0)
);

-- Indexes for performance optimization
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_chatrooms_owner_id ON chatrooms(owner_id);
CREATE INDEX idx_chatrooms_created_at ON chatrooms(created_at);
CREATE INDEX idx_chatrooms_is_private ON chatrooms(is_private);

CREATE INDEX idx_chatroom_members_chatroom_id ON chatroom_members(chatroom_id);
CREATE INDEX idx_chatroom_members_user_id ON chatroom_members(user_id);
CREATE INDEX idx_chatroom_members_joined_at ON chatroom_members(joined_at);

CREATE INDEX idx_invitations_invite_code ON invitations(invite_code);
CREATE INDEX idx_invitations_chatroom_id ON invitations(chatroom_id);
CREATE INDEX idx_invitations_expires_at ON invitations(expires_at);
CREATE INDEX idx_invitations_is_active ON invitations(is_active);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chatrooms_updated_at BEFORE UPDATE ON chatrooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chatroom_settings_updated_at BEFORE UPDATE ON chatroom_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW chatroom_members_with_details AS
SELECT 
    cm.id,
    cm.chatroom_id,
    cm.user_id,
    cm.role,
    cm.joined_at,
    cm.last_read_at,
    cm.is_muted,
    u.username,
    u.display_name,
    u.avatar_url,
    u.is_active as user_is_active
FROM chatroom_members cm
JOIN users u ON cm.user_id = u.id;

CREATE VIEW active_invitations AS
SELECT 
    i.*,
    c.name as chatroom_name,
    u.username as created_by_username
FROM invitations i
JOIN chatrooms c ON i.chatroom_id = c.id
JOIN users u ON i.created_by = u.id
WHERE i.is_active = true 
    AND (i.expires_at IS NULL OR i.expires_at > CURRENT_TIMESTAMP)
    AND i.current_uses < i.max_uses;

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_active = false;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to increment invitation usage
CREATE OR REPLACE FUNCTION use_invitation(invite_code_param VARCHAR(50))
RETURNS BOOLEAN AS $$
DECLARE
    invitation_record invitations%ROWTYPE;
BEGIN
    -- Get and lock the invitation record
    SELECT * INTO invitation_record 
    FROM invitations 
    WHERE invite_code = invite_code_param 
        AND is_active = true 
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        AND current_uses < max_uses
    FOR UPDATE;
    
    -- Check if invitation exists and is valid
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Increment usage count
    UPDATE invitations 
    SET current_uses = current_uses + 1,
        is_active = CASE 
            WHEN current_uses + 1 >= max_uses THEN false 
            ELSE true 
        END
    WHERE id = invitation_record.id;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Initial data for development
INSERT INTO users (username, email, password_hash, display_name, public_key) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx8L.jNe', 'Administrator', NULL),
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx8L.jNe', 'Test User', NULL);

-- Grant permissions (adjust as needed for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;

