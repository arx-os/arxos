"""
Search Engine for Knowledge Base

This module provides advanced search capabilities for building codes,
including semantic search, keyword matching, and relevance scoring.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
import asyncio

from pydantic import BaseModel, Field
from knowledge.knowledge_base import CodeRequirement

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Search result with relevance scoring"""

    code_requirement: CodeRequirement
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    matched_terms: List[str] = Field(
        default_factory=list, description="Matched search terms"
    )
    highlight_snippets: List[str] = Field(
        default_factory=list, description="Highlighted text snippets"
    )


class SearchQuery(BaseModel):
    """Search query model"""

    query: str = Field(..., description="Search query text")
    code_standard: Optional[str] = Field(None, description="Filter by code standard")
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    version: Optional[str] = Field(None, description="Filter by code version")
    max_results: int = Field(50, description="Maximum number of results")
    min_relevance: float = Field(0.1, description="Minimum relevance score")


class SearchEngine:
    """Advanced search engine for building codes"""

    def __init__(self):
        """Initialize the search engine"""
        # Common building code terms and their weights
        self.term_weights = {
            # High importance terms
            "shall": 2.0,
            "must": 2.0,
            "required": 2.0,
            "comply": 2.0,
            "minimum": 1.8,
            "maximum": 1.8,
            "prohibited": 1.8,
            "permitted": 1.5,
            # Medium importance terms
            "access": 1.5,
            "egress": 1.5,
            "safety": 1.5,
            "fire": 1.5,
            "electrical": 1.5,
            "structural": 1.5,
            "mechanical": 1.5,
            "plumbing": 1.5,
            # Code-specific terms
            "occupant": 1.3,
            "load": 1.3,
            "factor": 1.3,
            "area": 1.3,
            "height": 1.3,
            "width": 1.3,
            "distance": 1.3,
            "clearance": 1.3,
            # Standard terms
            "building": 1.2,
            "facility": 1.2,
            "structure": 1.2,
            "construction": 1.2,
            "installation": 1.2,
            "equipment": 1.2,
            "system": 1.2,
            "component": 1.2,
        }

        # Stop words to ignore
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize search query"""
        # Convert to lowercase and split
        tokens = re.findall(r"\b\w+\b", query.lower())

        # Remove stop words and short tokens
        tokens = [
            token for token in tokens if token not in self.stop_words and len(token) > 2
        ]

        return tokens

    def _calculate_term_frequency(self, text: str, term: str) -> float:
        """Calculate term frequency in text"""
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return 0.0

        term_count = words.count(term.lower())
        return term_count / len(words)

    def _calculate_relevance_score(
        self, code_requirement: CodeRequirement, search_terms: List[str]
    ) -> Tuple[float, List[str]]:
        """Calculate relevance score for a code requirement"""
        score = 0.0
        matched_terms = []

        # Combine all searchable text
        searchable_text = f"{code_requirement.title} {code_requirement.content}"
        searchable_text_lower = searchable_text.lower()

        for term in search_terms:
            term_lower = term.lower()

            # Check if term appears in text
            if term_lower in searchable_text_lower:
                matched_terms.append(term)

                # Base score for term match
                base_score = 0.1

                # Boost score for title matches
                if term_lower in code_requirement.title.lower():
                    base_score += 0.3

                # Boost score for weighted terms
                if term_lower in self.term_weights:
                    base_score *= self.term_weights[term_lower]

                # Boost score for exact phrase matches
                if term in code_requirement.title:
                    base_score += 0.2

                # Boost score for section number matches
                if term in code_requirement.section_number:
                    base_score += 0.4

                # Calculate term frequency
                tf = self._calculate_term_frequency(searchable_text, term)
                base_score += tf * 0.1

                score += base_score

        # Normalize score
        if score > 0:
            score = min(score, 1.0)

        return score, matched_terms

    def _generate_highlight_snippets(
        self, code_requirement: CodeRequirement, matched_terms: List[str]
    ) -> List[str]:
        """Generate highlighted snippets for search results"""
        snippets = []
        text = f"{code_requirement.title}. {code_requirement.content}"

        # Find sentences containing matched terms
        sentences = re.split(r"[.!?]+", text)

        for sentence in sentences:
            sentence_lower = sentence.lower()
            for term in matched_terms:
                if term.lower() in sentence_lower:
                    # Highlight the term in the snippet
                    highlighted = sentence.replace(term, f"**{term}**")
                    snippets.append(highlighted.strip())
                    break

        # Limit snippets to avoid overwhelming results
        return snippets[:3]

    async def search(
        self, search_query: SearchQuery, code_requirements: List[CodeRequirement]
    ) -> List[SearchResult]:
        """Perform advanced search on code requirements"""
        try:
            # Tokenize query
            search_terms = self._tokenize_query(search_query.query)

            if not search_terms:
                logger.warning("No valid search terms found in query")
                return []

            # Filter by criteria
            filtered_requirements = []
            for req in code_requirements:
                # Filter by code standard
                if (
                    search_query.code_standard
                    and req.code_standard != search_query.code_standard
                ):
                    continue

                # Filter by jurisdiction
                if (
                    search_query.jurisdiction
                    and req.jurisdiction != search_query.jurisdiction
                ):
                    continue

                # Filter by version
                if search_query.version and req.version != search_query.version:
                    continue

                filtered_requirements.append(req)

            # Calculate relevance scores
            search_results = []
            for req in filtered_requirements:
                relevance_score, matched_terms = self._calculate_relevance_score(
                    req, search_terms
                )

                # Only include results above minimum relevance
                if relevance_score >= search_query.min_relevance:
                    highlight_snippets = self._generate_highlight_snippets(
                        req, matched_terms
                    )

                    search_result = SearchResult(
                        code_requirement=req,
                        relevance_score=relevance_score,
                        matched_terms=matched_terms,
                        highlight_snippets=highlight_snippets,
                    )
                    search_results.append(search_result)

            # Sort by relevance score (highest first)
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)

            # Limit results
            search_results = search_results[: search_query.max_results]

            logger.info(
                f"Search returned {len(search_results)} results for query: {search_query.query}"
            )
            return search_results

        except Exception as e:
            logger.error(f"❌ Error performing search: {e}")
            return []

    async def search_by_section_number(
        self, section_number: str, code_standard: Optional[str] = None
    ) -> List[SearchResult]:
        """Search by exact section number"""
        try:
            search_query = SearchQuery(
                query=section_number, code_standard=code_standard, max_results=10
            )

            # This would typically search against the knowledge base
            # For now, return empty results as this requires database integration
            return []

        except Exception as e:
            logger.error(f"❌ Error searching by section number: {e}")
            return []

    async def search_similar_sections(
        self, code_requirement: CodeRequirement, max_results: int = 5
    ) -> List[SearchResult]:
        """Find similar code sections based on content similarity"""
        try:
            # Extract key terms from the requirement
            key_terms = self._extract_key_terms(code_requirement)

            # Create search query from key terms
            query_text = " ".join(key_terms[:5])  # Use top 5 terms

            search_query = SearchQuery(
                query=query_text,
                code_standard=code_requirement.code_standard,
                max_results=max_results,
                min_relevance=0.3,  # Lower threshold for similarity search
            )

            # This would search against the knowledge base
            # For now, return empty results
            return []

        except Exception as e:
            logger.error(f"❌ Error finding similar sections: {e}")
            return []

    def _extract_key_terms(self, code_requirement: CodeRequirement) -> List[str]:
        """Extract key terms from a code requirement"""
        # Combine title and content
        text = f"{code_requirement.title} {code_requirement.content}"

        # Tokenize
        tokens = self._tokenize_query(text)

        # Score tokens by importance
        token_scores = {}
        for token in tokens:
            score = 1.0

            # Boost score for weighted terms
            if token in self.term_weights:
                score *= self.term_weights[token]

            # Boost score for title terms
            if token in code_requirement.title.lower():
                score *= 1.5

            token_scores[token] = score

        # Sort by score and return top terms
        sorted_tokens = sorted(token_scores.items(), key=lambda x: x[1], reverse=True)
        return [token for token, score in sorted_tokens[:10]]

    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            suggestions = []

            # Common building code terms that might match
            common_terms = [
                "occupant load",
                "fire safety",
                "electrical",
                "structural",
                "accessibility",
                "egress",
                "clearance",
                "height",
                "width",
                "distance",
                "minimum",
                "maximum",
                "required",
                "prohibited",
            ]

            partial_lower = partial_query.lower()
            for term in common_terms:
                if partial_lower in term.lower():
                    suggestions.append(term)

            # Add code standards
            code_standards = ["IBC", "NEC", "IFC", "ADA", "NFPA", "ASHRAE"]
            for code in code_standards:
                if partial_lower in code.lower():
                    suggestions.append(code)

            return suggestions[:10]  # Limit suggestions

        except Exception as e:
            logger.error(f"❌ Error getting search suggestions: {e}")
            return []

    async def get_search_statistics(
        self, search_results: List[SearchResult]
    ) -> Dict[str, Any]:
        """Get statistics about search results"""
        try:
            if not search_results:
                return {
                    "total_results": 0,
                    "average_relevance": 0.0,
                    "code_standards": {},
                    "top_matched_terms": [],
                }

            # Calculate statistics
            total_results = len(search_results)
            average_relevance = (
                sum(r.relevance_score for r in search_results) / total_results
            )

            # Count by code standard
            code_standards = defaultdict(int)
            for result in search_results:
                code_standards[result.code_requirement.code_standard] += 1

            # Get top matched terms
            all_matched_terms = []
            for result in search_results:
                all_matched_terms.extend(result.matched_terms)

            term_counts = defaultdict(int)
            for term in all_matched_terms:
                term_counts[term] += 1

            top_matched_terms = sorted(
                term_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "total_results": total_results,
                "average_relevance": round(average_relevance, 3),
                "code_standards": dict(code_standards),
                "top_matched_terms": [term for term, count in top_matched_terms],
            }

        except Exception as e:
            logger.error(f"❌ Error getting search statistics: {e}")
            return {}
