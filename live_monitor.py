#!/usr/bin/env python3
"""
Live command-line monitoring tool for scrapers
Shows real-time activity and tests different scraping approaches
"""

import time
import threading
from datetime import datetime
from scraper_manager import ScrapingManager
import requests
from config import BOROUGHS_CONFIG

class LiveMonitor:
    def __init__(self):
        self.manager = ScrapingManager()
        self.running = False
        
    def print_status(self):
        """Print current status"""
        print("\n" + "="*80)
        print(f"🕐 {datetime.now().strftime('%H:%M:%S')} - LIVE SCRAPER MONITOR")
        print("="*80)
        
        status = self.manager.get_scraping_status()
        
        print(f"\n📊 SYSTEM STATUS:")
        print(f"   Total Boroughs: {status['total_boroughs']}")
        print(f"   Active Scrapers: {status['active_scrapers']}")
        print(f"   Completed: {status['completed_scrapers']}")
        print(f"   Errors: {status['error_scrapers']}")
        print(f"   Overall Progress: {status['overall_progress']:.1f}%")
        
        print(f"\n🏛️ BOROUGH STATUS:")
        for borough, info in status['boroughs'].items():
            status_emoji = {
                'initialized': '⚪',
                'running': '🟡', 
                'completed': '🟢',
                'error': '🔴'
            }.get(info['status'], '❓')
            
            progress = info.get('progress_percentage', 0)
            current_keyword = info.get('current_keyword', 'None')
            
            print(f"   {status_emoji} {borough:20} | Status: {info['status']:10} | Progress: {progress:5.1f}% | Keyword: {current_keyword}")
        
        print(f"\n📈 DATABASE STATS:")
        db_stats = status.get('database_stats', {})
        print(f"   Total Applications: {db_stats.get('total_applications', 0)}")
        for keyword, count in db_stats.get('by_keyword', {}).items():
            print(f"   {keyword}: {count}")
        
        print(f"\n🔍 RECENT ACTIVITY (last 10):")
        recent_activity = status.get('live_activity', [])
        for entry in recent_activity[-10:]:
            timestamp = entry['timestamp']
            borough = (entry['borough'] or 'SYSTEM')[:15].ljust(15)
            message = entry['message'][:50]
            level_emoji = {'error': '❌', 'warning': '⚠️', 'info': '✅'}.get(entry['level'], 'ℹ️')
            print(f"   [{timestamp}] {level_emoji} {borough} | {message}")

    def test_url_access(self):
        """Test basic URL access for all boroughs"""
        print("\n🌐 TESTING URL ACCESS:")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        for borough, config in BOROUGHS_CONFIG.items():
            try:
                response = requests.get(config['base_url'], headers=headers, timeout=10)
                status_emoji = '✅' if response.status_code == 200 else '❌'
                print(f"   {status_emoji} {borough:20} | {response.status_code} | {config['base_url']}")
            except Exception as e:
                print(f"   ❌ {borough:20} | ERROR | {str(e)[:50]}")

    def run_test_scrape(self, borough_name="Westminster", keyword="extension"):
        """Run a test scrape and show detailed output"""
        print(f"\n🧪 TESTING SCRAPE: {borough_name} for '{keyword}'")
        print("-" * 60)
        
        try:
            result = self.manager.scrape_single_borough(borough_name, [keyword])
            
            print(f"\n📊 SCRAPE RESULT:")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Borough: {result.get('borough', 'Unknown')}")
            print(f"   Applications Found: {result.get('total_found', 0)}")
            print(f"   New Applications: {result.get('new_applications', 0)}")
            print(f"   Duration: {result.get('duration', 0):.1f}s")
            print(f"   Requests Made: {result.get('requests_made', 0)}")
            print(f"   Pages Processed: {result.get('pages_processed', 0)}")
            
            if not result.get('success'):
                print(f"   Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")

    def live_monitor_loop(self):
        """Main monitoring loop"""
        print("🚀 Starting live monitoring... Press Ctrl+C to stop")
        
        try:
            while self.running:
                self.print_status()
                time.sleep(5)  # Update every 5 seconds
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitoring stopped by user")
            
    def start_live_monitor(self):
        """Start live monitoring in background"""
        self.running = True
        monitor_thread = threading.Thread(target=self.live_monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread

def main():
    monitor = LiveMonitor()
    
    while True:
        print("\n" + "="*80)
        print("🔍 PLANNING SCRAPER LIVE MONITOR")
        print("="*80)
        print("\nOptions:")
        print("1. 📊 Show current status")
        print("2. 🌐 Test URL access")
        print("3. 🧪 Run test scrape")
        print("4. 📺 Start live monitoring")
        print("5. 🚀 Start all borough scraping")
        print("6. ❌ Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            monitor.print_status()
            
        elif choice == "2":
            monitor.test_url_access()
            
        elif choice == "3":
            borough = input("Enter borough name (default: Westminster): ").strip() or "Westminster"
            keyword = input("Enter keyword (default: extension): ").strip() or "extension"
            monitor.run_test_scrape(borough, keyword)
            
        elif choice == "4":
            thread = monitor.start_live_monitor()
            input("\nPress Enter to stop live monitoring...")
            monitor.running = False
            
        elif choice == "5":
            print("\n🚀 Starting scraping for all boroughs...")
            print("This will show real-time progress. Watch for HTTP 403 errors.")
            
            # Start live monitoring in background
            monitor.start_live_monitor()
            
            # Start scraping
            try:
                results = monitor.manager.scrape_all_boroughs()
                print(f"\n🎉 SCRAPING COMPLETED!")
                print(f"Results: {results}")
            except Exception as e:
                print(f"\n❌ SCRAPING ERROR: {e}")
            finally:
                monitor.running = False
                
        elif choice == "6":
            print("\n👋 Goodbye!")
            monitor.running = False
            break
            
        else:
            print("\n❌ Invalid choice, please try again")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 