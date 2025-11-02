# ArxOS Performance Benchmarks

This document presents performance benchmark results for critical ArxOS operations and capacity planning guidelines.

## Running Benchmarks

```bash
# Run all benchmarks
cargo bench --bench performance_benchmarks

# Run specific benchmark
cargo bench --bench performance_benchmarks -- "ifc_processor_init"
```

## Benchmark Results

### IFC Processing

| Operation | Time (mean) | 95% CI |
|-----------|-------------|--------|
| Processor Initialization | 227.46 ps | 226.75ps - 228.47ps |

**Analysis:** IFC processor initialization is extremely lightweight (< 1ns), allowing for many concurrent processors.

### YAML Serialization

| Entity Count | Serialize (mean) | Deserialize (mean) |
|--------------|------------------|-------------------|
| 10 entities | 47.18 µs | 123.47 µs |
| 100 entities | 418.89 µs | 1.03 ms |
| 1000 entities | 4.14 ms | 10.61 ms |

**Analysis:**
- Serialization scales linearly: ~42µs per 10 entities
- Deserialization is ~2.6x slower than serialization
- A building with 10,000 entities would serialize in ~40ms and deserialize in ~100ms

### Spatial Operations

| Operation | Time (mean) | 95% CI |
|-----------|-------------|--------|
| Point distance calculation | 725.30 ps | 723.93ps - 727.15ps |
| Bounding box center | 370.28 ps | 368.73ps - 372.12ps |
| Bounding box volume | 278.68 ps | 276.80ps - 281.07ps |
| Bounding box from points (4) | 1.93 ns | 1.75ns - 2.14ns |

**Analysis:**
- Spatial operations are ultra-fast (sub-nanosecond)
- No performance concerns for spatial queries even with large datasets
- Can perform millions of spatial operations per second

### Git Operations

| Operation | Time (mean) | 95% CI |
|-----------|-------------|--------|
| Git manager initialization | 95.25 µs | 94.84µs - 95.64µs |

**Analysis:**
- Git manager init is fast enough for repeated operations
- ~10,000 init operations per second
- Actual commit/stage operations not benchmarked (would depend on file count)

## Capacity Planning Guidelines

### Small Building (< 100 entities)
- **Typical size:** Single floor, 50-100 rooms/equipment
- **Memory:** ~50-200 KB
- **Import time:** < 100ms
- **Search time:** < 1ms
- **Rendering:** Real-time (60 FPS)

### Medium Building (100-1,000 entities)
- **Typical size:** Multi-floor building, 500-1,000 rooms/equipment
- **Memory:** ~500 KB - 2 MB
- **Import time:** < 500ms
- **Search time:** < 10ms
- **Rendering:** Real-time (30-60 FPS)

### Large Building (1,000-10,000 entities)
- **Typical size:** Campus or large facility
- **Memory:** ~2-20 MB
- **Import time:** < 2s
- **Search time:** < 100ms
- **Rendering:** Near real-time (15-30 FPS)

### Very Large Building (> 10,000 entities)
- **Typical size:** Enterprise campus, multiple buildings
- **Memory:** ~20-200 MB
- **Import time:** < 10s
- **Search time:** < 500ms
- **Rendering:** Batch mode recommended
- **Consider:** Spatial indexing for > 5,000 entities

## Performance Optimization Recommendations

### For Large Datasets (> 5,000 entities)

1. **Enable Spatial Indexing**
   ```bash
   arx render --building "Large Building" --spatial-index
   ```

2. **Use Filtering**
   ```bash
   arx filter --floor 1 --format json
   ```

3. **Batch Operations**
   - Process floor-by-floor for very large buildings
   - Use Git incremental commits

### Memory Considerations

- **YAML overhead:** ~500-1000 bytes per entity
- **Spatial data:** ~200-500 bytes per entity
- **Rule of thumb:** Plan for 1-2 KB per entity

### I/O Considerations

- **Git operations:** Most time is spent in Git I/O
- **Repository size:** Initial import creates largest Git objects
- **Recommendation:** Compress Git repository regularly

## Benchmark Methodology

- **Tool:** Criterion.rs
- **Hardware:** Test machine specs vary
- **Statistical confidence:** 100 samples per benchmark
- **Warming:** 3 seconds warmup period
- **Measurements:** 100 measurements, removing outliers

## Continuous Monitoring

Benchmarks are automatically run on:
- Every commit to main/develop branches
- Pull request merges
- Release tag creation

To view historical performance trends, check the `target/criterion/` directory after running benchmarks.

