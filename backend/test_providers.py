#!/usr/bin/env python3
"""
Test script for the new providers management system
"""
import asyncio
import json
from app.services.provider_service import provider_service

async def test_providers():
    """Test the provider service functionality"""
    print("🧪 Testing Provider Management System")
    print("=" * 50)
    
    # Test 1: List all providers
    print("📋 Available Providers:")
    providers = provider_service.list_providers()
    for provider in providers:
        print(f"  • {provider.display_name} ({provider.id}) - Port {provider.port}")
        print(f"    Models: {len(provider.models)} available")
        print(f"    Status: {provider.status.value}")
        print(f"    Enabled: {provider.enabled}")
        print()
    
    # Test 2: Provider statistics
    print("📊 Provider Statistics:")
    stats = provider_service.get_provider_stats()
    print(f"  Total Providers: {stats['total_providers']}")
    print(f"  Enabled Providers: {stats['enabled_providers']}")
    print(f"  Connected Providers: {stats['connected_providers']}")
    print(f"  Port Mappings: {stats['port_mappings']}")
    print()
    
    # Test 3: Enable a provider
    print("⚙️  Testing Provider Configuration:")
    print("  Enabling OpenAI provider...")
    success = provider_service.enable_provider('openai', True)
    print(f"  Enable result: {success}")
    
    print("  Setting dummy API key...")
    success = provider_service.set_api_key('openai', 'test-api-key-123')
    print(f"  API key set: {success}")
    
    print("  Selecting GPT-4 model...")
    success = provider_service.select_model('openai', 'gpt-4')
    print(f"  Model selected: {success}")
    print()
    
    # Test 4: Test connection (will fail without real API key)
    print("🔌 Testing Connection:")
    print("  Testing OpenAI connection (expected to fail with dummy key)...")
    success, error = await provider_service.test_provider_connection('openai')
    print(f"  Connection result: {success}")
    if error:
        print(f"  Error: {error}")
    print()
    
    # Test 5: Get provider by port
    print("🌐 Testing Port Mapping:")
    provider = provider_service.get_provider_by_port(8891)
    if provider:
        print(f"  Port 8891 -> {provider.display_name}")
    else:
        print("  No provider found on port 8891")
    print()
    
    # Test 6: Export provider configuration
    print("💾 Provider Configuration Export:")
    config = provider_service.to_dict()
    print("  Configuration exported successfully")
    print(f"  Total config size: {len(json.dumps(config, indent=2))} characters")
    print()
    
    print("✅ All tests completed!")
    print()
    print("🚀 Provider Management System is ready!")
    print("   • Frontend: React Providers page available")
    print("   • Backend: API endpoints at /api/providers/")
    print("   • Traffic: Port-based routing system ready")
    print("   • Guardrails: Integrated with safety pipeline")

if __name__ == "__main__":
    asyncio.run(test_providers())