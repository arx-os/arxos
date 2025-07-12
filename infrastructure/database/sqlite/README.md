# SQLite Tools for Testing

This directory contains SQLite command-line tools for testing purposes.

## Installation

SQLite 3.50.1 (64-bit) has been downloaded and extracted from the official SQLite website.

## Files Included

- `sqlite3.exe` - The main SQLite command-line shell
- `sqldiff.exe` - Tool for comparing SQLite databases
- `sqlite3_analyzer.exe` - Tool for analyzing SQLite database files
- `sqlite3_rsync.exe` - Tool for synchronizing SQLite databases

## Usage

### Basic SQLite Shell
```powershell
.\sqlite3.exe database.db
```

### Run SQL Commands
```powershell
.\sqlite3.exe database.db "SELECT * FROM table_name;"
```

### Version Check
```powershell
.\sqlite3.exe --version
```

## Testing

To test that SQLite is working correctly:

```powershell
.\sqlite3.exe test.db "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT); INSERT INTO test (name) VALUES ('Test'); SELECT * FROM test;"
```

## Integration with Go Backend

For use with the `arx-backend` Go project, you can:

1. Use these tools for manual database inspection and testing
2. Reference the `sqlite3.exe` path in your test scripts
3. Use the tools for database migration verification

## Source

Downloaded from: https://www.sqlite.org/download.html
Version: 3.50.1 (2025-06-06)
Platform: Windows x64 