#!/usr/bin/env python3
"""
Setup script for Alembic autogeneration

This script helps set up the environment for Alembic autogeneration
by creating the necessary model imports and metadata configuration.
"""

import os
import sys
from pathlib import Path

def create_models_file():
    """Create a models.py file with SQLAlchemy model definitions."""

    models_content = '''""
SQLAlchemy models for Arxos database

This file contains all the SQLAlchemy model definitions that will be used
for Alembic autogeneration of migrations.
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, server_default='user')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    # Relationships
    projects = relationship("Project", back_populates="user")
    buildings_owned = relationship("Building", back_populates="owner")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    # Relationships
    user = relationship("User", back_populates="projects")
    buildings = relationship("Building", back_populates="project")

class Building(Base):
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    # Relationships
    owner = relationship("User", back_populates="buildings_owned")
    project = relationship("Project", back_populates="buildings")
    floors = relationship("Floor", back_populates="building")
    categories = relationship("Category", back_populates="building")

class Floor(Base):
    __tablename__ = 'floors'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE')
    svg_path = Column(String(255)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    # Relationships
    building = relationship("Building", back_populates="floors")
    rooms = relationship("Room", back_populates="floor")

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    building_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE')
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp()
    # Relationships
    building = relationship("Building", back_populates="categories")

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(String(64), primary_key=True)
    name = Column(String(255)
    layer = Column(String(100)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL')
    status = Column(String(50)
    source_svg = Column(String(255)
    svg_id = Column(String(255)
    locked_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL')
    assigned_to = Column(Integer, ForeignKey('users.id', ondelete='SET NULL')
    building_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE')
    floor_id = Column(Integer, ForeignKey('floors.id', ondelete='CASCADE')
    geom = Column(Text)  # PostGIS geometry
    category = Column(String(100), nullable=False, server_default='')
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE')
    # Relationships
    floor = relationship("Floor", back_populates="rooms")

# Add more model classes as needed for other tables
# This is a starting point - you can add the remaining models
# following the same pattern as above.

if __name__ == "__main__":
    print("Models file created successfully!")
    print("You can now use 'alembic revision --autogenerate -m \"description\"'")
    print("to automatically generate migration files based on model changes.")
'''

    with open('models.py', 'w') as f:
        f.write(models_content)

    print("✅ Created models.py file")

def update_env_py():
    """Update the env.py file to include model imports for autogeneration."""

    env_py_content = '''from logging.config import fileConfig'
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the current directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your SQLAlchemy models here
from models import Base, User, Project, Building, Floor, Category, Room

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here'
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.'

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    with open('alembic/env.py', 'w') as f:
        f.write(env_py_content)

    print("✅ Updated alembic/env.py for autogeneration")

def main():
    """Main setup function."""
    print("🔧 Setting up Alembic autogeneration...")

    # Check if we're in the right directory'
    if not os.path.exists('alembic'):
        print("❌ Error: alembic directory not found. Run 'alembic init alembic' first.")
        sys.exit(1)

    # Create models file
    create_models_file()

    # Update env.py
    update_env_py()

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Add your SQLAlchemy models to models.py")
    print("2. Run: alembic revision --autogenerate -m \"your migration description\"")
    print("3. Review the generated migration file")
    print("4. Run: alembic upgrade head")

if __name__ == "__main__":
    main()
