"""
Python client for high-performance Go ArxObject service.

This provides a Python interface to the Go-based ArxObject engine,
allowing existing Python services to leverage the performance benefits.
"""

import grpc
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Import generated protobuf modules
from arxos.proto import arxobject_pb2 as pb
from arxos.proto import arxobject_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)


@dataclass
class ArxObjectGeometry:
    """Python representation of ArxObject geometry"""
    x: float
    y: float  
    z: float
    length: float = 1.0
    width: float = 1.0
    height: float = 1.0
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    shape: str = "box"
    
    def to_proto(self) -> pb.Geometry:
        """Convert to protobuf geometry"""
        return pb.Geometry(
            x=int(self.x * 1000),  # Convert to mm
            y=int(self.y * 1000),
            z=int(self.z * 1000),
            length=int(self.length * 1000),
            width=int(self.width * 1000),
            height=int(self.height * 1000),
            rotation_x=int(self.rotation_x * 10),  # Decidegrees
            rotation_y=int(self.rotation_y * 10),
            rotation_z=int(self.rotation_z * 10),
            shape=self.shape
        )
    
    @classmethod
    def from_proto(cls, proto: pb.Geometry) -> 'ArxObjectGeometry':
        """Create from protobuf geometry"""
        return cls(
            x=proto.x / 1000.0,  # Convert from mm
            y=proto.y / 1000.0,
            z=proto.z / 1000.0,
            length=proto.length / 1000.0,
            width=proto.width / 1000.0,
            height=proto.height / 1000.0,
            rotation_x=proto.rotation_x / 10.0,
            rotation_y=proto.rotation_y / 10.0,
            rotation_z=proto.rotation_z / 10.0,
            shape=proto.shape
        )


@dataclass
class ArxObject:
    """Python representation of ArxObject"""
    id: int
    type: str
    geometry: ArxObjectGeometry
    precision: str = "standard"
    priority: int = 5
    properties: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    active: bool = True
    version: int = 1
    
    @classmethod
    def from_proto(cls, proto: pb.ArxObject) -> 'ArxObject':
        """Create from protobuf ArxObject"""
        return cls(
            id=proto.id,
            type=pb.ObjectType.Name(proto.type),
            geometry=ArxObjectGeometry.from_proto(proto.geometry),
            precision=pb.PrecisionLevel.Name(proto.precision),
            priority=proto.priority,
            properties=dict(proto.properties.values) if proto.properties else {},
            metadata={
                'name': proto.metadata.name,
                'description': proto.metadata.description,
                'tags': list(proto.metadata.tags),
                'custom': dict(proto.metadata.custom)
            } if proto.metadata else {},
            active=proto.active,
            version=proto.version
        )


class ArxObjectClient:
    """
    High-performance Python client for ArxObject service.
    
    This client provides async and sync interfaces to the Go-based
    ArxObject engine for maximum performance.
    """
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        Initialize ArxObject client.
        
        Args:
            host: gRPC server host
            port: gRPC server port
        """
        self.address = f"{host}:{port}"
        self.channel = None
        self.stub = None
        self._connected = False
        
        # Performance metrics
        self.metrics = {
            'calls_made': 0,
            'total_latency': 0,
            'errors': 0
        }
    
    async def connect(self):
        """Connect to ArxObject service"""
        if self._connected:
            return
        
        self.channel = grpc.aio.insecure_channel(
            self.address,
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', True),
            ]
        )
        
        self.stub = pb_grpc.ArxObjectServiceStub(self.channel)
        self._connected = True
        logger.info(f"Connected to ArxObject service at {self.address}")
    
    async def close(self):
        """Close connection to ArxObject service"""
        if self.channel:
            await self.channel.close()
        self._connected = False
    
    async def create_object(
        self,
        object_type: str,
        geometry: ArxObjectGeometry,
        properties: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ArxObject:
        """
        Create a new ArxObject.
        
        Args:
            object_type: Type of object (e.g., 'ELECTRICAL_OUTLET')
            geometry: Object geometry
            properties: Object properties
            metadata: Object metadata
            
        Returns:
            Created ArxObject
        """
        if not self._connected:
            await self.connect()
        
        # Convert type string to enum
        type_enum = pb.ObjectType.Value(object_type)
        
        # Build request
        request = pb.CreateObjectRequest(
            type=type_enum,
            geometry=geometry.to_proto()
        )
        
        if properties:
            request.properties.CopyFrom(pb.Properties(
                values={k: str(v) for k, v in properties.items()}
            ))
        
        if metadata:
            request.metadata.CopyFrom(pb.Metadata(
                name=metadata.get('name', ''),
                description=metadata.get('description', ''),
                tags=metadata.get('tags', []),
                custom={k: str(v) for k, v in metadata.get('custom', {}).items()}
            ))
        
        # Make gRPC call
        try:
            response = await self.stub.CreateObject(request)
            self.metrics['calls_made'] += 1
            return ArxObject.from_proto(response.object)
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to create object: {e}")
            raise
    
    async def get_object(
        self,
        object_id: int,
        include_relationships: bool = False
    ) -> Optional[ArxObject]:
        """
        Get an ArxObject by ID.
        
        Args:
            object_id: Object ID
            include_relationships: Whether to include relationships
            
        Returns:
            ArxObject or None if not found
        """
        if not self._connected:
            await self.connect()
        
        request = pb.GetObjectRequest(
            id=object_id,
            include_relationships=include_relationships
        )
        
        try:
            response = await self.stub.GetObject(request)
            self.metrics['calls_made'] += 1
            return ArxObject.from_proto(response.object)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            self.metrics['errors'] += 1
            logger.error(f"Failed to get object: {e}")
            raise
    
    async def update_object(
        self,
        object_id: int,
        geometry: Optional[ArxObjectGeometry] = None,
        properties: Optional[Dict[str, Any]] = None,
        validate: bool = True
    ) -> ArxObject:
        """
        Update an ArxObject.
        
        Args:
            object_id: Object ID
            geometry: New geometry (optional)
            properties: Properties to update (optional)
            validate: Whether to validate constraints
            
        Returns:
            Updated ArxObject
        """
        if not self._connected:
            await self.connect()
        
        request = pb.UpdateObjectRequest(
            id=object_id,
            validate_constraints=validate
        )
        
        if geometry:
            request.geometry.CopyFrom(geometry.to_proto())
        
        if properties:
            request.properties.CopyFrom(pb.Properties(
                values={k: str(v) for k, v in properties.items()}
            ))
        
        try:
            response = await self.stub.UpdateObject(request)
            self.metrics['calls_made'] += 1
            
            if response.errors:
                logger.warning(f"Validation errors: {response.errors}")
            
            return ArxObject.from_proto(response.object)
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to update object: {e}")
            raise
    
    async def delete_object(
        self,
        object_id: int,
        cascade: bool = False,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete an ArxObject.
        
        Args:
            object_id: Object ID
            cascade: Whether to cascade delete dependencies
            soft_delete: Whether to soft delete (mark inactive)
            
        Returns:
            True if deleted successfully
        """
        if not self._connected:
            await self.connect()
        
        request = pb.DeleteObjectRequest(
            id=object_id,
            cascade=cascade,
            soft_delete=soft_delete
        )
        
        try:
            response = await self.stub.DeleteObject(request)
            self.metrics['calls_made'] += 1
            return response.success
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to delete object: {e}")
            raise
    
    async def query_region(
        self,
        min_x: float, min_y: float, min_z: float,
        max_x: float, max_y: float, max_z: float,
        object_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[ArxObject]:
        """
        Query objects within a 3D region.
        
        Args:
            min_x, min_y, min_z: Minimum coordinates
            max_x, max_y, max_z: Maximum coordinates
            object_types: Optional filter by types
            limit: Maximum results
            
        Returns:
            List of ArxObjects in region
        """
        if not self._connected:
            await self.connect()
        
        request = pb.QueryRegionRequest(
            region=pb.BoundingBox(
                min=pb.Point3D(
                    x=int(min_x * 1000),
                    y=int(min_y * 1000),
                    z=int(min_z * 1000)
                ),
                max=pb.Point3D(
                    x=int(max_x * 1000),
                    y=int(max_y * 1000),
                    z=int(max_z * 1000)
                )
            ),
            limit=limit
        )
        
        if object_types:
            request.types.extend([
                pb.ObjectType.Value(t) for t in object_types
            ])
        
        try:
            response = await self.stub.QueryRegion(request)
            self.metrics['calls_made'] += 1
            return [ArxObject.from_proto(obj) for obj in response.objects]
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to query region: {e}")
            raise
    
    async def check_collisions(
        self,
        object_id: int,
        clearance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Check for spatial collisions.
        
        Args:
            object_id: Object ID
            clearance: Required clearance in meters
            
        Returns:
            List of collisions
        """
        if not self._connected:
            await self.connect()
        
        request = pb.CheckCollisionsRequest(
            object_id=object_id,
            clearance_mm=int(clearance * 1000)
        )
        
        try:
            response = await self.stub.CheckCollisions(request)
            self.metrics['calls_made'] += 1
            
            return [{
                'object_id': c.object_id,
                'object_type': pb.ObjectType.Name(c.object_type),
                'severity': c.severity,
                'description': c.description
            } for c in response.collisions]
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to check collisions: {e}")
            raise
    
    async def batch_create(
        self,
        objects: List[Dict[str, Any]],
        transaction: bool = True
    ) -> Tuple[List[ArxObject], List[str]]:
        """
        Create multiple objects efficiently.
        
        Args:
            objects: List of object specifications
            transaction: Whether to use transaction
            
        Returns:
            Tuple of (created objects, errors)
        """
        if not self._connected:
            await self.connect()
        
        # Build batch request
        create_requests = []
        for obj_spec in objects:
            req = pb.CreateObjectRequest(
                type=pb.ObjectType.Value(obj_spec['type']),
                geometry=ArxObjectGeometry(**obj_spec['geometry']).to_proto()
            )
            
            if 'properties' in obj_spec:
                req.properties.CopyFrom(pb.Properties(
                    values={k: str(v) for k, v in obj_spec['properties'].items()}
                ))
            
            create_requests.append(req)
        
        request = pb.BatchCreateObjectsRequest(
            objects=create_requests,
            transaction=transaction
        )
        
        try:
            response = await self.stub.BatchCreateObjects(request)
            self.metrics['calls_made'] += 1
            
            objects = [ArxObject.from_proto(obj) for obj in response.objects]
            errors = [e.message for e in response.errors]
            
            return objects, errors
        except grpc.RpcError as e:
            self.metrics['errors'] += 1
            logger.error(f"Failed to batch create: {e}")
            raise
    
    async def stream_changes(
        self,
        callback,
        object_types: Optional[List[str]] = None,
        region: Optional[Tuple[float, float, float, float, float, float]] = None
    ):
        """
        Stream real-time object changes.
        
        Args:
            callback: Async function to call for each change
            object_types: Optional filter by types
            region: Optional spatial region filter
        """
        if not self._connected:
            await self.connect()
        
        request = pb.StreamObjectChangesRequest()
        
        if object_types:
            request.types.extend([
                pb.ObjectType.Value(t) for t in object_types
            ])
        
        if region:
            request.region.CopyFrom(pb.BoundingBox(
                min=pb.Point3D(
                    x=int(region[0] * 1000),
                    y=int(region[1] * 1000),
                    z=int(region[2] * 1000)
                ),
                max=pb.Point3D(
                    x=int(region[3] * 1000),
                    y=int(region[4] * 1000),
                    z=int(region[5] * 1000)
                )
            ))
        
        try:
            stream = self.stub.StreamObjectChanges(request)
            async for event in stream:
                obj = ArxObject.from_proto(event.object)
                await callback(event.event_type, obj, event.timestamp)
        except grpc.RpcError as e:
            logger.error(f"Stream error: {e}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        return {
            'calls_made': self.metrics['calls_made'],
            'errors': self.metrics['errors'],
            'error_rate': self.metrics['errors'] / max(1, self.metrics['calls_made']),
            'avg_latency': self.metrics['total_latency'] / max(1, self.metrics['calls_made'])
        }


# Synchronous wrapper for compatibility
class ArxObjectClientSync:
    """Synchronous wrapper for ArxObject client"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.async_client = ArxObjectClient(host, port)
        self.loop = asyncio.new_event_loop()
    
    def __enter__(self):
        self.loop.run_until_complete(self.async_client.connect())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loop.run_until_complete(self.async_client.close())
        self.loop.close()
    
    def create_object(self, *args, **kwargs) -> ArxObject:
        return self.loop.run_until_complete(
            self.async_client.create_object(*args, **kwargs)
        )
    
    def get_object(self, *args, **kwargs) -> Optional[ArxObject]:
        return self.loop.run_until_complete(
            self.async_client.get_object(*args, **kwargs)
        )
    
    def update_object(self, *args, **kwargs) -> ArxObject:
        return self.loop.run_until_complete(
            self.async_client.update_object(*args, **kwargs)
        )
    
    def delete_object(self, *args, **kwargs) -> bool:
        return self.loop.run_until_complete(
            self.async_client.delete_object(*args, **kwargs)
        )
    
    def query_region(self, *args, **kwargs) -> List[ArxObject]:
        return self.loop.run_until_complete(
            self.async_client.query_region(*args, **kwargs)
        )
    
    def check_collisions(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return self.loop.run_until_complete(
            self.async_client.check_collisions(*args, **kwargs)
        )
    
    def batch_create(self, *args, **kwargs) -> Tuple[List[ArxObject], List[str]]:
        return self.loop.run_until_complete(
            self.async_client.batch_create(*args, **kwargs)
        )