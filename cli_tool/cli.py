#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
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


async def run_local_mode():
    """Run continuous monitoring in local mode (no API)"""
    collector = UsageCollector()
    print("🚀 Starting AI Usage Tracker in LOCAL mode")
    print("📊 Data will be displayed locally only (no API calls)")
    print("💡 Press Ctrl+C to stop")
    print("=" * 60)
    
    await collector.run_continuous_monitoring(send_to_api=False)


async def run_live_mode():
    """Run continuous monitoring in live mode (with API)"""
    # Check for API token
    api_token = load_api_token()
    if not api_token:
        print("❌ No API token found!")
        print("💡 To use live mode, you need to configure your API token:")
        print("   1. Register at your Django dashboard")
        print("   2. Get your API token from the dashboard")
        print("   3. Set it with: export AI_USAGE_TRACKER_TOKEN=your_token")
        print("   4. Or save it with: pricepertoken-ai-coding-tracker --configure your_token")
        return
    
    django_url = os.getenv("DJANGO_API_URL", "https://your-django-app.com")
    collector = UsageCollector(api_token, django_url)
    
    print("🚀 Starting AI Usage Tracker in LIVE mode")
    print("📊 Data will be sent to your dashboard")
    print(f"🌐 Dashboard URL: {django_url}")
    print("💡 Press Ctrl+C to stop")
    print("=" * 60)
    
    await collector.run_continuous_monitoring(send_to_api=True)


def main():
    parser = argparse.ArgumentParser(
        description="AI Usage Tracker CLI - Monitor Cursor and Claude usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  --local    Run continuous monitoring locally (no API calls)
  --live     Run continuous monitoring and send data to dashboard

Examples:
  %(prog)s --local                    # Monitor locally only
  %(prog)s --live                     # Monitor and send to dashboard
  %(prog)s --configure YOUR_TOKEN     # Save API token for live mode

Getting Started:
  1. Try local mode: %(prog)s --local
  2. For live mode, get API token from your dashboard
  3. Configure: %(prog)s --configure YOUR_TOKEN
  4. Run live: %(prog)s --live
        """
    )
    
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run continuous monitoring locally (no API calls)"
    )
    
    parser.add_argument(
        "--live", 
        action="store_true",
        help="Run continuous monitoring and send data to dashboard"
    )
    
    parser.add_argument(
        "--configure",
        metavar="TOKEN",
        help="Save API token for live mode"
    )
    
    args = parser.parse_args()
    
    # Handle configure command
    if args.configure:
        save_api_token(args.configure)
        print("✅ API token saved! You can now use --live mode")
        return
    
    # Check if any mode was specified
    if not args.local and not args.live:
        parser.print_help()
        return
    
    # Run the appropriate mode
    try:
        if args.local:
            asyncio.run(run_local_mode())
        elif args.live:
            asyncio.run(run_live_mode())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()