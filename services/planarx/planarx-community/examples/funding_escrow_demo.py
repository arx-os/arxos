"""
Funding Escrow System Demo
Demonstrates the complete funding escrow workflow with realistic scenarios
"""

import asyncio
import json
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from funding.escrow_engine import escrow_engine, EscrowStatus, MilestoneStatus, TransactionType


class FundingEscrowDemo:
    """Demo class for showcasing funding escrow functionality"""
    
    def __init__(self):
        self.demo_data = {
            "project": {
                "id": "proj-sustainable-office",
                "title": "Sustainable Office Complex",
                "creator": "architect-sarah",
                "description": "A LEED-certified office building with green technologies"
            },
            "backers": [
                {"id": "backer-1", "name": "GreenTech Ventures", "amount": 5000},
                {"id": "backer-2", "name": "EcoBuild Foundation", "amount": 3000},
                {"id": "backer-3", "name": "Sustainable Cities Fund", "amount": 2000}
            ],
            "governance_board": [
                {"id": "board-1", "name": "Sarah Johnson", "role": "Lead Architect"},
                {"id": "board-2", "name": "Michael Chen", "role": "Structural Engineer"},
                {"id": "board-3", "name": "Emily Rodriguez", "role": "Sustainability Expert"},
                {"id": "board-4", "name": "David Thompson", "role": "Project Manager"},
                {"id": "board-5", "name": "Lisa Wang", "role": "Community Representative"}
            ]
        }
    
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_step(self, step_num, title, description=""):
        """Print a formatted step"""
        print(f"\n[STEP {step_num}] {title}")
        if description:
            print(f"   {description}")
        print("-" * 40)
    
    def print_success(self, message):
        """Print a success message"""
        print(f"✅ {message}")
    
    def print_info(self, message):
        """Print an info message"""
        print(f"ℹ️  {message}")
    
    def print_warning(self, message):
        """Print a warning message"""
        print(f"⚠️  {message}")
    
    def print_error(self, message):
        """Print an error message"""
        print(f"❌ {message}")
    
    def demo_escrow_creation(self):
        """Demo escrow account creation"""
        self.print_header("ESCROW ACCOUNT CREATION")
        
        # Define milestones
        milestones = [
            {
                "title": "Concept Design",
                "description": "Initial concept and feasibility study with sustainability analysis",
                "amount": "2000",
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            },
            {
                "title": "Detailed Design",
                "description": "Complete architectural and engineering design with green building features",
                "amount": "3000",
                "due_date": (datetime.now() + timedelta(days=90)).isoformat()
            },
            {
                "title": "Construction Documents",
                "description": "Final construction drawings and specifications for LEED certification",
                "amount": "2500",
                "due_date": (datetime.now() + timedelta(days=150)).isoformat()
            },
            {
                "title": "Permit Acquisition",
                "description": "Obtain all necessary building permits and environmental approvals",
                "amount": "1500",
                "due_date": (datetime.now() + timedelta(days=180)).isoformat()
            },
            {
                "title": "Project Completion",
                "description": "Final project delivery and LEED certification documentation",
                "amount": "1000",
                "due_date": (datetime.now() + timedelta(days=240)).isoformat()
            }
        ]
        
        governance_board = [member["id"] for member in self.demo_data["governance_board"]]
        
        self.print_step(1, "Creating Escrow Account", 
                       f"Project: {self.demo_data['project']['title']}")
        
        # Create escrow account
        escrow_account = escrow_engine.create_escrow_account(
            project_id=self.demo_data["project"]["id"],
            creator_id=self.demo_data["project"]["creator"],
            total_amount=Decimal("10000"),
            milestones=milestones,
            governance_board=governance_board,
            auto_release=True
        )
        
        self.print_success(f"Escrow account created: {escrow_account.id}")
        self.print_info(f"Total funding goal: $10,000")
        self.print_info(f"Number of milestones: {len(escrow_account.milestones)}")
        self.print_info(f"Governance board members: {len(escrow_account.governance_board)}")
        
        return escrow_account
    
    def demo_fund_deposits(self, escrow_account):
        """Demo fund deposits from multiple backers"""
        self.print_header("FUND DEPOSITS")
        
        self.print_step(2, "Processing Fund Deposits", 
                       "Multiple backers contributing to the project")
        
        total_deposited = Decimal("0")
        
        for backer in self.demo_data["backers"]:
            self.print_info(f"Processing deposit from {backer['name']}: ${backer['amount']:,}")
            
            success = escrow_engine.deposit_funds(
                escrow_id=escrow_account.id,
                amount=Decimal(str(backer["amount"])),
                user_id=backer["id"]
            )
            
            if success:
                total_deposited += Decimal(str(backer["amount"]))
                self.print_success(f"Deposit successful: ${backer['amount']:,}")
            else:
                self.print_error(f"Deposit failed: ${backer['amount']:,}")
        
        # Check escrow status
        summary = escrow_engine.get_escrow_summary(escrow_account.id)
        
        self.print_info(f"Total deposited: ${total_deposited:,}")
        self.print_info(f"Escrow status: {summary['status']}")
        self.print_info(f"Funding progress: {summary['funding_progress']:.1f}%")
        
        if summary['status'] == 'active':
            self.print_success("Escrow account activated! Project can now begin.")
        
        return escrow_account
    
    def demo_milestone_submission(self, escrow_account):
        """Demo milestone submission by creator"""
        self.print_header("MILESTONE SUBMISSION")
        
        # Get first milestone
        milestone = escrow_account.milestones[0]
        
        self.print_step(3, "Submitting First Milestone", 
                       f"Milestone: {milestone.title}")
        
        self.print_info(f"Creator: {self.demo_data['project']['creator']}")
        self.print_info(f"Milestone amount: ${milestone.amount:,}")
        self.print_info(f"Due date: {milestone.due_date.strftime('%Y-%m-%d')}")
        
        # Submit milestone
        success = escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone.id,
            evidence_urls=[
                "https://example.com/concept-design.pdf",
                "https://example.com/sustainability-analysis.pdf",
                "https://example.com/feasibility-study.pdf"
            ],
            creator_id=self.demo_data["project"]["creator"]
        )
        
        if success:
            self.print_success("Milestone submitted successfully!")
            self.print_info("Evidence files uploaded:")
            for url in milestone.evidence_urls:
                self.print_info(f"  - {url}")
            
            # Show pending approvals
            pending = escrow_engine.get_pending_approvals("board-1")
            self.print_info(f"Pending approvals: {len(pending)}")
            
            for approval in pending:
                self.print_info(f"  - {approval['milestone_title']} (${approval['amount']})")
        else:
            self.print_error("Milestone submission failed!")
        
        return escrow_account
    
    def demo_governance_approval(self, escrow_account):
        """Demo governance board approval process"""
        self.print_header("GOVERNANCE APPROVAL PROCESS")
        
        milestone = escrow_account.milestones[0]
        
        self.print_step(4, "Governance Board Review", 
                       f"Reviewing milestone: {milestone.title}")
        
        # Simulate board member review
        for board_member in self.demo_data["governance_board"][:3]:  # First 3 members
            self.print_info(f"Board member {board_member['name']} ({board_member['role']}) reviewing...")
            
            # Simulate approval decision
            if board_member["id"] in ["board-1", "board-2"]:  # Approve
                success = escrow_engine.approve_milestone(
                    escrow_id=escrow_account.id,
                    milestone_id=milestone.id,
                    approver_id=board_member["id"],
                    is_override=False
                )
                
                if success:
                    self.print_success(f"Approved by {board_member['name']}")
                    break  # Only need one approval
                else:
                    self.print_error(f"Approval failed by {board_member['name']}")
            else:
                self.print_info(f"Reviewing... (simulating review process)")
        
        # Check milestone status
        updated_milestone = escrow_engine.get_milestone_details(escrow_account.id, milestone.id)
        
        if updated_milestone["status"] == "approved":
            self.print_success("Milestone approved and funds released!")
            self.print_info(f"Amount released: ${milestone.amount:,}")
            self.print_info(f"Approved by: {updated_milestone['approved_by']}")
            self.print_info(f"Approval date: {updated_milestone['approved_at']}")
        else:
            self.print_warning("Milestone still pending approval")
        
        return escrow_account
    
    def demo_milestone_rejection(self, escrow_account):
        """Demo milestone rejection scenario"""
        self.print_header("MILESTONE REJECTION SCENARIO")
        
        # Get second milestone
        milestone = escrow_account.milestones[1]
        
        self.print_step(5, "Milestone Rejection Scenario", 
                       f"Demonstrating rejection process for: {milestone.title}")
        
        # Submit milestone with insufficient evidence
        self.print_info("Creator submits milestone with incomplete documentation...")
        
        success = escrow_engine.submit_milestone(
            escrow_id=escrow_account.id,
            milestone_id=milestone.id,
            evidence_urls=[
                "https://example.com/incomplete-design.pdf"
            ],
            creator_id=self.demo_data["project"]["creator"]
        )
        
        if success:
            self.print_info("Milestone submitted (with insufficient evidence)")
            
            # Simulate rejection
            self.print_info("Governance board reviewing...")
            
            rejection_reason = "Incomplete design documentation. Missing structural analysis and sustainability calculations."
            
            reject_success = escrow_engine.reject_milestone(
                escrow_id=escrow_account.id,
                milestone_id=milestone.id,
                rejector_id="board-3",
                reason=rejection_reason
            )
            
            if reject_success:
                self.print_warning("Milestone rejected!")
                self.print_info(f"Rejection reason: {rejection_reason}")
                self.print_info("Creator must resubmit with complete documentation")
            else:
                self.print_error("Rejection failed!")
        else:
            self.print_error("Milestone submission failed!")
        
        return escrow_account
    
    def demo_escrow_summary(self, escrow_account):
        """Demo comprehensive escrow summary"""
        self.print_header("ESCROW SUMMARY & ANALYTICS")
        
        self.print_step(6, "Generating Comprehensive Summary", 
                       "Complete escrow account overview")
        
        summary = escrow_engine.get_escrow_summary(escrow_account.id)
        
        print("\n📊 ESCROW ACCOUNT SUMMARY")
        print("=" * 40)
        print(f"Project: {self.demo_data['project']['title']}")
        print(f"Escrow ID: {summary['escrow_id']}")
        print(f"Status: {summary['status'].upper()}")
        print(f"Creator: {summary['creator_id']}")
        print()
        
        print("💰 FUNDING OVERVIEW")
        print("-" * 20)
        print(f"Total Goal: ${summary['total_amount']:,}")
        print(f"Current Balance: ${summary['current_balance']:,}")
        print(f"Total Released: ${summary['total_released']:,}")
        print(f"Funding Progress: {summary['funding_progress']:.1f}%")
        print()
        
        print("🎯 MILESTONE STATISTICS")
        print("-" * 25)
        stats = summary['milestone_stats']
        print(f"Total Milestones: {stats['total']}")
        print(f"Completed: {stats['completed']}")
        print(f"Pending Approval: {stats['pending_approval']}")
        print(f"Remaining: {stats['remaining']}")
        print()
        
        print("👥 GOVERNANCE BOARD")
        print("-" * 18)
        print(f"Board Members: {len(summary['governance_board'])}")
        print(f"Auto Release: {'Enabled' if summary['auto_release_enabled'] else 'Disabled'}")
        print()
        
        print("📈 RECENT TRANSACTIONS")
        print("-" * 22)
        for tx in summary['recent_transactions'][:5]:
            print(f"• {tx['description']}")
            print(f"  {tx['timestamp']} | {tx['type'].replace('_', ' ').title()}")
            if tx['amount']:
                print(f"  Amount: ${tx['amount']:,}")
            print()
        
        return escrow_account
    
    def demo_transaction_history(self, escrow_account):
        """Demo transaction history and audit trail"""
        self.print_header("TRANSACTION HISTORY & AUDIT TRAIL")
        
        self.print_step(7, "Complete Transaction History", 
                       "Full audit trail for transparency")
        
        transactions = escrow_engine.get_escrow_transactions(escrow_account.id, limit=20)
        
        print("\n📋 TRANSACTION HISTORY")
        print("=" * 30)
        
        for i, tx in enumerate(transactions, 1):
            print(f"\n{i}. {tx['description']}")
            print(f"   Type: {tx['type'].replace('_', ' ').title()}")
            print(f"   Date: {tx['timestamp']}")
            if tx['amount']:
                print(f"   Amount: ${tx['amount']:,}")
            if tx['user_id']:
                print(f"   User: {tx['user_id']}")
            if tx['metadata']:
                print(f"   Details: {json.dumps(tx['metadata'], indent=2)}")
        
        return escrow_account
    
    def demo_governance_activity(self, escrow_account):
        """Demo governance board activity tracking"""
        self.print_header("GOVERNANCE BOARD ACTIVITY")
        
        self.print_step(8, "Governance Activity Tracking", 
                       "Board member actions and decisions")
        
        # Get pending approvals for each board member
        print("\n👥 GOVERNANCE BOARD ACTIVITY")
        print("=" * 35)
        
        for member in self.demo_data["governance_board"]:
            pending = escrow_engine.get_pending_approvals(member["id"])
            
            print(f"\n{member['name']} ({member['role']})")
            print(f"  Pending approvals: {len(pending)}")
            
            for approval in pending:
                print(f"  - {approval['milestone_title']} (${approval['amount']})")
                print(f"    Project: {approval['project_id']}")
                print(f"    Submitted: {approval['submitted_at']}")
        
        return escrow_account
    
    def run_complete_demo(self):
        """Run the complete funding escrow demo"""
        self.print_header("FUNDING ESCROW SYSTEM DEMO")
        self.print_info("This demo showcases the complete funding escrow workflow")
        self.print_info("from project creation to fund release and governance oversight.")
        
        try:
            # Step 1: Create escrow account
            escrow_account = self.demo_escrow_creation()
            
            # Step 2: Process fund deposits
            escrow_account = self.demo_fund_deposits(escrow_account)
            
            # Step 3: Submit milestone
            escrow_account = self.demo_milestone_submission(escrow_account)
            
            # Step 4: Governance approval
            escrow_account = self.demo_governance_approval(escrow_account)
            
            # Step 5: Demonstrate rejection scenario
            escrow_account = self.demo_milestone_rejection(escrow_account)
            
            # Step 6: Show comprehensive summary
            escrow_account = self.demo_escrow_summary(escrow_account)
            
            # Step 7: Display transaction history
            escrow_account = self.demo_transaction_history(escrow_account)
            
            # Step 8: Show governance activity
            escrow_account = self.demo_governance_activity(escrow_account)
            
            self.print_header("DEMO COMPLETED SUCCESSFULLY")
            self.print_success("All funding escrow features demonstrated!")
            self.print_info("The system provides:")
            self.print_info("  • Secure fund management with milestone-based releases")
            self.print_info("  • Transparent governance oversight")
            self.print_info("  • Complete audit trail for all transactions")
            self.print_info("  • Community-driven project funding")
            
        except Exception as e:
            self.print_error(f"Demo failed: {str(e)}")
            raise


def main():
    """Main demo function"""
    demo = FundingEscrowDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main() 