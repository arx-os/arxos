# ArxOS Test Suite

Cargo only discovers **`tests/*.rs`** as integration targets. Nested directories under
`tests/` are not run by `cargo test` unless listed as `[[test]]` targets.

## Active integration tests

| File | Role |
|---|---|
| `compiler_spine_test.rs` | Seed → backfill address → persist → query → IFC export |
| `ifc_compiler_path_test.rs` | Real IFC fixture → SSOT → validate → export → re-import |
| `ifc_native_tests.rs` | Native STEP geometry / strict validation / export Psets |
| `ifc_integration_test.rs` | Sample IFC files → native parse + bounding boxes |
| `ifc_extruded_solid_test.rs` | Extruded solid geometry |
| `lidar_tests.rs` | LiDAR pipeline + merge policy |
| `bidirectional_tests.rs` | Building ↔ IFC semantic round-trip |
| `config_validation_tests.rs` | Config loading |
| `security_tests.rs` | Path safety / input validation |
| `property_based_tests.rs` | Property tests |

## Fixtures

```
tests/fixtures/
├── golden/     # Expected samples
└── ifc/        # Minimal IFC files for unit/integration tests
```

Also used: `test_data/*.ifc` for mid-size native/import tests.

## Running

```bash
cargo test
cargo test --test compiler_spine_test --test ifc_compiler_path_test --test lidar_tests
```

CI: `.github/workflows/compiler-ci.yml`
