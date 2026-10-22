
USE skillswap;

CREATE OR REPLACE VIEW vw_teachable_skills AS
SELECT
    u.user_id,
    u.full_name,
    s.skill_id,
    s.skill_name,
    s.category,
    us.skill_level
FROM users AS u
JOIN user_skills AS us
    ON u.user_id = us.user_id
JOIN skills AS s
    ON us.skill_id = s.skill_id
WHERE us.skill_type = 'TEACH';
