-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Create ENUM types
CREATE TYPE project_status AS ENUM (
    'draft',
    'generating_script',
    'casting',
    'generating_audio',
    'generating_video',
    'completed',
    'uploading_youtube',
    'published',
    'failed'
);
CREATE TYPE asset_type AS ENUM ('audio', 'video');
CREATE TYPE privacy_status AS ENUM ('public', 'private', 'unlisted');
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status project_status DEFAULT 'draft',
    youtube_video_id VARCHAR(50),
    youtube_url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Scripts table
CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Casts table
CREATE TABLE casts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assignments JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Assets table
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    asset_type asset_type NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    character_name VARCHAR(255),
    file_size_bytes BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- YouTube connections table
CREATE TABLE youtube_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id VARCHAR(100) NOT NULL,
    channel_title VARCHAR(255),
    refresh_token TEXT NOT NULL,
    access_token TEXT NOT NULL,
    token_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- YouTube metadata table
CREATE TABLE youtube_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    tags JSONB DEFAULT '[]',
    category_id VARCHAR(10) DEFAULT '22',
    privacy_status privacy_status DEFAULT 'private',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Indexes for performance
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_scripts_project_id ON scripts(project_id);
CREATE INDEX idx_casts_project_id ON casts(project_id);
CREATE INDEX idx_assets_project_id ON assets(project_id);
CREATE INDEX idx_youtube_connections_user_id ON youtube_connections(user_id);
CREATE INDEX idx_youtube_metadata_project_id ON youtube_metadata(project_id);
-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
-- Apply trigger to projects table
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
-- Apply trigger to youtube_connections table
CREATE TRIGGER update_youtube_connections_updated_at
    BEFORE UPDATE ON youtube_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
-- Insert a default test user
INSERT INTO users (id, email) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'test@example.com');