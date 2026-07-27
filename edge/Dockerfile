# Arxos edge node — multi-arch (amd64 / arm64) for Raspberry Pi class hosts.
# Build: docker buildx build --platform linux/arm64,linux/amd64 -t arxos-edge -f edge/Dockerfile .

FROM rust:1.85-bookworm AS builder
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
COPY core ./core
COPY cli ./cli
COPY networking ./networking
COPY edge ./edge
COPY gateways ./gateways
# Workspace members not needed for edge binary still listed in root Cargo.toml
RUN mkdir -p contracts && touch contracts/.gitkeep
RUN cargo build --release -p arxos-edge -p arxos-cli

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /src/target/release/arxos-edge /usr/local/bin/arxos-edge
COPY --from=builder /src/target/release/arx /usr/local/bin/arx
ENV ARXOS_STORE=/data/store
VOLUME ["/data"]
EXPOSE 0
ENTRYPOINT ["arxos-edge"]
CMD ["version"]
