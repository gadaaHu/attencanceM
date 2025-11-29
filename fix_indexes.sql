USE membership_system;

-- Check which indexes already exist and only create missing ones
SET @index_exists = (SELECT COUNT(1) 
    FROM information_schema.statistics 
    WHERE table_schema = 'membership_system' 
    AND table_name = 'members' 
    AND index_name = 'idx_members_status');
    
SET @sql = IF(@index_exists = 0, 
    'CREATE INDEX idx_members_status ON members(status)', 
    'SELECT "Index idx_members_status already exists" AS status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;