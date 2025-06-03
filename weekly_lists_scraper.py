#!/usr/bin/env python3
"""
Weekly Lists Scraper - Accesses weekly/monthly application lists
that don't require search form submissions
"""

import requests
import time
from bs4 import BeautifulSoup
from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS
import re
from datetime import datetime

class WeeklyListsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
    def find_weekly_lists(self, borough_name):
        """Find and access weekly/monthly planning lists"""
        print(f"\n🗓️ ACCESSING WEEKLY LISTS for {borough_name.upper()}")
        print("=" * 60)
        
        config = BOROUGHS_CONFIG[borough_name]
        base_url = config['base_url']
        
        # Try to find weekly lists URLs
        weekly_urls = [
            f"{base_url}/online-applications/weeklyListResults.do?listType=PL_PlanningApplications",
            f"{base_url}/online-applications/weeklyListResults.do",
            f"{base_url}/online-applications/weekly.do",
            f"{base_url}/online-applications/monthlyListResults.do",
            f"{base_url}/weekly-lists/",
            f"{base_url}/planning/weekly-lists/",
            config['search_url'].replace('search.do', 'weeklyListResults.do')
        ]
        
        found_applications = []
        
        for url in weekly_urls:
            try:
                print(f"\n📍 Trying: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ SUCCESS! Found weekly lists page")
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for application tables
                    tables = soup.find_all('table')
                    print(f"📊 Found {len(tables)} tables to check")
                    
                    for i, table in enumerate(tables):
                        apps = self.parse_applications_table(table, borough_name, base_url)
                        if apps:
                            found_applications.extend(apps)
                            print(f"✅ Table {i+1}: Found {len(apps)} applications")
                    
                    if found_applications:
                        break  # Found applications, no need to try other URLs
                        
                elif response.status_code == 403:
                    print(f"❌ Still blocked (403)")
                else:
                    print(f"⚠️ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
                
        return found_applications
    
    def parse_applications_table(self, table, borough, base_url):
        """Parse planning applications from a table"""
        applications = []
        
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:  # Need header + data
                return applications
                
            # Look for application reference patterns in rows
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                    
                # Try to extract application info
                app_data = self.extract_application_from_row(cells, borough, base_url)
                if app_data:
                    applications.append(app_data)
                    
        except Exception as e:
            print(f"      Error parsing table: {str(e)[:30]}")
            
        return applications
    
    def extract_application_from_row(self, cells, borough, base_url):
        """Extract application data from table row"""
        try:
            # Look for application reference (usually first cell)
            ref_cell = cells[0]
            app_link = ref_cell.find('a')
            
            if not app_link:
                return None
                
            app_ref = app_link.get_text(strip=True)
            app_url = app_link.get('href', '')
            
            # Make sure we have a valid application reference
            if not re.search(r'[A-Z0-9]{4,}', app_ref):
                return None
                
            # Build full URL
            if app_url and not app_url.startswith('http'):
                app_url = base_url + app_url
                
            # Get other details from remaining cells
            address = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            description = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            date_received = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            
            print(f"      📋 Found: {app_ref} - {description[:40]}...")
            
            # Check for monitoring keywords
            combined_text = f"{description} {address}".lower()
            found_keywords = [kw for kw in MONITORING_KEYWORDS if kw.lower() in combined_text]
            
            if found_keywords:
                print(f"      🎯 KEYWORD MATCH! {', '.join(found_keywords)}")
                
                return {
                    'app_ref': app_ref,
                    'borough': borough,
                    'description': description,
                    'address': address,
                    'date_received': date_received,
                    'app_url': app_url,
                    'keywords': found_keywords,
                    'source': 'weekly_lists',
                    'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                # Still return it for analysis, but mark as no keywords
                return {
                    'app_ref': app_ref,
                    'borough': borough,
                    'description': description,
                    'address': address,
                    'date_received': date_received,
                    'app_url': app_url,
                    'keywords': [],
                    'source': 'weekly_lists',
                    'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            print(f"      ❌ Error extracting application: {str(e)[:30]}")
            return None

def run_weekly_lists_search():
    """Run the weekly lists scraper"""
    print("🗓️ WEEKLY PLANNING LISTS SCRAPER")
    print("Accessing weekly/monthly lists that bypass search blocking")
    print("=" * 80)
    
    scraper = WeeklyListsScraper()
    all_results = []
    
    for borough_name in BOROUGHS_CONFIG.keys():
        try:
            results = scraper.find_weekly_lists(borough_name)
            all_results.extend(results)
            
            print(f"\n📊 {borough_name} SUMMARY:")
            print(f"   Total applications: {len(results)}")
            keyword_matches = [app for app in results if app['keywords']]
            print(f"   Keyword matches: {len(keyword_matches)}")
            
            if keyword_matches:
                print("   🎯 MATCHES FOUND:")
                for app in keyword_matches[:3]:  # Show first 3
                    print(f"      {app['app_ref']}: {', '.join(app['keywords'])}")
            
            time.sleep(3)  # Be polite between boroughs
            
        except Exception as e:
            print(f"❌ Error with {borough_name}: {e}")
    
    print("\n\n🎯 FINAL RESULTS")
    print("=" * 80)
    
    total_apps = len(all_results)
    keyword_apps = [app for app in all_results if app['keywords']]
    
    print(f"📊 STATISTICS:")
    print(f"   Total applications found: {total_apps}")
    print(f"   Applications with keywords: {len(keyword_apps)}")
    print(f"   Success rate: {len(keyword_apps)/total_apps*100:.1f}%" if total_apps > 0 else "   No applications found")
    
    if keyword_apps:
        print(f"\n🎉 SUCCESS! Found {len(keyword_apps)} applications with monitoring keywords:")
        
        for i, app in enumerate(keyword_apps, 1):
            print(f"\n{i}. 📋 {app['app_ref']} ({app['borough']})")
            print(f"   Description: {app['description'][:60]}...")
            print(f"   Address: {app['address'][:60]}...")
            print(f"   Keywords: {', '.join(app['keywords'])}")
            print(f"   URL: {app['app_url']}")
            print(f"   Date: {app['date_received']}")
    else:
        print("\n❌ No applications with monitoring keywords found")
        if total_apps > 0:
            print(f"   But found {total_apps} total applications - try broader keywords")
    
    return all_results

if __name__ == "__main__":
    results = run_weekly_lists_search() 