"""
Performance monitoring utilities for QuantiPeak platform
"""

import time
import functools
import asyncio
from typing import Callable, Any, Optional
from contextlib import asynccontextmanager, contextmanager
import psutil
import os
from .logger import logger

class PerformanceMonitor:
    """Performance monitoring utility"""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, operation: str) -> str:
        """Start timing an operation"""
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.metrics[timer_id] = {
            'operation': operation,
            'start_time': time.time(),
            'end_time': None,
            'duration': None
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing an operation and return duration"""
        if timer_id in self.metrics:
            end_time = time.time()
            self.metrics[timer_id]['end_time'] = end_time
            self.metrics[timer_id]['duration'] = end_time - self.metrics[timer_id]['start_time']
            
            duration = self.metrics[timer_id]['duration']
            operation = self.metrics[timer_id]['operation']
            
            logger.info(f"Performance: {operation} completed", 
                       duration_ms=round(duration * 1000, 2))
            
            return duration
        return 0.0
    
    def get_system_metrics(self) -> dict:
        """Get current system performance metrics"""
        try:
            process = psutil.Process(os.getpid())
            
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'system_cpu_percent': psutil.cpu_percent(),
                'system_memory_percent': psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.error("Failed to get system metrics", exception=e)
            return {}

# Global performance monitor
perf_monitor = PerformanceMonitor()

def time_operation(operation_name: str = None):
    """Decorator to time function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            timer_id = perf_monitor.start_timer(op_name)
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                perf_monitor.end_timer(timer_id)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            timer_id = perf_monitor.start_timer(op_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                perf_monitor.end_timer(timer_id)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

@contextmanager
def time_context(operation_name: str):
    """Context manager for timing operations"""
    timer_id = perf_monitor.start_timer(operation_name)
    try:
        yield
    finally:
        perf_monitor.end_timer(timer_id)

@asynccontextmanager
async def async_time_context(operation_name: str):
    """Async context manager for timing operations"""
    timer_id = perf_monitor.start_timer(operation_name)
    try:
        yield
    finally:
        perf_monitor.end_timer(timer_id)

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier"""
        current_time = time.time()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.time_window
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        current_time = time.time()
        
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.time_window
            ]
            return max(0, self.max_requests - len(self.requests[identifier]))
        
        return self.max_requests

# Global rate limiter
rate_limiter = RateLimiter()

def check_rate_limit(identifier: str) -> bool:
    """Check rate limit for identifier"""
    return rate_limiter.is_allowed(identifier)
