"""
Distributed Processing Service

This module provides distributed processing capabilities for complex operations
with linear scaling, fault tolerance, and performance optimization.
"""

import logging
import time
import threading
import queue
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
import json
import pickle
from pathlib import Path
import uuid

from utils.logger import get_logger

logger = get_logger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStrategy(Enum):
    """Processing strategies"""
    MAPREDUCE = "mapreduce"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"
    STREAM = "stream"
    BATCH = "batch"


@dataclass
class ProcessingTask:
    """Processing task definition"""
    task_id: str
    function: Callable
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    strategy: ProcessingStrategy = ProcessingStrategy.PARALLEL
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """Worker information"""
    worker_id: str
    status: str = "idle"
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_processing_time: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)


@dataclass
class ProcessingMetrics:
    """Processing performance metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    active_workers: int = 0
    queue_size: int = 0
    throughput_tasks_per_second: float = 0.0


class TaskQueue:
    """Priority-based task queue"""
    
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.task_registry: Dict[str, ProcessingTask] = {}
        self.lock = threading.RLock()
    
    def add_task(self, task: ProcessingTask):
        """Add task to queue"""
        with self.lock:
            priority = task.priority.value
            self.queue.put((priority, task.task_id))
            self.task_registry[task.task_id] = task
    
    def get_next_task(self) -> Optional[ProcessingTask]:
        """Get next task from queue"""
        with self.lock:
            if self.queue.empty():
                return None
            
            try:
                _, task_id = self.queue.get_nowait()
                return self.task_registry.get(task_id)
            except queue.Empty:
                return None
    
    def update_task(self, task: ProcessingTask):
        """Update task in registry"""
        with self.lock:
            self.task_registry[task.task_id] = task
    
    def remove_task(self, task_id: str):
        """Remove task from registry"""
        with self.lock:
            self.task_registry.pop(task_id, None)
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self.lock:
            return len(self.task_registry)


class Worker:
    """Processing worker"""
    
    def __init__(self, worker_id: str, task_queue: TaskQueue, result_store: Dict[str, Any]):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.result_store = result_store
        self.info = WorkerInfo(worker_id=worker_id)
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop)
        self.thread.daemon = True
        self.logger = get_logger(__name__)
    
    def start(self):
        """Start worker thread"""
        self.thread.start()
        self.logger.info(f"Worker {self.worker_id} started")
    
    def stop(self):
        """Stop worker"""
        self.running = False
        self.thread.join()
        self.logger.info(f"Worker {self.worker_id} stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                task = self.task_queue.get_next_task()
                if task:
                    self._process_task(task)
                else:
                    time.sleep(0.1)  # Wait for tasks
            except Exception as e:
                self.logger.error(f"Worker {self.worker_id} error: {e}")
                time.sleep(1)  # Wait before retrying
    
    def _process_task(self, task: ProcessingTask):
        """Process a single task"""
        start_time = time.time()
        
        try:
            self.info.status = "running"
            self.info.current_task = task.task_id
            task.status = TaskStatus.RUNNING
            task.started_at = start_time
            
            self.logger.debug(f"Worker {self.worker_id} processing task {task.task_id}")
            
            # Execute task
            result = task.function(*task.args, **task.kwargs)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            
            # Store result
            self.result_store[task.task_id] = {
                'status': 'completed',
                'result': result,
                'processing_time': task.completed_at - start_time
            }
            
            # Update worker info
            self.info.tasks_completed += 1
            self.info.total_processing_time += task.completed_at - start_time
            self.info.status = "idle"
            self.info.current_task = None
            self.info.last_heartbeat = time.time()
            
            self.logger.debug(f"Worker {self.worker_id} completed task {task.task_id}")
            
        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            
            self.info.tasks_failed += 1
            self.info.status = "idle"
            self.info.current_task = None
            
            self.logger.error(f"Worker {self.worker_id} failed task {task.task_id}: {e}")
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.completed_at = None
                task.error = None
                self.task_queue.add_task(task)
                self.logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
        
        finally:
            self.task_queue.update_task(task)


class DistributedProcessingService:
    """
    Distributed processing service with linear scaling.
    
    Features:
    - Multi-worker processing
    - Priority-based task queuing
    - Fault tolerance and retry logic
    - Performance monitoring
    - Load balancing
    - Multiple processing strategies
    """
    
    def __init__(self, max_workers: int = None, enable_process_pool: bool = False):
        self.max_workers = max_workers or min(32, multiprocessing.cpu_count() + 4)
        self.enable_process_pool = enable_process_pool
        
        # Core components
        self.task_queue = TaskQueue()
        self.result_store: Dict[str, Any] = {}
        self.workers: List[Worker] = []
        self.worker_info: Dict[str, WorkerInfo] = {}
        
        # Thread and process pools
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers) if enable_process_pool else None
        
        # Performance tracking
        self.metrics = ProcessingMetrics()
        self.start_time = time.time()
        
        # Control
        self.running = False
        self.lock = threading.RLock()
        
        self.logger = get_logger(__name__)
    
    def start(self):
        """Start the distributed processing service"""
        with self.lock:
            if self.running:
                return
            
            self.running = True
            
            # Start workers
            for i in range(self.max_workers):
                worker_id = f"worker_{i}"
                worker = Worker(worker_id, self.task_queue, self.result_store)
                worker.start()
                self.workers.append(worker)
                self.worker_info[worker_id] = worker.info
            
            self.logger.info(f"Distributed processing service started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the distributed processing service"""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Stop workers
            for worker in self.workers:
                worker.stop()
            
            # Shutdown pools
            self.thread_pool.shutdown(wait=True)
            if self.process_pool:
                self.process_pool.shutdown(wait=True)
            
            self.logger.info("Distributed processing service stopped")
    
    def submit_task(self, function: Callable, *args, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   strategy: ProcessingStrategy = ProcessingStrategy.PARALLEL,
                   timeout_seconds: Optional[int] = None,
                   max_retries: int = 3,
                   **kwargs) -> str:
        """
        Submit a task for processing.
        
        Args:
            function: Function to execute
            *args: Function arguments
            priority: Task priority
            strategy: Processing strategy
            timeout_seconds: Task timeout
            max_retries: Maximum retry attempts
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task = ProcessingTask(
            task_id=task_id,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            strategy=strategy,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries
        )
        
        self.task_queue.add_task(task)
        self.metrics.total_tasks += 1
        
        self.logger.debug(f"Submitted task {task_id} with priority {priority.value}")
        return task_id
    
    def get_task_result(self, task_id: str, timeout_seconds: Optional[int] = None) -> Any:
        """
        Get task result.
        
        Args:
            task_id: Task ID
            timeout_seconds: Wait timeout
            
        Returns:
            Task result
        """
        start_time = time.time()
        
        while True:
            if task_id in self.result_store:
                result_data = self.result_store[task_id]
                if result_data['status'] == 'completed':
                    return result_data['result']
                elif result_data['status'] == 'failed':
                    raise Exception(f"Task {task_id} failed: {result_data.get('error', 'Unknown error')}")
            
            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                raise TimeoutError(f"Task {task_id} timed out")
            
            time.sleep(0.1)
    
    def distribute_task(self, task: ProcessingTask, priority: int = 1) -> str:
        """
        Distribute task to available workers.
        
        Args:
            task: Processing task
            priority: Task priority
            
        Returns:
            Task ID
        """
        return self.submit_task(
            task.function,
            *task.args,
            priority=task.priority,
            strategy=task.strategy,
            timeout_seconds=task.timeout_seconds,
            max_retries=task.max_retries,
            **task.kwargs
        )
    
    def scale_workers(self, load_metrics: Dict[str, Any]):
        """
        Scale workers based on system load.
        
        Args:
            load_metrics: Current load metrics
        """
        current_workers = len(self.workers)
        queue_size = self.task_queue.get_queue_size()
        avg_processing_time = self.metrics.average_processing_time
        
        # Simple scaling logic
        target_workers = current_workers
        
        if queue_size > current_workers * 2:
            # High queue, increase workers
            target_workers = min(current_workers + 2, self.max_workers * 2)
        elif queue_size < current_workers // 2 and current_workers > 2:
            # Low queue, decrease workers
            target_workers = max(current_workers - 1, 2)
        
        if target_workers != current_workers:
            self.logger.info(f"Scaling workers from {current_workers} to {target_workers}")
            
            if target_workers > current_workers:
                # Add workers
                for i in range(target_workers - current_workers):
                    worker_id = f"worker_{len(self.workers)}"
                    worker = Worker(worker_id, self.task_queue, self.result_store)
                    worker.start()
                    self.workers.append(worker)
                    self.worker_info[worker_id] = worker.info
            else:
                # Remove workers (graceful shutdown)
                workers_to_remove = current_workers - target_workers
                for i in range(workers_to_remove):
                    if self.workers:
                        worker = self.workers.pop()
                        worker.stop()
                        self.worker_info.pop(worker.worker_id, None)
    
    def handle_complex_operations(self, operation: Callable, 
                                data: List[Any],
                                strategy: ProcessingStrategy = ProcessingStrategy.MAPREDUCE,
                                chunk_size: int = 100) -> Any:
        """
        Handle complex operations with distributed processing.
        
        Args:
            operation: Operation to perform
            data: Input data
            strategy: Processing strategy
            chunk_size: Chunk size for data splitting
            
        Returns:
            Operation result
        """
        if strategy == ProcessingStrategy.MAPREDUCE:
            return self._mapreduce_operation(operation, data, chunk_size)
        elif strategy == ProcessingStrategy.PIPELINE:
            return self._pipeline_operation(operation, data)
        elif strategy == ProcessingStrategy.PARALLEL:
            return self._parallel_operation(operation, data)
        elif strategy == ProcessingStrategy.STREAM:
            return self._stream_operation(operation, data)
        elif strategy == ProcessingStrategy.BATCH:
            return self._batch_operation(operation, data, chunk_size)
        else:
            raise ValueError(f"Unknown processing strategy: {strategy}")
    
    def _mapreduce_operation(self, operation: Callable, data: List[Any], 
                            chunk_size: int) -> Any:
        """MapReduce operation"""
        # Split data into chunks
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # Map phase
        map_tasks = []
        for i, chunk in enumerate(chunks):
            task_id = self.submit_task(
                operation,
                chunk,
                priority=TaskPriority.HIGH,
                strategy=ProcessingStrategy.PARALLEL
            )
            map_tasks.append(task_id)
        
        # Collect map results
        map_results = []
        for task_id in map_tasks:
            result = self.get_task_result(task_id)
            map_results.append(result)
        
        # Reduce phase
        if len(map_results) == 1:
            return map_results[0]
        else:
            # Combine results
            combined_result = map_results[0]
            for result in map_results[1:]:
                if isinstance(combined_result, list):
                    combined_result.extend(result)
                elif isinstance(combined_result, dict):
                    combined_result.update(result)
                else:
                    # Assume numeric addition
                    combined_result += result
            
            return combined_result
    
    def _pipeline_operation(self, operation: Callable, data: List[Any]) -> Any:
        """Pipeline operation"""
        result = data
        
        # Process through pipeline stages
        for stage in range(3):  # Example: 3 pipeline stages
            task_id = self.submit_task(
                operation,
                result,
                priority=TaskPriority.NORMAL,
                strategy=ProcessingStrategy.PARALLEL
            )
            result = self.get_task_result(task_id)
        
        return result
    
    def _parallel_operation(self, operation: Callable, data: List[Any]) -> List[Any]:
        """Parallel operation"""
        # Submit all tasks in parallel
        task_ids = []
        for item in data:
            task_id = self.submit_task(
                operation,
                item,
                priority=TaskPriority.NORMAL,
                strategy=ProcessingStrategy.PARALLEL
            )
            task_ids.append(task_id)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = self.get_task_result(task_id)
            results.append(result)
        
        return results
    
    def _stream_operation(self, operation: Callable, data: List[Any]) -> List[Any]:
        """Stream operation"""
        results = []
        
        # Process data in streaming fashion
        for item in data:
            task_id = self.submit_task(
                operation,
                item,
                priority=TaskPriority.HIGH,
                strategy=ProcessingStrategy.PARALLEL
            )
            result = self.get_task_result(task_id)
            results.append(result)
        
        return results
    
    def _batch_operation(self, operation: Callable, data: List[Any], 
                        chunk_size: int) -> List[Any]:
        """Batch operation"""
        # Process data in batches
        batches = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        results = []
        for batch in batches:
            task_id = self.submit_task(
                operation,
                batch,
                priority=TaskPriority.NORMAL,
                strategy=ProcessingStrategy.PARALLEL
            )
            batch_result = self.get_task_result(task_id)
            results.extend(batch_result)
        
        return results
    
    def get_worker_status(self) -> Dict[str, WorkerInfo]:
        """Get status of all workers"""
        return self.worker_info.copy()
    
    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get processing performance metrics"""
        # Update metrics
        completed_tasks = sum(worker.tasks_completed for worker in self.workers)
        failed_tasks = sum(worker.tasks_failed for worker in self.workers)
        total_processing_time = sum(worker.total_processing_time for worker in self.workers)
        
        self.metrics.completed_tasks = completed_tasks
        self.metrics.failed_tasks = failed_tasks
        self.metrics.total_processing_time = total_processing_time
        self.metrics.active_workers = len([w for w in self.workers if w.info.status == "running"])
        self.metrics.queue_size = self.task_queue.get_queue_size()
        
        # Calculate averages
        if completed_tasks > 0:
            self.metrics.average_processing_time = total_processing_time / completed_tasks
        
        # Calculate throughput
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            self.metrics.throughput_tasks_per_second = completed_tasks / elapsed_time
        
        return self.metrics
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific task"""
        if task_id in self.result_store:
            return self.result_store[task_id]
        
        # Check if task is in queue
        for task in self.task_queue.task_registry.values():
            if task.task_id == task_id:
                return {
                    'status': task.status.value,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'retry_count': task.retry_count,
                    'error': task.error
                }
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        # Remove from queue
        self.task_queue.remove_task(task_id)
        
        # Remove from result store if present
        if task_id in self.result_store:
            del self.result_store[task_id]
        
        return True
    
    def clear_completed_tasks(self):
        """Clear completed tasks from result store"""
        completed_tasks = [task_id for task_id, result in self.result_store.items() 
                          if result['status'] == 'completed']
        
        for task_id in completed_tasks:
            del self.result_store[task_id]
        
        self.logger.info(f"Cleared {len(completed_tasks)} completed tasks")
    
    def get_system_load(self) -> Dict[str, Any]:
        """Get current system load information"""
        return {
            'active_workers': len([w for w in self.workers if w.info.status == "running"]),
            'idle_workers': len([w for w in self.workers if w.info.status == "idle"]),
            'queue_size': self.task_queue.get_queue_size(),
            'total_workers': len(self.workers),
            'max_workers': self.max_workers,
            'metrics': self.get_processing_metrics().__dict__
        } 