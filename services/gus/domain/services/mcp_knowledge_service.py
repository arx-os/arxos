"""
MCP Knowledge Service for Gus AI Agent

This module integrates the Building Code MCP (Model Context Protocol) system
with the Gus AI Agent, allowing it to learn from and apply engineering logic
and building codes.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPKnowledgeType(Enum):
    """Types of MCP knowledge"""
    BUILDING_CODE = "building_code"
    ENGINEERING_STANDARD = "engineering_standard"
    BEST_PRACTICE = "best_practice"
    SAFETY_REGULATION = "safety_regulation"
    ENERGY_EFFICIENCY = "energy_efficiency"
    ACCESSIBILITY = "accessibility"


@dataclass
class MCPRule:
    """Simplified MCP rule representation for Gus"""
    rule_id: str
    name: str
    description: str
    category: str
    priority: int
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    code_reference: str
    jurisdiction: Dict[str, str]
    
    def to_natural_language(self) -> str:
        """Convert rule to natural language explanation"""
        explanation = f"{self.name}: {self.description}"
        if self.code_reference:
            explanation += f" (Reference: {self.code_reference})"
        return explanation


@dataclass
class MCPKnowledge:
    """MCP knowledge representation"""
    mcp_id: str
    name: str
    description: str
    type: MCPKnowledgeType
    jurisdiction: Dict[str, str]
    rules: List[MCPRule]
    metadata: Dict[str, Any]
    
    def get_rules_for_category(self, category: str) -> List[MCPRule]:
        """Get rules for a specific category"""
        return [rule for rule in self.rules if rule.category == category]
    
    def get_high_priority_rules(self, threshold: int = 1) -> List[MCPRule]:
        """Get high priority rules"""
        return [rule for rule in self.rules if rule.priority <= threshold]


class MCPKnowledgeService:
    """
    Service for integrating MCP building codes and engineering logic
    with the Gus AI Agent.
    
    This service provides:
    - Loading and parsing MCP files
    - Converting rules to natural language
    - Querying applicable codes
    - Learning from code patterns
    - Compliance checking assistance
    """
    
    def __init__(self, mcp_base_path: str = "./mcp"):
        """
        Initialize MCP Knowledge Service.
        
        Args:
            mcp_base_path: Base path to MCP files
        """
        self.mcp_base_path = Path(mcp_base_path)
        self.loaded_mcps: Dict[str, MCPKnowledge] = {}
        self.rule_index: Dict[str, List[MCPRule]] = {}  # Category -> Rules
        self.jurisdiction_index: Dict[str, List[str]] = {}  # Jurisdiction -> MCP IDs
        
        logger.info(f"Initialized MCPKnowledgeService with base path: {mcp_base_path}")
    
    async def load_mcp(self, mcp_path: str) -> MCPKnowledge:
        """
        Load an MCP file and convert to knowledge representation.
        
        Args:
            mcp_path: Path to MCP file
            
        Returns:
            MCPKnowledge object
        """
        try:
            full_path = self.mcp_base_path / mcp_path
            with open(full_path, 'r') as f:
                mcp_data = json.load(f)
            
            # Parse rules
            rules = []
            for rule_data in mcp_data.get('rules', []):
                rule = MCPRule(
                    rule_id=rule_data['rule_id'],
                    name=rule_data['name'],
                    description=rule_data['description'],
                    category=rule_data.get('category', 'general'),
                    priority=rule_data.get('priority', 3),
                    conditions=rule_data.get('conditions', []),
                    actions=rule_data.get('actions', []),
                    code_reference=rule_data.get('code_reference', ''),
                    jurisdiction=mcp_data.get('jurisdiction', {})
                )
                rules.append(rule)
            
            # Create knowledge object
            knowledge = MCPKnowledge(
                mcp_id=mcp_data['mcp_id'],
                name=mcp_data['name'],
                description=mcp_data['description'],
                type=self._determine_knowledge_type(mcp_data),
                jurisdiction=mcp_data.get('jurisdiction', {}),
                rules=rules,
                metadata=mcp_data.get('metadata', {})
            )
            
            # Store and index
            self.loaded_mcps[knowledge.mcp_id] = knowledge
            self._index_knowledge(knowledge)
            
            logger.info(f"Loaded MCP: {knowledge.mcp_id} with {len(rules)} rules")
            return knowledge
            
        except Exception as e:
            logger.error(f"Error loading MCP {mcp_path}: {e}")
            raise
    
    async def load_jurisdiction(self, jurisdiction: str) -> List[MCPKnowledge]:
        """
        Load all MCPs for a jurisdiction (e.g., "us/fl").
        
        Args:
            jurisdiction: Jurisdiction path
            
        Returns:
            List of loaded MCPKnowledge objects
        """
        jurisdiction_path = self.mcp_base_path / jurisdiction
        loaded = []
        
        if jurisdiction_path.exists():
            for mcp_file in jurisdiction_path.glob("*.json"):
                try:
                    relative_path = mcp_file.relative_to(self.mcp_base_path)
                    knowledge = await self.load_mcp(str(relative_path))
                    loaded.append(knowledge)
                except Exception as e:
                    logger.warning(f"Failed to load {mcp_file}: {e}")
        
        logger.info(f"Loaded {len(loaded)} MCPs for jurisdiction {jurisdiction}")
        return loaded
    
    def query_rules(
        self,
        query: str,
        category: Optional[str] = None,
        jurisdiction: Optional[Dict[str, str]] = None
    ) -> List[Tuple[MCPRule, float]]:
        """
        Query relevant rules based on natural language.
        
        Args:
            query: Natural language query
            category: Optional category filter
            jurisdiction: Optional jurisdiction filter
            
        Returns:
            List of (rule, relevance_score) tuples
        """
        results = []
        query_lower = query.lower()
        
        # Get applicable MCPs
        applicable_mcps = self._get_applicable_mcps(jurisdiction)
        
        for mcp_id in applicable_mcps:
            if mcp_id not in self.loaded_mcps:
                continue
                
            mcp = self.loaded_mcps[mcp_id]
            
            for rule in mcp.rules:
                # Category filter
                if category and rule.category != category:
                    continue
                
                # Calculate relevance score
                score = self._calculate_relevance(query_lower, rule)
                
                if score > 0.3:  # Threshold for relevance
                    results.append((rule, score))
        
        # Sort by relevance
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:10]  # Return top 10 results
    
    def explain_rule(self, rule: MCPRule) -> str:
        """
        Generate natural language explanation of a rule.
        
        Args:
            rule: MCP rule to explain
            
        Returns:
            Natural language explanation
        """
        explanation = f"**{rule.name}**\n\n"
        explanation += f"{rule.description}\n\n"
        
        # Explain conditions
        if rule.conditions:
            explanation += "**When this applies:**\n"
            for condition in rule.conditions:
                explanation += f"- {self._explain_condition(condition)}\n"
            explanation += "\n"
        
        # Explain actions
        if rule.actions:
            explanation += "**Requirements:**\n"
            for action in rule.actions:
                explanation += f"- {self._explain_action(action)}\n"
            explanation += "\n"
        
        # Add reference
        if rule.code_reference:
            explanation += f"**Code Reference:** {rule.code_reference}\n"
        
        return explanation
    
    def get_compliance_guidance(
        self,
        system_type: str,
        location: Optional[str] = None,
        jurisdiction: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get compliance guidance for a system type.
        
        Args:
            system_type: Type of system (electrical, hvac, plumbing, etc.)
            location: Specific location in building
            jurisdiction: Jurisdiction for codes
            
        Returns:
            Compliance guidance dictionary
        """
        guidance = {
            'system': system_type,
            'location': location,
            'applicable_codes': [],
            'key_requirements': [],
            'common_violations': [],
            'best_practices': []
        }
        
        # Get applicable MCPs
        applicable_mcps = self._get_applicable_mcps(jurisdiction)
        
        for mcp_id in applicable_mcps:
            if mcp_id not in self.loaded_mcps:
                continue
            
            mcp = self.loaded_mcps[mcp_id]
            guidance['applicable_codes'].append({
                'code': mcp.name,
                'jurisdiction': mcp.jurisdiction
            })
            
            # Get relevant rules
            relevant_rules = [
                rule for rule in mcp.rules
                if system_type.lower() in rule.category.lower()
            ]
            
            # Extract key requirements
            for rule in relevant_rules[:5]:  # Top 5 rules
                guidance['key_requirements'].append({
                    'requirement': rule.name,
                    'description': rule.description,
                    'reference': rule.code_reference,
                    'priority': rule.priority
                })
        
        # Add common violations (these could be learned from historical data)
        guidance['common_violations'] = self._get_common_violations(system_type)
        
        # Add best practices
        guidance['best_practices'] = self._get_best_practices(system_type)
        
        return guidance
    
    def learn_from_violation(
        self,
        violation_description: str,
        rule_id: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Learn from a code violation to improve future guidance.
        
        Args:
            violation_description: Description of the violation
            rule_id: ID of the violated rule
            context: Context of the violation
        """
        # In a production system, this would:
        # 1. Store violation patterns
        # 2. Update relevance scoring
        # 3. Improve natural language generation
        # 4. Build a knowledge graph of common issues
        
        logger.info(f"Learning from violation: {rule_id} - {violation_description}")
        
        # TODO: Implement learning mechanism
        # This could involve:
        # - Storing in a violations database
        # - Training a classifier for violation prediction
        # - Updating rule priorities based on frequency
    
    def generate_code_summary(
        self,
        jurisdiction: Dict[str, str],
        system_types: List[str]
    ) -> str:
        """
        Generate a summary of applicable codes for given systems.
        
        Args:
            jurisdiction: Target jurisdiction
            system_types: List of system types
            
        Returns:
            Natural language summary
        """
        summary = f"# Building Code Summary\n\n"
        summary += f"**Jurisdiction:** {jurisdiction.get('state', 'N/A')}, "
        summary += f"{jurisdiction.get('country', 'N/A')}\n\n"
        
        applicable_mcps = self._get_applicable_mcps(jurisdiction)
        
        for system_type in system_types:
            summary += f"## {system_type.title()} Systems\n\n"
            
            rules_found = False
            for mcp_id in applicable_mcps:
                if mcp_id not in self.loaded_mcps:
                    continue
                
                mcp = self.loaded_mcps[mcp_id]
                relevant_rules = [
                    rule for rule in mcp.rules
                    if system_type.lower() in rule.category.lower()
                ]
                
                if relevant_rules:
                    rules_found = True
                    summary += f"### {mcp.name}\n"
                    for rule in relevant_rules[:3]:  # Top 3 rules
                        summary += f"- **{rule.name}**: {rule.description}\n"
                    summary += "\n"
            
            if not rules_found:
                summary += "No specific requirements found.\n\n"
        
        return summary
    
    def _determine_knowledge_type(self, mcp_data: Dict[str, Any]) -> MCPKnowledgeType:
        """Determine the type of MCP knowledge"""
        name_lower = mcp_data.get('name', '').lower()
        
        if 'energy' in name_lower:
            return MCPKnowledgeType.ENERGY_EFFICIENCY
        elif 'ada' in name_lower or 'accessibility' in name_lower:
            return MCPKnowledgeType.ACCESSIBILITY
        elif 'safety' in name_lower or 'fire' in name_lower:
            return MCPKnowledgeType.SAFETY_REGULATION
        elif 'standard' in name_lower:
            return MCPKnowledgeType.ENGINEERING_STANDARD
        elif 'practice' in name_lower:
            return MCPKnowledgeType.BEST_PRACTICE
        else:
            return MCPKnowledgeType.BUILDING_CODE
    
    def _index_knowledge(self, knowledge: MCPKnowledge) -> None:
        """Index knowledge for fast retrieval"""
        # Index by category
        for rule in knowledge.rules:
            if rule.category not in self.rule_index:
                self.rule_index[rule.category] = []
            self.rule_index[rule.category].append(rule)
        
        # Index by jurisdiction
        jurisdiction_key = f"{knowledge.jurisdiction.get('country', '')}/{knowledge.jurisdiction.get('state', '')}"
        if jurisdiction_key not in self.jurisdiction_index:
            self.jurisdiction_index[jurisdiction_key] = []
        self.jurisdiction_index[jurisdiction_key].append(knowledge.mcp_id)
    
    def _get_applicable_mcps(self, jurisdiction: Optional[Dict[str, str]]) -> List[str]:
        """Get applicable MCP IDs for a jurisdiction"""
        if not jurisdiction:
            return list(self.loaded_mcps.keys())
        
        jurisdiction_key = f"{jurisdiction.get('country', '')}/{jurisdiction.get('state', '')}"
        return self.jurisdiction_index.get(jurisdiction_key, [])
    
    def _calculate_relevance(self, query: str, rule: MCPRule) -> float:
        """Calculate relevance score between query and rule"""
        score = 0.0
        
        # Check name match
        if any(word in rule.name.lower() for word in query.split()):
            score += 0.4
        
        # Check description match
        if any(word in rule.description.lower() for word in query.split()):
            score += 0.3
        
        # Check category match
        if any(word in rule.category.lower() for word in query.split()):
            score += 0.2
        
        # Check code reference match
        if rule.code_reference and any(word in rule.code_reference.lower() for word in query.split()):
            score += 0.1
        
        return min(score, 1.0)
    
    def _explain_condition(self, condition: Dict[str, Any]) -> str:
        """Convert condition to natural language"""
        cond_type = condition.get('type', '')
        element = condition.get('element_type', 'element')
        prop = condition.get('property', '')
        operator = condition.get('operator', '')
        value = condition.get('value', '')
        
        if cond_type == 'property':
            return f"{element} has {prop} {operator} {value}"
        elif cond_type == 'spatial':
            return f"{element} is {operator} {value}"
        else:
            return f"{element} meets condition: {operator} {value}"
    
    def _explain_action(self, action: Dict[str, Any]) -> str:
        """Convert action to natural language"""
        action_type = action.get('type', '')
        
        if action_type == 'validation':
            return action.get('message', 'Validation required')
        elif action_type == 'calculation':
            return f"Calculate: {action.get('description', action.get('formula', ''))}"
        else:
            return action.get('description', 'Action required')
    
    def _get_common_violations(self, system_type: str) -> List[Dict[str, str]]:
        """Get common violations for a system type"""
        # This would be populated from historical data
        common_violations = {
            'electrical': [
                {
                    'violation': 'Missing GFCI protection',
                    'location': 'Bathrooms and kitchens',
                    'fix': 'Install GFCI outlets or breakers'
                },
                {
                    'violation': 'Improper grounding',
                    'location': 'Main panel',
                    'fix': 'Ensure proper grounding electrode system'
                }
            ],
            'hvac': [
                {
                    'violation': 'Inadequate ventilation',
                    'location': 'Mechanical rooms',
                    'fix': 'Increase CFM to meet code requirements'
                }
            ],
            'plumbing': [
                {
                    'violation': 'Missing backflow prevention',
                    'location': 'Water supply connections',
                    'fix': 'Install approved backflow preventers'
                }
            ]
        }
        
        return common_violations.get(system_type.lower(), [])
    
    def _get_best_practices(self, system_type: str) -> List[str]:
        """Get best practices for a system type"""
        best_practices = {
            'electrical': [
                'Use arc-fault circuit interrupters (AFCIs) in bedrooms',
                'Provide dedicated circuits for major appliances',
                'Label all circuits clearly in the panel'
            ],
            'hvac': [
                'Size equipment based on Manual J calculations',
                'Seal all ductwork with mastic',
                'Install programmable thermostats'
            ],
            'plumbing': [
                'Use expansion tanks on water heaters',
                'Install water hammer arrestors',
                'Provide accessible shutoff valves'
            ]
        }
        
        return best_practices.get(system_type.lower(), [])