#!/usr/bin/env python3
"""
Example demonstrating Gus AI Agent learning from and using MCP building codes.

This example shows how Gus can:
1. Load building code MCPs
2. Answer code compliance questions
3. Check designs for violations
4. Suggest code-compliant solutions
5. Learn from violations
"""

import asyncio
import json
from pathlib import Path

# Import Gus components
from domain.services.mcp_knowledge_service import MCPKnowledgeService
from domain.services.llm_service import LLMProvider, LLMConfig
from infrastructure.llm.openai_service import OpenAILLMService
from application.services.mcp_integration import GusMCPIntegration
from application.services.conversation_manager import ConversationManager
from domain.services.query_translator import QueryTranslator
from infrastructure.repositories.conversation_repository import ConversationRepository
import asyncpg


async def main():
    """Demonstrate Gus MCP integration"""
    
    print("🤖 Gus AI Agent - MCP Building Code Integration Demo\n")
    print("=" * 60)
    
    # Initialize services
    print("\n1️⃣ Initializing services...")
    
    # MCP Knowledge Service
    mcp_service = MCPKnowledgeService(mcp_base_path="./mcp")
    
    # LLM Service (using OpenAI)
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4-turbo-preview",
        api_key="your-api-key-here",  # Replace with actual key
        temperature=0.7,
        max_tokens=2000
    )
    llm_service = OpenAILLMService(llm_config)
    
    # MCP Integration
    mcp_integration = GusMCPIntegration(
        mcp_knowledge_service=mcp_service,
        llm_service=llm_service,
        default_jurisdiction={'country': 'US', 'state': 'FL'}
    )
    
    # Initialize MCP integration (load codes)
    await mcp_integration.initialize()
    print("✅ Services initialized")
    
    # ========================================
    # Example 1: Answer Building Code Question
    # ========================================
    print("\n2️⃣ Example: Answering Building Code Questions")
    print("-" * 40)
    
    question1 = "What are the GFCI requirements for kitchen outlets?"
    print(f"❓ Question: {question1}")
    
    response1 = await mcp_integration.answer_code_question(
        question=question1,
        context={'system_type': 'electrical'}
    )
    
    print(f"\n💡 Answer:\n{response1['answer']}")
    print(f"\n📚 Code References:")
    for ref in response1['references'][:3]:
        print(f"  - {ref['code']}: {ref['name']} (relevance: {ref['relevance']:.2f})")
    print(f"\n🎯 Confidence: {response1['confidence']:.2f}")
    
    # ========================================
    # Example 2: Check Design Compliance
    # ========================================
    print("\n3️⃣ Example: Checking Design Compliance")
    print("-" * 40)
    
    design_data = {
        'location': 'bathroom',
        'outlets': [
            {'id': 'OUT-001', 'location': 'near_sink', 'gfci_protected': False},
            {'id': 'OUT-002', 'location': 'wall', 'gfci_protected': True}
        ],
        'area_sqft': 50
    }
    
    print("🏗️ Design Data:")
    print(json.dumps(design_data, indent=2))
    
    compliance_report = await mcp_integration.check_compliance(
        design_data=design_data,
        system_type='electrical'
    )
    
    print(f"\n📋 Compliance Summary:\n{compliance_report['summary']}")
    
    if compliance_report['violations']:
        print("\n❌ Violations Found:")
        for violation in compliance_report['violations']:
            print(f"  - {violation['requirement']}: {violation['issue']}")
            print(f"    Fix: {violation['fix']}")
            print(f"    Reference: {violation['reference']}")
    
    if compliance_report['recommendations']:
        print("\n💡 Recommendations:")
        for rec in compliance_report['recommendations']:
            print(f"  - {rec}")
    
    # ========================================
    # Example 3: Suggest Code-Compliant Solution
    # ========================================
    print("\n4️⃣ Example: Suggesting Code-Compliant Solutions")
    print("-" * 40)
    
    problem = "Need to add outlets in a 200 sq ft kitchen island"
    constraints = {
        'island_dimensions': '8ft x 4ft',
        'existing_circuits': 2,
        'budget': 'moderate'
    }
    
    print(f"❓ Problem: {problem}")
    print(f"🔧 Constraints: {json.dumps(constraints, indent=2)}")
    
    solution = await mcp_integration.suggest_code_compliant_solution(
        problem=problem,
        constraints=constraints,
        system_type='electrical'
    )
    
    print(f"\n💡 Suggested Solution:\n{solution['suggested_solution']}")
    print(f"\n📚 Code Requirements Applied:")
    for req in solution['code_requirements']:
        print(f"  - {req['rule']}: {req['description']}")
        print(f"    Reference: {req['reference']}")
    print(f"\n🎯 Solution Confidence: {solution['confidence']:.2f}")
    
    # ========================================
    # Example 4: Learn from Violation
    # ========================================
    print("\n5️⃣ Example: Learning from Code Violations")
    print("-" * 40)
    
    violation_data = {
        'rule_id': 'nec_210_8',
        'description': 'Missing GFCI protection in bathroom outlet',
        'location': 'Master bathroom',
        'severity': 'high',
        'context': {
            'building_type': 'residential',
            'room_type': 'bathroom',
            'outlet_distance_from_water': '3ft'
        }
    }
    
    print("📝 Recording Violation:")
    print(json.dumps(violation_data, indent=2))
    
    await mcp_integration.learn_from_violation(
        violation_data=violation_data,
        resolution="Installed GFCI outlet and tested functionality"
    )
    
    print("✅ Violation recorded and learned for future guidance")
    
    # ========================================
    # Example 5: Generate Code Report
    # ========================================
    print("\n6️⃣ Example: Generating Building Code Report")
    print("-" * 40)
    
    report_scope = {
        'jurisdiction': {'country': 'US', 'state': 'FL'},
        'systems': ['electrical', 'plumbing', 'mechanical']
    }
    
    print("📊 Generating code summary report...")
    
    report = await mcp_integration.generate_code_report(
        scope=report_scope,
        format_type='summary'
    )
    
    print(f"\n{report[:1000]}...")  # Show first 1000 chars
    
    # ========================================
    # Example 6: Conversation with MCP Context
    # ========================================
    print("\n7️⃣ Example: Natural Conversation with Building Code Knowledge")
    print("-" * 40)
    
    # This would be integrated with the full conversation manager
    conversation_examples = [
        {
            'user': "I'm installing outlets in a commercial kitchen. What do I need to know?",
            'gus': """For commercial kitchen outlets, here are the key requirements:

**NEC Requirements:**
✅ **GFCI Protection (NEC 210.8)**: All outlets within 6 feet of sinks must have GFCI protection
✅ **Dedicated Circuits (NEC 210.23)**: Heavy appliances need dedicated circuits
✅ **Outlet Spacing (NEC 210.52)**: Outlets required every 4 feet along countertops

**Additional Considerations:**
- Use weather-resistant outlets in areas subject to moisture
- Consider stainless steel faceplates for durability
- Install outlets at least 18" above countertops
- Provide adequate circuits for expected equipment load

Would you like specific guidance for any particular equipment or area?"""
        },
        {
            'user': "What about ventilation requirements?",
            'gus': """Commercial kitchen ventilation must meet these codes:

**IMC (International Mechanical Code) Requirements:**
✅ **Hood Requirements (IMC 507)**: Type I hoods required over cooking equipment
✅ **Exhaust Rate (IMC 507.2)**: Minimum 100 CFM per linear foot of hood
✅ **Make-up Air (IMC 508)**: Required when exhaust exceeds 400 CFM

**Key Points:**
- Hood must extend 6" beyond equipment on all sides
- Ductwork must be welded steel, liquid-tight
- Fire suppression system required (NFPA 96)
- Monthly cleaning required for grease filters

Need help calculating CFM requirements for your equipment?"""
        }
    ]
    
    for example in conversation_examples:
        print(f"\n👤 User: {example['user']}")
        print(f"\n🤖 Gus: {example['gus']}")
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete - Gus successfully integrated with MCP building codes!")
    print("\nKey Capabilities Demonstrated:")
    print("• Answering code compliance questions with references")
    print("• Checking designs for violations")
    print("• Suggesting code-compliant solutions")
    print("• Learning from violations for improved guidance")
    print("• Generating comprehensive code reports")
    print("• Natural conversation with building code context")


if __name__ == "__main__":
    # Note: This is a demonstration. In production, you would:
    # 1. Use actual API keys
    # 2. Connect to a real database
    # 3. Load actual MCP files
    # 4. Implement proper error handling
    
    print("\n⚠️ Note: This is a demonstration example.")
    print("In production, configure with actual API keys and MCP files.\n")
    
    # Uncomment to run with actual services:
    # asyncio.run(main())