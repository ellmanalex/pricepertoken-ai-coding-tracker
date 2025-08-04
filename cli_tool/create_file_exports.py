#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli_tool.collector import UsageCollector


async def create_api_exports():
    """
    Create sample files showing what data would be sent to the Django API.
    This runs the actual collectors and saves the real data.
    """
    print("🚀 Creating API export files...")
    print("📁 Files will be saved in the same directory as this script")
    print("=" * 60)
    
    # Initialize collector (no API token needed for local collection)
    collector = UsageCollector()
    
    # Create exports directory
    exports_dir = Path(__file__).parent / "api_exports"
    exports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Collect Cursor data
    print("\n🔍 Collecting Cursor usage data...")
    try:
        cursor_data = await collector.collect_cursor_usage()
        if cursor_data:
            cursor_file = exports_dir / f"cursor_data_{timestamp}.json"
            with open(cursor_file, 'w') as f:
                json.dump(cursor_data, f, indent=2)
            print(f"✅ Cursor data saved to: {cursor_file}")
            
            # Also save a sample of the data structure
            cursor_sample = {
                "tool": cursor_data.get('tool'),
                "collection_info": cursor_data.get('collection_info'),
                "summary": cursor_data.get('summary'),
                "billing_period_summary": cursor_data.get('billing_period_summary'),
                "sample_events": cursor_data.get('usage_events', [])[:3] if cursor_data.get('usage_events') else []
            }
            cursor_sample_file = exports_dir / f"cursor_sample_{timestamp}.json"
            with open(cursor_sample_file, 'w') as f:
                json.dump(cursor_sample, f, indent=2)
            print(f"✅ Cursor sample saved to: {cursor_sample_file}")
        else:
            print("❌ No Cursor data collected")
    except Exception as e:
        print(f"❌ Error collecting Cursor data: {e}")
    
    # 2. Collect Claude data
    print("\n🔍 Collecting Claude usage data...")
    try:
        claude_data = collector.collect_claude_usage()
        if claude_data:
            claude_file = exports_dir / f"claude_data_{timestamp}.json"
            with open(claude_file, 'w') as f:
                json.dump(claude_data, f, indent=2)
            print(f"✅ Claude data saved to: {claude_file}")
            
            # Also save a sample of the data structure
            claude_sample = {
                "collection_info": claude_data.get('collection_info'),
                "totals": claude_data.get('totals'),
                "daily": claude_data.get('daily', [])[:3] if claude_data.get('daily') else [],
                "metadata": claude_data.get('metadata')
            }
            claude_sample_file = exports_dir / f"claude_sample_{timestamp}.json"
            with open(claude_sample_file, 'w') as f:
                json.dump(claude_sample, f, indent=2)
            print(f"✅ Claude sample saved to: {claude_sample_file}")
        else:
            print("❌ No Claude data collected")
    except Exception as e:
        print(f"❌ Error collecting Claude data: {e}")
    
    # 3. Create API request examples
    print("\n📝 Creating API request examples...")
    
    # Example headers that would be sent
    api_headers = {
        "Authorization": "Token YOUR_API_TOKEN_HERE",
        "Content-Type": "application/json",
        "X-Tracker-Auth": "ServerBearer YOUR_SERVER_JWT_HERE",
        "User-Agent": "ai-usage-tracker-cli/1.0.0"
    }
    
    headers_file = exports_dir / f"api_headers_{timestamp}.json"
    with open(headers_file, 'w') as f:
        json.dump(api_headers, f, indent=2)
    print(f"✅ API headers saved to: {headers_file}")
    
    # Example API endpoint info
    api_info = {
        "endpoint": "/api/usage/collect/",
        "method": "POST",
        "content_type": "application/json",
        "authentication": {
            "type": "Token",
            "header": "Authorization",
            "format": "Token YOUR_API_TOKEN"
        },
        "server_auth": {
            "type": "ServerBearer",
            "header": "X-Tracker-Auth",
            "format": "ServerBearer YOUR_SERVER_JWT"
        },
        "expected_responses": {
            "200": "Success - Data received and processed",
            "401": "Unauthorized - Invalid API token",
            "429": "Rate limit exceeded",
            "413": "Data too large",
            "500": "Server error"
        }
    }
    
    api_info_file = exports_dir / f"api_info_{timestamp}.json"
    with open(api_info_file, 'w') as f:
        json.dump(api_info, f, indent=2)
    print(f"✅ API info saved to: {api_info_file}")
    
    # 4. Create Django model examples
    print("\n🏗️  Creating Django model examples...")
    
    django_models = {
        "UsageEvent": {
            "description": "Model for storing individual usage events",
            "fields": {
                "id": "AutoField (primary key)",
                "user": "ForeignKey to User model",
                "tool": "CharField (choices: 'cursor', 'claude')",
                "date": "DateTimeField",
                "model": "CharField (e.g., 'claude-4-sonnet-thinking')",
                "input_tokens": "IntegerField",
                "output_tokens": "IntegerField", 
                "total_tokens": "IntegerField",
                "cost": "DecimalField",
                "raw_data": "JSONField (stores original event data)",
                "created_at": "DateTimeField (auto_now_add=True)"
            }
        },
        "UsageSummary": {
            "description": "Model for storing aggregated usage summaries",
            "fields": {
                "id": "AutoField (primary key)",
                "user": "ForeignKey to User model",
                "tool": "CharField (choices: 'cursor', 'claude')",
                "period_start": "DateTimeField",
                "period_end": "DateTimeField",
                "total_requests": "IntegerField",
                "total_tokens": "IntegerField",
                "total_cost": "DecimalField",
                "model_breakdown": "JSONField (stores model-specific stats)",
                "collection_info": "JSONField (stores metadata)",
                "created_at": "DateTimeField (auto_now_add=True)"
            }
        },
        "User": {
            "description": "Django User model extension",
            "fields": {
                "id": "AutoField (primary key)",
                "username": "CharField (unique)",
                "email": "EmailField (unique)",
                "api_token": "CharField (unique, for CLI authentication)",
                "is_active": "BooleanField",
                "date_joined": "DateTimeField"
            }
        }
    }
    
    models_file = exports_dir / f"django_models_{timestamp}.json"
    with open(models_file, 'w') as f:
        json.dump(django_models, f, indent=2)
    print(f"✅ Django models saved to: {models_file}")
    
    # 5. Create README for the exports
    readme_content = f"""# API Export Files - {timestamp}

This directory contains sample files showing what data would be sent to the Django API.

## Files Created:

### Data Files:
- `cursor_data_{timestamp}.json` - Complete Cursor usage data
- `cursor_sample_{timestamp}.json` - Sample Cursor data structure
- `claude_data_{timestamp}.json` - Complete Claude usage data  
- `claude_sample_{timestamp}.json` - Sample Claude data structure

### API Files:
- `api_headers_{timestamp}.json` - Headers sent with API requests
- `api_info_{timestamp}.json` - API endpoint information
- `django_models_{timestamp}.json` - Suggested Django models

## API Endpoint:

**POST** `/api/usage/collect/`

### Headers:
- `Authorization: Token YOUR_API_TOKEN`
- `Content-Type: application/json`
- `X-Tracker-Auth: ServerBearer YOUR_SERVER_JWT`
- `User-Agent: ai-usage-tracker-cli/1.0.0`

### Data Structure:
The API receives the complete data structures from the collectors.
See the sample files for exact formats.

## Django Setup:

1. Create models based on `django_models_{timestamp}.json`
2. Create API endpoint at `/api/usage/collect/`
3. Implement Token authentication
4. Validate ServerBearer JWT for origin authentication
5. Parse and store the usage data

## Notes:
- These files contain real data from your system
- The data structure may evolve as the collectors are updated
- Use the sample files to understand the data format
"""
    
    readme_file = exports_dir / f"README_{timestamp}.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    print(f"✅ README saved to: {readme_file}")
    
    print("\n" + "=" * 60)
    print("✅ API export files created successfully!")
    print(f"📁 All files saved in: {exports_dir}")
    print("\n💡 Use these files to set up your Django API:")
    print("   1. Check the data structures in the sample files")
    print("   2. Create Django models based on django_models file")
    print("   3. Implement the API endpoint at /api/usage/collect/")
    print("   4. Set up authentication and validation")


if __name__ == "__main__":
    asyncio.run(create_api_exports())
