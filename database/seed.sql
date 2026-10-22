
USE skillswap;

-- Sample users for testing only.
-- These placeholder hashes are NOT real login credentials.

INSERT INTO users (full_name, email, password_hash)
VALUES
    ('Aarav Sharma', 'aarav.test@example.com', 'TEST_HASH_NOT_FOR_LOGIN'),
    ('Diya Patel', 'diya.test@example.com', 'TEST_HASH_NOT_FOR_LOGIN'),
    ('Kabir Singh', 'kabir.test@example.com', 'TEST_HASH_NOT_FOR_LOGIN');

-- Sample skills
INSERT INTO skills (skill_name, category)
VALUES
    ('Python', 'Programming'),
    ('Graphic Design', 'Design'),
    ('Public Speaking', 'Communication');

-- Find the IDs using unique emails and skill names
SET @aarav = (
    SELECT user_id FROM users
    WHERE email = 'aarav.test@example.com'
);

SET @diya = (
    SELECT user_id FROM users
    WHERE email = 'diya.test@example.com'
);

SET @kabir = (
    SELECT user_id FROM users
    WHERE email = 'kabir.test@example.com'
);

SET @python = (
    SELECT skill_id FROM skills WHERE skill_name = 'Python'
);

SET @design = (
    SELECT skill_id FROM skills WHERE skill_name = 'Graphic Design'
);

SET @speaking = (
    SELECT skill_id FROM skills WHERE skill_name = 'Public Speaking'
);

-- Aarav teaches Python and wants to learn design
INSERT INTO user_skills (user_id, skill_id, skill_type, skill_level)
VALUES
    (@aarav, @python, 'TEACH', 'INTERMEDIATE'),
    (@aarav, @design, 'LEARN', 'BEGINNER');

-- Diya teaches design and wants to learn Python
INSERT INTO user_skills (user_id, skill_id, skill_type, skill_level)
VALUES
    (@diya, @design, 'TEACH', 'ADVANCED'),
    (@diya, @python, 'LEARN', 'BEGINNER');

-- Kabir teaches public speaking
INSERT INTO user_skills (user_id, skill_id, skill_type, skill_level)
VALUES
    (@kabir, @speaking, 'TEACH', 'ADVANCED');

-- Create a sample exchange request
INSERT INTO exchange_requests
    (sender_id, receiver_id, skill_id, message, status)
VALUES
    (@aarav, @diya, @design,
     'I can help you with Python in exchange for design lessons.',
     'ACCEPTED');

-- Schedule a sample session for that request
SET @request = LAST_INSERT_ID();

INSERT INTO sessions (request_id, scheduled_at, duration_minutes, status)
VALUES (@request, '2026-11-01 10:00:00', 60, 'SCHEDULED');
