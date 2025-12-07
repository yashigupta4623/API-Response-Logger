#!/usr/bin/env python3
"""
Log Analyzer - Analyze historical API monitoring logs
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from colorama import init, Fore, Style

init(autoreset=True)

class LogAnalyzer:
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        
    def load_logs(self, api_name: str) -> list:
        """Load logs for a specific API"""
        log_file = self.logs_dir / f"{api_name.replace(' ', '_').lower()}.log"
        
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def calculate_uptime(self, logs: list) -> dict:
        """Calculate uptime percentage"""
        if not logs:
            return {'uptime': 0, 'total_checks': 0, 'up_count': 0, 'down_count': 0}
        
        total = len(logs)
        up_count = sum(1 for log in logs if log['status'] == 'up')
        down_count = sum(1 for log in logs if log['status'] == 'down')
        
        uptime = (up_count / total) * 100 if total > 0 else 0
        
        return {
            'uptime': round(uptime, 2),
            'total_checks': total,
            'up_count': up_count,
            'down_count': down_count
        }
    
    def calculate_avg_response_time(self, logs: list) -> float:
        """Calculate average response time"""
        response_times = [log['response_time'] for log in logs if log.get('response_time')]
        
        if not response_times:
            return 0
        
        return round(sum(response_times) / len(response_times), 2)
    
    def get_incidents(self, logs: list) -> list:
        """Get list of downtime incidents"""
        incidents = []
        
        for log in logs:
            if log['status'] in ['down', 'error']:
                incidents.append({
                    'timestamp': log['timestamp'],
                    'status': log['status'],
                    'error': log.get('error', 'Unknown error')
                })
        
        return incidents
    
    def analyze_api(self, api_name: str):
        """Analyze logs for a specific API"""
        logs = self.load_logs(api_name)
        
        if not logs:
            print(f"{Fore.YELLOW}No logs found for {api_name}")
            return
        
        uptime_stats = self.calculate_uptime(logs)
        avg_response_time = self.calculate_avg_response_time(logs)
        incidents = self.get_incidents(logs)
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}Analysis for: {api_name}")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        print(f"{Fore.GREEN}📊 Uptime Statistics:")
        print(f"   Uptime: {uptime_stats['uptime']}%")
        print(f"   Total Checks: {uptime_stats['total_checks']}")
        print(f"   Successful: {uptime_stats['up_count']}")
        print(f"   Failed: {uptime_stats['down_count']}\n")
        
        print(f"{Fore.GREEN}⚡ Performance:")
        print(f"   Average Response Time: {avg_response_time}ms\n")
        
        if incidents:
            print(f"{Fore.RED}🚨 Recent Incidents ({len(incidents)}):")
            for incident in incidents[-5:]:  # Show last 5 incidents
                print(f"   [{incident['timestamp']}] {incident['status']}: {incident['error']}")
        else:
            print(f"{Fore.GREEN}✅ No incidents recorded!")
        
        print(f"\n{Fore.CYAN}{'='*60}\n")
    
    def analyze_all(self):
        """Analyze all available logs"""
        if not self.logs_dir.exists():
            print(f"{Fore.YELLOW}No logs directory found.")
            return
        
        log_files = list(self.logs_dir.glob("*.log"))
        
        if not log_files:
            print(f"{Fore.YELLOW}No log files found.")
            return
        
        for log_file in log_files:
            api_name = log_file.stem.replace('_', ' ').title()
            self.analyze_api(api_name)

def main():
    import sys
    
    analyzer = LogAnalyzer()
    
    if len(sys.argv) > 1:
        api_name = ' '.join(sys.argv[1:])
        analyzer.analyze_api(api_name)
    else:
        analyzer.analyze_all()

if __name__ == "__main__":
    main()
