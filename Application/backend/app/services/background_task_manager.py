"""
Background task management system for NBA Stats application.
Provides proper task tracking, cancellation, and status monitoring.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TaskInfo:
    def __init__(self, task_id: str, name: str, description: str = ""):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0
        self.current_step = ""
        self.error_message: Optional[str] = None
        self.result: Optional[Any] = None
        self.cancellation_token = asyncio.Event()
        self.task_handle: Optional[asyncio.Task] = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds() 
                if self.started_at and self.completed_at 
                else (datetime.utcnow() - self.started_at).total_seconds() 
                if self.started_at 
                else 0
            )
        }

class BackgroundTaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._max_completed_tasks = 50
        self._cleanup_task = None
        
    async def start_cleanup_task(self):
        """Start periodic cleanup of old completed tasks"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """Periodically clean up old completed tasks"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task cleanup: {e}")
    
    async def _cleanup_old_tasks(self):
        """Remove old completed/failed/cancelled tasks"""
        completed_tasks = [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        # Keep only the most recent completed tasks
        if len(completed_tasks) > self._max_completed_tasks:
            sorted_tasks = sorted(completed_tasks, key=lambda t: t.completed_at or t.created_at, reverse=True)
            tasks_to_remove = sorted_tasks[self._max_completed_tasks:]
            
            for task in tasks_to_remove:
                if task.task_id in self.tasks:
                    del self.tasks[task.task_id]
                    logger.info(f"Cleaned up old task: {task.task_id}")

    async def create_task(
        self, 
        name: str, 
        task_func: Callable, 
        description: str = "", 
        *args, 
        **kwargs
    ) -> str:
        """Create and start a new background task"""
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(task_id, name, description)
        self.tasks[task_id] = task_info
        
        # Start cleanup task if not running
        await self.start_cleanup_task()
        
        # Create the actual asyncio task
        task_info.task_handle = asyncio.create_task(
            self._run_task_with_monitoring(task_info, task_func, *args, **kwargs)
        )
        
        logger.info(f"Created task {task_id}: {name}")
        return task_id
    
    async def start_task(
        self, 
        name: str, 
        description: str,
        task_func: Callable, 
        *args, 
        **kwargs
    ) -> str:
        """Create and start a new background task (alias for create_task with different parameter order)"""
        return await self.create_task(name, task_func, description, *args, **kwargs)
    
    async def update_progress(
        self,
        task_id: str,
        progress: Optional[float] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        message: Optional[str] = None
    ):
        """Update progress information for a running task"""
        if task_id not in self.tasks:
            logger.warning(f"Attempted to update progress for unknown task: {task_id}")
            return
            
        task_info = self.tasks[task_id]
        
        if progress is not None:
            task_info.progress = min(100.0, max(0.0, progress))
        
        if message is not None:
            task_info.current_step = message
            
        logger.debug(f"Updated progress for task {task_id}: {task_info.progress}% - {task_info.current_step}")
    
    async def _run_task_with_monitoring(
        self, 
        task_info: TaskInfo, 
        task_func: Callable, 
        *args, 
        **kwargs
    ):
        """Run a task with proper monitoring and error handling"""
        try:
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.utcnow()
            
            logger.info(f"Starting task {task_info.task_id}: {task_info.name}")
            
            # Run the actual task function
            result = await task_func(task_info, *args, **kwargs)
            
            # Check if task was cancelled during execution
            if task_info.cancellation_token.is_set():
                task_info.status = TaskStatus.CANCELLED
                task_info.current_step = "Task was cancelled"
                logger.info(f"Task {task_info.task_id} was cancelled")
            else:
                task_info.status = TaskStatus.COMPLETED
                task_info.progress = 100.0
                task_info.current_step = "Completed successfully"
                task_info.result = result
                logger.info(f"Task {task_info.task_id} completed successfully")
                
        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELLED
            task_info.current_step = "Task was cancelled"
            logger.info(f"Task {task_info.task_id} was cancelled")
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            task_info.current_step = f"Failed: {str(e)}"
            logger.error(f"Task {task_info.task_id} failed: {e}")
            
        finally:
            task_info.completed_at = datetime.utcnow()
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id not in self.tasks:
            return False
            
        task_info = self.tasks[task_id]
        
        if task_info.status != TaskStatus.RUNNING:
            return False
        
        # Set cancellation token
        task_info.cancellation_token.set()
        
        # Cancel the asyncio task if it exists
        if task_info.task_handle and not task_info.task_handle.done():
            task_info.task_handle.cancel()
            try:
                await task_info.task_handle
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Cancelled task {task_id}")
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a specific task"""
        if task_id not in self.tasks:
            return None
        return self.tasks[task_id].to_dict()
    
    def get_all_tasks(self) -> Dict[str, Dict]:
        """Get status of all tasks"""
        return {task_id: task.to_dict() for task_id, task in self.tasks.items()}
    
    def get_active_tasks(self) -> Dict[str, Dict]:
        """Get all currently running tasks"""
        return {
            task_id: task.to_dict() 
            for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        }
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[Dict]:
        """Wait for a task to complete"""
        if task_id not in self.tasks:
            return None
            
        task_info = self.tasks[task_id]
        
        if task_info.task_handle:
            try:
                await asyncio.wait_for(task_info.task_handle, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Task {task_id} timed out after {timeout} seconds")
                
        return task_info.to_dict()
    
    async def shutdown(self):
        """Shutdown the task manager and cancel all running tasks"""
        logger.info("Shutting down background task manager")
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        running_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]
        
        for task in running_tasks:
            await self.cancel_task(task.task_id)
        
        # Wait for all tasks to complete
        if running_tasks:
            await asyncio.gather(
                *[task.task_handle for task in running_tasks if task.task_handle],
                return_exceptions=True
            )

# Global task manager instance
task_manager = BackgroundTaskManager()

async def update_task_progress(task_info: TaskInfo, progress: float, step: str):
    """Helper function to update task progress"""
    task_info.progress = min(100.0, max(0.0, progress))
    task_info.current_step = step
    
    # Check if task should be cancelled
    if task_info.cancellation_token.is_set():
        raise asyncio.CancelledError("Task was cancelled")

def check_cancellation(task_info: TaskInfo):
    """Helper function to check if task should be cancelled"""
    if task_info.cancellation_token.is_set():
        raise asyncio.CancelledError("Task was cancelled")
