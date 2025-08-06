#!/usr/bin/env python3

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
    
    def __init__(self, jwt_token: str = "", django_url: str = "https://api.pricepertoken.com"):
        """
        Initialize the usage collector.
        
        Args:
            jwt_token: User's JWT token for authentication (can be empty for local mode)
            django_url: URL of the Django server
        """
        self.jwt_token = jwt_token
        self.django_url = django_url
        
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
    
    def aggregate_cursor_data_for_api(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate Cursor usage data by date, model, kind, and included_in_subscription for API transmission.
        """
        usage_events = usage_data.get('usage_events', [])
        daily_aggregates = {}
        
        for event in usage_events:
            # Parse date to get just the date part
            from datetime import datetime
            try:
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
                date_key = event_date.isoformat()
            except:
                # Fallback if date parsing fails
                date_key = event['date'].split('T')[0] if 'T' in event['date'] else event['date']
            
            model = event.get('model', 'unknown')
            kind = event.get('kind', 'unknown')
            included_in_subscription = event.get('included_in_subscription', False)
            
            # Create unique key for date + model + kind + included_in_subscription
            aggregate_key = f"{date_key}_{model}_{kind}_{included_in_subscription}"
            
            # Initialize entry if not exists
            if aggregate_key not in daily_aggregates:
                daily_aggregates[aggregate_key] = {
                    'date': date_key,
                    'model': model,
                    'kind': kind,
                    'input_with_cache': 0,
                    'input_without_cache': 0,
                    'cache_read': 0,
                    'output': 0,
                    'total_tokens': 0,
                    'cost': 0.0,
                    'requests': 0,
                    'included_in_subscription': included_in_subscription
                }
            
            # Aggregate metrics
            daily_aggregates[aggregate_key]['input_with_cache'] += event.get('input_with_cache', 0)
            daily_aggregates[aggregate_key]['input_without_cache'] += event.get('input_without_cache', 0)
            daily_aggregates[aggregate_key]['cache_read'] += event.get('cache_read', 0)
            daily_aggregates[aggregate_key]['output'] += event.get('output', 0)
            daily_aggregates[aggregate_key]['total_tokens'] += event.get('total_tokens', 0)
            daily_aggregates[aggregate_key]['cost'] += event.get('cost', 0)
            daily_aggregates[aggregate_key]['requests'] += 1
        
        # Convert to list format for API
        daily_data = list(daily_aggregates.values())
        
        return {
            'tool': 'cursor',
            'daily_aggregates': daily_data,
            'collection_info': usage_data.get('collection_info', {}),
            'metadata': usage_data.get('metadata', {})
        }
    
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
    
    def aggregate_claude_data_for_api(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate Claude usage data by date and model for API transmission.
        """
        daily_data = usage_data.get('daily', [])
        daily_aggregates = []
        
        for day_entry in daily_data:
            if not isinstance(day_entry, dict):
                continue
                
            date = day_entry.get('date')
            model_breakdowns = day_entry.get('modelBreakdowns', [])
            
            # Aggregate by model for this day
            model_aggregates = {}
            
            for breakdown in model_breakdowns:
                if not isinstance(breakdown, dict):
                    continue
                    
                model_name = breakdown.get('modelName', 'unknown')
                
                if model_name not in model_aggregates:
                    model_aggregates[model_name] = {
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'cache_creation_tokens': 0,
                        'cache_read_tokens': 0,
                        'total_tokens': 0,
                        'cost': 0.0
                    }
                
                # Aggregate metrics for this model
                model_aggregates[model_name]['input_tokens'] += breakdown.get('inputTokens', 0)
                model_aggregates[model_name]['output_tokens'] += breakdown.get('outputTokens', 0)
                model_aggregates[model_name]['cache_creation_tokens'] += breakdown.get('cacheCreationTokens', 0)
                model_aggregates[model_name]['cache_read_tokens'] += breakdown.get('cacheReadTokens', 0)
                model_aggregates[model_name]['total_tokens'] += breakdown.get('totalTokens', 0)
                model_aggregates[model_name]['cost'] += breakdown.get('cost', 0)
            
            # Convert to list format for API
            for model_name, metrics in model_aggregates.items():
                daily_aggregates.append({
                    'date': date,
                    'model': model_name,
                    **metrics
                })
        
        return {
            'tool': 'claude',
            'daily_aggregates': daily_aggregates,
            'totals': usage_data.get('totals', {}),
            'collection_info': usage_data.get('collection_info', {}),
            'metadata': usage_data.get('metadata', {})
        }
    
    
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
                # TODO check if this is working
                # Fallback to totals if no model breakdown available
                model_name = "claude-sonnet-4-20250514 fallback"
                print(f"{'Claude':<12} {model_name:<30} {tokens:>14,} ${cost:>8.4f}")
        
        # Total row
        print("-" * 80)
        print(f"{'TOTAL':<12} {'':<30} {total_tokens:>14,} ${total_cost:>8.4f}")
        print("=" * 80)
    
    async def send_to_django(self, usage_data: Dict[str, Any]) -> bool:
        """
        Send usage data to Django server with JWT authentication.
        
        Args:
            usage_data: Usage data dictionary to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.jwt_token:
            print("❌ No JWT token configured - cannot send to dashboard")
            print("   Configure with: pricepertoken-ai-coding-tracker --configure <token>")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
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
                    f"{self.django_url}/api/coding-tracker/usage/collect/",
                    headers=headers,
                    json=usage_data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    message = response_data.get('message', 'Usage data sent successfully')
                    print(f"✅ {message}")
                    return True
                elif response.status_code == 401:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', 'Invalid JWT token')
                        print(f"❌ Authentication failed: {detail}")
                        print("   Please refresh your token from the web interface")
                    except:
                        print("❌ Invalid JWT token. Please refresh your token from the web interface")
                    return False
                elif response.status_code == 429:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', 'Rate limit exceeded')
                        print(f"⚠️  {detail}")
                    except:
                        print("⚠️  Rate limit exceeded. Please try again later.")
                    return False
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Validation error')
                        print(f"❌ Validation error: {error_msg}")
                    except:
                        print("❌ Bad request - invalid data format")
                    return False
                elif response.status_code == 413:
                    print("⚠️  Data too large. Try reducing the date range.")
                    return False
                else:
                    print(f"❌ Failed to send usage data: HTTP {response.status_code}")
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            print(f"   Error: {error_data['error']}")
                        elif 'detail' in error_data:
                            print(f"   Detail: {error_data['detail']}")
                    except:
                        print(f"   Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending usage data: {e}")
            return False
    
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
                print("\nNOTE: If Claude Code costs reflect your total token value.")
                print("\nIf you are using Claude Code through a subscription your tokens are included")
                print("\nYour Cursor costs reflect overage charges (pay for useage over your subscription amount)")
                if send_to_api:
                    print("\n📤 Sending complete usage data to dashboard...")
                    if results['cursor']:
                        # Aggregate Cursor data for API transmission
                        aggregated_cursor = self.aggregate_cursor_data_for_api(results['cursor'])
                        await self.send_to_django(aggregated_cursor)
                    if results['claude']:
                        # Aggregate Claude data for API transmission
                        aggregated_claude = self.aggregate_claude_data_for_api(results['claude'])
                        await self.send_to_django(aggregated_claude)
                
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
        await collector.run_continuous_monitoring(send_to_api=True)
    
    asyncio.run(main())