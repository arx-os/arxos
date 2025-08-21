"""
PDF quality assessment for confidence calibration
Determines extraction difficulty and expected accuracy
"""

import io
from typing import Dict, Any, List, Optional
import pdfplumber
import numpy as np
from PIL import Image
import cv2


class QualityAssessor:
    """
    Assess PDF quality to calibrate confidence expectations
    Identifies extraction challenges and provides recommendations
    """
    
    def __init__(self):
        self.quality_metrics = {
            "vector_content": 0.0,
            "text_quality": 0.0,
            "image_quality": 0.0,
            "scale_detection": False,
            "extractability": 0.0,
            "complexity": "unknown"
        }
    
    async def assess_pdf_quality(
        self,
        pdf_content: bytes
    ) -> Dict[str, Any]:
        """
        Comprehensive PDF quality assessment
        
        Args:
            pdf_content: Raw PDF bytes
        
        Returns:
            Quality assessment with metrics and recommendations
        """
        
        # Open PDF with pdfplumber
        pdf_doc = pdfplumber.open(io.BytesIO(pdf_content))
        
        # Assess vector content
        vector_score = self._assess_vector_content(pdf_doc)
        
        # Assess text content
        text_score = self._assess_text_quality(pdf_doc)
        
        # Assess raster content
        image_score = await self._assess_image_quality(pdf_doc)
        
        # Detect scale information
        has_scale = self._detect_scale_information(pdf_doc)
        
        # Assess complexity
        complexity = self._assess_complexity(pdf_doc)
        
        # Calculate overall extractability
        extractability = self._calculate_extractability(
            vector_score, text_score, image_score, has_scale
        )
        
        pdf_doc.close()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            vector_score, text_score, image_score, 
            has_scale, complexity, extractability
        )
        
        return {
            "extractability": extractability,
            "vector_content": vector_score,
            "text_quality": text_score,
            "image_quality": image_score,
            "scale_detection": has_scale,
            "complexity": complexity,
            "recommendations": recommendations,
            "confidence_adjustment": self._calculate_confidence_adjustment(
                extractability, complexity
            )
        }
    
    def _assess_vector_content(self, pdf_doc: Any) -> float:
        """Assess quality and quantity of vector graphics"""
        
        total_drawings = 0
        quality_scores = []
        
        for page in pdf_doc:
            drawings = page.get_drawings()
            total_drawings += len(drawings)
            
            # Assess drawing quality
            for drawing in drawings:
                score = 0.0
                
                # Check for precise coordinates
                if drawing.get("items"):
                    score += 0.3
                
                # Check for color information
                if drawing.get("color"):
                    score += 0.2
                
                # Check for stroke width
                if drawing.get("width"):
                    score += 0.2
                
                # Check for fill
                if drawing.get("fill"):
                    score += 0.1
                
                # Check complexity
                if len(drawing.get("items", [])) > 2:
                    score += 0.2
                
                quality_scores.append(score)
        
        if not quality_scores:
            return 0.0
        
        # Weight by quantity and average quality
        quantity_factor = min(total_drawings / 100, 1.0)  # Normalize by 100
        avg_quality = np.mean(quality_scores)
        
        return avg_quality * (0.7 + 0.3 * quantity_factor)
    
    def _assess_text_quality(self, pdf_doc: Any) -> float:
        """Assess quality of text content"""
        
        text_scores = []
        
        for page in pdf_doc:
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    score = 0.0
                    
                    # Check for font information
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("font"):
                                score += 0.3
                            if span.get("size"):
                                score += 0.2
                            if span.get("flags"):  # Bold, italic, etc.
                                score += 0.1
                            
                            # Check text content
                            text = span.get("text", "").strip()
                            if text:
                                # Check for labels
                                if any(keyword in text.lower() for keyword in 
                                      ["room", "wall", "door", "window", "panel"]):
                                    score += 0.4
                    
                    if score > 0:
                        text_scores.append(min(score, 1.0))
        
        return np.mean(text_scores) if text_scores else 0.0
    
    async def _assess_image_quality(self, pdf_doc: Any) -> float:
        """Assess quality of raster images"""
        
        image_scores = []
        
        for page_num, page in enumerate(pdf_doc):
            # Get page as image
            # Convert page to image with pdfplumber
            img = page.to_image(resolution=150).original
            img_data = mat.pil_tobytes(format="PNG")
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Assess resolution
            resolution_score = min(img_array.shape[0] * img_array.shape[1] / (3000 * 3000), 1.0)
            
            # Assess contrast
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            contrast = gray.std() / 128  # Normalize by half of 8-bit range
            contrast_score = min(contrast, 1.0)
            
            # Assess sharpness (using Laplacian)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var() / 1000  # Normalize
            sharpness_score = min(sharpness, 1.0)
            
            # Combine scores
            image_score = (resolution_score * 0.3 + 
                          contrast_score * 0.3 + 
                          sharpness_score * 0.4)
            
            image_scores.append(image_score)
        
        return np.mean(image_scores) if image_scores else 0.0
    
    def _detect_scale_information(self, pdf_doc: Any) -> bool:
        """Detect if PDF contains scale information"""
        
        scale_keywords = [
            "scale", "1:", "1/", "@", "=", 
            "feet", "meters", "ft", "m", "mm", "inches"
        ]
        
        for page in pdf_doc:
            text = page.get_text().lower()
            
            # Check for scale notation
            for keyword in scale_keywords:
                if keyword in text:
                    # Look for numeric scale (e.g., "1:100", "1/4")
                    if keyword in ["1:", "1/"]:
                        # Check if followed by number
                        idx = text.find(keyword)
                        if idx != -1 and idx + 2 < len(text):
                            next_chars = text[idx+2:idx+5]
                            if any(c.isdigit() for c in next_chars):
                                return True
                    else:
                        return True
        
        return False
    
    def _assess_complexity(self, pdf_doc: Any) -> str:
        """Assess drawing complexity"""
        
        total_elements = 0
        total_pages = pdf_doc.page_count
        
        for page in pdf_doc:
            # Count vector elements
            drawings = page.get_drawings()
            total_elements += len(drawings)
            
            # Count text blocks
            text_dict = page.get_text("dict")
            total_elements += len(text_dict.get("blocks", []))
        
        avg_elements = total_elements / total_pages if total_pages > 0 else 0
        
        if avg_elements < 50:
            return "simple"
        elif avg_elements < 200:
            return "medium"
        elif avg_elements < 500:
            return "complex"
        else:
            return "very_complex"
    
    def _calculate_extractability(
        self,
        vector_score: float,
        text_score: float,
        image_score: float,
        has_scale: bool
    ) -> float:
        """Calculate overall extractability score"""
        
        # Weight different aspects
        extractability = (
            vector_score * 0.5 +    # Vector most important
            text_score * 0.3 +       # Text labels important
            image_score * 0.2        # Raster fallback
        )
        
        # Boost if scale is detected
        if has_scale:
            extractability = min(extractability * 1.2, 1.0)
        
        return extractability
    
    def _generate_recommendations(
        self,
        vector_score: float,
        text_score: float,
        image_score: float,
        has_scale: bool,
        complexity: str,
        extractability: float
    ) -> List[str]:
        """Generate recommendations based on assessment"""
        
        recommendations = []
        
        # Overall assessment
        if extractability >= 0.8:
            recommendations.append("High quality PDF suitable for accurate extraction")
        elif extractability >= 0.6:
            recommendations.append("Good quality PDF with moderate extraction confidence")
        elif extractability >= 0.4:
            recommendations.append("Fair quality PDF - validation recommended for critical elements")
        else:
            recommendations.append("Poor quality PDF - extensive validation required")
        
        # Specific recommendations
        if vector_score < 0.5:
            recommendations.append("Limited vector content - consider requesting vector-based drawings")
        elif vector_score > 0.8:
            recommendations.append("Excellent vector content - expect high position accuracy")
        
        if text_score < 0.3:
            recommendations.append("Minimal text labels - object classification may be uncertain")
        elif text_score > 0.7:
            recommendations.append("Good text labeling - classification confidence will be higher")
        
        if not has_scale:
            recommendations.append("No scale detected - dimensions may need validation")
        else:
            recommendations.append("Scale information found - dimensional accuracy possible")
        
        if complexity == "very_complex":
            recommendations.append("Very complex drawing - consider processing by floor/section")
        elif complexity == "simple":
            recommendations.append("Simple drawing - may lack detail for complete extraction")
        
        # Validation strategy
        if extractability < 0.6:
            recommendations.append("Recommend validating 30-40% of extracted objects")
        elif extractability < 0.8:
            recommendations.append("Recommend validating 15-20% of critical objects")
        else:
            recommendations.append("Recommend spot-checking 5-10% of objects")
        
        return recommendations
    
    def _calculate_confidence_adjustment(
        self,
        extractability: float,
        complexity: str
    ) -> float:
        """
        Calculate confidence adjustment factor
        
        Returns:
            Multiplier for base confidence (0.5 to 1.2)
        """
        
        # Base adjustment from extractability
        base_adjustment = 0.5 + extractability * 0.5
        
        # Complexity adjustment
        complexity_factors = {
            "simple": 1.1,
            "medium": 1.0,
            "complex": 0.9,
            "very_complex": 0.8,
            "unknown": 0.95
        }
        
        complexity_factor = complexity_factors.get(complexity, 0.95)
        
        # Combine adjustments
        final_adjustment = base_adjustment * complexity_factor
        
        # Clamp between 0.5 and 1.2
        return max(0.5, min(1.2, final_adjustment))
    
    def get_extraction_strategy(
        self,
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine optimal extraction strategy based on quality
        
        Args:
            quality_assessment: Result from assess_pdf_quality
        
        Returns:
            Extraction strategy configuration
        """
        
        extractability = quality_assessment["extractability"]
        vector_score = quality_assessment["vector_content"]
        complexity = quality_assessment["complexity"]
        
        strategy = {
            "primary_method": "vector" if vector_score > 0.6 else "hybrid",
            "use_ocr": vector_score < 0.3,
            "confidence_threshold": max(0.5, 0.6 - extractability * 0.2),
            "validation_percentage": self._calculate_validation_percentage(
                extractability, complexity
            ),
            "processing_options": []
        }
        
        # Add specific options
        if complexity in ["complex", "very_complex"]:
            strategy["processing_options"].append("segment_by_region")
        
        if not quality_assessment["scale_detection"]:
            strategy["processing_options"].append("estimate_scale")
        
        if vector_score < 0.5:
            strategy["processing_options"].append("enhance_images")
        
        return strategy
    
    def _calculate_validation_percentage(
        self,
        extractability: float,
        complexity: str
    ) -> float:
        """Calculate recommended validation percentage"""
        
        # Base percentage from extractability
        base_pct = max(5, 40 * (1 - extractability))
        
        # Adjust for complexity
        if complexity == "very_complex":
            base_pct *= 1.5
        elif complexity == "simple":
            base_pct *= 0.7
        
        return min(50, base_pct)  # Cap at 50%