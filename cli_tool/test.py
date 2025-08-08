#!/usr/bin/env python3

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli_tool.collector import UsageCollector


async def test_api_data_output():
    """
    Test function that shows exactly what data gets sent to Django API.
    This mimics the same logic as the main CLI but outputs the data locally.
    """
    print("🧪 Testing API Data Output - What gets sent to Django")
    print("=" * 80)
    
    # Initialize collector (same as CLI)
    collector = UsageCollector()
    
    print("📊 Collecting data from both Cursor and Claude...")
    print("-" * 40)
    
    # Collect data from both tools (same as collector.py)
    results = await collector.collect_both_usage()
    
    # Display the combined usage table (same as collector.py)
    collector.display_combined_usage_table(results['cursor'], results['claude'])
    
    print("\n" + "=" * 80)
    print("🌐 API DATA THAT WOULD BE SENT TO DJANGO")
    print("=" * 80)
    
    # Prepare the data structure that would be sent to the API
    api_data = {
        "collection_timestamp": datetime.now().isoformat(),
        "tools": []
    }
    
    # Show what gets sent to Django API
    if results['cursor']:
        print("\n📤 CURSOR DATA FOR API:")
        print("-" * 40)
        
        # Aggregate Cursor data for API transmission (same as collector.py)
        aggregated_cursor = collector.aggregate_cursor_data_for_api(results['cursor'])
        api_data["tools"].append(aggregated_cursor)
        
        # Show the structure that gets sent
        print("Tool:", aggregated_cursor['tool'])
        print("Collection Info:", aggregated_cursor['collection_info'])
        print(f"Daily Aggregates: {len(aggregated_cursor['daily_aggregates'])} entries")
        
        # Show first few daily aggregates
        print("\n📅 Sample Daily Aggregates (first 3):")
        for i, entry in enumerate(aggregated_cursor['daily_aggregates'][:3]):
            print(f"  {i+1}. Date: {entry['date']}")
            print(f"     Model: {entry['model']}")
            print(f"     Kind: {entry['kind']}")
            print(f"     Total Tokens: {entry['total_tokens']:,}")
            print(f"     Cost: ${entry['cost']:.4f}")
            print(f"     Requests: {entry['requests']}")
            print(f"     Included in Subscription: {entry['included_in_subscription']}")
            print()
        
        if len(aggregated_cursor['daily_aggregates']) > 3:
            print(f"  ... and {len(aggregated_cursor['daily_aggregates']) - 3} more entries")
    
    if results['claude']:
        print("\n📤 CLAUDE DATA FOR API:")
        print("-" * 40)
        
        # Aggregate Claude data for API transmission (same as collector.py)
        aggregated_claude = collector.aggregate_claude_data_for_api(results['claude'])
        api_data["tools"].append(aggregated_claude)
        
        # Show the structure that gets sent
        print("Tool:", aggregated_claude['tool'])
        print("Collection Info:", aggregated_claude['collection_info'])
        print(f"Daily Aggregates: {len(aggregated_claude['daily_aggregates'])} entries")
        
        if 'totals' in aggregated_claude:
            print("Totals:", aggregated_claude['totals'])
        
        # Show first few daily aggregates
        print("\n📅 Sample Daily Aggregates (first 3):")
        for i, entry in enumerate(aggregated_claude['daily_aggregates'][:3]):
            print(f"  {i+1}. Date: {entry['date']}")
            print(f"     Model: {entry['model']}")
            print(f"     Input Tokens: {entry['input_tokens']:,}")
            print(f"     Output Tokens: {entry['output_tokens']:,}")
            print(f"     Cache Creation Tokens: {entry['cache_creation_tokens']:,}")
            print(f"     Cache Read Tokens: {entry['cache_read_tokens']:,}")
            print(f"     Total Tokens: {entry['total_tokens']:,}")
            print(f"     Cost: ${entry['cost']:.4f}")
            print()
        
        if len(aggregated_claude['daily_aggregates']) > 3:
            print(f"  ... and {len(aggregated_claude['daily_aggregates']) - 3} more entries")
    
    # Save the API data to a local JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"api_data_test_{timestamp}.json"
    json_filepath = Path(__file__).parent / json_filename
    
    try:
        with open(json_filepath, 'w') as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 API data saved to: {json_filepath}")
        print(f"📁 File size: {json_filepath.stat().st_size:,} bytes")
        
    except Exception as e:
        print(f"\n❌ Error saving JSON file: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed - This is exactly what gets sent to Django API")
    print("=" * 80)


async def main():
    """Main function to test API data output"""
    try:
        await test_api_data_output()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
