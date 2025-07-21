"""
Auto Snapshot Router

Provides endpoints for automatic snapshot creation and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path

from ..models.snapshot import Snapshot, SnapshotCreate, SnapshotResponse
from ..services.snapshot_service import SnapshotService
from core.utils.auth

router = APIRouter(prefix="/auto-snapshot", tags=["Auto Snapshot"])

@router.post("/create", response_model=SnapshotResponse)
async def create_auto_snapshot(
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(get_current_user)
):
    """Create an automatic snapshot of the current state"""
    try:
        snapshot_service = SnapshotService()
        snapshot = await snapshot_service.create_snapshot(snapshot_data, current_user)
        return SnapshotResponse(
            id=snapshot.id,
            name=snapshot.name,
            description=snapshot.description,
            created_at=snapshot.created_at,
            created_by=snapshot.created_by,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")

@router.get("/list", response_model=List[SnapshotResponse])
async def list_auto_snapshots(
    current_user: User = Depends(get_current_user),
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """List all automatic snapshots"""
    try:
        snapshot_service = SnapshotService()
        snapshots = await snapshot_service.list_snapshots(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        return [
            SnapshotResponse(
                id=snapshot.id,
                name=snapshot.name,
                description=snapshot.description,
                created_at=snapshot.created_at,
                created_by=snapshot.created_by,
                status="completed"
            )
            for snapshot in snapshots
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")

@router.delete("/{snapshot_id}")
async def delete_auto_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an automatic snapshot"""
    try:
        snapshot_service = SnapshotService()
        await snapshot_service.delete_snapshot(snapshot_id, current_user.id)
        return {"message": "Snapshot deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete snapshot: {str(e)}") 