#!/usr/bin/env python3
"""
gRPC server for AI-powered ingestion services.
Bridges Python ML/CV capabilities with Go orchestration.
"""

import grpc
import logging
import asyncio
import traceback
from concurrent import futures
from typing import Optional, List, Dict, Any
import numpy as np
from dataclasses import dataclass
import json
import time

# Import proto-generated files (will be generated from proto)
# from proto.ingestion import ingestion_pb2, ingestion_pb2_grpc

# Import AI service modules
from services.pdf_extractor import PDFExtractor
from services.wall_detector import WallDetector
from services.measurement_extractor import MeasurementExtractor
from services.bim_generator import BIMGenerator
from services.confidence_scorer import ConfidenceScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingSession:
    """Track processing session state."""
    session_id: str
    status: str
    progress: float
    current_stage: str
    started_at: float
    updated_at: float
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_stages: List[str] = None
    pending_stages: List[str] = None


class IngestionServicer:
    """
    gRPC service implementation for AI-powered ingestion.
    """
    
    def __init__(self):
        """Initialize AI service modules."""
        logger.info("Initializing AI Ingestion Service")
        
        # Initialize AI modules
        self.pdf_extractor = PDFExtractor()
        self.wall_detector = WallDetector()
        self.measurement_extractor = MeasurementExtractor()
        self.bim_generator = BIMGenerator()
        self.confidence_scorer = ConfidenceScorer()
        
        # Session tracking
        self.sessions: Dict[str, ProcessingSession] = {}
        
        # Performance metrics
        self.metrics = {
            'pdf_extractions': 0,
            'wall_detections': 0,
            'bim_generations': 0,
            'total_processing_time': 0,
            'error_count': 0
        }
    
    async def ExtractPDF(self, request, context):
        """
        Extract text, images, and structure from PDF.
        
        Args:
            request: PDFExtractionRequest
            context: gRPC context
            
        Returns:
            PDFExtractionResponse
        """
        session_id = self._generate_session_id()
        logger.info(f"Starting PDF extraction for session {session_id}")
        
        try:
            # Create session
            session = ProcessingSession(
                session_id=session_id,
                status="processing",
                progress=0.0,
                current_stage="pdf_extraction",
                started_at=time.time(),
                updated_at=time.time(),
                completed_stages=[],
                pending_stages=["text_extraction", "image_extraction", "structure_detection"]
            )
            self.sessions[session_id] = session
            
            # Extract PDF content
            pdf_data = request.pdf_data if request.pdf_data else None
            file_path = request.file_path if request.file_path else None
            
            if not pdf_data and not file_path:
                raise ValueError("Either pdf_data or file_path must be provided")
            
            # Update progress
            self._update_session(session_id, progress=0.2, current_stage="loading_pdf")
            
            # Extract text
            if request.options.extract_text:
                text_result = await self.pdf_extractor.extract_text(
                    pdf_data=pdf_data,
                    file_path=file_path
                )
                self._update_session(session_id, progress=0.4, current_stage="text_extraction")
            
            # Extract images
            if request.options.extract_images:
                image_result = await self.pdf_extractor.extract_images(
                    pdf_data=pdf_data,
                    file_path=file_path,
                    dpi=request.options.dpi or 150
                )
                self._update_session(session_id, progress=0.6, current_stage="image_extraction")
            
            # Detect floor plans
            if request.options.detect_floor_plans:
                floor_plans = await self.pdf_extractor.detect_floor_plans(
                    images=image_result.get('images', [])
                )
                self._update_session(session_id, progress=0.8, current_stage="floor_plan_detection")
            
            # Calculate confidence
            confidence = self.confidence_scorer.score_pdf_extraction(
                text_quality=text_result.get('quality', 0),
                image_count=len(image_result.get('images', [])),
                floor_plan_count=len(floor_plans) if request.options.detect_floor_plans else 0
            )
            
            # Build response
            response = self._build_pdf_response(
                session_id=session_id,
                text_result=text_result if request.options.extract_text else None,
                image_result=image_result if request.options.extract_images else None,
                floor_plans=floor_plans if request.options.detect_floor_plans else None,
                confidence=confidence
            )
            
            # Update session
            self._update_session(
                session_id, 
                progress=1.0, 
                status="completed",
                result=response
            )
            
            # Update metrics
            self.metrics['pdf_extractions'] += 1
            
            logger.info(f"PDF extraction completed for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._update_session(session_id, status="error", error=str(e))
            self.metrics['error_count'] += 1
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def DetectWalls(self, request, context):
        """
        Detect walls, doors, windows from floor plan images.
        
        Args:
            request: WallDetectionRequest
            context: gRPC context
            
        Returns:
            WallDetectionResponse
        """
        session_id = self._generate_session_id()
        logger.info(f"Starting wall detection for session {session_id}")
        
        try:
            # Create session
            session = ProcessingSession(
                session_id=session_id,
                status="processing",
                progress=0.0,
                current_stage="wall_detection",
                started_at=time.time(),
                updated_at=time.time(),
                completed_stages=[],
                pending_stages=["preprocessing", "wall_detection", "room_detection"]
            )
            self.sessions[session_id] = session
            
            # Preprocess image
            self._update_session(session_id, progress=0.2, current_stage="preprocessing")
            processed_image = await self.wall_detector.preprocess_image(
                image_data=request.image_data,
                format=request.image_format
            )
            
            # Detect walls
            self._update_session(session_id, progress=0.4, current_stage="detecting_walls")
            walls = await self.wall_detector.detect_walls(
                image=processed_image,
                min_thickness=request.options.min_wall_thickness,
                max_thickness=request.options.max_wall_thickness
            )
            
            # Detect doors
            doors = []
            if request.options.detect_doors:
                self._update_session(session_id, progress=0.5, current_stage="detecting_doors")
                doors = await self.wall_detector.detect_doors(
                    image=processed_image,
                    walls=walls
                )
            
            # Detect windows
            windows = []
            if request.options.detect_windows:
                self._update_session(session_id, progress=0.6, current_stage="detecting_windows")
                windows = await self.wall_detector.detect_windows(
                    image=processed_image,
                    walls=walls
                )
            
            # Detect columns
            columns = []
            if request.options.detect_columns:
                self._update_session(session_id, progress=0.7, current_stage="detecting_columns")
                columns = await self.wall_detector.detect_columns(image=processed_image)
            
            # Detect rooms
            self._update_session(session_id, progress=0.8, current_stage="detecting_rooms")
            rooms = await self.wall_detector.detect_rooms(
                walls=walls,
                doors=doors
            )
            
            # Calculate confidence
            confidence = self.confidence_scorer.score_wall_detection(
                wall_count=len(walls),
                room_count=len(rooms),
                door_count=len(doors),
                window_count=len(windows)
            )
            
            # Build response
            response = self._build_wall_response(
                walls=walls,
                doors=doors,
                windows=windows,
                columns=columns,
                rooms=rooms,
                confidence=confidence
            )
            
            # Update session
            self._update_session(
                session_id,
                progress=1.0,
                status="completed",
                result=response
            )
            
            # Update metrics
            self.metrics['wall_detections'] += 1
            
            logger.info(f"Wall detection completed for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Wall detection failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._update_session(session_id, status="error", error=str(e))
            self.metrics['error_count'] += 1
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def ExtractMeasurements(self, request, context):
        """
        Extract measurements and dimensions from technical drawings.
        
        Args:
            request: MeasurementRequest
            context: gRPC context
            
        Returns:
            MeasurementResponse
        """
        session_id = self._generate_session_id()
        logger.info(f"Starting measurement extraction for session {session_id}")
        
        try:
            # Create session
            session = ProcessingSession(
                session_id=session_id,
                status="processing",
                progress=0.0,
                current_stage="measurement_extraction",
                started_at=time.time(),
                updated_at=time.time()
            )
            self.sessions[session_id] = session
            
            # Extract dimensions
            dimensions = []
            if request.options.extract_dimensions:
                self._update_session(session_id, progress=0.3, current_stage="extracting_dimensions")
                dimensions = await self.measurement_extractor.extract_dimensions(
                    image_data=request.image_data,
                    walls=request.walls
                )
            
            # Extract annotations
            annotations = []
            if request.options.extract_annotations:
                self._update_session(session_id, progress=0.6, current_stage="extracting_annotations")
                annotations = await self.measurement_extractor.extract_annotations(
                    image_data=request.image_data
                )
            
            # Extract scale
            scale = None
            if request.options.extract_scale:
                self._update_session(session_id, progress=0.8, current_stage="detecting_scale")
                scale = await self.measurement_extractor.detect_scale(
                    image_data=request.image_data,
                    dimensions=dimensions
                )
            
            # Calculate confidence
            confidence = self.confidence_scorer.score_measurement_extraction(
                dimension_count=len(dimensions),
                annotation_count=len(annotations),
                scale_detected=scale is not None
            )
            
            # Build response
            response = self._build_measurement_response(
                dimensions=dimensions,
                annotations=annotations,
                scale=scale,
                confidence=confidence
            )
            
            # Update session
            self._update_session(
                session_id,
                progress=1.0,
                status="completed",
                result=response
            )
            
            logger.info(f"Measurement extraction completed for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Measurement extraction failed: {str(e)}")
            self._update_session(session_id, status="error", error=str(e))
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def Generate3DBIM(self, request, context):
        """
        Generate 3D BIM model from 2D floor plans.
        
        Args:
            request: BIMGenerationRequest
            context: gRPC context
            
        Returns:
            BIMGenerationResponse
        """
        session_id = self._generate_session_id()
        logger.info(f"Starting BIM generation for session {session_id}")
        
        try:
            # Create session
            session = ProcessingSession(
                session_id=session_id,
                status="processing",
                progress=0.0,
                current_stage="bim_generation",
                started_at=time.time(),
                updated_at=time.time(),
                pending_stages=["extrusion", "element_creation", "space_generation", "ifc_export"]
            )
            self.sessions[session_id] = session
            
            # Generate 3D walls
            self._update_session(session_id, progress=0.2, current_stage="extruding_walls")
            wall_elements = await self.bim_generator.extrude_walls(
                walls=request.walls,
                height=request.options.default_wall_height
            )
            
            # Generate doors and windows
            self._update_session(session_id, progress=0.4, current_stage="creating_openings")
            door_elements = await self.bim_generator.create_doors(
                doors=request.doors,
                wall_elements=wall_elements
            )
            window_elements = await self.bim_generator.create_windows(
                windows=request.windows,
                wall_elements=wall_elements
            )
            
            # Generate spaces
            self._update_session(session_id, progress=0.6, current_stage="generating_spaces")
            spaces = await self.bim_generator.generate_spaces(
                rooms=request.rooms,
                height=request.options.default_floor_height
            )
            
            # Generate ceiling if requested
            ceiling_elements = []
            if request.options.generate_ceiling:
                self._update_session(session_id, progress=0.7, current_stage="generating_ceiling")
                ceiling_elements = await self.bim_generator.generate_ceiling(spaces=spaces)
            
            # Generate roof if requested
            roof_elements = []
            if request.options.generate_roof:
                self._update_session(session_id, progress=0.8, current_stage="generating_roof")
                roof_elements = await self.bim_generator.generate_roof(
                    floor_plan=request.floor_plan
                )
            
            # Export to IFC
            self._update_session(session_id, progress=0.9, current_stage="exporting_ifc")
            ifc_data = await self.bim_generator.export_ifc(
                walls=wall_elements,
                doors=door_elements,
                windows=window_elements,
                spaces=spaces,
                ceiling=ceiling_elements,
                roof=roof_elements
            )
            
            # Generate glTF for visualization
            gltf_data = await self.bim_generator.export_gltf(
                walls=wall_elements,
                doors=door_elements,
                windows=window_elements
            )
            
            # Calculate confidence
            confidence = self.confidence_scorer.score_bim_generation(
                element_count=len(wall_elements) + len(door_elements) + len(window_elements),
                space_count=len(spaces),
                has_ceiling=len(ceiling_elements) > 0,
                has_roof=len(roof_elements) > 0
            )
            
            # Build response
            response = self._build_bim_response(
                ifc_data=ifc_data,
                gltf_data=gltf_data,
                elements=wall_elements + door_elements + window_elements,
                spaces=spaces,
                confidence=confidence
            )
            
            # Update session
            self._update_session(
                session_id,
                progress=1.0,
                status="completed",
                result=response
            )
            
            # Update metrics
            self.metrics['bim_generations'] += 1
            
            logger.info(f"BIM generation completed for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"BIM generation failed: {str(e)}")
            logger.error(traceback.format_exc())
            self._update_session(session_id, status="error", error=str(e))
            self.metrics['error_count'] += 1
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def ProcessLargeFile(self, request_iterator, context):
        """
        Stream processing for large files.
        
        Args:
            request_iterator: Stream of FileChunk
            context: gRPC context
            
        Yields:
            ProcessingStatus updates
        """
        session_id = None
        chunks = []
        
        try:
            # Receive chunks
            async for chunk in request_iterator:
                if not session_id:
                    session_id = chunk.session_id
                    logger.info(f"Starting streamed processing for session {session_id}")
                    
                    # Create session
                    session = ProcessingSession(
                        session_id=session_id,
                        status="receiving",
                        progress=0.0,
                        current_stage="receiving_data",
                        started_at=time.time(),
                        updated_at=time.time()
                    )
                    self.sessions[session_id] = session
                
                chunks.append(chunk.data)
                progress = chunk.chunk_index / chunk.total_chunks * 0.5
                self._update_session(session_id, progress=progress)
                
                # Send progress update
                yield self._create_status_update(session_id)
                
                if chunk.is_last:
                    break
            
            # Process complete file
            self._update_session(session_id, progress=0.5, current_stage="processing")
            complete_data = b''.join(chunks)
            
            # Determine file type and process accordingly
            result = await self._process_complete_file(complete_data, session_id)
            
            # Send final result
            self._update_session(
                session_id,
                progress=1.0,
                status="completed",
                result=result
            )
            yield self._create_status_update(session_id, result=result)
            
        except Exception as e:
            logger.error(f"Stream processing failed: {str(e)}")
            if session_id:
                self._update_session(session_id, status="error", error=str(e))
                yield self._create_status_update(session_id)
            context.abort(grpc.StatusCode.INTERNAL, str(e))
    
    async def GetStatus(self, request, context):
        """
        Get processing status for a session.
        
        Args:
            request: StatusRequest
            context: gRPC context
            
        Returns:
            StatusResponse
        """
        session = self.sessions.get(request.session_id)
        if not session:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Session {request.session_id} not found"
            )
        
        return self._build_status_response(session)
    
    # Helper methods
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _update_session(self, session_id: str, **kwargs):
        """Update session state."""
        session = self.sessions.get(session_id)
        if session:
            for key, value in kwargs.items():
                setattr(session, key, value)
            session.updated_at = time.time()
    
    def _create_status_update(self, session_id: str, result=None):
        """Create ProcessingStatus message."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # This would be converted to proto message
        return {
            'session_id': session_id,
            'status': session.status,
            'progress': session.progress,
            'current_stage': session.current_stage,
            'message': f"Processing stage: {session.current_stage}",
            'result': result
        }
    
    def _build_pdf_response(self, **kwargs):
        """Build PDFExtractionResponse."""
        # This would create the actual proto message
        return kwargs
    
    def _build_wall_response(self, **kwargs):
        """Build WallDetectionResponse."""
        # This would create the actual proto message
        return kwargs
    
    def _build_measurement_response(self, **kwargs):
        """Build MeasurementResponse."""
        # This would create the actual proto message
        return kwargs
    
    def _build_bim_response(self, **kwargs):
        """Build BIMGenerationResponse."""
        # This would create the actual proto message
        return kwargs
    
    def _build_status_response(self, session: ProcessingSession):
        """Build StatusResponse."""
        # This would create the actual proto message
        return {
            'session_id': session.session_id,
            'status': session.status,
            'progress': session.progress,
            'current_stage': session.current_stage,
            'started_at': int(session.started_at),
            'updated_at': int(session.updated_at),
            'completed_stages': session.completed_stages or [],
            'pending_stages': session.pending_stages or []
        }
    
    async def _process_complete_file(self, data: bytes, session_id: str):
        """Process complete file data."""
        # Detect file type and route to appropriate processor
        # This is simplified - actual implementation would detect type
        if data.startswith(b'%PDF'):
            return await self._process_pdf_data(data, session_id)
        else:
            return await self._process_image_data(data, session_id)
    
    async def _process_pdf_data(self, data: bytes, session_id: str):
        """Process PDF data."""
        # Simplified processing
        return {'type': 'pdf', 'pages': 1}
    
    async def _process_image_data(self, data: bytes, session_id: str):
        """Process image data."""
        # Simplified processing
        return {'type': 'image', 'format': 'png'}


async def serve():
    """Start the gRPC server."""
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
            ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
        ]
    )
    
    # Add servicer to server
    servicer = IngestionServicer()
    # ingestion_pb2_grpc.add_IngestionServiceServicer_to_server(servicer, server)
    
    # Listen on port
    port = '50051'
    server.add_insecure_port(f'[::]:{port}')
    
    logger.info(f"Starting gRPC server on port {port}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server")
        await server.stop(grace_period=10)


if __name__ == '__main__':
    asyncio.run(serve())