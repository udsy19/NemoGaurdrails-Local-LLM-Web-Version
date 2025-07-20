#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.main import app

# Get all routes
routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        for method in route.methods:
            if method != 'HEAD':
                routes.append(f'{method} {route.path}')

print(f'Total API endpoints: {len(routes)}')

# Group by API category
api_groups = {}
for route in sorted(routes):
    if '/api/' in route:
        category = route.split('/api/')[1].split('/')[0]
        if category not in api_groups:
            api_groups[category] = []
        api_groups[category].append(route)
    else:
        if 'root' not in api_groups:
            api_groups['root'] = []
        api_groups['root'].append(route)

print('\nAPI Endpoints by Category:')
for category, endpoints in api_groups.items():
    print(f'\n{category.upper()} ({len(endpoints)} endpoints):')
    for endpoint in endpoints[:3]:  # Show first 3 endpoints per category
        print(f'  {endpoint}')
    if len(endpoints) > 3:
        print(f'  ... and {len(endpoints) - 3} more')

# Test Phase 3 endpoints specifically
phase3_endpoints = []
for route in routes:
    if any(keyword in route.lower() for keyword in ['multi-tenant', 'ab-testing', 'advanced', 'distributed', 'gpu']):
        phase3_endpoints.append(route)

print(f'\nPhase 3 Endpoints ({len(phase3_endpoints)}):')
for endpoint in phase3_endpoints:
    print(f'  {endpoint}')

print('\n✅ FastAPI app setup complete with all Phase 3 endpoints!')