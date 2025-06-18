-- scripts/init.sql
-- PostgreSQL initialization script for KomuniTech

-- Create database if not exists
-- Note: This part needs to be run as superuser
-- CREATE DATABASE komunitech_db;

-- Connect to the database
\c komunitech_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For full-text search

-- Set timezone
SET timezone = 'UTC';

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('Regular', 'Developer', 'Admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('Aktif', 'Selesai', 'Ditutup');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE kebutuhan_status AS ENUM ('Diajukan', 'Diproses', 'Selesai', 'Ditolak');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE kebutuhan_priority AS ENUM ('Rendah', 'Sedang', 'Tinggi');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for better performance
-- These will be created after tables are created by Flask-Migrate

-- Indexes for users table
-- CREATE INDEX idx_users_email ON users(email);
-- CREATE INDEX idx_users_username ON users(username);
-- CREATE INDEX idx_users_created_at ON users(created_at);

-- Indexes for projects table
-- CREATE INDEX idx_projects_status ON projects(status);
-- CREATE INDEX idx_projects_kategori ON projects(kategori_id);
-- CREATE INDEX idx_projects_timestamp ON projects(timestamp);
-- CREATE INDEX idx_projects_pengguna ON projects(pengguna_id);

-- Indexes for requirements table
-- CREATE INDEX idx_requirements_status ON requirements(status);
-- CREATE INDEX idx_requirements_project ON requirements(project_id);
-- CREATE INDEX idx_requirements_timestamp ON requirements(timestamp);
-- CREATE INDEX idx_requirements_prioritas ON requirements(prioritas);

-- Indexes for comments table
-- CREATE INDEX idx_comments_kebutuhan ON comments(kebutuhan_id);
-- CREATE INDEX idx_comments_timestamp ON comments(timestamp);
-- CREATE INDEX idx_comments_parent ON comments(parent_id);

-- Indexes for supports table
-- CREATE INDEX idx_supports_kebutuhan ON supports(kebutuhan_id);
-- CREATE INDEX idx_supports_pengguna ON supports(pengguna_id);

-- Full-text search indexes
-- CREATE INDEX idx_projects_search ON projects USING gin(to_tsvector('indonesian', judul || ' ' || deskripsi));
-- CREATE INDEX idx_requirements_search ON requirements USING gin(to_tsvector('indonesian', judul || ' ' || deskripsi));

-- Create function for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Triggers will be created after tables are created by Flask-Migrate
-- Example:
-- CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO komunitech_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO komunitech_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO komunitech_user;