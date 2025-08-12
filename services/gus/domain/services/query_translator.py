"""
Query Translator Domain Service

This module translates natural language queries to Arxos Query Language (AQL).
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re


class QueryType(Enum):
    """Types of queries that can be generated"""
    FIND = "find"  # Find objects
    SELECT = "select"  # Select with conditions
    AGGREGATE = "aggregate"  # Aggregation queries
    SPATIAL = "spatial"  # Spatial relationship queries
    ANALYSIS = "analysis"  # Complex analysis queries
    UPDATE = "update"  # Update operations
    CREATE = "create"  # Create operations
    DELETE = "delete"  # Delete operations


@dataclass
class AQLQuery:
    """Represents an AQL query"""
    query_type: QueryType
    query_string: str
    parameters: Dict[str, Any]
    entities: List[str]  # Extracted entities (outlets, beams, etc.)
    spatial_relations: List[str]  # within, near, adjacent-to, etc.
    confidence: float
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query_type': self.query_type.value,
            'query_string': self.query_string,
            'parameters': self.parameters,
            'entities': self.entities,
            'spatial_relations': self.spatial_relations,
            'confidence': self.confidence,
            'explanation': self.explanation
        }


class QueryTranslator:
    """
    Service for translating natural language to AQL.
    
    This service handles the conversion of user queries in natural language
    to structured Arxos Query Language (AQL) commands.
    """
    
    # Common building entity types
    ENTITY_TYPES = {
        'electrical': ['outlet', 'outlets', 'circuit', 'circuits', 'breaker', 'breakers', 
                      'panel', 'panels', 'switch', 'switches', 'light', 'lights'],
        'structural': ['beam', 'beams', 'column', 'columns', 'wall', 'walls', 
                      'slab', 'slabs', 'foundation', 'roof'],
        'hvac': ['duct', 'ducts', 'vav', 'vav box', 'ahu', 'air handler', 
                'chiller', 'boiler', 'thermostat', 'damper'],
        'plumbing': ['pipe', 'pipes', 'valve', 'valves', 'pump', 'pumps', 
                    'fixture', 'fixtures', 'drain', 'drains'],
        'spaces': ['room', 'rooms', 'floor', 'floors', 'zone', 'zones', 
                  'area', 'areas', 'space', 'spaces']
    }
    
    # Spatial relationships
    SPATIAL_RELATIONS = {
        'within': ['within', 'inside', 'in'],
        'near': ['near', 'close to', 'nearby', 'around'],
        'adjacent': ['adjacent to', 'next to', 'beside'],
        'above': ['above', 'over'],
        'below': ['below', 'under', 'beneath'],
        'between': ['between'],
        'connected': ['connected to', 'linked to', 'attached to']
    }
    
    # Query patterns
    PATTERNS = {
        'find_all': r'(?:find|show|list|get)(?: all)? (\w+)',
        'find_where': r'(?:find|show|get) (\w+) (?:where|with|that have) (.+)',
        'find_spatial': r'(?:find|show|get) (\w+) (within|near|adjacent to|above|below) (.+)',
        'count': r'(?:how many|count)(?: of)? (\w+)',
        'check_compliance': r'(?:check|verify|validate) (?:compliance|code|requirements) (?:for|of) (.+)',
        'analyze': r'(?:analyze|calculate|compute) (.+) (?:for|of) (.+)',
        'optimize': r'(?:optimize|improve|enhance) (.+)',
        'overloaded': r'(?:overloaded|over capacity|exceeded) (\w+)',
        'status': r'(?:status|state|condition) (?:of|for) (.+)'
    }
    
    def translate(self, natural_query: str) -> AQLQuery:
        """
        Translate natural language query to AQL.
        
        Args:
            natural_query: The natural language query
            
        Returns:
            AQLQuery object with translated query
        """
        # Normalize the query
        query_lower = natural_query.lower().strip()
        
        # Extract entities and relationships
        entities = self._extract_entities(query_lower)
        spatial_relations = self._extract_spatial_relations(query_lower)
        
        # Determine query type and generate AQL
        query_type = self._determine_query_type(query_lower)
        
        # Generate AQL based on query type
        if query_type == QueryType.FIND:
            aql = self._generate_find_query(query_lower, entities, spatial_relations)
        elif query_type == QueryType.SPATIAL:
            aql = self._generate_spatial_query(query_lower, entities, spatial_relations)
        elif query_type == QueryType.AGGREGATE:
            aql = self._generate_aggregate_query(query_lower, entities)
        elif query_type == QueryType.ANALYSIS:
            aql = self._generate_analysis_query(query_lower, entities)
        else:
            aql = self._generate_generic_query(query_lower, entities)
        
        return aql
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract building entities from query"""
        entities = []
        for category, entity_list in self.ENTITY_TYPES.items():
            for entity in entity_list:
                if entity in query:
                    entities.append(entity)
        return entities
    
    def _extract_spatial_relations(self, query: str) -> List[str]:
        """Extract spatial relationships from query"""
        relations = []
        for relation_type, phrases in self.SPATIAL_RELATIONS.items():
            for phrase in phrases:
                if phrase in query:
                    relations.append(relation_type)
                    break
        return relations
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query"""
        if any(word in query for word in ['find', 'show', 'list', 'get', 'search']):
            if any(rel in query for rel in ['within', 'near', 'adjacent', 'above', 'below']):
                return QueryType.SPATIAL
            return QueryType.FIND
        elif any(word in query for word in ['count', 'how many', 'total']):
            return QueryType.AGGREGATE
        elif any(word in query for word in ['analyze', 'calculate', 'check', 'verify']):
            return QueryType.ANALYSIS
        elif any(word in query for word in ['update', 'modify', 'change', 'set']):
            return QueryType.UPDATE
        elif any(word in query for word in ['create', 'add', 'insert']):
            return QueryType.CREATE
        elif any(word in query for word in ['delete', 'remove']):
            return QueryType.DELETE
        else:
            return QueryType.SELECT
    
    def _generate_find_query(self, query: str, entities: List[str], spatial_relations: List[str]) -> AQLQuery:
        """Generate FIND query"""
        if not entities:
            entities = ['objects']  # Default to all objects
        
        entity = entities[0]
        
        # Check for conditions
        conditions = []
        if 'overloaded' in query or 'over capacity' in query:
            conditions.append('load > rated_capacity')
        if 'floor' in query:
            # Extract floor number
            floor_match = re.search(r'floor[:\s]+(\d+)', query)
            if floor_match:
                conditions.append(f"floor = {floor_match.group(1)}")
        if 'room' in query:
            # Extract room identifier
            room_match = re.search(r'room[:\s]+([A-Z0-9\-]+)', query, re.IGNORECASE)
            if room_match:
                conditions.append(f"room = '{room_match.group(1)}'")
        
        # Build AQL
        if conditions:
            aql_string = f"SELECT {entity} WHERE {' AND '.join(conditions)}"
        else:
            aql_string = f"FIND {entity}"
        
        return AQLQuery(
            query_type=QueryType.FIND,
            query_string=aql_string,
            parameters={'entity': entity, 'conditions': conditions},
            entities=entities,
            spatial_relations=spatial_relations,
            confidence=0.85,
            explanation=f"Finding {entity} with conditions: {conditions if conditions else 'none'}"
        )
    
    def _generate_spatial_query(self, query: str, entities: List[str], spatial_relations: List[str]) -> AQLQuery:
        """Generate spatial query"""
        if not entities or len(entities) < 1:
            entities = ['objects']
        if not spatial_relations:
            spatial_relations = ['near']
        
        source_entity = entities[0]
        relation = spatial_relations[0]
        
        # Extract target and distance
        target_match = re.search(rf'{relation}\s+(?:to\s+)?([a-zA-Z0-9:\-]+)', query)
        target = target_match.group(1) if target_match else 'unknown'
        
        distance_match = re.search(r'(\d+)\s*(ft|feet|m|meters?)', query)
        distance = f"{distance_match.group(1)}{distance_match.group(2)}" if distance_match else "10ft"
        
        aql_string = f"FIND {source_entity} {relation.upper()} {distance} OF {target}"
        
        return AQLQuery(
            query_type=QueryType.SPATIAL,
            query_string=aql_string,
            parameters={
                'source': source_entity,
                'relation': relation,
                'distance': distance,
                'target': target
            },
            entities=entities,
            spatial_relations=spatial_relations,
            confidence=0.80,
            explanation=f"Finding {source_entity} {relation} {distance} of {target}"
        )
    
    def _generate_aggregate_query(self, query: str, entities: List[str]) -> AQLQuery:
        """Generate aggregate query"""
        entity = entities[0] if entities else 'objects'
        
        # Determine aggregation type
        if 'count' in query or 'how many' in query:
            agg_type = 'COUNT'
        elif 'sum' in query or 'total' in query:
            agg_type = 'SUM'
        elif 'average' in query or 'avg' in query:
            agg_type = 'AVG'
        else:
            agg_type = 'COUNT'
        
        aql_string = f"SELECT {agg_type}({entity}) AS total"
        
        # Add grouping if specified
        if 'by floor' in query or 'per floor' in query:
            aql_string += " GROUP BY floor"
        elif 'by room' in query or 'per room' in query:
            aql_string += " GROUP BY room"
        
        return AQLQuery(
            query_type=QueryType.AGGREGATE,
            query_string=aql_string,
            parameters={'entity': entity, 'aggregation': agg_type},
            entities=entities,
            spatial_relations=[],
            confidence=0.75,
            explanation=f"Counting {entity}"
        )
    
    def _generate_analysis_query(self, query: str, entities: List[str]) -> AQLQuery:
        """Generate analysis query"""
        entity = entities[0] if entities else 'system'
        
        if 'compliance' in query or 'code' in query:
            aql_string = f"ANALYZE {entity} FOR compliance WITH nec_2020"
        elif 'efficiency' in query:
            aql_string = f"ANALYZE {entity} FOR efficiency"
        elif 'load' in query:
            aql_string = f"ANALYZE {entity} FOR load_distribution"
        else:
            aql_string = f"ANALYZE {entity}"
        
        return AQLQuery(
            query_type=QueryType.ANALYSIS,
            query_string=aql_string,
            parameters={'entity': entity, 'analysis_type': 'general'},
            entities=entities,
            spatial_relations=[],
            confidence=0.70,
            explanation=f"Analyzing {entity}"
        )
    
    def _generate_generic_query(self, query: str, entities: List[str]) -> AQLQuery:
        """Generate generic query as fallback"""
        entity = entities[0] if entities else 'objects'
        
        return AQLQuery(
            query_type=QueryType.SELECT,
            query_string=f"SELECT * FROM {entity}",
            parameters={'entity': entity},
            entities=entities,
            spatial_relations=[],
            confidence=0.50,
            explanation="Generic query - may need refinement"
        )