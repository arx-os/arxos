"""
Prompt Templates for Gus AI Agent

This module contains prompt templates for various interaction scenarios,
ensuring consistent and high-quality AI responses.
"""

from typing import Dict, Any, List
from enum import Enum


class PromptCategory(Enum):
    """Categories of prompt templates"""
    QUERY = "query"
    ANALYSIS = "analysis"
    COMPLIANCE = "compliance"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    REPORTING = "reporting"


class PromptTemplates:
    """
    Manages prompt templates for different scenarios.
    
    This class provides structured prompts for various building-related queries
    and analyses, ensuring consistent AI behavior.
    """
    
    # Base system prompts by category
    SYSTEM_PROMPTS = {
        PromptCategory.QUERY: """You are analyzing building data. Provide clear, specific information about the requested objects or systems.
Focus on: location, status, specifications, and any notable issues.
Format numbers clearly and include units.""",
        
        PromptCategory.ANALYSIS: """You are performing building system analysis. Provide detailed technical insights.
Include: current state, performance metrics, identified issues, and root causes.
Use technical terminology appropriately for the user's expertise level.""",
        
        PromptCategory.COMPLIANCE: """You are checking building code compliance. Reference specific codes and standards.
Format: ✅ Compliant items, ⚠️ Warnings, ❌ Violations
Always cite the specific code section (e.g., NEC 210.52, IBC 1009.3).""",
        
        PromptCategory.OPTIMIZATION: """You are providing optimization recommendations. Focus on practical, actionable improvements.
Include: estimated savings, implementation difficulty, ROI timeline.
Prioritize recommendations by impact and feasibility.""",
        
        PromptCategory.TROUBLESHOOTING: """You are troubleshooting building system issues. Use systematic problem-solving.
Structure: 1) Symptoms observed, 2) Possible causes, 3) Diagnostic steps, 4) Recommended solutions.
Consider both immediate fixes and long-term solutions.""",
        
        PromptCategory.REPORTING: """You are generating a professional report. Use clear structure and formatting.
Include: Executive summary, detailed findings, recommendations, next steps.
Tailor detail level to the specified audience."""
    }
    
    # Specific query templates
    QUERY_TEMPLATES = {
        "find_objects": """Analyze this query: {query}
Building context: {building_id}
Current location: {location}

Translate to AQL and explain what objects will be found.
If spatial relationships are mentioned, specify distances and relationships clearly.""",
        
        "count_objects": """Count query: {query}
Scope: {scope}

Provide the count with breakdown by relevant categories (floor, room, type, status).
Include percentages and highlight any anomalies.""",
        
        "object_status": """Status check for: {object_id}
System type: {system_type}

Report: operational status, last maintenance, current readings, any alerts.
Compare against normal operating parameters."""
    }
    
    # Analysis templates
    ANALYSIS_TEMPLATES = {
        "load_analysis": """Analyze electrical load for: {scope}
Current time: {timestamp}

Calculate:
- Current load vs. rated capacity
- Peak load times
- Load distribution across phases
- Overloaded circuits
- Available capacity

Identify optimization opportunities.""",
        
        "hvac_efficiency": """Analyze HVAC efficiency for: {scope}
Period: {time_period}

Evaluate:
- Energy consumption vs. design
- Temperature control accuracy
- Equipment efficiency (COP, EER)
- Airflow balance
- Occupancy patterns impact

Recommend efficiency improvements with ROI.""",
        
        "space_utilization": """Analyze space utilization for: {scope}
Period: {time_period}

Assess:
- Occupancy rates by time
- Peak usage periods
- Underutilized spaces
- Overcrowded areas
- Movement patterns

Suggest layout optimizations."""
    }
    
    # Compliance templates
    COMPLIANCE_TEMPLATES = {
        "electrical_code": """Check electrical compliance for: {scope}
Standards: {standards}

Verify:
✅/⚠️/❌ Circuit breaker ratings (NEC 210.20)
✅/⚠️/❌ Outlet spacing (NEC 210.52)
✅/⚠️/❌ GFCI protection (NEC 210.8)
✅/⚠️/❌ Grounding system (NEC 250)
✅/⚠️/❌ Panel labeling (NEC 408.4)

For violations, specify location and required correction.""",
        
        "fire_safety": """Check fire safety compliance for: {scope}
Standards: {standards}

Verify:
✅/⚠️/❌ Exit routes (IBC 1003)
✅/⚠️/❌ Emergency lighting (IBC 1008)
✅/⚠️/❌ Fire alarm system (NFPA 72)
✅/⚠️/❌ Sprinkler coverage (NFPA 13)
✅/⚠️/❌ Fire ratings (IBC 703)

Priority ranking for any violations.""",
        
        "accessibility": """Check accessibility compliance for: {scope}
Standards: ADA, IBC Chapter 11

Verify:
✅/⚠️/❌ Door widths (36" minimum)
✅/⚠️/❌ Ramp slopes (1:12 maximum)
✅/⚠️/❌ Bathroom accessibility
✅/⚠️/❌ Elevator requirements
✅/⚠️/❌ Signage compliance

Include remediation requirements."""
    }
    
    # Troubleshooting templates
    TROUBLESHOOTING_TEMPLATES = {
        "temperature_issue": """Troubleshoot temperature issue in: {location}
Reported problem: {problem_description}
Current reading: {current_temp}
Setpoint: {setpoint}

Diagnostic approach:
1. Check thermostat calibration
2. Verify VAV box operation
3. Measure actual airflow vs. design
4. Check for air balance issues
5. Inspect damper positions
6. Review equipment operation

Provide specific action items.""",
        
        "power_issue": """Troubleshoot power issue: {problem_description}
Location: {location}
Affected equipment: {equipment}

Systematic check:
1. Breaker status and ratings
2. Voltage measurements
3. Load calculations
4. Grounding verification
5. Connection integrity
6. Power quality issues

Safety warnings and repair sequence.""",
        
        "water_leak": """Investigate water leak: {location}
Observed symptoms: {symptoms}

Investigation steps:
1. Identify source (plumbing, HVAC, roof)
2. Assess damage extent
3. Check pressure readings
4. Inspect joints and connections
5. Review recent maintenance

Immediate actions and permanent fix."""
    }
    
    @classmethod
    def get_system_prompt(cls, category: PromptCategory, context: Dict[str, Any]) -> str:
        """
        Get system prompt for a category with context.
        
        Args:
            category: Prompt category
            context: Context dictionary
            
        Returns:
            Formatted system prompt
        """
        base_prompt = cls.SYSTEM_PROMPTS.get(category, "You are a helpful building management AI assistant.")
        
        # Add context-specific modifications
        if context.get('user_role') == 'technician':
            base_prompt += "\nProvide detailed technical information and step-by-step procedures."
        elif context.get('user_role') == 'manager':
            base_prompt += "\nFocus on costs, timelines, and business impact."
        
        if context.get('emergency'):
            base_prompt += "\n⚠️ EMERGENCY CONTEXT: Prioritize immediate safety and critical systems."
        
        return base_prompt
    
    @classmethod
    def get_query_prompt(cls, query_type: str, **kwargs) -> str:
        """Get formatted query prompt"""
        template = cls.QUERY_TEMPLATES.get(query_type, cls.QUERY_TEMPLATES['find_objects'])
        return template.format(**kwargs)
    
    @classmethod
    def get_analysis_prompt(cls, analysis_type: str, **kwargs) -> str:
        """Get formatted analysis prompt"""
        template = cls.ANALYSIS_TEMPLATES.get(analysis_type, "Analyze {scope} for {analysis_type}")
        return template.format(**kwargs)
    
    @classmethod
    def get_compliance_prompt(cls, compliance_type: str, **kwargs) -> str:
        """Get formatted compliance prompt"""
        template = cls.COMPLIANCE_TEMPLATES.get(
            compliance_type,
            "Check compliance for {scope} against {standards}"
        )
        return template.format(**kwargs)
    
    @classmethod
    def get_troubleshooting_prompt(cls, issue_type: str, **kwargs) -> str:
        """Get formatted troubleshooting prompt"""
        template = cls.TROUBLESHOOTING_TEMPLATES.get(
            issue_type,
            "Troubleshoot {problem_description} in {location}"
        )
        return template.format(**kwargs)
    
    @classmethod
    def format_response_with_actions(cls, content: str, actions: List[Dict[str, Any]]) -> str:
        """
        Format response with action buttons/links.
        
        Args:
            content: Main response content
            actions: List of available actions
            
        Returns:
            Formatted response with actions
        """
        if not actions:
            return content
        
        formatted = content + "\n\n**Available Actions:**\n"
        for i, action in enumerate(actions, 1):
            action_type = action.get('type', 'action')
            action_label = action.get('label', f'Action {i}')
            action_desc = action.get('description', '')
            
            if action_type == 'query':
                formatted += f"{i}. 🔍 {action_label}: {action_desc}\n"
            elif action_type == 'report':
                formatted += f"{i}. 📊 {action_label}: {action_desc}\n"
            elif action_type == 'modify':
                formatted += f"{i}. ⚙️ {action_label}: {action_desc}\n"
            elif action_type == 'ticket':
                formatted += f"{i}. 🎫 {action_label}: {action_desc}\n"
            else:
                formatted += f"{i}. • {action_label}: {action_desc}\n"
        
        return formatted
    
    @classmethod
    def format_data_table(cls, data: List[Dict[str, Any]], columns: List[str]) -> str:
        """
        Format data as a text table.
        
        Args:
            data: List of data rows
            columns: Column names to display
            
        Returns:
            Formatted table string
        """
        if not data:
            return "No data available."
        
        # Calculate column widths
        widths = {}
        for col in columns:
            widths[col] = max(
                len(col),
                max(len(str(row.get(col, ''))) for row in data)
            )
        
        # Build header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        separator = "-+-".join("-" * widths[col] for col in columns)
        
        # Build rows
        rows = []
        for row in data:
            row_str = " | ".join(
                str(row.get(col, '')).ljust(widths[col]) for col in columns
            )
            rows.append(row_str)
        
        return f"{header}\n{separator}\n" + "\n".join(rows)