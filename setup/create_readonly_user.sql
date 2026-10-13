-- Read-only account for the text-to-SQL app.
-- Run as root in MySQL Workbench. Replace CHANGE_ME before running,
-- and do NOT save the real password back into this file.
CREATE USER IF NOT EXISTS 'text2sql_reader'@'localhost' IDENTIFIED BY 'CHANGE_ME';
GRANT SELECT, SHOW VIEW ON coffee_chain_db.* TO 'text2sql_reader'@'localhost';
FLUSH PRIVILEGES;

-- Check: should show only SELECT and SHOW VIEW
SHOW GRANTS FOR 'text2sql_reader'@'localhost';
