
USE skillswap;

DELIMITER //

CREATE PROCEDURE sp_find_teachers(
    IN p_skill_name VARCHAR(100)
)
BEGIN
    SELECT
        u.user_id,
        u.full_name,
        s.skill_name,
        us.skill_level
    FROM users AS u
    JOIN user_skills AS us
        ON u.user_id = us.user_id
    JOIN skills AS s
        ON us.skill_id = s.skill_id
    WHERE s.skill_name = p_skill_name
      AND us.skill_type = 'TEACH'
    ORDER BY u.full_name;
END //

DELIMITER ;
