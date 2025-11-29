-- Create database
CREATE DATABASE IF NOT EXISTS membership_system;
USE membership_system;

-- Users Table (System Administrators)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fullname VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Members Table
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(255) NOT NULL,
    membership_number VARCHAR(100) UNIQUE,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    date_of_birth DATE,
    emergency_contact TEXT,
    membership_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    join_date DATE,
    profile_image VARCHAR(500),
    face_encoding_path TEXT,
    approved_by INT,
    approved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Events Table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(500),
    description TEXT,
    event_type VARCHAR(100),
    created_by INT,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    event_id INT,
    status VARCHAR(50) NOT NULL DEFAULT 'present',
    recognized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence DECIMAL(5,4),
    marked_by INT,
    UNIQUE(member_id, event_id),
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES users(id)
);

-- Annual Plans Table
CREATE TABLE IF NOT EXISTS annual_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    plan_type VARCHAR(50),
    year INT,
    file_path VARCHAR(500) NOT NULL,
    analysis_data JSON,
    uploaded_by INT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP NULL,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- Member Activities Table
CREATE TABLE IF NOT EXISTS member_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    activity_type VARCHAR(100),
    description TEXT,
    points_earned INT DEFAULT 0,
    activity_date DATE DEFAULT (CURRENT_DATE),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- Create indexes for better query performance (with conditional checks)
CREATE INDEX IF NOT EXISTS idx_members_status ON members(status);
CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);
CREATE INDEX IF NOT EXISTS idx_members_membership_number ON members(membership_number);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_attendance_member_event ON attendance(member_id, event_id);
CREATE INDEX IF NOT EXISTS idx_attendance_recognized ON attendance(recognized_at);
CREATE INDEX IF NOT EXISTS idx_attendance_event ON attendance(event_id);
CREATE INDEX IF NOT EXISTS idx_annual_plans_year ON annual_plans(year);
CREATE INDEX IF NOT EXISTS idx_member_activities_member ON member_activities(member_id);
CREATE INDEX IF NOT EXISTS idx_member_activities_date ON member_activities(activity_date);

-- Create Views
CREATE OR REPLACE VIEW member_attendance_summary AS
SELECT 
    m.id,
    m.fullname,
    m.membership_number,
    COUNT(a.id) as total_events_attended,
    AVG(a.confidence) as avg_confidence,
    MAX(a.recognized_at) as last_attendance
FROM members m
LEFT JOIN attendance a ON m.id = a.member_id
WHERE m.status = 'active'
GROUP BY m.id, m.fullname, m.membership_number;

CREATE OR REPLACE VIEW event_attendance_stats AS
SELECT 
    e.id,
    e.title,
    e.event_date,
    COUNT(a.id) as total_attendance,
    COUNT(DISTINCT a.member_id) as unique_members,
    AVG(a.confidence) as avg_confidence
FROM events e
LEFT JOIN attendance a ON e.id = a.event_id
GROUP BY e.id, e.title, e.event_date;