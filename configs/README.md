# ArxOS Configuration Files

This directory contains configuration files and examples for different deployment scenarios.

## Structure

- `development.yml` - Development configuration
- `production.yml` - Production configuration  
- `docker/` - Docker compose configurations

## Usage

```bash
# Use development config
arx --config configs/development.yml

# Use production config  
arx --config configs/production.yml

# Docker development
docker-compose -f configs/docker/docker-compose.yml up

# Docker production
docker-compose -f configs/docker/docker-compose.yml -f configs/docker/docker-compose.prod.yml up
```
