#!/usr/bin/env python3
"""
Setup script for Arxos SVG-BIM Integration System.

This package provides comprehensive SVG to BIM conversion capabilities
with symbol management, validation, and API services.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the README file for long description
def read_readme():
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return "Arxos SVG-BIM Integration System"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Package metadata
PACKAGE_NAME = "arx_svg_parser"
VERSION = "1.0.0"
AUTHOR = "Arxos Development Team"
AUTHOR_EMAIL = "dev@arxos.com"
DESCRIPTION = "Comprehensive SVG to BIM conversion and symbol management system"
LONG_DESCRIPTION = read_readme()
URL = "https://github.com/arxos/arxos"
PROJECT_URLS = {
    "Bug Tracker": "https://github.com/arxos/arxos/issues",
    "Documentation": "https://docs.arxos.com",
    "Source Code": "https://github.com/arxos/arxos",
}

# Classifiers for PyPI
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup :: XML",
]

# Keywords for PyPI search
KEYWORDS = [
    "svg", "bim", "building-information-modeling", "symbol-management",
    "architecture", "engineering", "construction", "aec", "fastapi",
    "validation", "json-schema", "api"
]

# Package configuration
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    project_urls=PROJECT_URLS,
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    packages=find_packages(include=["arx_svg_parser", "arx_svg_parser.*"]),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "isort>=5.13.2",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
            "bandit>=1.7.5",
            "safety>=2.3.5",
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "production": [
            "gunicorn>=21.2.0",
            "celery>=5.3.4",
            "redis>=5.0.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "arx-svg-parser=arx_svg_parser.main:main",
            "arx-validate-symbols=arx_svg_parser.scripts.validate_symbols:main",
        ],
    },
    include_package_data=True,
    package_data={
        "arx_svg_parser": [
            "schemas/*.json",
            "data/*.json",
            "docs/*.md",
        ],
    },
    zip_safe=False,
    license="MIT",
    platforms=["any"],
) 