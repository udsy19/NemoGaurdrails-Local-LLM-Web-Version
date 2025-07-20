"""
Performance Monitor for Phase 2 Optimization
Implements comprehensive performance monitoring and benchmarking
Target: Track and optimize inference speed, memory usage, and throughput
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import psutil
import threading
from contextlib import contextmanager
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BenchmarkResult:
    """Benchmark execution result"""
    benchmark_name: str
    duration_seconds: float
    throughput_ops_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    metrics: List[PerformanceMetric] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system:
    - Real-time performance tracking
    - Benchmarking capabilities
    - Performance regression detection
    - Resource usage monitoring
    - Automated performance reporting
    """
    
    def __init__(self, 
                 monitoring_interval: float = 1.0,
                 max_history_size: int = 1000,
                 enable_detailed_logging: bool = True):
        
        self.monitoring_interval = monitoring_interval
        self.max_history_size = max_history_size
        self.enable_detailed_logging = enable_detailed_logging
        
        # Performance data storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.benchmark_results: List[BenchmarkResult] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        self.monitoring_lock = threading.Lock()
        
        # Performance counters
        self.counters = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_processing_time": 0.0,
            "total_memory_usage": 0.0,
            "peak_memory_usage": 0.0,
            "average_response_time": 0.0
        }
        
        # Custom metrics
        self.custom_metrics: Dict[str, Callable] = {}
        
        # Performance thresholds
        self.thresholds = {
            "max_response_time_ms": 5000,
            "max_memory_usage_mb": 2048,
            "min_throughput_ops_per_second": 10,
            "max_cpu_usage_percent": 80,
            "min_success_rate": 0.95
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable] = []
        
        logger.info("PerformanceMonitor initialized")
    
    def add_custom_metric(self, name: str, collector_func: Callable) -> None:
        """Add custom metric collector"""
        self.custom_metrics[name] = collector_func
        logger.info(f"Added custom metric: {name}")
    
    def remove_custom_metric(self, name: str) -> bool:
        """Remove custom metric collector"""
        if name in self.custom_metrics:
            del self.custom_metrics[name]
            logger.info(f"Removed custom metric: {name}")
            return True
        return False
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add performance alert callback"""
        self.alert_callbacks.append(callback)
        logger.info(f"Added alert callback: {callback.__name__}")
    
    def set_threshold(self, threshold_name: str, value: float) -> bool:
        """Set performance threshold"""
        if threshold_name in self.thresholds:
            old_value = self.thresholds[threshold_name]
            self.thresholds[threshold_name] = value
            logger.info(f"Updated threshold {threshold_name}: {old_value} -> {value}")
            return True
        return False
    
    def record_metric(self, 
                     name: str, 
                     value: float, 
                     unit: str = "ms",
                     metadata: Dict[str, Any] = None) -> None:
        """Record a performance metric"""
        try:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            
            with self.monitoring_lock:
                self.metrics_history[name].append(metric)
                
                # Update counters
                if name == "response_time":
                    self.counters["total_requests"] += 1
                    self.counters["total_processing_time"] += value
                    self.counters["average_response_time"] = (
                        self.counters["total_processing_time"] / self.counters["total_requests"]
                    )
                
                elif name == "memory_usage":
                    self.counters["peak_memory_usage"] = max(
                        self.counters["peak_memory_usage"], value
                    )
                
                # Check thresholds
                self._check_thresholds(metric)
            
            if self.enable_detailed_logging:
                logger.debug(f"Recorded metric {name}: {value} {unit}")
                
        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")
    
    def record_request_result(self, 
                            success: bool, 
                            response_time_ms: float,
                            memory_usage_mb: float = 0.0,
                            metadata: Dict[str, Any] = None) -> None:
        """Record request processing result"""
        try:
            with self.monitoring_lock:
                if success:
                    self.counters["successful_requests"] += 1
                else:
                    self.counters["failed_requests"] += 1
            
            # Record individual metrics
            self.record_metric("response_time", response_time_ms, "ms", metadata)
            
            if memory_usage_mb > 0:
                self.record_metric("memory_usage", memory_usage_mb, "MB", metadata)
            
        except Exception as e:
            logger.error(f"Error recording request result: {e}")
    
    @contextmanager
    def measure_performance(self, operation_name: str, metadata: Dict[str, Any] = None):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        try:
            yield
            
            # Record successful operation
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            duration_ms = (end_time - start_time) * 1000
            memory_delta = end_memory - start_memory
            
            self.record_metric(f"{operation_name}_duration", duration_ms, "ms", metadata)
            self.record_metric(f"{operation_name}_memory_delta", memory_delta, "MB", metadata)
            self.record_request_result(True, duration_ms, end_memory, metadata)
            
        except Exception as e:
            # Record failed operation
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            error_metadata = (metadata or {}).copy()
            error_metadata["error"] = str(e)
            
            self.record_request_result(False, duration_ms, 0.0, error_metadata)
            raise
    
    async def run_benchmark(self, 
                          benchmark_name: str,
                          benchmark_func: Callable,
                          num_iterations: int = 100,
                          warmup_iterations: int = 10,
                          **kwargs) -> BenchmarkResult:
        """
        Run performance benchmark
        
        Args:
            benchmark_name: Name of the benchmark
            benchmark_func: Function to benchmark
            num_iterations: Number of benchmark iterations
            warmup_iterations: Number of warmup iterations
            **kwargs: Additional arguments for benchmark function
            
        Returns:
            BenchmarkResult with performance metrics
        """
        try:
            logger.info(f"Starting benchmark '{benchmark_name}' with {num_iterations} iterations")
            
            # Warmup phase
            logger.info(f"Warmup phase: {warmup_iterations} iterations")
            for i in range(warmup_iterations):
                try:
                    if asyncio.iscoroutinefunction(benchmark_func):
                        await benchmark_func(**kwargs)
                    else:
                        benchmark_func(**kwargs)
                except Exception as e:
                    logger.warning(f"Warmup iteration {i} failed: {e}")
            
            # Benchmark phase
            durations = []
            memory_usages = []
            cpu_usages = []
            successful_runs = 0
            error_count = 0
            
            benchmark_start = time.time()
            
            for i in range(num_iterations):
                try:
                    # Measure system resources before
                    process = psutil.Process()
                    memory_before = process.memory_info().rss / (1024 * 1024)
                    cpu_before = process.cpu_percent()
                    
                    # Run benchmark iteration
                    iteration_start = time.time()
                    
                    if asyncio.iscoroutinefunction(benchmark_func):
                        result = await benchmark_func(**kwargs)
                    else:
                        result = benchmark_func(**kwargs)
                    
                    iteration_end = time.time()
                    
                    # Measure system resources after
                    memory_after = process.memory_info().rss / (1024 * 1024)
                    cpu_after = process.cpu_percent()
                    
                    # Record metrics
                    duration_ms = (iteration_end - iteration_start) * 1000
                    memory_usage = max(memory_before, memory_after)
                    cpu_usage = max(cpu_before, cpu_after)
                    
                    durations.append(duration_ms)
                    memory_usages.append(memory_usage)
                    cpu_usages.append(cpu_usage)
                    
                    successful_runs += 1
                    
                    # Progress logging
                    if (i + 1) % 10 == 0:
                        logger.info(f"Benchmark progress: {i + 1}/{num_iterations}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Benchmark iteration {i} failed: {e}")
            
            benchmark_end = time.time()
            
            # Calculate results
            total_duration = benchmark_end - benchmark_start
            success_rate = successful_runs / num_iterations
            
            # Calculate statistics
            avg_duration = statistics.mean(durations) if durations else 0
            avg_memory = statistics.mean(memory_usages) if memory_usages else 0
            avg_cpu = statistics.mean(cpu_usages) if cpu_usages else 0
            
            # Calculate throughput
            throughput = successful_runs / total_duration if total_duration > 0 else 0
            
            # Create detailed metrics
            metrics = []
            
            if durations:
                metrics.extend([
                    PerformanceMetric("avg_duration", avg_duration, "ms", time.time()),
                    PerformanceMetric("min_duration", min(durations), "ms", time.time()),
                    PerformanceMetric("max_duration", max(durations), "ms", time.time()),
                    PerformanceMetric("duration_std", statistics.stdev(durations) if len(durations) > 1 else 0, "ms", time.time()),
                    PerformanceMetric("p95_duration", statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else avg_duration, "ms", time.time()),
                    PerformanceMetric("p99_duration", statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else avg_duration, "ms", time.time())
                ])
            
            if memory_usages:
                metrics.extend([
                    PerformanceMetric("avg_memory", avg_memory, "MB", time.time()),
                    PerformanceMetric("peak_memory", max(memory_usages), "MB", time.time())
                ])
            
            # Create benchmark result
            result = BenchmarkResult(
                benchmark_name=benchmark_name,
                duration_seconds=total_duration,
                throughput_ops_per_second=throughput,
                memory_usage_mb=avg_memory,
                cpu_usage_percent=avg_cpu,
                success_rate=success_rate,
                error_count=error_count,
                metrics=metrics
            )
            
            # Store result
            self.benchmark_results.append(result)
            
            logger.info(f"Benchmark '{benchmark_name}' completed: {throughput:.2f} ops/sec, {success_rate:.2%} success rate")
            
            return result
            
        except Exception as e:
            logger.error(f"Benchmark '{benchmark_name}' failed: {e}")
            
            # Return error result
            return BenchmarkResult(
                benchmark_name=benchmark_name,
                duration_seconds=0,
                throughput_ops_per_second=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                success_rate=0,
                error_count=1,
                metrics=[PerformanceMetric("error", 1, "count", time.time(), {"error": str(e)})]
            )
    
    async def start_monitoring(self) -> bool:
        """Start performance monitoring"""
        try:
            if self.monitoring_active:
                logger.warning("Performance monitoring already active")
                return False
            
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("Performance monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting performance monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """Stop performance monitoring"""
        try:
            if not self.monitoring_active:
                return False
            
            self.monitoring_active = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            
            logger.info("Performance monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping performance monitoring: {e}")
            return False
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                try:
                    # Collect system metrics
                    process = psutil.Process()
                    cpu_percent = process.cpu_percent()
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    
                    # Record system metrics
                    self.record_metric("cpu_usage", cpu_percent, "%")
                    self.record_metric("memory_usage", memory_mb, "MB")
                    
                    # Collect custom metrics
                    for metric_name, collector_func in self.custom_metrics.items():
                        try:
                            value = collector_func()
                            if value is not None:
                                self.record_metric(metric_name, value, "custom")
                        except Exception as e:
                            logger.error(f"Custom metric {metric_name} collection failed: {e}")
                    
                    # Wait for next cycle
                    await asyncio.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    logger.error(f"Monitoring loop iteration error: {e}")
                    await asyncio.sleep(self.monitoring_interval)
                    
        except asyncio.CancelledError:
            logger.info("Performance monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Performance monitoring loop error: {e}")
    
    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if metric exceeds thresholds"""
        try:
            threshold_key = None
            
            # Map metric names to threshold keys
            if metric.name == "response_time":
                threshold_key = "max_response_time_ms"
            elif metric.name == "memory_usage":
                threshold_key = "max_memory_usage_mb"
            elif metric.name == "cpu_usage":
                threshold_key = "max_cpu_usage_percent"
            
            if threshold_key and threshold_key in self.thresholds:
                threshold_value = self.thresholds[threshold_key]
                
                if metric.value > threshold_value:
                    alert_data = {
                        "metric": metric.name,
                        "value": metric.value,
                        "threshold": threshold_value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp
                    }
                    
                    self._trigger_alert(f"Threshold exceeded: {metric.name}", alert_data)
                    
        except Exception as e:
            logger.error(f"Threshold check error: {e}")
    
    def _trigger_alert(self, message: str, data: Dict[str, Any]) -> None:
        """Trigger performance alert"""
        try:
            logger.warning(f"Performance alert: {message}")
            
            for callback in self.alert_callbacks:
                try:
                    callback(message, data)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Alert trigger error: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        try:
            with self.monitoring_lock:
                summary = {
                    "counters": self.counters.copy(),
                    "recent_metrics": {},
                    "benchmark_summary": {},
                    "thresholds": self.thresholds.copy(),
                    "monitoring_active": self.monitoring_active
                }
                
                # Get recent metrics (last 10 for each type)
                for metric_name, metric_history in self.metrics_history.items():
                    recent_metrics = list(metric_history)[-10:]
                    if recent_metrics:
                        values = [m.value for m in recent_metrics]
                        summary["recent_metrics"][metric_name] = {
                            "count": len(values),
                            "latest": values[-1],
                            "average": statistics.mean(values),
                            "min": min(values),
                            "max": max(values),
                            "unit": recent_metrics[-1].unit
                        }
                
                # Benchmark summary
                if self.benchmark_results:
                    recent_benchmarks = self.benchmark_results[-10:]
                    summary["benchmark_summary"] = {
                        "total_benchmarks": len(self.benchmark_results),
                        "recent_benchmarks": len(recent_benchmarks),
                        "avg_throughput": statistics.mean([b.throughput_ops_per_second for b in recent_benchmarks]),
                        "avg_success_rate": statistics.mean([b.success_rate for b in recent_benchmarks]),
                        "latest_benchmark": recent_benchmarks[-1].benchmark_name if recent_benchmarks else None
                    }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def export_metrics(self, output_file: str) -> bool:
        """Export performance metrics to file"""
        try:
            export_data = {
                "export_timestamp": time.time(),
                "counters": self.counters,
                "metrics_history": {},
                "benchmark_results": [],
                "thresholds": self.thresholds
            }
            
            # Export metrics history
            for metric_name, metric_history in self.metrics_history.items():
                export_data["metrics_history"][metric_name] = [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp,
                        "metadata": m.metadata
                    }
                    for m in metric_history
                ]
            
            # Export benchmark results
            for benchmark in self.benchmark_results:
                export_data["benchmark_results"].append({
                    "benchmark_name": benchmark.benchmark_name,
                    "duration_seconds": benchmark.duration_seconds,
                    "throughput_ops_per_second": benchmark.throughput_ops_per_second,
                    "memory_usage_mb": benchmark.memory_usage_mb,
                    "cpu_usage_percent": benchmark.cpu_usage_percent,
                    "success_rate": benchmark.success_rate,
                    "error_count": benchmark.error_count,
                    "timestamp": benchmark.timestamp,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "unit": m.unit,
                            "timestamp": m.timestamp,
                            "metadata": m.metadata
                        }
                        for m in benchmark.metrics
                    ]
                })
            
            # Write to file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Performance metrics exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False
    
    def clear_metrics(self) -> bool:
        """Clear all performance metrics"""
        try:
            with self.monitoring_lock:
                self.metrics_history.clear()
                self.benchmark_results.clear()
                
                # Reset counters
                self.counters = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_processing_time": 0.0,
                    "total_memory_usage": 0.0,
                    "peak_memory_usage": 0.0,
                    "average_response_time": 0.0
                }
            
            logger.info("Performance metrics cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing metrics: {e}")
            return False