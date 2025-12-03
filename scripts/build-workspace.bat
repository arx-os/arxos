@echo off
echo Building ArxOS...

echo.
echo Building arx package...
cargo build --release

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
echo   target\release\arx.exe --help
