#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli_tool.collector import UsageCollector


def load_api_token() -> str:
    """Load API token from environment or config file"""
    # First try environment variable
    token = os.getenv("AI_USAGE_TRACKER_TOKEN")
    if token:
        return token
    
    # Try to load from config file
    config_file = Path.home() / ".ai-usage-tracker" / "config"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('token='):
                        return line.strip().split('=', 1)[1]
        except Exception as e:
            print(f"Error reading config file: {e}")
    
    return ""


def save_api_token(token: str):
    """Save API token to config file"""
    config_dir = Path.home() / ".ai-usage-tracker"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config"
    try:
        with open(config_file, 'w') as f:
            f.write(f"token={token}\n")
        
        # Set restrictive permissions
        os.chmod(config_file, 0o600)
        print(f"API token saved to {config_file}")
    except Exception as e:
        print(f"Error saving config file: {e}")


def generate_usage_report() -> dict:
    """Generate a comprehensive usage report"""
    collector = UsageCollector("", "")
    
    # Initialize the report object
    report = {
        "timestamp": datetime.now().isoformat(),
        "tool_version": "1.0.0",
        "os": f"{platform.system()} {platform.release()}",
        "python_version": platform.python_version(),
        "cursor_stats": None,
        "claude_stats": None,
        "raw_data": {},
        "errors": {},
        "summary": {}
    }
    
    try:
        print("🔍 Collecting Cursor usage data...")
        cursor_data = collector.collect_cursor_usage()
        if cursor_data:
            report["cursor_stats"] = cursor_data
            report["raw_data"]["cursor"] = cursor_data
            print("✅ Cursor data collected")
        else:
            report["errors"]["cursor"] = "No Cursor data found"
            print("❌ No Cursor data found")
        
        print("🔍 Collecting Claude usage data...")
        claude_data = collector.collect_claude_usage()
        if claude_data:
            report["claude_stats"] = claude_data
            report["raw_data"]["claude"] = claude_data
            print("✅ Claude data collected")
        else:
            report["errors"]["claude"] = "No Claude data found"
            print("❌ No Claude data found")
        
        # Generate summary
        total_tokens = 0
        total_cost = 0.0
        
        if cursor_data:
            total_tokens += cursor_data.get('tokens_used', 0)
            total_cost += cursor_data.get('cost_estimate', 0.0)
        
        if claude_data:
            total_tokens += claude_data.get('tokens_used', 0)
            total_cost += claude_data.get('cost_estimate', 0.0)
        
        report["summary"] = {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "tools_with_data": [k for k, v in [("cursor", cursor_data), ("claude", claude_data)] if v is not None]
        }
        
        print(f"📊 Summary: {total_tokens} tokens, ${total_cost:.4f} total cost")
        
    except Exception as e:
        report["errors"]["general"] = f"General error: {str(e)}"
        print(f"❌ Error generating report: {e}")
    
    return report


def save_report(report: dict) -> str:
    """Save the report to a JSON file"""
    try:
        timestamp = datetime.now().isoformat().replace(':', '-').split('.')[0]
        filename = f"ai-usage-report-{timestamp}.json"
        
        # Create reports directory
        reports_dir = Path.home() / ".ai-usage-tracker" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / filename
        
        # Pretty-print the JSON with 2-space indentation
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {report_path}")
        return str(report_path)
        
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return ""


async def collect_usage_local(tool: str) -> bool:
    """Collect usage data and display locally without sending to API"""
    collector = UsageCollector("", "")  # No token needed for local mode
    
    print(f"🔍 Collecting {tool} usage data...")
    
    if tool == "cursor":
        # Use the new API-based collection method
        data = await collector.collect_cursor_usage_with_api()
        if data:
            print("✅ Cursor data collected from CSV export:")
            
            # Show a nice summary
            summary = data.get('summary', {})
            usage_events = data.get('usage_events', [])
            
            print(f"📊 Summary:")
            print(f"  Total Events: {summary.get('total_events', 0)}")
            print(f"  Total Tokens: {summary.get('total_tokens', 0):,}")
            print(f"  Total Cost: ${summary.get('total_cost', 0):.4f}")
            print(f"  Models Used: {', '.join(summary.get('models_used', []))}")
            
            if summary.get('date_range', {}).get('start'):
                print(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
            
            if usage_events:
                print(f"\n📋 Recent Usage Events:")
                for i, event in enumerate(usage_events[:5]):  # Show last 5 events
                    print(f"  {i+1}. {event['date']} - {event['model']} - {event['tokens']:,} tokens - {event['cost']}")
                
                if len(usage_events) > 5:
                    print(f"  ... and {len(usage_events) - 5} more events")
            
            print(f"\n📄 Full Data (JSON):")
            print(json.dumps(data, indent=2))
            return True
        else:
            print("❌ No Cursor data found")
            return False
            
    elif tool == "claude":
        data = collector.collect_claude_usage()
        if data:
            print("✅ Claude data collected:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print("❌ No Claude data found")
            return False
            
    elif tool == "both":
        cursor_data = await collector.collect_cursor_usage_with_api()
        claude_data = collector.collect_claude_usage()
        
        print("📊 Usage Summary:")
        if cursor_data:
            print(f"✅ Cursor: {cursor_data.get('tokens_used', 0)} tokens, ${cursor_data.get('cost_estimate', 0):.4f}")
        else:
            print("❌ Cursor: No data found")
            
        if claude_data:
            print(f"✅ Claude: {claude_data.get('tokens_used', 0)} tokens, ${claude_data.get('cost_estimate', 0):.4f}")
        else:
            print("❌ Claude: No data found")
            
        return cursor_data is not None or claude_data is not None
    
    else:
        print(f"❌ Unknown tool: {tool}")
        return False


async def collect_usage(tool: str, api_token: str, django_url: str) -> bool:
    """Collect usage data for specified tool and send to API"""
    collector = UsageCollector(api_token, django_url)
    
    if tool == "cursor":
        return await collector.collect_and_send_cursor()
    elif tool == "claude":
        return await collector.collect_and_send_claude()
    elif tool == "both":
        cursor_success = await collector.collect_and_send_cursor()
        claude_success = await collector.collect_and_send_claude()
        return cursor_success or claude_success
    else:
        print(f"Unknown tool: {tool}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="AI Usage Tracker CLI - Collect and analyze usage data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Getting Started:
  1. Register at: https://your-django-app.com/register/
  2. Get your API token from: https://your-django-app.com/dashboard/
  3. Configure: %(prog)s --configure YOUR_API_TOKEN
  4. Start tracking: %(prog)s --collect both

Examples:
  %(prog)s --local cursor                    # View Cursor usage locally
  %(prog)s --local claude                    # View Claude usage locally  
  %(prog)s --local both                      # View both tools locally
  %(prog)s --report                          # Generate comprehensive usage report
  %(prog)s --configure YOUR_API_TOKEN        # Setup for hosted service
  %(prog)s --collect cursor                  # Send Cursor data to dashboard
  %(prog)s --collect claude                  # Send Claude data to dashboard
  %(prog)s --collect both                    # Send both tools data to dashboard
        """
    )
    
    parser.add_argument(
        "--local",
        choices=["cursor", "claude", "both"],
        help="Collect and view usage data locally (no API token required)"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive usage report and save to file"
    )
    
    parser.add_argument(
        "--configure", 
        metavar="TOKEN",
        help="Configure API token for hosted service"
    )
    
    parser.add_argument(
        "--collect",
        choices=["cursor", "claude", "both"],
        help="Collect usage data and send to hosted service"
    )
    
    parser.add_argument(
        "--api-url",
        default=os.getenv("DJANGO_API_URL", "https://your-django-app.com"),
        help="Django server URL (default: from DJANGO_API_URL env var)"
    )
    
    parser.add_argument(
        "--token",
        help="API token (overrides saved token)"
    )
    
    args = parser.parse_args()
    
    # Generate comprehensive report
    if args.report:
        print("📊 Generating comprehensive usage report...")
        report = generate_usage_report()
        report_path = save_report(report)
        if report_path:
            print(f"✅ Report generated successfully: {report_path}")
            return 0
        else:
            print("❌ Failed to generate report")
            return 1
    
    # Local mode (no API token required)
    if args.local:
        try:
            success = asyncio.run(collect_usage_local(args.local))
            return 0 if success else 1
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    # Configure token
    if args.configure:
        save_api_token(args.configure)
        print("API token configured successfully")
        return 0
    
    # Collect usage data (requires API token)
    if args.collect:
        # Get API token
        api_token = args.token or load_api_token()
        if not api_token:
            print("Error: No API token found.")
            print("Configure with: python cli.py --configure YOUR_TOKEN")
            print("Or set AI_USAGE_TRACKER_TOKEN environment variable")
            print("Or use --local to view data without sending to API")
            return 1
        
        # Run collection
        try:
            success = asyncio.run(collect_usage(args.collect, api_token, args.api_url))
            if success:
                print(f"Successfully collected {args.collect} usage data")
                return 0
            else:
                print(f"Failed to collect {args.collect} usage data")
                return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 1
    
    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())