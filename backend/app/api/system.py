import psutil
import platform
import cpuinfo
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import subprocess
import re
import time

router = APIRouter()

def get_gpu_info() -> Optional[Dict[str, Any]]:
    """Get GPU information if available"""
    try:
        # Try nvidia-smi first
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                parts = lines[0].split(', ')
                if len(parts) == 2:
                    return {
                        'vendor': 'NVIDIA',
                        'model': parts[0].strip(),
                        'memory': int(parts[1].strip())
                    }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try to detect other GPUs (basic detection)
    try:
        # Check for AMD GPU
        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            if 'AMD' in result.stdout or 'Radeon' in result.stdout:
                # Basic AMD detection
                amd_match = re.search(r'AMD.*?Radeon.*?(\w+)', result.stdout)
                if amd_match:
                    return {
                        'vendor': 'AMD',
                        'model': amd_match.group(0),
                        'memory': 0  # Memory detection requires more complex tools
                    }
            elif 'Intel' in result.stdout and ('Graphics' in result.stdout or 'UHD' in result.stdout):
                intel_match = re.search(r'Intel.*?Graphics.*?(\w+)', result.stdout)
                if intel_match:
                    return {
                        'vendor': 'Intel',
                        'model': intel_match.group(0),
                        'memory': 0  # Integrated graphics share system memory
                    }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return None

def get_cpu_info() -> Dict[str, Any]:
    """Get detailed CPU information"""
    try:
        cpu_info = cpuinfo.get_cpu_info()
        return {
            'cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'model': cpu_info.get('brand_raw', 'Unknown CPU'),
            'architecture': cpu_info.get('arch', platform.machine()),
            'frequency': cpu_info.get('hz_advertised_friendly', 'Unknown'),
        }
    except Exception:
        return {
            'cores': psutil.cpu_count(logical=False) or 1,
            'logical_cores': psutil.cpu_count(logical=True) or 1,
            'model': 'Unknown CPU',
            'architecture': platform.machine(),
            'frequency': 'Unknown',
        }

def get_memory_info() -> Dict[str, Any]:
    """Get memory information"""
    memory = psutil.virtual_memory()
    return {
        'total': memory.total // (1024 * 1024),  # Convert to MB
        'available': memory.available // (1024 * 1024),  # Convert to MB
        'used': memory.used // (1024 * 1024),  # Convert to MB
        'percentage': memory.percent
    }

def get_disk_info() -> Dict[str, Any]:
    """Get disk information"""
    try:
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total // (1024 * 1024 * 1024),  # Convert to GB
            'used': disk.used // (1024 * 1024 * 1024),  # Convert to GB
            'free': disk.free // (1024 * 1024 * 1024),  # Convert to GB
            'percentage': (disk.used / disk.total) * 100
        }
    except Exception:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'percentage': 0
        }

@router.get("/info")
async def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information for model recommendations"""
    try:
        system_info = {
            'cpu': get_cpu_info(),
            'memory': get_memory_info(),
            'disk': get_disk_info(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
        }
        
        # Add GPU info if available
        gpu_info = get_gpu_info()
        if gpu_info:
            system_info['gpu'] = gpu_info
        
        return system_info
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

def get_cpu_temperature():
    """Get CPU temperature if available"""
    try:
        # Try different methods to get temperature
        if hasattr(psutil, 'sensors_temperatures'):
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower() or 'thermal' in name.lower():
                        if entries:
                            return round(entries[0].current, 1)
    except Exception:
        pass
    
    # Try alternative methods for specific platforms
    try:
        # macOS
        if platform.system() == "Darwin":
            result = subprocess.run(['sudo', 'powermetrics', '--samplers', 'smc', '-n', '1', '-i', '1'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                temp_match = re.search(r'CPU die temperature:\s+(\d+\.\d+)', result.stdout)
                if temp_match:
                    return float(temp_match.group(1))
    except Exception:
        pass
    
    return None

def get_gpu_usage():
    """Get real-time GPU usage statistics"""
    try:
        # Try nvidia-smi for NVIDIA GPUs
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw', 
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                parts = lines[0].split(', ')
                if len(parts) >= 4:
                    return {
                        'utilization': float(parts[0].strip()) if parts[0].strip() != 'N/A' else 0,
                        'memory_used': int(parts[1].strip()) if parts[1].strip() != 'N/A' else 0,
                        'memory_total': int(parts[2].strip()) if parts[2].strip() != 'N/A' else 0,
                        'temperature': float(parts[3].strip()) if parts[3].strip() != 'N/A' else None,
                        'power_draw': float(parts[4].strip()) if len(parts) > 4 and parts[4].strip() != 'N/A' else None
                    }
    except Exception:
        pass
    
    return None

@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get current system performance metrics with real-time monitoring"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Load average (Unix systems)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            # Windows doesn't have load average
            pass
        
        # Process count
        process_count = len(psutil.pids())
        
        # Boot time
        boot_time = psutil.boot_time()
        
        # CPU temperature
        cpu_temp = get_cpu_temperature()
        
        # GPU usage
        gpu_usage = get_gpu_usage()
        
        performance_data = {
            'cpu': {
                'usage_percent': cpu_percent,
                'per_core_usage': cpu_per_core,
                'load_average': load_avg,
                'count': psutil.cpu_count(logical=True),
                'temperature': cpu_temp
            },
            'memory': {
                'total': memory.total // (1024 * 1024),
                'available': memory.available // (1024 * 1024),
                'used': memory.used // (1024 * 1024),
                'percentage': memory.percent,
                'cached': getattr(memory, 'cached', 0) // (1024 * 1024),
                'buffers': getattr(memory, 'buffers', 0) // (1024 * 1024)
            },
            'disk': {
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            },
            'network': {
                'bytes_sent': network_io.bytes_sent if network_io else 0,
                'bytes_recv': network_io.bytes_recv if network_io else 0,
                'packets_sent': network_io.packets_sent if network_io else 0,
                'packets_recv': network_io.packets_recv if network_io else 0
            },
            'gpu': gpu_usage,
            'system': {
                'process_count': process_count,
                'boot_time': boot_time,
                'uptime': time.time() - boot_time
            },
            'timestamp': time.time()
        }
        
        return performance_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/hardware")
async def get_hardware_metrics() -> Dict[str, Any]:
    """Get real-time hardware metrics for analytics dashboard"""
    try:
        # Get performance data
        perf_data = await get_performance_metrics()
        
        # Get model load times from model manager if available
        model_load_times = {}
        try:
            from app.main import model_manager
            if model_manager and hasattr(model_manager, 'gpu_accelerator'):
                # Simulate model load times based on cached models
                cache_info = model_manager.gpu_accelerator.get_device_info().get('cache_info', {})
                cached_models = cache_info.get('cached_models', 0)
                hit_rate = cache_info.get('hit_rate', 0)
                
                # Estimate load times based on cache performance
                base_load_time = 500  # Base 500ms
                for detector_name in model_manager.available_detectors.keys():
                    if detector_name in model_manager.detectors:
                        # Faster load time if cached
                        load_time = base_load_time * (1 - hit_rate / 100) + 50
                        model_load_times[detector_name] = round(load_time, 1)
        except Exception:
            # Default model load times if model manager not available
            model_load_times = {
                'toxicity': 450,
                'pii': 380,
                'prompt_injection': 520,
                'topic': 600,
                'fact_check': 750,
                'spam': 320
            }
        
        # Calculate system temperature (highest of CPU/GPU)
        system_temp = 45  # Default safe temperature
        if perf_data['cpu'].get('temperature'):
            system_temp = max(system_temp, perf_data['cpu']['temperature'])
        if perf_data.get('gpu') and perf_data['gpu'].get('temperature'):
            system_temp = max(system_temp, perf_data['gpu']['temperature'])
        
        # Format for analytics dashboard
        hardware_metrics = {
            'cpu_usage': perf_data['cpu']['usage_percent'],
            'memory_usage': perf_data['memory']['percentage'],
            'gpu_usage': perf_data.get('gpu', {}).get('utilization', 0),
            'disk_usage': min(90, perf_data['memory']['percentage'] * 0.8),  # Estimate disk usage
            'network_io': {
                'sent': perf_data['network']['bytes_sent'],
                'received': perf_data['network']['bytes_recv']
            },
            'temperature': system_temp,
            'model_load_times': model_load_times,
            'timestamp': perf_data['timestamp']
        }
        
        return hardware_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hardware metrics: {str(e)}")

@router.get("/recommendations")
async def get_model_recommendations() -> Dict[str, Any]:
    """Get AI model recommendations based on system specs"""
    try:
        system_info = await get_system_info()
        
        # Get system specs
        total_memory_gb = system_info['memory']['total'] / 1024
        cpu_cores = system_info['cpu']['cores']
        has_gpu = 'gpu' in system_info
        
        recommendations = []
        
        # Model recommendations based on system specs
        models = [
            {
                'name': 'llama3.2:1b',
                'size_gb': 0.7,
                'min_memory_gb': 2,
                'recommended_memory_gb': 4,
                'description': 'Lightweight model for basic tasks'
            },
            {
                'name': 'llama3.2:3b',
                'size_gb': 2.0,
                'min_memory_gb': 4,
                'recommended_memory_gb': 8,
                'description': 'Balanced model for general use'
            },
            {
                'name': 'phi3:mini',
                'size_gb': 2.3,
                'min_memory_gb': 4,
                'recommended_memory_gb': 8,
                'description': 'Microsoft\'s efficient model'
            },
            {
                'name': 'gemma2:2b',
                'size_gb': 1.6,
                'min_memory_gb': 3,
                'recommended_memory_gb': 6,
                'description': 'Google\'s compact model'
            },
            {
                'name': 'llama3.1:8b',
                'size_gb': 4.7,
                'min_memory_gb': 8,
                'recommended_memory_gb': 16,
                'description': 'High-quality model for advanced tasks'
            },
            {
                'name': 'mistral:7b',
                'size_gb': 4.1,
                'min_memory_gb': 8,
                'recommended_memory_gb': 16,
                'description': 'Excellent general-purpose model'
            }
        ]
        
        for model in models:
            # Determine compatibility
            if total_memory_gb >= model['recommended_memory_gb']:
                compatibility = 'perfect'
                performance = 'excellent' if cpu_cores >= 8 else 'good'
                reason = f"Perfect fit! You have {total_memory_gb:.1f}GB RAM and {cpu_cores} CPU cores."
            elif total_memory_gb >= model['min_memory_gb']:
                compatibility = 'good'
                performance = 'good' if cpu_cores >= 4 else 'acceptable'
                reason = f"Should work well with {total_memory_gb:.1f}GB RAM and {cpu_cores} CPU cores."
            elif total_memory_gb >= model['min_memory_gb'] * 0.8:
                compatibility = 'partial'
                performance = 'acceptable'
                reason = f"Might work but could be slow. Consider upgrading memory."
            else:
                compatibility = 'incompatible'
                performance = 'poor'
                reason = f"Not enough memory. Need at least {model['min_memory_gb']}GB, have {total_memory_gb:.1f}GB."
            
            recommendations.append({
                'model': model,
                'compatibility': compatibility,
                'performance': performance,
                'reason': reason,
                'gpu_acceleration': has_gpu
            })
        
        # Sort by compatibility and performance
        compatibility_order = {'perfect': 4, 'good': 3, 'partial': 2, 'incompatible': 1}
        performance_order = {'excellent': 4, 'good': 3, 'acceptable': 2, 'poor': 1}
        
        recommendations.sort(
            key=lambda x: (compatibility_order[x['compatibility']], performance_order[x['performance']]),
            reverse=True
        )
        
        return {
            'system_info': system_info,
            'recommendations': recommendations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@router.get("/hardware")
async def get_hardware_metrics() -> Dict[str, Any]:
    """Get detailed hardware metrics for the analytics dashboard"""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Temperature (try to get if available)
        temperature = 0
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
        except:
            temperature = 0
        
        # GPU usage (if available)
        gpu_usage = None
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_usage = float(result.stdout.strip())
        except:
            gpu_usage = None
        
        # Model load times (simulated for now)
        model_load_times = {
            "toxicity_detector": 120,
            "pii_detector": 85,
            "spam_detector": 95,
            "prompt_injection_detector": 110,
            "topic_classifier": 140,
            "fact_checker": 160
        }
        
        hardware_data = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_io": {
                "sent": network_io.bytes_sent,
                "received": network_io.bytes_recv
            },
            "temperature": temperature,
            "model_load_times": model_load_times
        }
        
        if gpu_usage is not None:
            hardware_data["gpu_usage"] = gpu_usage
        
        return hardware_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hardware metrics: {str(e)}")

system_router = router