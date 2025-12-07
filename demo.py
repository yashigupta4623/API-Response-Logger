#!/usr/bin/env python3
"""
Quick demo of API Response Logger
Runs a few checks and shows the analysis
"""

import time
from monitor import APIMonitor
from analyzer import LogAnalyzer
from colorama import Fore

def main():
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}API Response Logger - Quick Demo")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    # Initialize monitor
    monitor = APIMonitor()
    
    # Run 3 checks
    print(f"{Fore.GREEN}Running 3 API checks...\n")
    for i in range(3):
        print(f"{Fore.YELLOW}Check #{i+1}")
        monitor.run_checks()
        if i < 2:
            print(f"{Fore.CYAN}Waiting 5 seconds...\n")
            time.sleep(5)
    
    # Show analysis
    print(f"\n{Fore.GREEN}Generating analysis report...\n")
    analyzer = LogAnalyzer()
    analyzer.analyze_all()
    
    print(f"{Fore.GREEN}✅ Demo complete! Check the logs/ directory for detailed logs.")

if __name__ == "__main__":
    main()
