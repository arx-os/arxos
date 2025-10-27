@echo off
echo Building ArxOS workspace...

echo.
echo Building arxos package with git features...
cargo build --features git

echo.
echo Building tests...
cargo test --no-run

echo.
echo Running benchmarks...
cargo bench --no-run

echo.
echo All builds completed successfully!
echo.
echo To run the CLI:
echo   cargo run --bin arxos -- --help
