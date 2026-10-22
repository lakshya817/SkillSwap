
USE skillswap;

DELIMITER //

CREATE TRIGGER trg_validate_review_participant
BEFORE INSERT ON reviews
FOR EACH ROW
BEGIN
    DECLARE v_sender_id BIGINT UNSIGNED;
    DECLARE v_receiver_id BIGINT UNSIGNED;

    SELECT er.sender_id, er.receiver_id
    INTO v_sender_id, v_receiver_id
    FROM sessions AS se
    JOIN exchange_requests AS er
        ON se.request_id = er.request_id
    WHERE se.session_id = NEW.session_id;

    IF NEW.reviewer_id <> v_sender_id
       AND NEW.reviewer_id <> v_receiver_id THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Only exchange participants can submit a review';
    END IF;
END //

DELIMITER ;
