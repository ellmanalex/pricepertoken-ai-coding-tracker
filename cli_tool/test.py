#!/usr/bin/env python3

import asyncio
import httpx
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cli_tool.collector import UsageCollector


async def fetch_cursor_csv_export(session_token: str, start_date: str = None, end_date: str = None) -> str:
    """Fetch CSV export from Cursor's API"""
    
    # If no dates provided, use last 30 days
    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Convert to milliseconds timestamp
        start_date = str(int(start_date.timestamp() * 1000))
        end_date = str(int(end_date.timestamp() * 1000))
    
    url = f"https://cursor.com/api/dashboard/export-usage-events-csv?startDate={start_date}&endDate={end_date}&showTokenView=true"
    
    headers = {
        "Cookie": f"WorkosCursorSessionToken={session_token}",
        "Accept": "text/csv,application/csv"
    }

    try:
        print(f"🌐 Fetching CSV from: {url}")
        print(f"📅 Date range: {datetime.fromtimestamp(int(start_date)/1000)} to {datetime.fromtimestamp(int(end_date)/1000)}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Get the CSV content
            csv_content = response.text
            print(f"✅ CSV downloaded successfully ({len(csv_content)} characters)")
            
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


def save_csv_to_file(csv_content: str, filename: str = None) -> str:
    """Save CSV content to a file in the same directory as the script"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cursor_usage_last_30_days_{timestamp}.csv"
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    file_path = script_dir / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print(f"💾 CSV saved to: {file_path}")
        return str(file_path)
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return ""


async def get_cursor_session_token() -> str:
    """Get Cursor session token from database"""
    from cli_tool.cursor_collector import CursorCollector
    
    cursor_collector = CursorCollector()
    db_path = cursor_collector.get_database_path()
    
    if not db_path.exists():
        print(f"❌ Cursor database not found at {db_path}")
        return None
    
    try:
        import sqlite3
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
        print(f"🔑 Found Cursor API token: {access_token[:20]}...")
        
        # Get user email
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'")
        email_result = cursor.fetchone()
        user_email = email_result[0] if email_result else "unknown"
        
        conn.close()
        
        # Create session token
        import jwt
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        user_id = decoded.get('sub', '').split('|')[1] if 'sub' in decoded else 'unknown'
        session_token = f"{user_id}%3A%3A{access_token}"
        print(f"🔗 Created session token for user: {user_email}")
        
        return session_token
        
    except Exception as e:
        print(f"❌ Error getting session token: {e}")
        return None


async def main():
    """Main function to test CSV export for last 30 days"""
    print("🚀 Testing Cursor CSV Export - Last 30 Days")
    print("=" * 60)
    
    # Get session token
    session_token = await get_cursor_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return
    
    # Calculate last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    # Fetch CSV data for last 30 days
    csv_content = await fetch_cursor_csv_export(session_token)
    
    if csv_content:
        # Save to file in script directory
        filename = f"cursor_usage_last_30_days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = save_csv_to_file(csv_content, filename)
        
        if file_path:
            # Show summary of the data
            lines = csv_content.split('\n')
            if len(lines) > 1:  # Has header + data
                data_lines = lines[1:]  # Skip header
                print(f"\n📊 Data Summary:")
                print(f"   • Total rows: {len(data_lines)}")
                print(f"   • File size: {len(csv_content)} characters")
                
                # Show first few lines as preview
                print(f"\n📄 CSV Preview (first 5 lines):")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}: {line}")
                
                if len(lines) > 5:
                    print(f"  ... and {len(lines) - 5} more lines")
                
                print(f"\n✅ Successfully saved last 30 days of Cursor usage to: {file_path}")
            else:
                print("⚠️  CSV file is empty or has no data rows")
        else:
            print("❌ Failed to save CSV file")
    else:
        print("❌ Failed to get CSV data")


if __name__ == "__main__":
    asyncio.run(main())
