# Set the password for PostgreSQL
$env:PGPASSWORD = "123@Team*"

# Run the SQL script
psql -h 127.0.0.1 -p 5432 -U ouma_fred -d oreno -f drop_audit_tables.sql