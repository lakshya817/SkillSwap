
USE skillswap;

-- Example: transfer credits between two users.
-- Replace the example IDs and amount when testing.

START TRANSACTION;

SET @sender_id = 1;
SET @receiver_id = 2;
SET @transfer_amount = 5;

-- Lock both users' credit ledger rows before calculating balances.
-- In a real application, use a dedicated account-balance
-- table or another reliable method to initialize and lock accounts.

SELECT user_id
FROM users
WHERE user_id IN (@sender_id, @receiver_id)
FOR UPDATE;

-- Calculate the sender's current ledger balance.
SELECT COALESCE(SUM(amount), 0)
INTO @sender_balance
FROM credit_transactions
WHERE user_id = @sender_id;

-- Only transfer if the users exist, are different,
-- the amount is positive, and the sender has enough credits.
-- This example is a template to adapt and test with real data.
SELECT @sender_balance AS sender_balance,
       @transfer_amount AS requested_transfer;

ROLLBACK;
