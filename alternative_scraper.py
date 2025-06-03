#!/usr/bin/env python3
"""
Alternative scraper that works around anti-bot protection
by accessing available applications and filtering locally
"""

import requests
import time
from bs4 import BeautifulSoup
from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS
import re
from datetime import datetime

class AlternativeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
    def find_recent_applications(self, borough_name):
        """Find recent applications by exploring the portal structure"""
        print(f"\n🏛️ EXPLORING {borough_name.upper()}")
        print("=" * 60)
        
        config = BOROUGHS_CONFIG[borough_name]
        base_url = config['base_url']
        
        found_applications = []
        
        try:
            # Try different approaches to find applications
            search_urls = [
                config['search_url'],
                f"{base_url}/online-applications/",
                f"{base_url}/applications/",
                f"{base_url}/planning/"
            ]
            
            for url in search_urls:
                try:
                    print(f"\n📍 Checking: {url}")
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"✅ Access successful")
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for application links
                        app_links = self.find_application_links(soup, base_url)
                        print(f"🔗 Found {len(app_links)} application links")
                        
                        # Check each application for keywords
                        for i, (app_id, app_url, title) in enumerate(app_links[:10]):  # Check first 10
                            print(f"\n   📄 Checking application {i+1}: {app_id}")
                            print(f"      Title: {title[:50]}...")
                            
                            app_data = self.check_application_details(app_id, app_url, title, borough_name)
                            if app_data:
                                found_applications.append(app_data)
                                print(f"      🎯 MATCH! Keywords: {', '.join(app_data['keywords'])}")
                            else:
                                print(f"      ⏭️ No monitoring keywords found")
                            
                            time.sleep(1)  # Be polite
                        
                        if app_links:
                            break  # Found applications, no need to try other URLs
                            
                    else:
                        print(f"❌ HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error accessing {url}: {str(e)[:50]}")
                    
        except Exception as e:
            print(f"❌ Error exploring {borough_name}: {e}")
            
        print(f"\n🎉 SUMMARY for {borough_name}:")
        print(f"   Applications checked: {len(found_applications) if found_applications else 'None'}")
        print(f"   Matches found: {len(found_applications)}")
        
        return found_applications
    
    def find_application_links(self, soup, base_url):
        """Extract application links from a page"""
        app_links = []
        
        # Look for various patterns of application links
        patterns = [
            # Standard Idox patterns
            'a[href*="application"]',
            'a[href*="planning"]', 
            'a[href*="detail"]',
            'a[href*="view"]',
            # Look for specific application ID patterns
            'a[href*="/"]'
        ]
        
        for pattern in patterns:
            links = soup.select(pattern)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Skip navigation links, look for actual applications
                if any(skip in text.lower() for skip in ['home', 'search', 'help', 'about', 'login', 'menu']):
                    continue
                    
                # Look for application ID patterns
                app_id_match = re.search(r'([A-Z0-9/\-\.]{6,})', text)
                if app_id_match or 'application' in href.lower():
                    
                    # Make sure we have full URL
                    full_url = href if href.startswith('http') else base_url + href
                    app_id = app_id_match.group(1) if app_id_match else text[:20]
                    
                    app_links.append((app_id, full_url, text))
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for app_id, url, title in app_links:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_links.append((app_id, url, title))
                
        return unique_links[:20]  # Limit to first 20
    
    def check_application_details(self, app_id, app_url, title, borough):
        """Check if an application contains monitoring keywords"""
        try:
            response = self.session.get(app_url, timeout=10)
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get all text content
            page_text = soup.get_text().lower()
            title_text = title.lower()
            combined_text = f"{title_text} {page_text}"
            
            # Check for monitoring keywords
            found_keywords = []
            for keyword in MONITORING_KEYWORDS:
                if keyword.lower() in combined_text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                return {
                    'app_id': app_id,
                    'borough': borough,
                    'title': title,
                    'url': app_url,
                    'keywords': found_keywords,
                    'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            print(f"      ❌ Error checking {app_id}: {str(e)[:30]}")
            
        return None

def run_alternative_search():
    """Run the alternative search approach"""
    print("🚀 ALTERNATIVE PLANNING APPLICATION SEARCH")
    print("This approach accesses available applications directly")
    print("=" * 80)
    
    scraper = AlternativeScraper()
    all_results = []
    
    # Test each borough
    for borough_name in BOROUGHS_CONFIG.keys():
        try:
            results = scraper.find_recent_applications(borough_name)
            all_results.extend(results)
            time.sleep(2)  # Be polite between boroughs
        except Exception as e:
            print(f"❌ Error with {borough_name}: {e}")
    
    print("\n\n🎯 FINAL RESULTS")
    print("=" * 80)
    
    if all_results:
        print(f"✅ Found {len(all_results)} applications with monitoring keywords!")
        
        for i, app in enumerate(all_results, 1):
            print(f"\n{i}. 📋 {app['app_id']} ({app['borough']})")
            print(f"   Title: {app['title'][:60]}...")
            print(f"   Keywords: {', '.join(app['keywords'])}")
            print(f"   URL: {app['url']}")
            print(f"   Found: {app['found_at']}")
    else:
        print("❌ No applications with monitoring keywords found")
        print("\nPossible reasons:")
        print("- Applications may not contain the specific keywords we're looking for")
        print("- Recent applications might not have environmental monitoring requirements")
        print("- The sites may only show applications after user authentication")
    
    return all_results

if __name__ == "__main__":
    results = run_alternative_search() 