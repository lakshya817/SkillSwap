
-- SkillSwap database schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS skillswap;
USE skillswap;

-- 1. Users
CREATE TABLE users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('STUDENT', 'ADMIN') NOT NULL DEFAULT 'STUDENT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Skills
CREATE TABLE skills (
    skill_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL
);

-- 3. Skills a user can teach or wants to learn
CREATE TABLE user_skills (
    user_skill_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    skill_id BIGINT UNSIGNED NOT NULL,
    skill_type ENUM('TEACH', 'LEARN') NOT NULL,
    skill_level ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED')
        NOT NULL DEFAULT 'BEGINNER',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_skills_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_skills_skill
        FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_user_skill_type
        UNIQUE (user_id, skill_id, skill_type)
);

-- 4. Requests to exchange skills
CREATE TABLE exchange_requests (
    request_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sender_id BIGINT UNSIGNED NOT NULL,
    receiver_id BIGINT UNSIGNED NOT NULL,
    skill_id BIGINT UNSIGNED NOT NULL,
    message VARCHAR(500),
    status ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED')
        NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_request_sender
        FOREIGN KEY (sender_id) REFERENCES users(user_id),
    CONSTRAINT fk_request_receiver
        FOREIGN KEY (receiver_id) REFERENCES users(user_id),
    CONSTRAINT fk_request_skill
        FOREIGN KEY (skill_id) REFERENCES skills(skill_id),
    CONSTRAINT chk_request_different_users
        CHECK (sender_id <> receiver_id)
);

-- 5. Sessions scheduled for accepted requests
CREATE TABLE sessions (
    session_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id BIGINT UNSIGNED NOT NULL UNIQUE,
    scheduled_at DATETIME NOT NULL,
    duration_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 60,
    status ENUM('SCHEDULED', 'COMPLETED', 'CANCELLED')
        NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_request
        FOREIGN KEY (request_id)
        REFERENCES exchange_requests(request_id),
    CONSTRAINT chk_session_duration
        CHECK (duration_minutes BETWEEN 15 AND 240)
);

-- 6. Reviews after a session
CREATE TABLE reviews (
    review_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT UNSIGNED NOT NULL,
    reviewer_id BIGINT UNSIGNED NOT NULL,
    rating TINYINT UNSIGNED NOT NULL,
    comment VARCHAR(1000),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_review_session
        FOREIGN KEY (session_id) REFERENCES sessions(session_id),
    CONSTRAINT fk_review_reviewer
        FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
    CONSTRAINT uq_session_reviewer
        UNIQUE (session_id, reviewer_id),
    CONSTRAINT chk_review_rating
        CHECK (rating BETWEEN 1 AND 5)
);

-- 7. Credit transaction ledger
CREATE TABLE credit_transactions (
    transaction_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    amount INT NOT NULL,
    transaction_type ENUM('EARNED', 'SPENT', 'ADJUSTMENT') NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_credit_user
        FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT chk_credit_amount
        CHECK (amount <> 0)
);

-- Indexes for common searches
CREATE INDEX idx_user_skills_skill_type
    ON user_skills(skill_id, skill_type);

CREATE INDEX idx_requests_receiver_status
    ON exchange_requests(receiver_id, status);

CREATE INDEX idx_sessions_schedule
    ON sessions(scheduled_at, status);

CREATE INDEX idx_reviews_reviewer
    ON reviews(reviewer_id);

CREATE INDEX idx_credit_user_date
    ON credit_transactions(user_id, created_at);
