#!/usr/bin/env python3

import jwt
import time
import os
import httpx
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cursor_collector import CursorCollector
from claude_code_collector import ClaudeCodeCollector


class UsageCollector:
    """
    Main usage collector that coordinates data collection from multiple sources.
    
    This class handles:
    - Coordinating Cursor and Claude Code data collection
    - Sending data to the FastAPI service
    - Managing authentication and API communication
    - Continuous monitoring with 5-minute intervals
    """
    
    def __init__(self, api_token: str = "", django_url: str = "https://your-django-app.com"):
        """
        Initialize the usage collector.
        
        Args:
            api_token: User's API token for authentication (can be empty for local mode)
            django_url: URL of the Django server
        """
        self.api_token = api_token
        self.django_url = django_url
        
        # Server JWT secret - will be bundled in distributed binaries
        # For development, use environment variable
        self.server_jwt_secret = os.getenv("SERVER_JWT_SECRET", "development-secret-change-in-production")
        
        # Initialize specialized collectors
        self.cursor_collector = CursorCollector()
        self.claude_collector = ClaudeCodeCollector()
        
        # Monitoring state
        self.running = False
        self.interval_seconds = 300  # 5 minutes
    
    async def collect_cursor_usage(self) -> Optional[Dict[str, Any]]:
        """
        Collect Cursor usage data using the specialized CursorCollector.
        Returns the complete month-to-date CSV data.
        
        Returns:
            Complete Cursor usage data dictionary or None if failed
        """
        # Get current month period
        period_start, period_end = self.cursor_collector.get_current_month_period()
        
        # Fetch complete usage data (full month-to-date CSV)
        usage_data = await self.cursor_collector.collect_usage()
        if not usage_data:
            return None
        
        # Calculate billing period usage for display purposes
        billing_summary = self.cursor_collector.calculate_billing_period_usage(
            usage_data['usage_events'], 
            period_start, 
            period_end
        )
        
        # Add billing summary to usage data (for local display)
        usage_data['billing_period_summary'] = billing_summary
        
        # Add metadata for Django
        usage_data['collection_info'] = {
            'tool': 'cursor',
            'data_type': 'month_to_date_csv',
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_events': len(usage_data.get('usage_events', [])),
            'collection_method': 'csv_export_api'
        }
        
        return usage_data
    
    def collect_claude_usage(self) -> Optional[Dict[str, Any]]:
        """
        Collect Claude Code usage data using the specialized ClaudeCodeCollector.
        Returns the complete usage data structure from ccusage.
        
        Returns:
            Complete Claude usage data dictionary or None if failed
        """
        # Get the full usage data from ccusage (daily breakdown for current month)
        usage_data = self.claude_collector.collect_usage()
        if not usage_data:
            return None
        
        # Add collection info for Django
        usage_data['collection_info'] = {
            'tool': 'claude',
            'data_type': 'ccusage_daily_breakdown',
            'has_totals': 'totals' in usage_data,
            'has_daily': 'daily' in usage_data and bool(usage_data['daily']),
            'daily_entries': len(usage_data.get('daily', [])),
            'collection_method': 'ccusage_cli'
        }
        
        return usage_data
    
    def _create_server_jwt(self) -> str:
        """
        Create a short-lived server JWT for origin authentication.
        This proves the request comes from an official CLI binary.
        """
        payload = {
            "iss": "ai-usage-tracker-cli",
            "aud": "django-backend", 
            "version": "1.0.0",
            "iat": int(time.time()),
            "exp": int(time.time()) + 300  # 5 minutes
        }
        
        return jwt.encode(payload, self.server_jwt_secret, algorithm="HS256")
    
    async def collect_both_usage(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Collect usage data from both Cursor and Claude Code.
        
        Returns:
            Dictionary with 'cursor' and 'claude' keys containing respective data
        """
        results = {
            'cursor': None,
            'claude': None
        }
        
        # Collect Cursor data (async)
        try:
            results['cursor'] = await self.collect_cursor_usage()
        except Exception as e:
            print(f"❌ Error collecting Cursor data: {e}")
        
        # Collect Claude data (sync)
        try:
            results['claude'] = self.collect_claude_usage()
        except Exception as e:
            print(f"❌ Error collecting Claude data: {e}")
        
        return results
    
    def display_combined_usage_table(self, cursor_data: Optional[Dict[str, Any]], claude_data: Optional[Dict[str, Any]]) -> None:
        """
        Display a combined usage table for both Cursor and Claude data.
        
        Args:
            cursor_data: Cursor usage data dictionary
            claude_data: Claude usage data dictionary
        """
        print("\n📊 AI Usage Summary - Current Month")
        print("=" * 80)
        
        # Table header
        print(f"{'Provider':<12} {'Model':<30} {'Tokens':<15} {'Cost':<10}")
        print("-" * 80)
        
        total_tokens = 0
        total_cost = 0.0
        
        # Process Cursor data
        if cursor_data and 'billing_period_summary' in cursor_data:
            billing_summary = cursor_data['billing_period_summary']
            model_usage = billing_summary.get('model_usage', {})
            
            for model, stats in model_usage.items():
                tokens = stats.get('tokens', 0)
                cost = stats.get('cost', 0)
                total_tokens += tokens
                total_cost += cost
                
                print(f"{'Cursor':<12} {model:<30} {tokens:>14,} ${cost:>8.4f}")
        
        # Process Claude data
        if claude_data and 'totals' in claude_data:
            totals = claude_data['totals']
            tokens = totals.get('totalTokens', 0)
            cost = totals.get('totalCost', 0)
            total_tokens += tokens
            total_cost += cost
            
            # Get model info from daily data if available
            models_used = set()
            if 'daily' in claude_data and claude_data['daily']:
                for day in claude_data['daily']:
                    if isinstance(day, dict) and 'modelBreakdowns' in day:
                        for breakdown in day['modelBreakdowns']:
                            if isinstance(breakdown, dict) and 'modelName' in breakdown:
                                models_used.add(breakdown['modelName'])
            
            # Display each model or default if none found
            if models_used:
                for model_name in sorted(models_used):
                    # Calculate tokens/cost for this specific model across all days
                    model_tokens = 0
                    model_cost = 0.0
                    
                    for day in claude_data['daily']:
                        if isinstance(day, dict) and 'modelBreakdowns' in day:
                            for breakdown in day['modelBreakdowns']:
                                if isinstance(breakdown, dict) and breakdown.get('modelName') == model_name:
                                    model_tokens += breakdown.get('inputTokens', 0) + breakdown.get('outputTokens', 0)
                                    model_cost += breakdown.get('cost', 0)
                    
                    print(f"{'Claude':<12} {model_name:<30} {model_tokens:>14,} ${model_cost:>8.4f}")
            else:
                # Fallback to totals if no model breakdown available
                model_name = "claude-sonnet-4-20250514"
                print(f"{'Claude':<12} {model_name:<30} {tokens:>14,} ${cost:>8.4f}")
        
        # Total row
        print("-" * 80)
        print(f"{'TOTAL':<12} {'':<30} {total_tokens:>14,} ${total_cost:>8.4f}")
        print("=" * 80)
    
    async def send_to_django(self, usage_data: Dict[str, Any]) -> bool:
        """
        Send usage data to Django server with authentication.
        
        Args:
            usage_data: Usage data dictionary to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_token:
            print("❌ No API token configured - cannot send to dashboard")
            return False
        
        # Create server JWT for origin authentication
        server_jwt = self._create_server_jwt()
        
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
            "X-Tracker-Auth": f"ServerBearer {server_jwt}",
            "User-Agent": "ai-usage-tracker-cli/1.0.0"
        }
        
        try:
            # Log what we're sending (without sensitive data)
            data_info = usage_data.get('collection_info', {})
            tool = data_info.get('tool', 'unknown')
            data_type = data_info.get('data_type', 'unknown')
            
            if tool == 'cursor':
                event_count = data_info.get('total_events', 0)
                print(f"🌐 Sending {tool} data to dashboard ({event_count} events, {data_type})...")
            elif tool == 'claude':
                daily_entries = data_info.get('daily_entries', 0)
                print(f"🌐 Sending {tool} data to dashboard ({daily_entries} daily entries, {data_type})...")
            else:
                print(f"🌐 Sending data to dashboard...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.django_url}/api/usage/collect/",
                    headers=headers,
                    json=usage_data
                )
                
                if response.status_code == 200:
                    print("✅ Usage data sent successfully")
                    return True
                elif response.status_code == 401:
                    print("❌ Invalid API token. Please reconfigure with: ai-usage-tracker --configure YOUR_TOKEN")
                    return False
                elif response.status_code == 429:
                    print("⚠️  Rate limit exceeded. Please try again later.")
                    return False
                elif response.status_code == 413:
                    print("⚠️  Data too large. Try reducing the date range.")
                    return False
                else:
                    print(f"❌ Failed to send usage data: {response.status_code}")
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            print(f"   Error: {error_data['error']}")
                    except:
                        pass
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending usage data: {e}")
            return False
    
    async def collect_and_send_cursor(self) -> bool:
        """
        Collect Cursor usage data and send to Django.
        
        Returns:
            True if successful, False otherwise
        """
        usage_data = await self.collect_cursor_usage()
        if usage_data:
            return await self.send_to_django(usage_data)
        return False
    
    async def collect_and_send_claude(self) -> bool:
        """
        Collect Claude usage data and send to Django.
        
        Returns:
            True if successful, False otherwise
        """
        usage_data = self.collect_claude_usage()
        if usage_data:
            return await self.send_to_django(usage_data)
        return False
    
    async def collect_and_send_both(self) -> bool:
        """
        Collect usage data from both tools and send to Django.
        
        Returns:
            True if both successful, False if either failed
        """
        results = await self.collect_both_usage()
        
        success = True
        if results['cursor']:
            if not await self.send_to_django(results['cursor']):
                success = False
        else:
            success = False
        
        if results['claude']:
            if not await self.send_to_django(results['claude']):
                success = False
        else:
            success = False
        
        return success
    
    async def run_continuous_monitoring(self, send_to_api: bool = False) -> None:
        """
        Run continuous monitoring, collecting data every 5 minutes.
        
        Args:
            send_to_api: Whether to send data to API (if False, just display locally)
        """
        self.running = True
        cycle_count = 0
        
        print("🚀 Starting continuous AI usage monitoring...")
        print(f"📊 Collection interval: {self.interval_seconds} seconds ({self.interval_seconds/60:.1f} minutes)")
        print(f"🌐 Dashboard mode: {'Enabled' if send_to_api else 'Local only'}")
        print("=" * 60)
        
        try:
            while self.running:
                cycle_count += 1
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n🔄 Cycle #{cycle_count} - {current_time}")
                print("-" * 40)
                
                # Collect data from both tools
                # Reset interval check time on first cycle
                if cycle_count == 1:
                    print("🔄 First cycle - resetting interval timers...")
                    # Reset the last fetch time for Cursor to force immediate collection
                    cursor_state = self.cursor_collector.load_state()
                    cursor_state['last_cursor_fetch'] = 0  # Reset to force immediate fetch
                    self.cursor_collector.save_state(cursor_state)
                
                results = await self.collect_both_usage()
                
                # Display combined usage table
                self.display_combined_usage_table(results['cursor'], results['claude'])
                
                # Send to Django if enabled
                if send_to_api:
                    print("\n📤 Sending complete usage data to dashboard...")
                    if results['cursor']:
                        await self.send_to_django(results['cursor'])
                    if results['claude']:
                        await self.send_to_django(results['claude'])
                
                # Show next collection time
                next_collection = time.time() + self.interval_seconds
                next_time = time.strftime("%H:%M:%S", time.localtime(next_collection))
                print(f"\n⏰ Next collection at: {next_time}")
                print("=" * 60)
                
                # Wait for next cycle
                await asyncio.sleep(self.interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.running = False
        except Exception as e:
            print(f"\n❌ Error in monitoring loop: {e}")
            self.running = False
    
    def stop_monitoring(self) -> None:
        """Stop the continuous monitoring"""
        self.running = False


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test continuous monitoring (local mode)
        collector = UsageCollector()
        
        print("🧪 Starting continuous monitoring (local mode)...")
        print("💡 Press Ctrl+C to stop")
        
        # Run continuous monitoring (local mode - no API)
        await collector.run_continuous_monitoring(send_to_api=False)
    
    asyncio.run(main())