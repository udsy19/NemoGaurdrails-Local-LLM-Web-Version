"""
Core application components and utilities
"""

from .dependencies import *

__all__ = [
    'ServiceContainer',
    'initialize_dependencies',
    'get_model_manager',
    'get_detection_service',
    'get_chat_service',
    'get_config_service',
    'AuthDependencies',
    'ValidationDependencies',
    'DependencyFactory'
]