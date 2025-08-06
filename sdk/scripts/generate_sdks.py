#!/usr/bin/env python3
"""
Arxos SDK Generation Script
Main script for generating client SDKs from OpenAPI specifications.

Usage:
    python generate_sdks.py [--service SERVICE] [--language LANGUAGE] [--config CONFIG]
"""

import argparse
import sys
import logging
from pathlib import Path

# Add the generator module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "generator"))

from generator import SDKGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for SDK generation"""
    parser = argparse.ArgumentParser(
        description="Generate Arxos SDKs from OpenAPI specifications"
    )
    parser.add_argument(
        "--service",
        help="Specific service to generate SDK for (e.g., arx-backend, arx-cmms)",
        default=None,
    )
    parser.add_argument(
        "--language",
        help="Specific language to generate SDK for (e.g., typescript, python, go)",
        default=None,
    )
    parser.add_argument(
        "--config",
        help="Path to generator configuration file",
        default="generator/config/generator.yaml",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate OpenAPI specs without generating SDKs",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize SDK generator
        generator = SDKGenerator(args.config)

        if args.validate_only:
            # Only validate OpenAPI specs
            logger.info("🔍 Validating OpenAPI specifications...")
            for service_name, service_config in generator.services.items():
                if args.service and service_name != args.service:
                    continue

                logger.info(f"Validating {service_name}...")
                if generator.validator.validate_spec(service_config.openapi_spec):
                    logger.info(f"✅ {service_name} spec is valid")
                else:
                    logger.error(f"❌ {service_name} spec is invalid")
                    sys.exit(1)

            logger.info("🎉 All OpenAPI specifications are valid!")
            return

        # Generate SDKs
        if args.service and args.language:
            # Generate specific service and language
            if args.service not in generator.services:
                logger.error(f"Service '{args.service}' not found")
                sys.exit(1)

            if args.language not in generator.config.languages:
                logger.error(f"Language '{args.language}' not supported")
                sys.exit(1)

            service_config = generator.services[args.service]
            if args.language not in service_config.languages:
                logger.error(
                    f"Language '{args.language}' not supported for service '{args.service}'"
                )
                sys.exit(1)

            logger.info(f"🚀 Generating {args.language} SDK for {args.service}...")
            generator.generate_sdk(args.service, args.language, service_config)
            logger.info(f"✅ Generated {args.language} SDK for {args.service}")

        elif args.service:
            # Generate all languages for specific service
            if args.service not in generator.services:
                logger.error(f"Service '{args.service}' not found")
                sys.exit(1)

            service_config = generator.services[args.service]
            logger.info(f"🚀 Generating all language SDKs for {args.service}...")

            for language in generator.config.languages:
                if language in service_config.languages:
                    try:
                        generator.generate_sdk(args.service, language, service_config)
                        logger.info(f"✅ Generated {language} SDK for {args.service}")
                    except Exception as e:
                        logger.error(
                            f"❌ Failed to generate {language} SDK for {args.service}: {e}"
                        )
                else:
                    logger.info(
                        f"⏭️ Skipping {language} for {args.service} (not supported)"
                    )

        elif args.language:
            # Generate specific language for all services
            if args.language not in generator.config.languages:
                logger.error(f"Language '{args.language}' not supported")
                sys.exit(1)

            logger.info(f"🚀 Generating {args.language} SDKs for all services...")

            for service_name, service_config in generator.services.items():
                if args.language in service_config.languages:
                    try:
                        generator.generate_sdk(
                            service_name, args.language, service_config
                        )
                        logger.info(
                            f"✅ Generated {args.language} SDK for {service_name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"❌ Failed to generate {args.language} SDK for {service_name}: {e}"
                        )
                else:
                    logger.info(
                        f"⏭️ Skipping {service_name} for {args.language} (not supported)"
                    )

        else:
            # Generate all SDKs
            logger.info("🚀 Generating all SDKs...")
            generator.generate_all_sdks()

        logger.info("🎉 SDK generation completed successfully!")

    except Exception as e:
        logger.error(f"❌ SDK generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
