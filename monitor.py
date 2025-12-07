#!/usr/bin/env python3
"""
API Response Logger - Monitor APIs for downtime and changes
"""

import json
import time
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style
from typing import Dict, List, Optional

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class APIMonitor:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.api_states = {}
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}Error: {config_path} not found. Please create it from config.example.json")
            exit(1)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error: Invalid JSON in {config_path}: {e}")
            exit(1)
    
    def get_response_hash(self, response_data: str) -> str:
        """Generate hash of response for change detection"""
        return hashlib.md5(response_data.encode()).hexdigest()
    
    def check_api(self, api_config: Dict) -> Dict:
        """Check a single API endpoint"""
        name = api_config.get('name', 'Unknown API')
        url = api_config['url']
        method = api_config.get('method', 'GET').upper()
        headers = api_config.get('headers', {})
        expected_status = api_config.get('expected_status', 200)
        
        result = {
            'name': name,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'response_time': None,
            'status_code': None,
            'error': None,
            'response_hash': None
        }
        
        try:
            start_time = time.time()
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result['response_time'] = round(response_time, 2)
            result['status_code'] = response.status_code
            
            # Check if API is up
            if response.status_code == expected_status:
                result['status'] = 'up'
            else:
                result['status'] = 'error'
                result['error'] = f"Unexpected status code: {response.status_code}"
            
            # Generate response hash for change detection
            if api_config.get('check_response_structure', False):
                result['response_hash'] = self.get_response_hash(response.text)
                
        except requests.exceptions.Timeout:
            result['status'] = 'down'
            result['error'] = 'Request timeout'
        except requests.exceptions.ConnectionError:
            result['status'] = 'down'
            result['error'] = 'Connection error'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def detect_changes(self, api_name: str, current_hash: Optional[str]) -> bool:
        """Detect if API response structure has changed"""
        if current_hash is None:
            return False
            
        if api_name not in self.api_states:
            self.api_states[api_name] = {'last_hash': current_hash}
            return False
        
        last_hash = self.api_states[api_name].get('last_hash')
        if last_hash and last_hash != current_hash:
            self.api_states[api_name]['last_hash'] = current_hash
            return True
        
        self.api_states[api_name]['last_hash'] = current_hash
        return False

    def log_result(self, result: Dict):
        """Log result to file"""
        log_file = self.logs_dir / f"{result['name'].replace(' ', '_').lower()}.log"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
    
    def alert(self, message: str, level: str = 'info'):
        """Send alerts based on configuration"""
        alert_settings = self.config.get('alert_settings', {})
        
        # Console alert (always enabled by default)
        if alert_settings.get('console', True):
            color = Fore.GREEN
            if level == 'warning':
                color = Fore.YELLOW
            elif level == 'critical':
                color = Fore.RED
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"{color}[{timestamp}] {message}{Style.RESET_ALL}")
        
        # Webhook alert
        if alert_settings.get('webhook', False) and level in ['warning', 'critical']:
            webhook_url = alert_settings.get('webhook_url')
            if webhook_url:
                try:
                    requests.post(webhook_url, json={'text': message}, timeout=5)
                except:
                    pass  # Silently fail webhook alerts
    
    def analyze_result(self, result: Dict):
        """Analyze result and send appropriate alerts"""
        name = result['name']
        status = result['status']
        response_time = result.get('response_time')
        thresholds = self.config.get('thresholds', {})
        
        # Check if API is down
        if status == 'down':
            self.alert(f"🔴 {name} is DOWN! Error: {result['error']}", 'critical')
        elif status == 'error':
            self.alert(f"⚠️  {name} returned an error: {result['error']}", 'warning')
        elif status == 'up':
            # Check response time
            if response_time:
                critical_threshold = thresholds.get('response_time_critical', 5000)
                warning_threshold = thresholds.get('response_time_warning', 2000)
                
                if response_time > critical_threshold:
                    self.alert(
                        f"🐌 {name} is VERY SLOW! Response time: {response_time}ms",
                        'critical'
                    )
                elif response_time > warning_threshold:
                    self.alert(
                        f"⏱️  {name} is slow. Response time: {response_time}ms",
                        'warning'
                    )
                else:
                    self.alert(
                        f"✅ {name} is healthy. Response time: {response_time}ms",
                        'info'
                    )
            
            # Check for response structure changes
            response_hash = result.get('response_hash')
            if response_hash and self.detect_changes(name, response_hash):
                self.alert(
                    f"🔄 {name} response structure has CHANGED!",
                    'warning'
                )
    
    def run_checks(self):
        """Run checks for all configured APIs"""
        apis = self.config.get('apis', [])
        
        if not apis:
            print(f"{Fore.YELLOW}No APIs configured. Please add APIs to config.json")
            return
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}Starting API checks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        for api_config in apis:
            result = self.check_api(api_config)
            self.log_result(result)
            self.analyze_result(result)
        
        print(f"\n{Fore.CYAN}{'='*60}\n")
    
    def start(self):
        """Start monitoring loop"""
        check_interval = self.config.get('check_interval', 60)
        
        print(f"{Fore.GREEN}🚀 API Monitor Started!")
        print(f"{Fore.GREEN}Monitoring {len(self.config.get('apis', []))} APIs")
        print(f"{Fore.GREEN}Check interval: {check_interval} seconds")
        print(f"{Fore.GREEN}Logs directory: {self.logs_dir.absolute()}\n")
        
        try:
            while True:
                self.run_checks()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitor stopped by user.")

def main():
    monitor = APIMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
