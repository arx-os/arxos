"""Create initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_projects_user_id", "projects", ["user_id"])
    op.create_index("idx_projects_created_at", "projects", ["created_at"])

    # Create buildings table
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_buildings_project_id", "buildings", ["project_id"])
    op.create_index("idx_buildings_owner_id", "buildings", ["owner_id"])
    op.create_index("idx_buildings_created_at", "buildings", ["created_at"])
    op.create_index("idx_buildings_updated_at", "buildings", ["updated_at"])

    # Create floors table
    op.create_table(
        "floors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("svg_path", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_floors_building_id", "floors", ["building_id"])
    op.create_index("idx_floors_name", "floors", ["name"])

    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_categories_building_id", "categories", ["building_id"])
    op.create_index("idx_categories_name", "categories", ["name"])

    # Create rooms table
    op.create_table(
        "rooms",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rooms_geom", "rooms", ["geom"], postgresql_using="gist")
    op.create_index("idx_rooms_assigned_to", "rooms", ["assigned_to"])
    op.create_index("idx_rooms_status", "rooms", ["status"])
    op.create_index("idx_rooms_created_by", "rooms", ["created_by"])
    op.create_index("idx_rooms_locked_by", "rooms", ["locked_by"])
    op.create_index("idx_rooms_building_id", "rooms", ["building_id"])
    op.create_index("idx_rooms_project_id", "rooms", ["project_id"])
    op.create_index("idx_rooms_floor_id", "rooms", ["floor_id"])
    op.create_index("idx_rooms_building_floor", "rooms", ["building_id", "floor_id"])
    op.create_index("idx_rooms_category", "rooms", ["category"])
    op.create_index("idx_rooms_layer", "rooms", ["layer"])
    op.create_index("idx_rooms_name", "rooms", ["name"])

    # Create walls table
    op.create_table(
        "walls",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("material", sa.String(length=100), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_walls_geom", "walls", ["geom"], postgresql_using="gist")
    op.create_index("idx_walls_assigned_to", "walls", ["assigned_to"])
    op.create_index("idx_walls_status", "walls", ["status"])
    op.create_index("idx_walls_created_by", "walls", ["created_by"])
    op.create_index("idx_walls_locked_by", "walls", ["locked_by"])
    op.create_index("idx_walls_building_id", "walls", ["building_id"])
    op.create_index("idx_walls_project_id", "walls", ["project_id"])
    op.create_index("idx_walls_room_id", "walls", ["room_id"])
    op.create_index("idx_walls_floor_id", "walls", ["floor_id"])
    op.create_index("idx_walls_building_floor", "walls", ["building_id", "floor_id"])
    op.create_index("idx_walls_project_status", "walls", ["project_id", "status"])
    op.create_index("idx_walls_material", "walls", ["material"])
    op.create_index("idx_walls_layer", "walls", ["layer"])
    op.create_index("idx_walls_category", "walls", ["category"])

    # Create doors table
    op.create_table(
        "doors",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("material", sa.String(length=100), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_doors_geom", "doors", ["geom"], postgresql_using="gist")
    op.create_index("idx_doors_assigned_to", "doors", ["assigned_to"])
    op.create_index("idx_doors_status", "doors", ["status"])
    op.create_index("idx_doors_created_by", "doors", ["created_by"])
    op.create_index("idx_doors_locked_by", "doors", ["locked_by"])
    op.create_index("idx_doors_building_id", "doors", ["building_id"])
    op.create_index("idx_doors_project_id", "doors", ["project_id"])
    op.create_index("idx_doors_room_id", "doors", ["room_id"])
    op.create_index("idx_doors_floor_id", "doors", ["floor_id"])
    op.create_index("idx_doors_building_floor", "doors", ["building_id", "floor_id"])
    op.create_index("idx_doors_project_status", "doors", ["project_id", "status"])
    op.create_index("idx_doors_material", "doors", ["material"])
    op.create_index("idx_doors_layer", "doors", ["layer"])
    op.create_index("idx_doors_category", "doors", ["category"])

    # Create windows table
    op.create_table(
        "windows",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("material", sa.String(length=100), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_windows_geom", "windows", ["geom"], postgresql_using="gist")
    op.create_index("idx_windows_assigned_to", "windows", ["assigned_to"])
    op.create_index("idx_windows_status", "windows", ["status"])
    op.create_index("idx_windows_created_by", "windows", ["created_by"])
    op.create_index("idx_windows_locked_by", "windows", ["locked_by"])
    op.create_index("idx_windows_building_id", "windows", ["building_id"])
    op.create_index("idx_windows_project_id", "windows", ["project_id"])
    op.create_index("idx_windows_room_id", "windows", ["room_id"])
    op.create_index("idx_windows_floor_id", "windows", ["floor_id"])
    op.create_index(
        "idx_windows_building_floor", "windows", ["building_id", "floor_id"]
    )
    op.create_index("idx_windows_project_status", "windows", ["project_id", "status"])
    op.create_index("idx_windows_material", "windows", ["material"])
    op.create_index("idx_windows_layer", "windows", ["layer"])
    op.create_index("idx_windows_category", "windows", ["category"])

    # Create devices table
    op.create_table(
        "devices",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=True),
        sa.Column("system", sa.String(length=100), nullable=True),
        sa.Column("subtype", sa.String(length=100), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_devices_geom", "devices", ["geom"], postgresql_using="gist")
    op.create_index("idx_devices_assigned_to", "devices", ["assigned_to"])
    op.create_index("idx_devices_status", "devices", ["status"])
    op.create_index("idx_devices_created_by", "devices", ["created_by"])
    op.create_index("idx_devices_locked_by", "devices", ["locked_by"])
    op.create_index("idx_devices_building_id", "devices", ["building_id"])
    op.create_index("idx_devices_project_id", "devices", ["project_id"])
    op.create_index("idx_devices_room_id", "devices", ["room_id"])
    op.create_index("idx_devices_floor_id", "devices", ["floor_id"])
    op.create_index(
        "idx_devices_building_floor", "devices", ["building_id", "floor_id"]
    )
    op.create_index("idx_devices_project_status", "devices", ["project_id", "status"])
    op.create_index("idx_devices_type", "devices", ["type"])
    op.create_index("idx_devices_system", "devices", ["system"])
    op.create_index("idx_devices_subtype", "devices", ["subtype"])
    op.create_index("idx_devices_layer", "devices", ["layer"])
    op.create_index("idx_devices_category", "devices", ["category"])

    # Create labels table
    op.create_table(
        "labels",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_labels_geom", "labels", ["geom"], postgresql_using="gist")
    op.create_index("idx_labels_assigned_to", "labels", ["assigned_to"])
    op.create_index("idx_labels_status", "labels", ["status"])
    op.create_index("idx_labels_created_by", "labels", ["created_by"])
    op.create_index("idx_labels_locked_by", "labels", ["locked_by"])
    op.create_index("idx_labels_building_id", "labels", ["building_id"])
    op.create_index("idx_labels_project_id", "labels", ["project_id"])
    op.create_index("idx_labels_room_id", "labels", ["room_id"])
    op.create_index("idx_labels_floor_id", "labels", ["floor_id"])
    op.create_index("idx_labels_building_floor", "labels", ["building_id", "floor_id"])
    op.create_index("idx_labels_project_status", "labels", ["project_id", "status"])
    op.create_index("idx_labels_text", "labels", ["text"])
    op.create_index("idx_labels_layer", "labels", ["layer"])
    op.create_index("idx_labels_category", "labels", ["category"])

    # Create zones table
    op.create_table(
        "zones",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("layer", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("source_svg", sa.String(length=255), nullable=True),
        sa.Column("svg_id", sa.String(length=255), nullable=True),
        sa.Column("locked_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=64), nullable=True),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("floor_id", sa.Integer(), nullable=True),
        sa.Column("geom", sa.Text(), nullable=True),  # PostGIS geometry
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["locked_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_zones_geom", "zones", ["geom"], postgresql_using="gist")
    op.create_index("idx_zones_assigned_to", "zones", ["assigned_to"])
    op.create_index("idx_zones_status", "zones", ["status"])
    op.create_index("idx_zones_created_by", "zones", ["created_by"])
    op.create_index("idx_zones_locked_by", "zones", ["locked_by"])
    op.create_index("idx_zones_building_id", "zones", ["building_id"])
    op.create_index("idx_zones_project_id", "zones", ["project_id"])
    op.create_index("idx_zones_room_id", "zones", ["room_id"])
    op.create_index("idx_zones_floor_id", "zones", ["floor_id"])
    op.create_index("idx_zones_building_floor", "zones", ["building_id", "floor_id"])
    op.create_index("idx_zones_project_status", "zones", ["project_id", "status"])
    op.create_index("idx_zones_name", "zones", ["name"])
    op.create_index("idx_zones_layer", "zones", ["layer"])
    op.create_index("idx_zones_category", "zones", ["category"])

    # Create drawings table
    op.create_table(
        "drawings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_drawings_project_id", "drawings", ["project_id"])
    op.create_index("idx_drawings_name", "drawings", ["name"])
    op.create_index("idx_drawings_created_at", "drawings", ["created_at"])

    # Create comments table
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.String(length=64), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_comments_user_id", "comments", ["user_id"])
    op.create_index("idx_comments_object_id", "comments", ["object_id"])
    op.create_index("idx_comments_object_type", "comments", ["object_type"])
    op.create_index("idx_comments_created_at", "comments", ["created_at"])

    # Create assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.String(length=64), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column(
            "assigned_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_assignments_user_id", "assignments", ["user_id"])
    op.create_index("idx_assignments_object_id", "assignments", ["object_id"])
    op.create_index("idx_assignments_status", "assignments", ["status"])
    op.create_index("idx_assignments_object_type", "assignments", ["object_type"])
    op.create_index("idx_assignments_assigned_at", "assignments", ["assigned_at"])

    # Create object_history table
    op.create_table(
        "object_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.String(length=64), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=True),
        sa.Column("change_type", sa.String(length=50), nullable=True),
        sa.Column(
            "changed_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_object_history_user_id", "object_history", ["user_id"])
    op.create_index("idx_object_history_object_id", "object_history", ["object_id"])
    op.create_index("idx_object_history_change_type", "object_history", ["change_type"])
    op.create_index("idx_object_history_object_type", "object_history", ["object_type"])
    op.create_index("idx_object_history_changed_at", "object_history", ["changed_at"])

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.String(length=64), nullable=True),
        sa.Column("object_type", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_object_id", "audit_logs", ["object_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_object_type", "audit_logs", ["object_type"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])

    # Create user_category_permissions table
    op.create_table(
        "user_category_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("can_edit", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_category_permissions_user_id",
        "user_category_permissions",
        ["user_id"],
    )
    op.create_index(
        "idx_user_category_permissions_category_id",
        "user_category_permissions",
        ["category_id"],
    )
    op.create_index(
        "idx_user_category_permissions_project_id",
        "user_category_permissions",
        ["project_id"],
    )
    op.create_index(
        "idx_user_category_permissions_can_edit",
        "user_category_permissions",
        ["can_edit"],
    )

    # Create chat_messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("audit_log_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["audit_log_id"], ["audit_logs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_messages_building_id", "chat_messages", ["building_id"])
    op.create_index("idx_chat_messages_user_id", "chat_messages", ["user_id"])
    op.create_index("idx_chat_messages_audit_log_id", "chat_messages", ["audit_log_id"])
    op.create_index("idx_chat_messages_created_at", "chat_messages", ["created_at"])

    # Create catalog_items table
    op.create_table(
        "catalog_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("make", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("type", sa.String(length=100), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_catalog_items_category_id", "catalog_items", ["category_id"])
    op.create_index("idx_catalog_items_created_by", "catalog_items", ["created_by"])
    op.create_index("idx_catalog_items_make", "catalog_items", ["make"])
    op.create_index("idx_catalog_items_model", "catalog_items", ["model"])
    op.create_index("idx_catalog_items_type", "catalog_items", ["type"])
    op.create_index("idx_catalog_items_approved", "catalog_items", ["approved"])
    op.create_index("idx_catalog_items_created_at", "catalog_items", ["created_at"])
    op.create_index(
        "idx_catalog_items_make_model_type", "catalog_items", ["make", "model", "type"]
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("catalog_items")
    op.drop_table("chat_messages")
    op.drop_table("user_category_permissions")
    op.drop_table("audit_logs")
    op.drop_table("object_history")
    op.drop_table("assignments")
    op.drop_table("comments")
    op.drop_table("drawings")
    op.drop_table("zones")
    op.drop_table("labels")
    op.drop_table("devices")
    op.drop_table("windows")
    op.drop_table("doors")
    op.drop_table("walls")
    op.drop_table("rooms")
    op.drop_table("categories")
    op.drop_table("floors")
    op.drop_table("buildings")
    op.drop_table("projects")
    op.drop_table("users")

    # Drop PostGIS extension
    op.execute("DROP EXTENSION IF EXISTS postgis")
