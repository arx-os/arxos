## Multi-stage Dockerfile for ArxOS

# ---- Builder Stage -------------------------------------------------------
FROM rust:1.83-bookworm AS builder

LABEL org.opencontainers.image.source="https://github.com/arx-os/arxos"

ENV CARGO_HOME=/usr/local/cargo \
    RUSTUP_HOME=/usr/local/rustup \
    PATH="/usr/local/cargo/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    clang \
    pkg-config \
    libssl-dev \
    libclang-dev \
    cmake \
    protobuf-compiler \
    python3 \
    python3-pip \
    git \
    curl \
    unzip && \
    rm -rf /var/lib/apt/lists/*

# Install tooling needed by build.rs (cbindgen) and optional wasm support
RUN cargo install --locked cbindgen wasm-pack

WORKDIR /workspace

# Pre-copy manifests to maximize Docker layer caching
COPY Cargo.toml Cargo.lock ./

# Fetch dependencies first (cached)
RUN cargo fetch

# Copy the rest of the workspace
COPY benches ./benches
COPY docs ./docs
COPY include ./include
COPY scripts ./scripts
COPY tests ./tests
COPY examples ./examples
COPY test_data ./test_data
COPY src ./src
COPY README.md .
COPY SECURITY.txt .

# Build release mode
RUN cargo build --release

# Export commonly used artifacts for downstream stages
RUN mkdir -p /artifacts/bin /artifacts/lib /artifacts/include && \
    cp target/release/arx /artifacts/bin/ && \
    find target/release -maxdepth 1 -type f -name "libarx*.so" -exec cp {} /artifacts/lib/ \; && \
    if [ -f include/arxos_mobile.h ]; then cp include/arxos_mobile.h /artifacts/include/; fi && \
    cp docs/CLI_REFERENCE.md /artifacts/CLI_REFERENCE.md

# ---- Runtime Stage -------------------------------------------------------
FROM debian:bookworm-slim AS runtime

ARG ARXOS_USER=arxos
ARG ARXOS_UID=10001
ARG ARXOS_GID=10001

ENV ARX_HOME=/opt/arxos \
    PATH="/usr/local/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    git && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid ${ARXOS_GID} ${ARXOS_USER} && \
    useradd --home-dir ${ARX_HOME} --shell /usr/sbin/nologin \
    --uid ${ARXOS_UID} --gid ${ARXOS_GID} ${ARXOS_USER}

WORKDIR ${ARX_HOME}

COPY --from=builder /artifacts/bin/arx /usr/local/bin/arx
COPY --from=builder /artifacts/lib ${ARX_HOME}/lib
COPY --from=builder /artifacts/include ${ARX_HOME}/include
COPY --from=builder /artifacts/CLI_REFERENCE.md ${ARX_HOME}/CLI_REFERENCE.md

VOLUME ["/workspace"]

USER ${ARXOS_USER}

ENTRYPOINT ["arx"]
CMD ["--help"]

# ---- Metadata ------------------------------------------------------------
LABEL org.opencontainers.image.title="ArxOS Runtime" \
    org.opencontainers.image.url="https://arxos.io" \
    org.opencontainers.image.description="Official ArxOS runtime image with CLI." \
    org.opencontainers.image.licenses="MIT"
