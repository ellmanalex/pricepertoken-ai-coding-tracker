#!/usr/bin/env python3

import subprocess
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime


class ClaudeCodeCollector:
    """
    Collects usage data from Claude Code using the ccusage CLI tool.
    
    This class handles:
    - Running the ccusage command to get usage data
    - Parsing the JSON output from ccusage
    - Structuring the data for the AI usage tracker
    """
    
    def __init__(self):
        """Initialize the Claude Code collector"""
        pass
    
    def run_ccusage_command(self, command: str = "daily", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Run ccusage command and get JSON output.
        
        Args:
            command: ccusage command (daily, monthly, session, blocks)
            **kwargs: Additional options like --since, --until, --json, etc.
            
        Returns:
            JSON data from ccusage or None if failed
        """
        try:
            # Build the command
            cmd = ["ccusage", command, "--json"]
            
            # Add date filters if provided
            if kwargs.get('since'):
                cmd.extend(["--since", kwargs['since']])
            if kwargs.get('until'):
                cmd.extend(["--until", kwargs['until']])
            
            # Add other options
            if kwargs.get('breakdown'):
                cmd.append("--breakdown")
            if kwargs.get('timezone'):
                cmd.extend(["--timezone", kwargs['timezone']])
            
            print(f"🔍 Running: {' '.join(cmd)}")
            
            # Run the command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                check=True,
                timeout=30
            )
            
            print(f"✅ ccusage command completed successfully")
            
            # Parse JSON output
            usage_data = json.loads(result.stdout)
            return usage_data
            
        except subprocess.CalledProcessError as e:
            print(f"❌ ccusage command failed: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
            return None
        except FileNotFoundError:
            print("❌ ccusage command not found")
            print("💡 Install with: npm install -g ccusage")
            print("💡 Or run with: npx ccusage@latest")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse ccusage JSON output: {e}")
            return None
        except subprocess.TimeoutExpired:
            print("❌ ccusage command timed out after 30 seconds")
            return None
        except Exception as e:
            print(f"❌ Unexpected error running ccusage: {e}")
            return None
    
    def collect_usage(self) -> Optional[Dict[str, Any]]:
        """
        Collect Claude Code usage data for current month.
        
        Returns:
            Complete usage data dictionary or None if failed
        """
        print("🔍 Collecting Claude Code usage data...")
        
        # Get current month in YYYYMMDD format
        now = datetime.now()
        start_of_month = now.replace(day=1)
        
        # Format dates for ccusage
        since_date = start_of_month.strftime("%Y%m%d")
        until_date = now.strftime("%Y%m%d")
        
        # Get daily usage with breakdown
        usage_data = self.run_ccusage_command(
            "daily",
            since=since_date,
            until=until_date,
            breakdown=True,
            timezone="UTC"
        )
        
        if usage_data:
            # Add metadata
            usage_data["metadata"] = {
                "data_collection_method": "claude_ccusage_cli",
                "command_used": f"ccusage daily --since {since_date} --until {until_date} --breakdown --json",
                "collection_timestamp": time.time()
            }
            
            return usage_data
        
        return None
    
    def collect_monthly_usage(self) -> Optional[Dict[str, Any]]:
        """
        Collect Claude Code monthly usage data.
        
        Returns:
            Monthly usage data dictionary or None if failed
        """
        print("🔍 Collecting Claude Code monthly usage data...")
        
        # Get monthly usage
        usage_data = self.run_ccusage_command(
            "monthly",
            breakdown=True,
            timezone="UTC"
        )
        
        if usage_data:
            # Add metadata
            usage_data["metadata"] = {
                "data_collection_method": "claude_ccusage_cli_monthly",
                "command_used": "ccusage monthly --breakdown --json",
                "collection_timestamp": time.time()
            }
            
            return usage_data
        
        return None
    
    def get_usage_summary(self, usage_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of usage data.
        """
        if not usage_data:
            return "No usage data available"
        
        summary_parts = []
        summary_parts.append(f"📊 Claude Code Usage Summary:")
        
        # Handle different possible data structures
        if isinstance(usage_data, list):
            # If it's a list of daily data
            total_cost = 0.0
            total_input_tokens = 0
            total_output_tokens = 0
            total_requests = 0
            
            for day_data in usage_data:
                if isinstance(day_data, dict):
                    total_cost += day_data.get('totalCost', 0)
                    total_input_tokens += day_data.get('totalInputTokens', 0)
                    total_output_tokens += day_data.get('totalOutputTokens', 0)
                    total_requests += day_data.get('totalRequests', 0)
            
            summary_parts.append(f"   • Total Requests: {total_requests:,}")
            summary_parts.append(f"   • Total Input Tokens: {total_input_tokens:,}")
            summary_parts.append(f"   • Total Output Tokens: {total_output_tokens:,}")
            summary_parts.append(f"   • Total Cost: ${total_cost:.4f}")
            
            # Show model breakdown if available
            if usage_data and isinstance(usage_data[0], dict) and 'modelBreakdown' in usage_data[0]:
                summary_parts.append(f"\n🤖 Model Usage:")
                for model, stats in usage_data[0]['modelBreakdown'].items():
                    summary_parts.append(f"   • {model}: {stats['requests']:,} requests, ${stats['cost']:.4f}")
        
        elif isinstance(usage_data, dict):
            # Handle ccusage output structure
            if 'totals' in usage_data:
                totals = usage_data['totals']
                summary_parts.append(f"   • Total Input Tokens: {totals.get('inputTokens', 0):,}")
                summary_parts.append(f"   • Total Output Tokens: {totals.get('outputTokens', 0):,}")
                summary_parts.append(f"   • Total Tokens: {totals.get('totalTokens', 0):,}")
                summary_parts.append(f"   • Total Cost: ${totals.get('totalCost', 0):.4f}")
            
            # Show daily breakdown if available
            if 'daily' in usage_data and usage_data['daily']:
                daily_data = usage_data['daily']
                if isinstance(daily_data, list) and len(daily_data) > 0:
                    summary_parts.append(f"\n📅 Daily Usage (Last {len(daily_data)} days):")
                    for day in daily_data[-3:]:  # Show last 3 days
                        if isinstance(day, dict):
                            date = day.get('date', 'Unknown')
                            input_tokens = day.get('inputTokens', 0)
                            output_tokens = day.get('outputTokens', 0)
                            cost = day.get('totalCost', 0)
                            summary_parts.append(f"   • {date}: {input_tokens:,} input + {output_tokens:,} output tokens, ${cost:.4f}")
            
            # Show model breakdown if available
            if 'daily' in usage_data and usage_data['daily']:
                daily_data = usage_data['daily']
                if isinstance(daily_data, list) and len(daily_data) > 0:
                    # Look for model breakdown in the most recent day
                    latest_day = daily_data[-1]
                    if isinstance(latest_day, dict) and 'modelBreakdowns' in latest_day:
                        summary_parts.append(f"\n🤖 Model Usage:")
                        for model_breakdown in latest_day['modelBreakdowns']:
                            if isinstance(model_breakdown, dict):
                                model_name = model_breakdown.get('modelName', 'Unknown')
                                input_tokens = model_breakdown.get('inputTokens', 0)
                                output_tokens = model_breakdown.get('outputTokens', 0)
                                cost = model_breakdown.get('cost', 0)
                                summary_parts.append(f"   • {model_name}: {input_tokens:,} input + {output_tokens:,} output tokens, ${cost:.4f}")
        
        else:
            # Fallback for unexpected data types
            summary_parts.append(f"   • Data Type: {type(usage_data).__name__}")
            summary_parts.append(f"   • Raw Data: {str(usage_data)[:200]}...")
        
        return "\n".join(summary_parts)
    
    def get_monthly_usage_summary(self, usage_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of monthly usage data.
        """
        if not usage_data:
            return "No monthly usage data available"
        
        summary_parts = []
        summary_parts.append(f"📊 Claude Code Monthly Usage Summary:")
        
        # Handle monthly data structure
        if isinstance(usage_data, dict):
            if 'months' in usage_data:
                months_data = usage_data['months']
                if isinstance(months_data, list) and len(months_data) > 0:
                    # Show current month and total
                    current_month = months_data[-1] if months_data else None
                    if current_month and isinstance(current_month, dict):
                        month_name = current_month.get('month', 'Unknown')
                        input_tokens = current_month.get('inputTokens', 0)
                        output_tokens = current_month.get('outputTokens', 0)
                        total_tokens = current_month.get('totalTokens', 0)
                        cost = current_month.get('totalCost', 0)
                        
                        summary_parts.append(f"   • Current Month ({month_name}):")
                        summary_parts.append(f"     - Input Tokens: {input_tokens:,}")
                        summary_parts.append(f"     - Output Tokens: {output_tokens:,}")
                        summary_parts.append(f"     - Total Tokens: {total_tokens:,}")
                        summary_parts.append(f"     - Cost: ${cost:.4f}")
                    
                    # Show total across all months
                    if 'totals' in usage_data:
                        totals = usage_data['totals']
                        total_input = totals.get('inputTokens', 0)
                        total_output = totals.get('outputTokens', 0)
                        total_all = totals.get('totalTokens', 0)
                        total_cost = totals.get('totalCost', 0)
                        
                        summary_parts.append(f"\n   • All Time Totals:")
                        summary_parts.append(f"     - Input Tokens: {total_input:,}")
                        summary_parts.append(f"     - Output Tokens: {total_output:,}")
                        summary_parts.append(f"     - Total Tokens: {total_all:,}")
                        summary_parts.append(f"     - Total Cost: ${total_cost:.4f}")
            
            # Show model breakdown if available
            if 'months' in usage_data and usage_data['months']:
                months_data = usage_data['months']
                if isinstance(months_data, list) and len(months_data) > 0:
                    current_month = months_data[-1]
                    if isinstance(current_month, dict) and 'models' in current_month:
                        summary_parts.append(f"\n🤖 Current Month Models:")
                        for model, stats in current_month['models'].items():
                            if isinstance(stats, dict):
                                input_tokens = stats.get('inputTokens', 0)
                                output_tokens = stats.get('outputTokens', 0)
                                cost = stats.get('cost', 0)
                                summary_parts.append(f"   • {model}: {input_tokens:,} input + {output_tokens:,} output tokens, ${cost:.4f}")
        
        return "\n".join(summary_parts)


# Example usage
if __name__ == "__main__":
    def main():
        collector = ClaudeCodeCollector()
        data = collector.collect_usage()
        
        if data:
            print("✅ Claude Code data collected successfully!")
            print()
            print(collector.get_usage_summary(data))
            print()
            print("📄 Full data structure:")
            print(json.dumps(data, indent=2))
        else:
            print("❌ Failed to collect Claude Code data")
    
    main()
