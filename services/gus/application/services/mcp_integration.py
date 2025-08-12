"""
MCP Integration for Gus AI Agent

This module provides the integration layer between the Gus AI Agent and the
MCP building code validation system, enabling Gus to learn from and apply
engineering logic and building codes in conversations.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio

from domain.services.mcp_knowledge_service import (
    MCPKnowledgeService, MCPKnowledge, MCPRule, MCPKnowledgeType
)
from domain.services.llm_service import LLMService, LLMMessage
from application.prompts.templates import PromptTemplates, PromptCategory

logger = logging.getLogger(__name__)


class GusM CPIntegration:
    """
    Integration service that connects Gus with MCP building codes.
    
    This service enables Gus to:
    - Answer code compliance questions
    - Provide engineering guidance based on standards
    - Learn from code violations and patterns
    - Generate compliance reports
    - Suggest code-compliant solutions
    """
    
    def __init__(
        self,
        mcp_knowledge_service: MCPKnowledgeService,
        llm_service: LLMService,
        default_jurisdiction: Optional[Dict[str, str]] = None
    ):
        """
        Initialize MCP integration.
        
        Args:
            mcp_knowledge_service: MCP knowledge service instance
            llm_service: LLM service for enhanced responses
            default_jurisdiction: Default jurisdiction for codes
        """
        self.mcp_service = mcp_knowledge_service
        self.llm_service = llm_service
        self.default_jurisdiction = default_jurisdiction or {'country': 'US', 'state': 'FL'}
        
        # Cache for frequently accessed codes
        self.code_cache: Dict[str, MCPKnowledge] = {}
        
        # Learning history
        self.violation_history: List[Dict[str, Any]] = []
        self.successful_solutions: List[Dict[str, Any]] = []
        
        logger.info("Initialized Gus MCP Integration")
    
    async def initialize(self) -> None:
        """Initialize by loading common building codes"""
        try:
            # Load default jurisdiction codes
            jurisdiction_path = f"{self.default_jurisdiction['country'].lower()}/{self.default_jurisdiction['state'].lower()}"
            await self.mcp_service.load_jurisdiction(jurisdiction_path)
            
            # Load common codes
            common_codes = [
                "nec-2020.json",  # Electrical
                "ipc-2021.json",  # Plumbing
                "imc-2021.json",  # Mechanical
                "ibc-2021.json",  # Building
                "ada-2010.json"   # Accessibility
            ]
            
            for code_file in common_codes:
                try:
                    code_path = f"{jurisdiction_path}/{code_file}"
                    knowledge = await self.mcp_service.load_mcp(code_path)
                    self.code_cache[knowledge.mcp_id] = knowledge
                    logger.info(f"Loaded code: {knowledge.name}")
                except Exception as e:
                    logger.warning(f"Could not load {code_file}: {e}")
            
            logger.info(f"Initialized with {len(self.code_cache)} building codes")
            
        except Exception as e:
            logger.error(f"Error initializing MCP integration: {e}")
    
    async def answer_code_question(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer a building code question using MCP knowledge.
        
        Args:
            question: User's code-related question
            context: Optional context (building type, location, etc.)
            
        Returns:
            Response with answer and relevant code references
        """
        # Extract system type and jurisdiction from context
        system_type = context.get('system_type') if context else None
        jurisdiction = context.get('jurisdiction', self.default_jurisdiction) if context else self.default_jurisdiction
        
        # Query relevant rules
        relevant_rules = self.mcp_service.query_rules(
            query=question,
            category=system_type,
            jurisdiction=jurisdiction
        )
        
        if not relevant_rules:
            return {
                'answer': "I couldn't find specific code requirements for that question. Could you provide more details about the system or location?",
                'confidence': 0.3,
                'references': []
            }
        
        # Build response using top rules
        response = await self._build_code_response(question, relevant_rules[:5], context)
        
        # Learn from the interaction
        self._record_interaction(question, relevant_rules, response)
        
        return response
    
    async def check_compliance(
        self,
        design_data: Dict[str, Any],
        system_type: str,
        jurisdiction: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Check design compliance against building codes.
        
        Args:
            design_data: Design specifications to check
            system_type: Type of system to check
            jurisdiction: Jurisdiction for codes
            
        Returns:
            Compliance report with violations and recommendations
        """
        jurisdiction = jurisdiction or self.default_jurisdiction
        
        # Get compliance guidance
        guidance = self.mcp_service.get_compliance_guidance(
            system_type=system_type,
            location=design_data.get('location'),
            jurisdiction=jurisdiction
        )
        
        # Analyze design against requirements
        violations = []
        warnings = []
        compliant = []
        
        for requirement in guidance['key_requirements']:
            status = await self._check_requirement(design_data, requirement)
            
            if status['status'] == 'violation':
                violations.append({
                    'requirement': requirement['requirement'],
                    'description': requirement['description'],
                    'reference': requirement['reference'],
                    'issue': status['issue'],
                    'fix': status['fix']
                })
            elif status['status'] == 'warning':
                warnings.append({
                    'requirement': requirement['requirement'],
                    'description': requirement['description'],
                    'issue': status['issue']
                })
            else:
                compliant.append({
                    'requirement': requirement['requirement'],
                    'description': requirement['description']
                })
        
        # Generate summary
        summary = self._generate_compliance_summary(violations, warnings, compliant)
        
        return {
            'summary': summary,
            'violations': violations,
            'warnings': warnings,
            'compliant': compliant,
            'guidance': guidance,
            'recommendations': self._generate_recommendations(violations, system_type)
        }
    
    async def suggest_code_compliant_solution(
        self,
        problem: str,
        constraints: Dict[str, Any],
        system_type: str
    ) -> Dict[str, Any]:
        """
        Suggest a code-compliant solution to a design problem.
        
        Args:
            problem: Description of the problem
            constraints: Design constraints
            system_type: Type of system
            
        Returns:
            Suggested solution with code references
        """
        # Get relevant codes
        relevant_rules = self.mcp_service.query_rules(
            query=problem,
            category=system_type,
            jurisdiction=self.default_jurisdiction
        )
        
        # Build prompt for LLM with code context
        prompt = self._build_solution_prompt(problem, constraints, relevant_rules)
        
        # Get LLM suggestion
        llm_response = await self.llm_service.complete(
            messages=[
                LLMMessage(role="system", content=PromptTemplates.SYSTEM_PROMPTS[PromptCategory.COMPLIANCE]),
                LLMMessage(role="user", content=prompt)
            ],
            temperature=0.7
        )
        
        # Parse and structure the solution
        solution = {
            'problem': problem,
            'suggested_solution': llm_response.content,
            'code_requirements': [
                {
                    'rule': rule.name,
                    'description': rule.description,
                    'reference': rule.code_reference
                }
                for rule, _ in relevant_rules[:3]
            ],
            'constraints_considered': constraints,
            'confidence': self._calculate_solution_confidence(relevant_rules)
        }
        
        # Record successful solution for learning
        if solution['confidence'] > 0.7:
            self.successful_solutions.append({
                'problem': problem,
                'solution': solution['suggested_solution'],
                'system_type': system_type,
                'rules_applied': [r.rule_id for r, _ in relevant_rules[:3]]
            })
        
        return solution
    
    async def learn_from_violation(
        self,
        violation_data: Dict[str, Any],
        resolution: Optional[str] = None
    ) -> None:
        """
        Learn from a code violation to improve future guidance.
        
        Args:
            violation_data: Data about the violation
            resolution: How the violation was resolved
        """
        # Record violation
        self.violation_history.append({
            'violation': violation_data,
            'resolution': resolution,
            'timestamp': Path(__file__).stat().st_mtime
        })
        
        # Update MCP knowledge service
        if 'rule_id' in violation_data:
            self.mcp_service.learn_from_violation(
                violation_description=violation_data.get('description', ''),
                rule_id=violation_data['rule_id'],
                context=violation_data.get('context', {})
            )
        
        # Analyze patterns if enough history
        if len(self.violation_history) >= 10:
            patterns = self._analyze_violation_patterns()
            logger.info(f"Identified violation patterns: {patterns}")
    
    async def generate_code_report(
        self,
        scope: Dict[str, Any],
        format_type: str = "summary"
    ) -> str:
        """
        Generate a building code report.
        
        Args:
            scope: Scope of the report (systems, jurisdiction, etc.)
            format_type: Type of report (summary, detailed, checklist)
            
        Returns:
            Formatted report
        """
        jurisdiction = scope.get('jurisdiction', self.default_jurisdiction)
        system_types = scope.get('systems', ['electrical', 'mechanical', 'plumbing'])
        
        if format_type == "summary":
            report = self.mcp_service.generate_code_summary(jurisdiction, system_types)
        elif format_type == "detailed":
            report = await self._generate_detailed_report(jurisdiction, system_types)
        elif format_type == "checklist":
            report = await self._generate_checklist_report(jurisdiction, system_types)
        else:
            report = "Invalid report format requested."
        
        return report
    
    async def _build_code_response(
        self,
        question: str,
        relevant_rules: List[Tuple[MCPRule, float]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a response using relevant code rules"""
        # Format rules for response
        rule_explanations = []
        references = []
        
        for rule, score in relevant_rules:
            explanation = self.mcp_service.explain_rule(rule)
            rule_explanations.append(explanation)
            references.append({
                'code': rule.code_reference,
                'name': rule.name,
                'relevance': score
            })
        
        # Build comprehensive answer
        if rule_explanations:
            answer = f"Based on applicable building codes:\n\n"
            answer += "\n\n".join(rule_explanations[:3])  # Top 3 explanations
            
            # Add context-specific guidance
            if context and context.get('specific_scenario'):
                answer += f"\n\n**For your specific scenario:**\n"
                answer += await self._get_scenario_guidance(context['specific_scenario'], relevant_rules[0][0])
        else:
            answer = "I couldn't find specific code requirements for this question."
        
        return {
            'answer': answer,
            'confidence': relevant_rules[0][1] if relevant_rules else 0.0,
            'references': references,
            'applicable_codes': list(set(r['code'] for r in references if r['code']))
        }
    
    async def _check_requirement(
        self,
        design_data: Dict[str, Any],
        requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if design meets a specific requirement"""
        # This would integrate with the actual MCP validation engine
        # For now, return a simplified check
        
        # Simulate checking based on requirement priority
        if requirement['priority'] == 1:  # Critical requirement
            # Check if design has required properties
            if 'gfci_protection' in requirement['description'].lower():
                if not design_data.get('gfci_protected', False):
                    return {
                        'status': 'violation',
                        'issue': 'Missing GFCI protection',
                        'fix': 'Install GFCI protection for outlets in wet locations'
                    }
        
        return {'status': 'compliant'}
    
    def _generate_compliance_summary(
        self,
        violations: List[Dict],
        warnings: List[Dict],
        compliant: List[Dict]
    ) -> str:
        """Generate a compliance summary"""
        total = len(violations) + len(warnings) + len(compliant)
        
        if not violations:
            summary = f"✅ **Fully Compliant**: All {total} requirements met.\n"
        elif len(violations) <= 2:
            summary = f"⚠️ **Minor Issues**: {len(violations)} violations found out of {total} requirements.\n"
        else:
            summary = f"❌ **Compliance Issues**: {len(violations)} violations found out of {total} requirements.\n"
        
        if violations:
            summary += f"\n**Critical Issues:**\n"
            for v in violations[:3]:
                summary += f"- {v['requirement']}: {v['issue']}\n"
        
        if warnings:
            summary += f"\n**Warnings:**\n"
            for w in warnings[:2]:
                summary += f"- {w['requirement']}: {w['issue']}\n"
        
        return summary
    
    def _generate_recommendations(
        self,
        violations: List[Dict],
        system_type: str
    ) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []
        
        for violation in violations:
            if violation.get('fix'):
                recommendations.append(violation['fix'])
        
        # Add system-specific best practices
        if system_type == 'electrical':
            recommendations.append("Consider hiring a licensed electrician for code compliance verification")
        elif system_type == 'mechanical':
            recommendations.append("Perform Manual J calculations for proper HVAC sizing")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _build_solution_prompt(
        self,
        problem: str,
        constraints: Dict[str, Any],
        relevant_rules: List[Tuple[MCPRule, float]]
    ) -> str:
        """Build prompt for solution generation"""
        prompt = f"Problem: {problem}\n\n"
        prompt += f"Constraints:\n"
        for key, value in constraints.items():
            prompt += f"- {key}: {value}\n"
        prompt += "\n"
        
        prompt += "Applicable Building Codes:\n"
        for rule, _ in relevant_rules[:3]:
            prompt += f"- {rule.name}: {rule.description} (Ref: {rule.code_reference})\n"
        prompt += "\n"
        
        prompt += "Please suggest a code-compliant solution that:\n"
        prompt += "1. Addresses the problem\n"
        prompt += "2. Meets all constraints\n"
        prompt += "3. Complies with the listed building codes\n"
        prompt += "4. Is practical and cost-effective\n"
        
        return prompt
    
    def _calculate_solution_confidence(self, relevant_rules: List[Tuple[MCPRule, float]]) -> float:
        """Calculate confidence in the suggested solution"""
        if not relevant_rules:
            return 0.3
        
        # Base confidence on rule relevance scores
        avg_relevance = sum(score for _, score in relevant_rules[:3]) / min(3, len(relevant_rules))
        
        # Boost confidence if we have high-priority rules
        has_critical = any(rule.priority == 1 for rule, _ in relevant_rules[:3])
        if has_critical:
            avg_relevance += 0.1
        
        return min(avg_relevance, 0.95)
    
    def _analyze_violation_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in violation history"""
        patterns = {
            'most_common_violations': {},
            'systems_with_issues': {},
            'resolution_success_rate': 0
        }
        
        # Count violation types
        for record in self.violation_history:
            violation_type = record['violation'].get('type', 'unknown')
            patterns['most_common_violations'][violation_type] = \
                patterns['most_common_violations'].get(violation_type, 0) + 1
        
        # Calculate resolution rate
        resolved = sum(1 for r in self.violation_history if r.get('resolution'))
        if self.violation_history:
            patterns['resolution_success_rate'] = resolved / len(self.violation_history)
        
        return patterns
    
    async def _get_scenario_guidance(self, scenario: str, rule: MCPRule) -> str:
        """Get specific guidance for a scenario"""
        # Use LLM to provide scenario-specific guidance
        prompt = f"Given the scenario: {scenario}\n"
        prompt += f"And the building code requirement: {rule.description}\n"
        prompt += f"Provide specific, practical guidance."
        
        response = await self.llm_service.complete(
            messages=[LLMMessage(role="user", content=prompt)],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.content
    
    async def _generate_detailed_report(
        self,
        jurisdiction: Dict[str, str],
        system_types: List[str]
    ) -> str:
        """Generate a detailed code report"""
        report = "# Detailed Building Code Report\n\n"
        
        for system in system_types:
            report += f"## {system.title()} System Requirements\n\n"
            
            # Get all relevant rules
            rules = self.mcp_service.query_rules(
                query=system,
                category=system,
                jurisdiction=jurisdiction
            )
            
            for rule, score in rules[:10]:
                report += f"### {rule.name}\n"
                report += f"**Description:** {rule.description}\n"
                report += f"**Reference:** {rule.code_reference}\n"
                report += f"**Priority:** {rule.priority}\n\n"
        
        return report
    
    async def _generate_checklist_report(
        self,
        jurisdiction: Dict[str, str],
        system_types: List[str]
    ) -> str:
        """Generate a checklist-style code report"""
        report = "# Building Code Compliance Checklist\n\n"
        
        for system in system_types:
            report += f"## {system.title()} System\n\n"
            
            # Get key requirements
            guidance = self.mcp_service.get_compliance_guidance(
                system_type=system,
                jurisdiction=jurisdiction
            )
            
            for req in guidance['key_requirements']:
                report += f"- [ ] {req['requirement']}\n"
                report += f"  - {req['description']}\n"
                report += f"  - Reference: {req['reference']}\n\n"
        
        return report
    
    def _record_interaction(
        self,
        question: str,
        relevant_rules: List[Tuple[MCPRule, float]],
        response: Dict[str, Any]
    ) -> None:
        """Record interaction for learning"""
        # This could be stored in a database for analysis
        logger.debug(f"Recorded interaction: {question[:50]}... with {len(relevant_rules)} rules")