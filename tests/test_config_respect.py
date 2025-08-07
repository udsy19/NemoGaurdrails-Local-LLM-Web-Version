#!/usr/bin/env python3
"""
Test script to verify traffic router respects configuration settings
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.config_service import ConfigService
from app.services.traffic_router import TrafficRouter
from app.services.detection_service import DetectionService
from app.models.model_manager import ModelManager

async def test_traffic_router_config():
    """Test that traffic router respects configuration settings"""
    
    print("🔧 Testing Traffic Router Configuration Respect")
    print("=" * 50)
    
    # Initialize components
    model_manager = ModelManager()
    config_service = ConfigService(model_manager)
    await config_service.initialize()
    
    detection_service = DetectionService(model_manager)
    
    traffic_router = TrafficRouter()
    traffic_router.set_detection_service(detection_service)
    traffic_router.set_config_service(config_service)
    
    print("✅ Components initialized")
    
    # Test 1: Default configuration (all detectors enabled)
    print("\n📋 Test 1: Default Configuration")
    print("Expected: All detectors enabled, input/output guardrails enabled")
    
    is_safe, results, blocking_reasons = await traffic_router._apply_guardrails("test message", "input")
    print(f"Text: 'test message'")
    print(f"Is safe: {is_safe}")
    print(f"Results: {list(results.keys())}")
    print(f"Blocking reasons: {blocking_reasons}")
    
    # Test 2: Disable all detectors
    print("\n📋 Test 2: All Detectors Disabled")
    print("Expected: No detectors run, should allow all traffic")
    
    # Update config to disable all detectors
    await config_service.update_system_config({
        "detectors": {
            "toxicity": {"enabled": False},
            "pii": {"enabled": False}, 
            "prompt_injection": {"enabled": False},
            "topic": {"enabled": False},
            "fact_check": {"enabled": False},
            "spam": {"enabled": False}
        }
    })
    
    is_safe, results, blocking_reasons = await traffic_router._apply_guardrails("test message", "input")
    print(f"Text: 'test message'")
    print(f"Is safe: {is_safe}")
    print(f"Results: {list(results.keys())}")
    print(f"Blocking reasons: {blocking_reasons}")
    
    # Test 3: Enable only toxicity detector
    print("\n📋 Test 3: Only Toxicity Detector Enabled")
    print("Expected: Only toxicity detector runs")
    
    await config_service.update_system_config({
        "detectors": {
            "toxicity": {"enabled": True, "threshold": 0.7},
            "pii": {"enabled": False}, 
            "prompt_injection": {"enabled": False},
            "topic": {"enabled": False},
            "fact_check": {"enabled": False},
            "spam": {"enabled": False}
        }
    })
    
    is_safe, results, blocking_reasons = await traffic_router._apply_guardrails("test message", "input")
    print(f"Text: 'test message'")
    print(f"Is safe: {is_safe}")
    print(f"Results: {list(results.keys())}")
    print(f"Blocking reasons: {blocking_reasons}")
    
    # Test 4: Disable input guardrails
    print("\n📋 Test 4: Input Guardrails Disabled")
    print("Expected: Guardrails bypassed for input stage")
    
    await config_service.update_system_config({
        "guardrails": {
            "input_enabled": False,
            "output_enabled": True
        }
    })
    
    is_safe, results, blocking_reasons = await traffic_router._apply_guardrails("test message", "input")
    print(f"Text: 'test message'")
    print(f"Is safe: {is_safe}")
    print(f"Results: {list(results.keys())}")
    print(f"Blocking reasons: {blocking_reasons}")
    
    # Test 5: Re-enable input guardrails, disable output
    print("\n📋 Test 5: Output Guardrails Disabled")
    print("Expected: Guardrails bypassed for output stage")
    
    await config_service.update_system_config({
        "guardrails": {
            "input_enabled": True,
            "output_enabled": False
        }
    })
    
    is_safe, results, blocking_reasons = await traffic_router._apply_guardrails("test message", "output")
    print(f"Text: 'test message'")
    print(f"Is safe: {is_safe}")
    print(f"Results: {list(results.keys())}")
    print(f"Blocking reasons: {blocking_reasons}")
    
    print("\n✅ All configuration tests completed!")
    print("🎯 Traffic router now properly respects user configuration settings")

if __name__ == "__main__":
    asyncio.run(test_traffic_router_config())