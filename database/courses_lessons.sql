
-- =============================================
-- SKILLSWAP: COURSES & LESSONS MODULE
-- MySQL 8.0+
-- Additive migration: preserves existing tables
-- =============================================

USE skillswap;

-- 1. Courses
CREATE TABLE IF NOT EXISTS courses (
    course_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    instructor_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    level ENUM('BEGINNER', 'INTERMEDIATE', 'ADVANCED')
        NOT NULL DEFAULT 'BEGINNER',
    language VARCHAR(80),
    thumbnail_url VARCHAR(500),
    status ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED')
        NOT NULL DEFAULT 'PUBLISHED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_course_instructor
        FOREIGN KEY (instructor_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    INDEX idx_courses_category (category),
    INDEX idx_courses_status (status),
    INDEX idx_courses_instructor (instructor_id)
);

-- 2. Course enrollments
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    course_id BIGINT UNSIGNED NOT NULL,
    student_id BIGINT UNSIGNED NOT NULL,
    status ENUM('ACTIVE', 'COMPLETED', 'CANCELLED')
        NOT NULL DEFAULT 'ACTIVE',
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_enrollment_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_enrollment_student
        FOREIGN KEY (student_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_course_student
        UNIQUE (course_id, student_id),

    INDEX idx_enrollment_student (student_id)
);

-- 3. Lessons
-- Supports LIVE, RECORDED and UPLOAD formats.
-- course_id is nullable so standalone lessons are possible.
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    course_id BIGINT UNSIGNED NULL,
    instructor_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,

    lesson_type ENUM('LIVE', 'RECORDED', 'UPLOAD')
        NOT NULL,

    -- Live lesson details
    meeting_url VARCHAR(1000),
    scheduled_at DATETIME,
    duration_minutes SMALLINT UNSIGNED,

    -- Recorded video or uploaded learning material
    content_url VARCHAR(1000),
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_size_bytes BIGINT UNSIGNED,

    status ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED')
        NOT NULL DEFAULT 'PUBLISHED',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lesson_course
        FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_lesson_instructor
        FOREIGN KEY (instructor_id)
        REFERENCES users(user_id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_lesson_duration
        CHECK (
            duration_minutes IS NULL
            OR duration_minutes BETWEEN 1 AND 600
        ),

    CONSTRAINT chk_lesson_content
        CHECK (
            (lesson_type = 'LIVE'
                AND meeting_url IS NOT NULL
                AND scheduled_at IS NOT NULL)
            OR
            (lesson_type IN ('RECORDED', 'UPLOAD')
                AND content_url IS NOT NULL)
        ),

    INDEX idx_lessons_course (course_id),
    INDEX idx_lessons_instructor (instructor_id),
    INDEX idx_lessons_type_status (lesson_type, status),
    INDEX idx_lessons_schedule (scheduled_at)
);

-- =============================================
-- END OF COURSES & LESSONS MODULE
-- =============================================
