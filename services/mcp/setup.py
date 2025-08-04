from setuptools import setup, find_packages

setup(
    name="arx-mcp",
    version="1.0.0",
    description="Arxos MCP (Model Context Protocol) Package for regulatory compliance workflows",
    author="Arxos Platform Team",
    packages=find_packages(),
    install_requires=[
        "jsonschema>=4.0.0",
        "python-dateutil>=2.8.0",
        "numpy>=1.21.0",
        "colorlog>=6.0.0",
    ],
    python_requires=">=3.8",
) 