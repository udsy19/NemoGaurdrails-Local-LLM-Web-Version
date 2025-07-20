"""
Distributed Processing System
Handles workload distribution, load balancing, and parallel processing
"""

import asyncio
import threading
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, Empty
import multiprocessing as mp
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkerType(Enum):
    THREAD = "thread"
    PROCESS = "process"
    ASYNC = "async"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Represents a distributed processing task"""
    id: str
    function_name: str
    args: tuple
    kwargs: dict
    priority: Priority = Priority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Worker:
    """Represents a worker in the distributed system"""
    id: str
    type: WorkerType
    status: str = "idle"
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DistributedConfig:
    """Configuration for distributed processing"""
    max_workers: int = mp.cpu_count()
    worker_type: WorkerType = WorkerType.THREAD
    queue_size: int = 1000
    task_timeout: float = 300.0  # 5 minutes
    heartbeat_interval: float = 30.0  # 30 seconds
    cleanup_interval: float = 60.0  # 1 minute
    retry_delay: float = 1.0
    enable_load_balancing: bool = True
    enable_auto_scaling: bool = True
    min_workers: int = 2
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    enable_metrics: bool = True

class DistributedProcessor:
    """
    Main distributed processing system
    Manages workers, tasks, and load balancing
    """
    
    def __init__(self, config: DistributedConfig = None):
        self.config = config or DistributedConfig()
        self.tasks: Dict[str, Task] = {}
        self.workers: Dict[str, Worker] = {}
        self.task_queue = Queue(maxsize=self.config.queue_size)
        self.result_queue = Queue()
        
        # Executors
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        
        # State management
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # Monitoring threads
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.cleanup_thread: Optional[threading.Thread] = None
        self.load_balancer_thread: Optional[threading.Thread] = None
        
        # Metrics
        self.metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "avg_processing_time": 0.0,
            "queue_size": 0,
            "active_workers": 0,
            "cpu_utilization": 0.0,
            "memory_utilization": 0.0,
            "throughput": 0.0,
            "error_rate": 0.0,
            "processing_times": [],
            "load_distribution": {}
        }
        
        # Function registry for distributed execution
        self.function_registry: Dict[str, Callable] = {}
        
        logger.info("Distributed Processor initialized")
    
    def register_function(self, name: str, func: Callable):
        """Register a function for distributed execution"""
        self.function_registry[name] = func
        logger.info(f"Registered function: {name}")
    
    async def start(self):
        """Start the distributed processing system"""
        if self.is_running:
            logger.warning("Distributed processor already running")
            return
        
        logger.info("Starting distributed processing system...")
        
        try:
            # Initialize executors
            if self.config.worker_type in [WorkerType.THREAD, WorkerType.ASYNC]:
                self.thread_executor = ThreadPoolExecutor(
                    max_workers=self.config.max_workers,
                    thread_name_prefix="DistributedWorker"
                )
            
            if self.config.worker_type == WorkerType.PROCESS:
                self.process_executor = ProcessPoolExecutor(
                    max_workers=self.config.max_workers
                )
            
            # Create initial workers
            await self._create_initial_workers()
            
            # Start monitoring threads
            self.is_running = True
            self.shutdown_event.clear()
            
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop, 
                daemon=True, 
                name="HeartbeatMonitor"
            )
            self.heartbeat_thread.start()
            
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop, 
                daemon=True, 
                name="CleanupManager"
            )
            self.cleanup_thread.start()
            
            if self.config.enable_load_balancing:
                self.load_balancer_thread = threading.Thread(
                    target=self._load_balancer_loop, 
                    daemon=True, 
                    name="LoadBalancer"
                )
                self.load_balancer_thread.start()
            
            # Start task processing
            asyncio.create_task(self._process_tasks())
            
            logger.info(f"Distributed processor started with {len(self.workers)} workers")
            
        except Exception as e:
            logger.error(f"Failed to start distributed processor: {e}")
            await self.shutdown()
            raise
    
    async def _create_initial_workers(self):
        """Create initial set of workers"""
        for i in range(self.config.min_workers):
            worker_id = f"worker_{i}_{uuid.uuid4().hex[:8]}"
            worker = Worker(
                id=worker_id,
                type=self.config.worker_type,
                metadata={"initial": True}
            )
            self.workers[worker_id] = worker
            logger.debug(f"Created worker: {worker_id}")
    
    async def submit_task(
        self, 
        function_name: str, 
        *args, 
        priority: Priority = Priority.NORMAL,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Submit a task for distributed processing"""
        
        if not self.is_running:
            raise RuntimeError("Distributed processor is not running")
        
        if function_name not in self.function_registry:
            raise ValueError(f"Function '{function_name}' not registered")
        
        task_id = f"task_{uuid.uuid4().hex}"
        task = Task(
            id=task_id,
            function_name=function_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout or self.config.task_timeout,
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        
        try:
            # Add to queue with priority
            self.task_queue.put((priority.value, time.time(), task), block=False)
            self.metrics["tasks_submitted"] += 1
            self.metrics["queue_size"] = self.task_queue.qsize()
            
            logger.info(f"Task submitted: {task_id} ({function_name})")
            return task_id
            
        except Exception as e:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].error = str(e)
            logger.error(f"Failed to submit task {task_id}: {e}")
            raise
    
    async def _process_tasks(self):
        """Main task processing loop"""
        while self.is_running:
            try:
                if self.task_queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                # Get task with priority
                try:
                    priority, submit_time, task = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Find available worker
                worker = await self._get_available_worker()
                if not worker:
                    # Put task back in queue
                    self.task_queue.put((priority, submit_time, task))
                    await asyncio.sleep(0.1)
                    continue
                
                # Process task
                await self._execute_task(task, worker)
                
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _get_available_worker(self) -> Optional[Worker]:
        """Get an available worker for task execution"""
        idle_workers = [w for w in self.workers.values() if w.status == "idle"]
        
        if not idle_workers:
            # Try to scale up if auto-scaling is enabled
            if self.config.enable_auto_scaling:
                await self._scale_workers()
                idle_workers = [w for w in self.workers.values() if w.status == "idle"]
        
        if idle_workers:
            # Load balancing: pick worker with least completed tasks
            return min(idle_workers, key=lambda w: w.tasks_completed)
        
        return None
    
    async def _execute_task(self, task: Task, worker: Worker):
        """Execute a task on a specific worker"""
        try:
            task.status = TaskStatus.PROCESSING
            task.started_at = time.time()
            task.worker_id = worker.id
            
            worker.status = "busy"
            worker.current_task = task.id
            worker.last_heartbeat = time.time()
            
            # Get the function to execute
            func = self.function_registry[task.function_name]
            
            # Execute based on worker type
            if worker.type == WorkerType.THREAD:
                future = self.thread_executor.submit(func, *task.args, **task.kwargs)
                result = await asyncio.get_event_loop().run_in_executor(None, future.result, task.timeout)
            
            elif worker.type == WorkerType.PROCESS:
                future = self.process_executor.submit(func, *task.args, **task.kwargs)
                result = await asyncio.get_event_loop().run_in_executor(None, future.result, task.timeout)
            
            elif worker.type == WorkerType.ASYNC:
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*task.args, **task.kwargs), timeout=task.timeout)
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_executor, func, *task.args, **task.kwargs
                    )
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = result
            
            worker.status = "idle"
            worker.current_task = None
            worker.tasks_completed += 1
            
            # Update metrics
            processing_time = task.completed_at - task.started_at
            self.metrics["tasks_completed"] += 1
            self.metrics["processing_times"].append(processing_time)
            self._update_metrics()
            
            logger.debug(f"Task {task.id} completed in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "Task timeout"
            task.completed_at = time.time()
            
            worker.status = "idle"
            worker.current_task = None
            worker.tasks_failed += 1
            
            self.metrics["tasks_failed"] += 1
            logger.warning(f"Task {task.id} timed out")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = time.time()
            
            worker.status = "idle"
            worker.current_task = None
            worker.tasks_failed += 1
            
            self.metrics["tasks_failed"] += 1
            logger.error(f"Task {task.id} failed: {e}")
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                task.worker_id = None
                
                # Re-queue task with delay
                await asyncio.sleep(self.config.retry_delay * task.retry_count)
                priority = task.priority.value
                self.task_queue.put((priority, time.time(), task))
                
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")
    
    async def _scale_workers(self):
        """Auto-scale workers based on queue size and load"""
        if not self.config.enable_auto_scaling:
            return
        
        queue_load = self.task_queue.qsize() / self.config.queue_size
        
        # Scale up if queue is getting full
        if queue_load > self.config.scale_up_threshold and len(self.workers) < self.config.max_workers:
            await self._add_worker()
            logger.info(f"Scaled up to {len(self.workers)} workers")
        
        # Scale down if queue is mostly empty
        elif queue_load < self.config.scale_down_threshold and len(self.workers) > self.config.min_workers:
            await self._remove_idle_worker()
            logger.info(f"Scaled down to {len(self.workers)} workers")
    
    async def _add_worker(self):
        """Add a new worker to the pool"""
        worker_id = f"worker_{len(self.workers)}_{uuid.uuid4().hex[:8]}"
        worker = Worker(
            id=worker_id,
            type=self.config.worker_type,
            metadata={"auto_scaled": True}
        )
        self.workers[worker_id] = worker
        logger.debug(f"Added worker: {worker_id}")
    
    async def _remove_idle_worker(self):
        """Remove an idle worker from the pool"""
        idle_workers = [w for w in self.workers.values() if w.status == "idle"]
        if idle_workers:
            worker = max(idle_workers, key=lambda w: w.created_at)  # Remove newest idle worker
            del self.workers[worker.id]
            logger.debug(f"Removed worker: {worker.id}")
    
    def _heartbeat_loop(self):
        """Monitor worker heartbeats"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                
                for worker in list(self.workers.values()):
                    worker.last_heartbeat = current_time
                    
                    # Update worker metrics (simulated)
                    import psutil
                    worker.cpu_usage = psutil.cpu_percent()
                    worker.memory_usage = psutil.virtual_memory().percent
                
                self.shutdown_event.wait(self.config.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(1.0)
    
    def _cleanup_loop(self):
        """Cleanup completed and failed tasks"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                current_time = time.time()
                cleanup_age = 3600  # 1 hour
                
                tasks_to_remove = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and current_time - task.created_at > cleanup_age
                ]
                
                for task_id in tasks_to_remove:
                    del self.tasks[task_id]
                
                if tasks_to_remove:
                    logger.debug(f"Cleaned up {len(tasks_to_remove)} old tasks")
                
                self.shutdown_event.wait(self.config.cleanup_interval)
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(1.0)
    
    def _load_balancer_loop(self):
        """Load balancing and optimization"""
        while self.is_running and not self.shutdown_event.is_set():
            try:
                self._update_metrics()
                self.shutdown_event.wait(5.0)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in load balancer loop: {e}")
                time.sleep(1.0)
    
    def _update_metrics(self):
        """Update system metrics"""
        try:
            self.metrics["queue_size"] = self.task_queue.qsize()
            self.metrics["active_workers"] = len([w for w in self.workers.values() if w.status == "busy"])
            
            # Calculate averages
            if self.metrics["processing_times"]:
                self.metrics["avg_processing_time"] = sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"])
                
                # Keep only last 100 processing times
                if len(self.metrics["processing_times"]) > 100:
                    self.metrics["processing_times"] = self.metrics["processing_times"][-100:]
            
            # Calculate error rate
            total_tasks = self.metrics["tasks_completed"] + self.metrics["tasks_failed"]
            if total_tasks > 0:
                self.metrics["error_rate"] = self.metrics["tasks_failed"] / total_tasks * 100
            
            # Calculate throughput (tasks per minute)
            current_time = time.time()
            recent_tasks = [t for t in self.tasks.values() 
                          if t.completed_at and current_time - t.completed_at < 60]
            self.metrics["throughput"] = len(recent_tasks)
            
            # Load distribution
            self.metrics["load_distribution"] = {
                worker.id: worker.tasks_completed for worker in self.workers.values()
            }
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get status of a specific task"""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or processing task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            self.metrics["tasks_cancelled"] += 1
            return True
        
        return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "is_running": self.is_running,
            "config": {
                "max_workers": self.config.max_workers,
                "worker_type": self.config.worker_type.value,
                "queue_size": self.config.queue_size,
                "auto_scaling": self.config.enable_auto_scaling,
                "load_balancing": self.config.enable_load_balancing
            },
            "workers": {
                "total": len(self.workers),
                "active": len([w for w in self.workers.values() if w.status == "busy"]),
                "idle": len([w for w in self.workers.values() if w.status == "idle"]),
                "details": [
                    {
                        "id": w.id,
                        "type": w.type.value,
                        "status": w.status,
                        "tasks_completed": w.tasks_completed,
                        "tasks_failed": w.tasks_failed,
                        "cpu_usage": w.cpu_usage,
                        "memory_usage": w.memory_usage,
                        "current_task": w.current_task
                    }
                    for w in self.workers.values()
                ]
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "processing": len([t for t in self.tasks.values() if t.status == TaskStatus.PROCESSING]),
                "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
                "cancelled": len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED])
            },
            "metrics": self.metrics.copy(),
            "registered_functions": list(self.function_registry.keys())
        }
    
    async def shutdown(self):
        """Shutdown the distributed processing system"""
        if not self.is_running:
            return
        
        logger.info("Shutting down distributed processing system...")
        
        # Stop accepting new tasks
        self.is_running = False
        self.shutdown_event.set()
        
        # Cancel pending tasks
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
        
        # Wait for monitoring threads to finish
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5.0)
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
        
        if self.load_balancer_thread and self.load_balancer_thread.is_alive():
            self.load_balancer_thread.join(timeout=5.0)
        
        # Shutdown executors
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
        
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
        
        logger.info("Distributed processing system shutdown complete")

# Global distributed processor instance
_distributed_processor: Optional[DistributedProcessor] = None

def get_distributed_processor() -> DistributedProcessor:
    """Get the global distributed processor instance"""
    global _distributed_processor
    if _distributed_processor is None:
        _distributed_processor = DistributedProcessor()
    return _distributed_processor

async def initialize_distributed_processing(config: DistributedConfig = None):
    """Initialize the distributed processing system"""
    processor = get_distributed_processor()
    if config:
        processor.config = config
    await processor.start()
    return processor