# ArxOS Database Migrations

This directory contains SQL migration files for the ArxOS PostgreSQL/PostGIS database.

## Migration Naming Convention

Migration files follow this naming pattern:
```
XXX_description.up.sql   - Apply migration
XXX_description.down.sql - Rollback migration
```

Where XXX is a zero-padded sequential number (001, 002, etc.)

## Running Migrations

### Apply all migrations:
```bash
arx migrate up
```

### Rollback last migration:
```bash
arx migrate down
```

### Check migration status:
```bash
arx migrate status
```

## Creating New Migrations

1. Create a new pair of migration files with the next sequence number
2. Write the forward migration in the `.up.sql` file
3. Write the rollback migration in the `.down.sql` file
4. Test both forward and rollback migrations

## Migration Best Practices

1. **Always include rollback**: Every `.up.sql` should have a corresponding `.down.sql`
2. **Use transactions**: Wrap migrations in BEGIN/COMMIT when possible
3. **Be idempotent**: Migrations should be safe to run multiple times
4. **Test thoroughly**: Test both up and down migrations before deploying
5. **Keep it simple**: One logical change per migration
6. **Use IF EXISTS**: Make migrations defensive against partial application

## PostGIS Specific Notes

- Always specify SRID for geometry columns (typically 4326 for WGS84)
- Create spatial indices for geometry columns used in queries
- Use appropriate geometry types (POINT, POINTZ, POLYGON, etc.)
- Consider using geography type for distance calculations