-- Drop audit tables from all schemas
DO $$
DECLARE
    schema_rec RECORD;
    table_rec RECORD;
BEGIN
    -- Loop through all non-system schemas
    FOR schema_rec IN 
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
        AND schema_name NOT LIKE 'pg_%'
        AND schema_name != 'information_schema'
    LOOP
        RAISE NOTICE 'Processing schema: %', schema_rec.schema_name;
        
        -- For each schema, find and drop all audit_* tables
        FOR table_rec IN
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = schema_rec.schema_name
            AND table_name LIKE 'audit_%'
            AND table_type = 'BASE TABLE'
        LOOP
            EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', 
                          schema_rec.schema_name, table_rec.table_name);
            RAISE NOTICE 'Dropped table %.%', 
                schema_rec.schema_name, table_rec.table_name;
        END LOOP;
    END LOOP;
    
    -- Also drop public schema audit tables
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'audit_%'
        AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', table_rec.table_name);
        RAISE NOTICE 'Dropped table public.%', table_rec.table_name;
    END LOOP;
END $$;