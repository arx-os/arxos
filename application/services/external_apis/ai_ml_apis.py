"""
AI and ML API Integration

This module provides integration with external AI and ML services
for building optimization recommendations and performance predictions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from domain.mcp_engineering_entities import (
    BuildingData,
    AIRecommendation,
    MLPrediction,
    SuggestionType,
)
from infrastructure.services.mcp_engineering_client import (
    MCPEngineeringHTTPClient,
    APIConfig,
)


class AIMLAPIs:
    """
    AI and ML API integration service.

    Provides integration with external AI and ML services for:
    - Building optimization recommendations
    - Energy efficiency predictions
    - Cost savings analysis
    - Performance optimization suggestions
    - Risk assessment predictions
    - Compliance optimization recommendations
    """

    def __init__(self, client: MCPEngineeringHTTPClient):
        """Initialize the AI/ML API integration."""
        self.client = client
        self.logger = logging.getLogger(__name__)

    async def get_ai_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get AI-powered recommendations for building improvements.

        Args:
            building_data: Building data to analyze

        Returns:
            List of AIRecommendation objects
        """
        self.logger.info(
            f"Getting AI recommendations for building: {building_data.building_type}"
        )

        try:
            recommendations = await self.client.get_ai_recommendations(building_data)

            self.logger.info(
                f"AI recommendations completed: {len(recommendations)} recommendations generated"
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"AI recommendations failed: {e}")
            return []

    async def get_ml_predictions(
        self, building_data: BuildingData
    ) -> List[MLPrediction]:
        """
        Get ML predictions for building performance and compliance.

        Args:
            building_data: Building data to analyze

        Returns:
            List of MLPrediction objects
        """
        self.logger.info(
            f"Getting ML predictions for building: {building_data.building_type}"
        )

        try:
            predictions = await self.client.get_ml_predictions(building_data)

            self.logger.info(
                f"ML predictions completed: {len(predictions)} predictions generated"
            )

            return predictions

        except Exception as e:
            self.logger.error(f"ML predictions failed: {e}")
            return []

    async def get_optimization_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get optimization-specific recommendations.

        Args:
            building_data: Building data to analyze

        Returns:
            List of optimization recommendations
        """
        self.logger.info(
            f"Getting optimization recommendations for building: {building_data.building_type}"
        )

        try:
            all_recommendations = await self.get_ai_recommendations(building_data)

            # Filter for optimization recommendations
            optimization_recommendations = [
                rec
                for rec in all_recommendations
                if rec.type == SuggestionType.OPTIMIZATION
            ]

            self.logger.info(
                f"Optimization recommendations: {len(optimization_recommendations)} found"
            )

            return optimization_recommendations

        except Exception as e:
            self.logger.error(f"Optimization recommendations failed: {e}")
            return []

    async def get_cost_savings_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get cost savings recommendations.

        Args:
            building_data: Building data to analyze

        Returns:
            List of cost savings recommendations
        """
        self.logger.info(
            f"Getting cost savings recommendations for building: {building_data.building_type}"
        )

        try:
            all_recommendations = await self.get_ai_recommendations(building_data)

            # Filter for cost saving recommendations
            cost_savings_recommendations = [
                rec
                for rec in all_recommendations
                if rec.type == SuggestionType.COST_SAVING
            ]

            self.logger.info(
                f"Cost savings recommendations: {len(cost_savings_recommendations)} found"
            )

            return cost_savings_recommendations

        except Exception as e:
            self.logger.error(f"Cost savings recommendations failed: {e}")
            return []

    async def get_safety_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get safety improvement recommendations.

        Args:
            building_data: Building data to analyze

        Returns:
            List of safety recommendations
        """
        self.logger.info(
            f"Getting safety recommendations for building: {building_data.building_type}"
        )

        try:
            all_recommendations = await self.get_ai_recommendations(building_data)

            # Filter for safety recommendations
            safety_recommendations = [
                rec for rec in all_recommendations if rec.type == SuggestionType.SAFETY
            ]

            self.logger.info(
                f"Safety recommendations: {len(safety_recommendations)} found"
            )

            return safety_recommendations

        except Exception as e:
            self.logger.error(f"Safety recommendations failed: {e}")
            return []

    async def get_efficiency_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get efficiency improvement recommendations.

        Args:
            building_data: Building data to analyze

        Returns:
            List of efficiency recommendations
        """
        self.logger.info(
            f"Getting efficiency recommendations for building: {building_data.building_type}"
        )

        try:
            all_recommendations = await self.get_ai_recommendations(building_data)

            # Filter for efficiency recommendations
            efficiency_recommendations = [
                rec
                for rec in all_recommendations
                if rec.type == SuggestionType.EFFICIENCY
            ]

            self.logger.info(
                f"Efficiency recommendations: {len(efficiency_recommendations)} found"
            )

            return efficiency_recommendations

        except Exception as e:
            self.logger.error(f"Efficiency recommendations failed: {e}")
            return []

    async def get_compliance_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get compliance improvement recommendations.

        Args:
            building_data: Building data to analyze

        Returns:
            List of compliance recommendations
        """
        self.logger.info(
            f"Getting compliance recommendations for building: {building_data.building_type}"
        )

        try:
            all_recommendations = await self.get_ai_recommendations(building_data)

            # Filter for compliance recommendations
            compliance_recommendations = [
                rec
                for rec in all_recommendations
                if rec.type == SuggestionType.COMPLIANCE
            ]

            self.logger.info(
                f"Compliance recommendations: {len(compliance_recommendations)} found"
            )

            return compliance_recommendations

        except Exception as e:
            self.logger.error(f"Compliance recommendations failed: {e}")
            return []

    async def get_energy_performance_predictions(
        self, building_data: BuildingData
    ) -> List[MLPrediction]:
        """
        Get energy performance predictions.

        Args:
            building_data: Building data to analyze

        Returns:
            List of energy performance predictions
        """
        self.logger.info(
            f"Getting energy performance predictions for building: {building_data.building_type}"
        )

        try:
            all_predictions = await self.get_ml_predictions(building_data)

            # Filter for energy performance predictions
            energy_predictions = [
                pred
                for pred in all_predictions
                if "energy" in pred.prediction_type.lower()
            ]

            self.logger.info(
                f"Energy performance predictions: {len(energy_predictions)} found"
            )

            return energy_predictions

        except Exception as e:
            self.logger.error(f"Energy performance predictions failed: {e}")
            return []

    async def get_risk_assessment_predictions(
        self, building_data: BuildingData
    ) -> List[MLPrediction]:
        """
        Get risk assessment predictions.

        Args:
            building_data: Building data to analyze

        Returns:
            List of risk assessment predictions
        """
        self.logger.info(
            f"Getting risk assessment predictions for building: {building_data.building_type}"
        )

        try:
            all_predictions = await self.get_ml_predictions(building_data)

            # Filter for risk assessment predictions
            risk_predictions = [
                pred
                for pred in all_predictions
                if "risk" in pred.prediction_type.lower()
            ]

            self.logger.info(
                f"Risk assessment predictions: {len(risk_predictions)} found"
            )

            return risk_predictions

        except Exception as e:
            self.logger.error(f"Risk assessment predictions failed: {e}")
            return []

    async def get_comprehensive_analysis(
        self, building_data: BuildingData
    ) -> Dict[str, Any]:
        """
        Get comprehensive AI/ML analysis for a building.

        Args:
            building_data: Building data to analyze

        Returns:
            Comprehensive analysis results
        """
        self.logger.info(
            f"Getting comprehensive AI/ML analysis for building: {building_data.building_type}"
        )

        try:
            # Get all recommendations and predictions concurrently
            import asyncio

            tasks = [
                self.get_ai_recommendations(building_data),
                self.get_ml_predictions(building_data),
                self.get_optimization_recommendations(building_data),
                self.get_cost_savings_recommendations(building_data),
                self.get_safety_recommendations(building_data),
                self.get_efficiency_recommendations(building_data),
                self.get_compliance_recommendations(building_data),
                self.get_energy_performance_predictions(building_data),
                self.get_risk_assessment_predictions(building_data),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            all_recommendations = (
                results[0] if not isinstance(results[0], Exception) else []
            )
            all_predictions = (
                results[1] if not isinstance(results[1], Exception) else []
            )
            optimization_recommendations = (
                results[2] if not isinstance(results[2], Exception) else []
            )
            cost_savings_recommendations = (
                results[3] if not isinstance(results[3], Exception) else []
            )
            safety_recommendations = (
                results[4] if not isinstance(results[4], Exception) else []
            )
            efficiency_recommendations = (
                results[5] if not isinstance(results[5], Exception) else []
            )
            compliance_recommendations = (
                results[6] if not isinstance(results[6], Exception) else []
            )
            energy_predictions = (
                results[7] if not isinstance(results[7], Exception) else []
            )
            risk_predictions = (
                results[8] if not isinstance(results[8], Exception) else []
            )

            # Calculate total estimated savings
            total_estimated_savings = sum(
                rec.estimated_savings or 0
                for rec in all_recommendations
                if rec.estimated_savings
            )

            # Calculate total implementation cost
            total_implementation_cost = sum(
                rec.implementation_cost or 0
                for rec in all_recommendations
                if rec.implementation_cost
            )

            # Calculate ROI
            roi = (
                (total_estimated_savings - total_implementation_cost)
                / total_implementation_cost
                * 100
                if total_implementation_cost > 0
                else 0
            )

            analysis = {
                "building_data": {
                    "building_type": building_data.building_type,
                    "area": building_data.area,
                    "floors": building_data.floors,
                    "jurisdiction": building_data.jurisdiction,
                },
                "recommendations": {
                    "total_recommendations": len(all_recommendations),
                    "optimization_recommendations": len(optimization_recommendations),
                    "cost_savings_recommendations": len(cost_savings_recommendations),
                    "safety_recommendations": len(safety_recommendations),
                    "efficiency_recommendations": len(efficiency_recommendations),
                    "compliance_recommendations": len(compliance_recommendations),
                    "all_recommendations": all_recommendations,
                },
                "predictions": {
                    "total_predictions": len(all_predictions),
                    "energy_predictions": len(energy_predictions),
                    "risk_predictions": len(risk_predictions),
                    "all_predictions": all_predictions,
                },
                "financial_analysis": {
                    "total_estimated_savings": total_estimated_savings,
                    "total_implementation_cost": total_implementation_cost,
                    "roi_percentage": roi,
                    "payback_period_months": (
                        total_implementation_cost / (total_estimated_savings / 12)
                        if total_estimated_savings > 0
                        else None
                    ),
                },
                "summary": {
                    "high_impact_recommendations": len(
                        [
                            r
                            for r in all_recommendations
                            if r.impact_score and r.impact_score > 0.7
                        ]
                    ),
                    "high_confidence_predictions": len(
                        [
                            p
                            for p in all_predictions
                            if p.confidence and p.confidence > 0.8
                        ]
                    ),
                    "priority_recommendations": sorted(
                        [
                            r
                            for r in all_recommendations
                            if r.impact_score and r.impact_score > 0.6
                        ],
                        key=lambda x: x.impact_score,
                        reverse=True,
                    )[:5],
                },
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(
                f"Comprehensive analysis completed: {len(all_recommendations)} recommendations, "
                f"{len(all_predictions)} predictions, ${total_estimated_savings:,.2f} estimated savings"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_recommendation_summary(
        self, recommendations: List[AIRecommendation]
    ) -> Dict[str, Any]:
        """
        Generate a summary of AI recommendations.

        Args:
            recommendations: List of AI recommendations

        Returns:
            Summary dictionary with statistics
        """
        if not recommendations:
            return {
                "total_recommendations": 0,
                "recommendations_by_type": {},
                "total_estimated_savings": 0,
                "total_implementation_cost": 0,
                "average_confidence": 0,
                "average_impact_score": 0,
            }

        # Group recommendations by type
        recommendations_by_type = {}
        for rec in recommendations:
            rec_type = rec.type.value if hasattr(rec.type, "value") else str(rec.type)
            if rec_type not in recommendations_by_type:
                recommendations_by_type[rec_type] = []
            recommendations_by_type[rec_type].append(rec)

        # Calculate financial metrics
        total_estimated_savings = sum(
            rec.estimated_savings or 0 for rec in recommendations
        )
        total_implementation_cost = sum(
            rec.implementation_cost or 0 for rec in recommendations
        )

        # Calculate average scores
        confidences = [rec.confidence for rec in recommendations if rec.confidence]
        impact_scores = [
            rec.impact_score for rec in recommendations if rec.impact_score
        ]

        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        average_impact_score = (
            sum(impact_scores) / len(impact_scores) if impact_scores else 0
        )

        return {
            "total_recommendations": len(recommendations),
            "recommendations_by_type": {
                rec_type: len(recs)
                for rec_type, recs in recommendations_by_type.items()
            },
            "total_estimated_savings": total_estimated_savings,
            "total_implementation_cost": total_implementation_cost,
            "average_confidence": average_confidence,
            "average_impact_score": average_impact_score,
            "roi_percentage": (
                (total_estimated_savings - total_implementation_cost)
                / total_implementation_cost
                * 100
                if total_implementation_cost > 0
                else 0
            ),
        }

    def get_prediction_summary(self, predictions: List[MLPrediction]) -> Dict[str, Any]:
        """
        Generate a summary of ML predictions.

        Args:
            predictions: List of ML predictions

        Returns:
            Summary dictionary with statistics
        """
        if not predictions:
            return {
                "total_predictions": 0,
                "predictions_by_type": {},
                "average_confidence": 0,
                "high_confidence_predictions": 0,
            }

        # Group predictions by type
        predictions_by_type = {}
        for pred in predictions:
            pred_type = pred.prediction_type
            if pred_type not in predictions_by_type:
                predictions_by_type[pred_type] = []
            predictions_by_type[pred_type].append(pred)

        # Calculate confidence metrics
        confidences = [pred.confidence for pred in predictions if pred.confidence]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_confidence_predictions = len(
            [p for p in predictions if p.confidence and p.confidence > 0.8]
        )

        return {
            "total_predictions": len(predictions),
            "predictions_by_type": {
                pred_type: len(preds)
                for pred_type, preds in predictions_by_type.items()
            },
            "average_confidence": average_confidence,
            "high_confidence_predictions": high_confidence_predictions,
            "confidence_distribution": {
                "high": len(
                    [p for p in predictions if p.confidence and p.confidence > 0.8]
                ),
                "medium": len(
                    [
                        p
                        for p in predictions
                        if p.confidence and 0.5 <= p.confidence <= 0.8
                    ]
                ),
                "low": len(
                    [p for p in predictions if p.confidence and p.confidence < 0.5]
                ),
            },
        }
