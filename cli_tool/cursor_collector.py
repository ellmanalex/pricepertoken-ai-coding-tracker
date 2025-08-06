#!/usr/bin/env python3

import sqlite3
import jwt
import time
import os
import json
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import csv
from io import StringIO


def get_current_billing_period(anchor: datetime, now: datetime = None):
    now = now or datetime.now(timezone.utc)

    period_start = anchor
    while True:
        if period_start.month == 12:
            next_month = 1
            year = period_start.year + 1
        else:
            next_month = period_start.month + 1
            year = period_start.year
        
        period_end = period_start.replace(year=year, month=next_month)

        if period_start <= now < period_end:
            return period_start, period_end
        period_start = period_end


def should_fetch_usage(last_fetch_time: float, min_interval_seconds: int = 300) -> bool:
    """
    Check if enough time has passed since last fetch.
    
    Args:
        last_fetch_time: Timestamp of last fetch
        min_interval_seconds: Minimum seconds between fetches (default 5 minutes)
        
    Returns:
        True if should fetch, False if should skip
    """
    return (time.time() - last_fetch_time) > min_interval_seconds


class CursorCollector:
    """
    Collects usage data from Cursor IDE using the CSV export API.
    
    This class handles:
    - Reading Cursor's local SQLite database
    - Extracting authentication tokens
    - Fetching usage data from Cursor's CSV export API
    - Parsing CSV data into structured format
    - Automatic fetching every 5 minutes with local state tracking
    """
    
    def __init__(self):
        """Initialize the Cursor collector"""
        self.state_file = Path.home() / ".ai-usage-tracker" / "state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_database_path(self) -> Path:
        """Get platform-specific path to Cursor's SQLite database"""
        home = Path.home()
        
        # Use platform module for better OS detection
        import platform
        system = platform.system().lower()
        
        if system == 'darwin':  # macOS
            return home / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
        elif system == 'windows':  # Windows
            return home / "AppData/Roaming/Cursor/User/globalStorage/state.vscdb"
        else:  # Linux and others
            return home / ".config/Cursor/User/globalStorage/state.vscdb"
    
    def load_state(self) -> Dict[str, Any]:
        """Load local state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading state: {e}")
        return {
            "last_cursor_fetch": 0,
            "last_sent_summary": {},
            "billing_anchor_date": "2024-09-28"  # Default anchor date
        }
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save local state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving state: {e}")
    
    def get_current_month_period(self) -> tuple[datetime, datetime]:
        """Get current month period (1st of month to now)"""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start_of_month, now
    
    def calculate_billing_period_usage(self, usage_events: list, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """
        Calculate usage metrics for the current billing period.
        
        Args:
            usage_events: List of usage events
            period_start: Start of billing period
            period_end: End of billing period
            
        Returns:
            Dictionary with billing period usage summary
        """
        period_events = []
        model_usage = {}
        total_requests = 0
        total_tokens = 0
        total_cost = 0.0
        
        for event in usage_events:
            try:
                # Parse event date
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                
                # Check if event is within billing period
                if period_start <= event_date <= period_end:
                    period_events.append(event)
                    total_requests += 1
                    total_tokens += event['total_tokens']
                    total_cost += event['cost']
                    
                    # Track model usage
                    model = event['model']
                    if model not in model_usage:
                        model_usage[model] = {
                            'requests': 0,
                            'tokens': 0,
                            'cost': 0.0
                        }
                    model_usage[model]['requests'] += 1
                    model_usage[model]['tokens'] += event['total_tokens']
                    model_usage[model]['cost'] += event['cost']
                    
            except Exception as e:
                print(f"⚠️  Error processing event: {e}")
                continue
        
        return {
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'model_usage': model_usage,
            'events_count': len(period_events)
        }
    
    def display_billing_period_summary(self, billing_summary: Dict[str, Any]) -> None:
        """Display billing period usage summary in terminal"""
        print("\n" + "="*60)
        print("📊 CURSOR USAGE - CURRENT MONTH")
        print("="*60)
        
        period_start = datetime.fromisoformat(billing_summary['period_start'])
        period_end = datetime.fromisoformat(billing_summary['period_end'])
        
        print(f"📅 Current Month: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
        print(f"📈 Total Requests: {billing_summary['total_requests']:,}")
        print(f"🔢 Total Tokens: {billing_summary['total_tokens']:,}")
        print(f"💰 Total Cost: ${billing_summary['total_cost']:.4f}")
        
        if billing_summary['model_usage']:
            print(f"\n🤖 Model Usage Breakdown:")
            for model, stats in billing_summary['model_usage'].items():
                print(f"   • {model}:")
                print(f"     - Requests: {stats['requests']:,}")
                print(f"     - Tokens: {stats['tokens']:,}")
                print(f"     - Cost: ${stats['cost']:.4f}")
        
        print("="*60)
    
    async def fetch_usage_with_interval_check(self, force_fetch: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch usage data with automatic interval checking.
        
        Args:
            force_fetch: Force fetch even if interval hasn't passed
            
        Returns:
            Usage data or None if skipped
        """
        state = self.load_state()
        current_time = time.time()
        
        # Check if we should fetch
        if not force_fetch and not should_fetch_usage(state['last_cursor_fetch']):
            time_since_last = current_time - state['last_cursor_fetch']
            minutes_since = int(time_since_last / 60)
            print(f"⏰ Last fetch was {minutes_since} minutes ago. Skipping... (fetch every 5 minutes)")
            return None
        

        
        # Get current month period
        period_start, period_end = self.get_current_month_period()
        
        # Fetch usage data
        usage_data = await self.collect_usage()
        if not usage_data:
            return None
        
        # Calculate billing period usage
        billing_summary = self.calculate_billing_period_usage(
            usage_data['usage_events'], 
            period_start, 
            period_end
        )
        
        # Display summary
        self.display_billing_period_summary(billing_summary)
        
        # Update state
        state['last_cursor_fetch'] = current_time
        state['last_sent_summary'] = billing_summary
        self.save_state(state)
        
        # Add billing summary to usage data
        usage_data['billing_period_summary'] = billing_summary
        
        return usage_data
    
    def get_session_token(self) -> Optional[str]:
        """
        Get Cursor session token from local database.
        
        Returns:
            Session token string or None if not found
        """
        db_path = self.get_database_path()
        
        if not db_path.exists():
            print(f"❌ Cursor database not found at {db_path}")
            return None
        
        try:
            # Connect to database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get the access token
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken'")
            result = cursor.fetchone()
            
            if not result:
                print("❌ No Cursor API token found in database")
                conn.close()
                return None
            
            access_token = result[0]
            
            # Get user email for display
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'")
            email_result = cursor.fetchone()
            user_email = email_result[0] if email_result else "unknown"
            
            conn.close()
            
            # Create session token (like Cursor's TypeScript code)
            try:
                decoded = jwt.decode(access_token, options={"verify_signature": False})
                user_id = decoded.get('sub', '').split('|')[1] if 'sub' in decoded else 'unknown'
                session_token = f"{user_id}%3A%3A{access_token}"
                return session_token
                
            except Exception as e:
                print(f"❌ Error processing token: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Error reading Cursor database: {e}")
            return None
    
    def get_first_session_date(self) -> Optional[str]:
        """
        Get the first session date from Cursor database.
        
        Returns:
            First session date string or None if not found
        """
        db_path = self.get_database_path()
        
        if not db_path.exists():
            return None
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get the first session date
            cursor.execute("SELECT *, CAST(value AS TEXT) FROM ItemTable WHERE key = 'telemetry.firstSessionDate'")
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                first_session_date = result[1]  # The value column
                return first_session_date
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error reading first session date: {e}")
            return None
    
    async def fetch_csv_export(self, session_token: str, start_date: str = None, end_date: str = None) -> str:
        """
        Fetch CSV export from Cursor's API.
        
        Args:
            session_token: Cursor session token
            start_date: Start date in milliseconds timestamp (optional)
            end_date: End date in milliseconds timestamp (optional)
            
        Returns:
            CSV content as string
        """
        # If no dates provided, use ALL available data (from first session to now)
        if not start_date or not end_date:
            # Get first session date for start
            first_session_date = self.get_first_session_date()
            if first_session_date:
                # Parse first session date
                try:
                    first_date = datetime.strptime(first_session_date, "%Y-%m-%d")
                    start_date = str(int(first_date.timestamp() * 1000))
                except:
                    # Fallback to 1 year ago if parsing fails
                    one_year_ago = datetime.now() - timedelta(days=365)
                    start_date = str(int(one_year_ago.timestamp() * 1000))
            else:
                # Fallback to 1 year ago if no first session date
                one_year_ago = datetime.now() - timedelta(days=365)
                start_date = str(int(one_year_ago.timestamp() * 1000))
            
            # End date is now
            end_date = str(int(datetime.now().timestamp() * 1000))
        
        url = f"https://cursor.com/api/dashboard/export-usage-events-csv?startDate={start_date}&endDate={end_date}&showTokenView=true"
        
        headers = {
            "Cookie": f"WorkosCursorSessionToken={session_token}",
            "Accept": "text/csv,application/csv"
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for large data
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Get the CSV content
                csv_content = response.text
                
                return csv_content
                
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                print("❌ Unauthorized - Invalid session token")
            elif e.response.status_code == 403:
                print("❌ Forbidden - Token may be expired or insufficient permissions")
            elif e.response.status_code == 500:
                print("❌ Server error - Cursor API is down")
        except Exception as e:
            print(f"Unexpected error: {e}")

        return ""
    
    def parse_csv_data(self, csv_content: str) -> dict:
        """
        Parse CSV content from Cursor API.
        
        Args:
            csv_content: Raw CSV content from Cursor API
            
        Returns:
            Dictionary with parsed usage data
        """
        import csv
        from io import StringIO
        
        f = StringIO(csv_content)
        reader = csv.DictReader(f)
        usage_events = []
        total_tokens = 0
        total_cost = 0.0

        for row in reader:
            try:
                # Parse and clean up each field
                date = row.get('Date', '').strip('"')
                user = row.get('User', '').strip('"')
                kind = row.get('Kind', '').strip('"')
                model = row.get('Model', '').strip('"')
                input_with_cache = int(row.get('Input (w/ Cache Write)', 0))
                input_without_cache = int(row.get('Input (w/o Cache Write)', 0))
                cache_read = int(row.get('Cache Read', 0))
                output = int(row.get('Output', 0))
                total_tokens_event = int(row.get('Total Tokens', 0))
                cost_str = row.get('Cost ($)', '').strip('"')

                # Determine if cost is included in subscription
                included_in_subscription = cost_str in ("Included", "0", "")

                cost = 0.0
                if not included_in_subscription:
                    try:
                        cost = float(cost_str.replace('$', ''))
                    except ValueError:
                        cost = 0.0

                usage_event = {
                    "date": date,
                    "user": user,
                    "kind": kind,
                    "model": model,
                    "input_with_cache": input_with_cache,
                    "input_without_cache": input_without_cache,
                    "cache_read": cache_read,
                    "output": output,
                    "total_tokens": total_tokens_event,
                    "cost": cost,
                    "included_in_subscription": included_in_subscription
                }

                usage_events.append(usage_event)
                total_tokens += total_tokens_event
                total_cost += cost

            except Exception as e:
                continue

        return {
            "usage_events": usage_events,
            "summary": {
                "total_events": len(usage_events),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "models_used": list(set(event["model"] for event in usage_events)),
                "kind": list(set(event["kind"] for event in usage_events if event["kind"])),
                "date_range": {
                    "start": usage_events[0]["date"] if usage_events else None,
                    "end": usage_events[-1]["date"] if usage_events else None
                }
            },
            "raw_csv": csv_content
        }
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for tracking"""
        import hashlib
        import uuid
        session_data = f"{time.time()}{uuid.uuid4()}"
        return hashlib.md5(session_data.encode()).hexdigest()
    
    async def collect_usage(self) -> Optional[Dict[str, Any]]:
        """
        Collect Cursor usage data using CSV export API.
        
        Returns:
            Complete usage data dictionary or None if failed
        """
        # Get session token from database (fresh each time, no storage)
        session_token = self.get_session_token()
        if not session_token:
            print("❌ Failed to get session token")
            return None
        
        # Get first session date
        first_session_date = self.get_first_session_date()
        
        # Fetch CSV usage data from Cursor API
        csv_content = await self.fetch_csv_export(session_token)
        
        if csv_content:
            # Parse the CSV data
            parsed_data = self.parse_csv_data(csv_content)
            
            if parsed_data and parsed_data.get('usage_events'):
                # Return the complete data
                complete_data = {
                    "tool": "cursor",
                    "timestamp": int(time.time()),
                    "session_id": self._generate_session_id(),
                    
                    # Parsed CSV data
                    "usage_events": parsed_data['usage_events'],
                    "summary": parsed_data['summary'],
                    
                    # Raw data for debugging
                    "raw_csv": parsed_data['raw_csv'],
                    
                    # Metadata
                    "metadata": {
                        "data_collection_method": "cursor_csv_export",
                        "api_endpoint": "/api/dashboard/export-usage-events-csv",
                        "csv_columns": ["Date", "User", "Kind", "Model", "Input (w/ Cache Write)", "Input (w/o Cache Write)", "Cache Read", "Output", "Total Tokens", "Cost ($)"],
                        "first_session_date": first_session_date
                    }
                }
                
                return complete_data
            else:
                print("❌ No usage events found in CSV data")
                return None
        else:
            print("❌ Failed to fetch CSV data from Cursor API")
            return None


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        collector = CursorCollector()
        
        # Use the new interval-checking method
        data = await collector.fetch_usage_with_interval_check(force_fetch=True)
        
        if data:
            print("✅ Cursor data collected successfully!")
            print(f"📊 Summary: {data['summary']['total_events']} events, {data['summary']['total_tokens']:,} tokens")
            
            # Show billing period summary if available
            if 'billing_period_summary' in data:
                print(f"💰 Billing Period Cost: ${data['billing_period_summary']['total_cost']:.4f}")
        else:
            print("❌ Failed to collect Cursor data or skipped due to interval")
    
    asyncio.run(main())
