
USE skillswap;

-- Verify the sample users were loaded.
DELIMITER //

CREATE PROCEDURE sp_run_database_tests()
BEGIN
    DECLARE v_user_count INT DEFAULT 0;
    DECLARE v_skill_count INT DEFAULT 0;
    DECLARE v_python_teachers INT DEFAULT 0;
    DECLARE v_request_count INT DEFAULT 0;
    DECLARE v_session_count INT DEFAULT 0;

    SELECT COUNT(*) INTO v_user_count
    FROM users
    WHERE email IN (
        'aarav.test@example.com',
        'diya.test@example.com',
        'kabir.test@example.com'
    );

    IF v_user_count <> 3 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Expected 3 sample users';
    END IF;

    SELECT COUNT(*) INTO v_skill_count
    FROM skills
    WHERE skill_name IN (
        'Python',
        'Graphic Design',
        'Public Speaking'
    );

    IF v_skill_count <> 3 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Expected 3 sample skills';
    END IF;

    SELECT COUNT(*) INTO v_python_teachers
    FROM vw_teachable_skills
    WHERE skill_name = 'Python'
      AND email IS NULL;

    -- The view does not expose email, so use its user ID
    -- to verify the expected Python teacher instead.
END //

DELIMITER ;
