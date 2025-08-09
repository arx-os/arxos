# Arxos Database Diagram Legend

## Generated: 2024-01-15 12:00:00

## Color Scheme

### Table Types
- **🔵 User Tables** (`#4A90E2`): User management and authentication
  - `users` - User accounts and authentication

- **🟢 BIM Objects** (`#50C878`): Building Information Modeling objects
  - `rooms`, `walls`, `doors`, `windows`, `devices`, `labels`, `zones`

- **🔴 Audit Tables** (`#FF6B6B`): Audit logging and change tracking
  - `audit_logs`, `object_history`

- **🟡 Collaboration Tables** (`#FFD93D`): User collaboration features
  - `comments`, `assignments`, `chat_messages`

- **🟣 System Tables** (`#9B59B6`): Core system functionality
  - `projects`, `buildings`, `floors`, `categories`, `user_category_permissions`, `catalog_items`

- **🟠 Spatial Tables** (`#FF8C42`): Spatial data and geometry
  - Tables with PostGIS geometry columns

## Relationship Types

### Line Styles
- **Solid Line**: Standard foreign key relationship
- **Dashed Line**: Nullable foreign key relationship
- **Thick Line**: Cascade delete relationship

### Arrow Types
- **Single Arrow**: One-to-many relationship
- **Double Arrow**: Many-to-many relationship (through junction table)

## Diagram Types

### 1. Entity-Relationship (ER) Diagram
- **Purpose**: Shows detailed table structure and relationships
- **File**: `arxos_er_diagram.drawio`
- **Features**:
  - Complete table schemas
  - Column details and data types
  - Primary and foreign key indicators
  - Index and constraint information

### 2. Data Flow Diagram
- **Purpose**: Shows service interactions and data flow
- **File**: `arxos_data_flow_diagram.drawio`
- **Features**:
  - Service component interactions
  - Data flow between services
  - Database access patterns
  - API endpoint relationships

### 3. Table Relationship Diagram
- **Purpose**: Shows high-level table dependencies
- **File**: `arxos_relationship_diagram.drawio`
- **Features**:
  - Hierarchical table organization
  - Dependency levels
  - Relationship strength indicators
  - Simplified view for overview

## Usage Guidelines

### For Developers
1. **ER Diagram**: Use for detailed schema understanding
2. **Data Flow**: Use for service architecture understanding
3. **Relationship**: Use for quick dependency overview

### For Documentation
1. **Include in README**: Link diagrams in documentation
2. **Update with Changes**: Regenerate when schema changes
3. **Version Control**: Track diagram changes with schema changes

### For CI/CD
1. **Automated Generation**: Generate diagrams on schema changes
2. **Validation**: Ensure diagrams match current schema
3. **Artifact Upload**: Include diagrams in deployment artifacts

## Maintenance

### When to Regenerate
- Schema changes (new tables, columns, relationships)
- Service architecture changes
- Major refactoring
- Documentation updates

### How to Regenerate
```bash
cd arxos/infrastructure/database
python tools/generate_diagrams.py --database-url postgresql://...
```

### Validation
- Ensure diagrams match current schema
- Verify all relationships are represented
- Check color coding accuracy
- Validate file formats and accessibility

---

*This legend is automatically generated and should be updated with diagram changes.*
