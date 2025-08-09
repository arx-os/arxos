"""
Tests for Funding Escrow System
Comprehensive test suite for escrow engine and API endpoints
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from funding.escrow_engine import (
    escrow_engine,
    EscrowAccount,
    Milestone,
    Transaction,
    EscrowStatus,
    MilestoneStatus,
    TransactionType
)


class TestEscrowEngine:
    """Test cases for the escrow engine core functionality"""

    def setup_method(self):
        """Reset escrow engine state before each test"""
        escrow_engine.escrow_accounts.clear()
        escrow_engine.pending_approvals.clear()

    def test_create_escrow_account(self):
        """Test creating a new escrow account"""
        project_id = "proj-123"
        creator_id = "user-456"
        total_amount = Decimal("10000")
        milestones = [
            {
                "title": "Design Phase",
                "description": "Complete architectural design",
                "amount": "5000",
                "due_date": "2024-12-31T23:59:59"
            },
            {
                "title": "Construction Phase",
                "description": "Complete construction",
                "amount": "5000",
                "due_date": "2025-06-30T23:59:59"
            }
        ]
        governance_board = ["board-1", "board-2", "board-3"]

        escrow_account = escrow_engine.create_escrow_account(
            project_id=project_id,
            creator_id=creator_id,
            total_amount=total_amount,
            milestones=milestones,
            governance_board=governance_board
        )

        assert escrow_account.project_id == project_id
        assert escrow_account.creator_id == creator_id
        assert escrow_account.total_amount == total_amount
        assert escrow_account.status == EscrowStatus.PENDING
        assert len(escrow_account.milestones) == 2
        assert len(escrow_account.governance_board) == 3
        assert len(escrow_account.transactions) == 1

        # Verify transaction
        transaction = escrow_account.transactions[0]
        assert transaction.transaction_type == TransactionType.ESCROW_CREATED
        assert transaction.escrow_id == escrow_account.id

    def test_deposit_funds(self):
        """Test depositing funds into escrow account"""
        # Create escrow account first
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[],
            governance_board=[]
        )

        # Deposit funds
        success = escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("5000"),
            user_id="backer-1"
        )

        assert success is True
        assert escrow_account.current_balance == Decimal("5000")
        assert len(escrow_account.transactions) == 2

        # Verify deposit transaction
        deposit_transaction = escrow_account.transactions[1]
        assert deposit_transaction.transaction_type == TransactionType.FUNDS_DEPOSITED
        assert deposit_transaction.amount == Decimal("5000")
        assert deposit_transaction.user_id == "backer-1"

    def test_deposit_funds_activate_escrow(self):
        """Test that escrow activates when target amount is reached"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[],
            governance_board=[]
        )

        # Deposit full amount
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        assert escrow_account.status == EscrowStatus.ACTIVE
        assert escrow_account.current_balance == Decimal("10000")

    def test_submit_milestone(self):
        """Test submitting a milestone for approval"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "10000",
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Activate escrow
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        # Submit milestone
        milestone_id = escrow_account.milestones[0].id
        success = escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            evidence_urls=["https://example.com/design.pdf"],
            creator_id="user-456"
        )

        assert success is True
        assert escrow_account.milestones[0].status == MilestoneStatus.SUBMITTED
        assert escrow_account.milestones[0].submitted_at is not None
        assert len(escrow_account.milestones[0].evidence_urls) == 1

        # Verify transaction
        submit_transaction = escrow_account.transactions[-1]
        assert submit_transaction.transaction_type == TransactionType.MILESTONE_SUBMITTED
        assert submit_transaction.amount == Decimal("10000")

    def test_approve_milestone(self):
        """Test approving a milestone and releasing funds"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "10000",
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Activate escrow and submit milestone
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        milestone_id = escrow_account.milestones[0].id
        escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            evidence_urls=["https://example.com/design.pdf"],
            creator_id="user-456"
        )

        # Approve milestone
        success = escrow_engine.approve_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            approver_id="board-1"
        )

        assert success is True
        assert escrow_account.milestones[0].status == MilestoneStatus.APPROVED
        assert escrow_account.milestones[0].approved_at is not None
        assert escrow_account.milestones[0].approved_by == "board-1"
        assert escrow_account.current_balance == Decimal("0")
        assert escrow_account.status == EscrowStatus.COMPLETED

        # Verify transactions
        transactions = escrow_account.transactions
        assert len(transactions) == 5  # created, deposit, submit, approve, release
        assert transactions[-2].transaction_type == TransactionType.MILESTONE_APPROVED
        assert transactions[-1].transaction_type == TransactionType.FUNDS_RELEASED

    def test_reject_milestone(self):
        """Test rejecting a milestone"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "10000",
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Activate escrow and submit milestone
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        milestone_id = escrow_account.milestones[0].id
        escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            evidence_urls=["https://example.com/design.pdf"],
            creator_id="user-456"
        )

        # Reject milestone
        success = escrow_engine.reject_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            rejector_id="board-1",
            reason="Incomplete design documentation"
        )

        assert success is True
        assert escrow_account.milestones[0].status == MilestoneStatus.REJECTED
        assert escrow_account.milestones[0].rejection_reason == "Incomplete design documentation"
        assert escrow_account.current_balance == Decimal("10000")  # No funds released

        # Verify transaction
        reject_transaction = escrow_account.transactions[-1]
        assert reject_transaction.transaction_type == TransactionType.MILESTONE_REJECTED
        assert reject_transaction.user_id == "board-1"

    def test_get_escrow_summary(self):
        """Test getting escrow account summary"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "5000",
                    "due_date": "2024-12-31T23:59:59"
                },
                {
                    "title": "Construction Phase",
                    "description": "Complete construction",
                    "amount": "5000",
                    "due_date": "2025-06-30T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Deposit funds
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        summary = escrow_engine.get_escrow_summary(escrow_account.id)

        assert summary["escrow_id"] == escrow_account.id
        assert summary["project_id"] == "proj-123"
        assert summary["status"] == "active"
        assert summary["total_amount"] == "10000"
        assert summary["current_balance"] == "10000"
        assert summary["funding_progress"] == 100.0
        assert summary["milestone_stats"]["total"] == 2
        assert summary["milestone_stats"]["completed"] == 0
        assert summary["milestone_stats"]["remaining"] == 2

    def test_get_pending_approvals(self):
        """Test getting pending approvals for governance board member"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "10000",
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Activate escrow and submit milestone
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        milestone_id = escrow_account.milestones[0].id
        escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            evidence_urls=["https://example.com/design.pdf"],
            creator_id="user-456"
        )

        # Get pending approvals for board member
        pending = escrow_engine.get_pending_approvals("board-1")

        assert len(pending) == 1
        assert pending[0]["escrow_id"] == escrow_account.id
        assert pending[0]["milestone_id"] == milestone_id
        assert pending[0]["project_id"] == "proj-123"
        assert pending[0]["milestone_title"] == "Design Phase"
        assert pending[0]["amount"] == "10000"

    def test_unauthorized_approval(self):
        """Test that non-board members cannot approve milestones"""
        escrow_account = escrow_engine.create_escrow_account(
            project_id="proj-123",
            creator_id="user-456",
            total_amount=Decimal("10000"),
            milestones=[
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": "10000",
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            governance_board=["board-1", "board-2"]
        )

        # Activate escrow and submit milestone
        escrow_engine.deposit_funds(
            escrow_id=escrow_account.id,
            amount=Decimal("10000"),
            user_id="backer-1"
        )

        milestone_id = escrow_account.milestones[0].id
        escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone_id,
            evidence_urls=["https://example.com/design.pdf"],
            creator_id="user-456"
        )

        # Try to approve with unauthorized user
        with pytest.raises(ValueError, match="User unauthorized-user not authorized"):
            escrow_engine.approve_milestone(
                escrow_id=escrow_account.id,
                milestone_id=milestone_id,
                approver_id="unauthorized-user"
            )

    def test_invalid_escrow_id(self):
        """Test handling of invalid escrow IDs"""
        with pytest.raises(ValueError, match="Escrow account invalid-id not found"):
            escrow_engine.deposit_funds(
                escrow_id="invalid-id",
                amount=Decimal("1000"),
                user_id="user-1"
            )

    def test_milestone_amount_validation(self):
        """Test that milestone amounts must sum to total amount"""
        with pytest.raises(ValueError, match="Milestone amounts"):
            escrow_engine.create_escrow_account(
                project_id="proj-123",
                creator_id="user-456",
                total_amount=Decimal("10000"),
                milestones=[
                    {
                        "title": "Design Phase",
                        "description": "Complete architectural design",
                        "amount": "3000",
                        "due_date": "2024-12-31T23:59:59"
                    },
                    {
                        "title": "Construction Phase",
                        "description": "Complete construction",
                        "amount": "3000",
                        "due_date": "2025-06-30T23:59:59"
                    }
                ],
                governance_board=["board-1"]
            )


class TestEscrowAPI:
    """Test cases for the escrow API endpoints"""

    @pytest.fixture
def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_create_escrow_account_api(self, client):
        """Test creating escrow account via API"""
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": 5000,
                    "due_date": "2024-12-31T23:59:59"
                },
                {
                    "title": "Construction Phase",
                    "description": "Complete construction",
                    "amount": 5000,
                    "due_date": "2025-06-30T23:59:59"
                }
            ],
            "governance_board": ["board-1", "board-2"],
            "auto_release": True
        }

        response = client.post("/api/funding/escrow/create", json=escrow_data)

        assert response.status_code == 200
        data = response.json()
        assert "escrow_id" in data
        assert data["status"] == "created"

    def test_deposit_funds_api(self, client):
        """Test depositing funds via API"""
        # First create escrow account
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [],
            "governance_board": []
        }

        create_response = client.post("/api/funding/escrow/create", json=escrow_data)
        escrow_id = create_response.json()["escrow_id"]

        # Deposit funds
        deposit_data = {
            "amount": 5000,
            "user_id": "backer-1"
        }

        response = client.post(f"/api/funding/escrow/{escrow_id}/deposit", json=deposit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["amount_deposited"] == "5000"

    def test_submit_milestone_api(self, client):
        """Test submitting milestone via API"""
        # Create escrow with milestone
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": 10000,
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            "governance_board": ["board-1"]
        }

        create_response = client.post("/api/funding/escrow/create", json=escrow_data)
        escrow_id = create_response.json()["escrow_id"]

        # Activate escrow
        client.post(f"/api/funding/escrow/{escrow_id}/deposit", json={
            "amount": 10000,
            "user_id": "backer-1"
        })

        # Get milestone ID from summary import summary
        summary_response = client.get(f"/api/funding/escrow/{escrow_id}/summary")
        milestone_id = summary_response.json()["milestones"][0]["id"]

        # Submit milestone
        submit_data = {
            "evidence_urls": ["https://example.com/design.pdf"],
            "user_id": "user-456"
        }

        response = client.post(f"/api/funding/escrow/{escrow_id}/milestones/{milestone_id}/submit", json=submit_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"

    def test_approve_milestone_api(self, client):
        """Test approving milestone via API"""
        # Create escrow with milestone
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": 10000,
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            "governance_board": ["board-1"]
        }

        create_response = client.post("/api/funding/escrow/create", json=escrow_data)
        escrow_id = create_response.json()["escrow_id"]

        # Activate escrow and submit milestone
        client.post(f"/api/funding/escrow/{escrow_id}/deposit", json={
            "amount": 10000,
            "user_id": "backer-1"
        })

        summary_response = client.get(f"/api/funding/escrow/{escrow_id}/summary")
        milestone_id = summary_response.json()["milestones"][0]["id"]

        client.post(f"/api/funding/escrow/{escrow_id}/milestones/{milestone_id}/submit", json={
            "evidence_urls": ["https://example.com/design.pdf"],
            "user_id": "user-456"
        })

        # Approve milestone
        approve_data = {
            "approver_id": "board-1",
            "is_override": False
        }

        response = client.post(f"/api/funding/escrow/{escrow_id}/milestones/{milestone_id}/approve", json=approve_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_get_escrow_summary_api(self, client):
        """Test getting escrow summary via API"""
        # Create escrow account
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [],
            "governance_board": []
        }

        create_response = client.post("/api/funding/escrow/create", json=escrow_data)
        escrow_id = create_response.json()["escrow_id"]

        # Get summary
        response = client.get(f"/api/funding/escrow/{escrow_id}/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["escrow_id"] == escrow_id
        assert data["project_id"] == "proj-123"
        assert data["status"] == "pending"

    def test_get_pending_approvals_api(self, client):
        """Test getting pending approvals via API"""
        # Create escrow with milestone
        escrow_data = {
            "project_id": "proj-123",
            "creator_id": "user-456",
            "total_amount": 10000,
            "milestones": [
                {
                    "title": "Design Phase",
                    "description": "Complete architectural design",
                    "amount": 10000,
                    "due_date": "2024-12-31T23:59:59"
                }
            ],
            "governance_board": ["board-1"]
        }

        create_response = client.post("/api/funding/escrow/create", json=escrow_data)
        escrow_id = create_response.json()["escrow_id"]

        # Activate escrow and submit milestone
        client.post(f"/api/funding/escrow/{escrow_id}/deposit", json={
            "amount": 10000,
            "user_id": "backer-1"
        })

        summary_response = client.get(f"/api/funding/escrow/{escrow_id}/summary")
        milestone_id = summary_response.json()["milestones"][0]["id"]

        client.post(f"/api/funding/escrow/{escrow_id}/milestones/{milestone_id}/submit", json={
            "evidence_urls": ["https://example.com/design.pdf"],
            "user_id": "user-456"
        })

        # Get pending approvals
        response = client.get("/api/funding/escrow/pending-approvals/board-1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["escrow_id"] == escrow_id
        assert data[0]["milestone_id"] == milestone_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
