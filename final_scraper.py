#!/usr/bin/env python3
"""
FINAL WORKING WESTMINSTER SCRAPER
Based on actual HTML structure analysis
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def scrape_westminster_monitoring():
    print("🎉 FINAL WORKING WESTMINSTER SCRAPER")
    print("Extracting real planning applications with monitoring keywords")
    print("=" * 80)
    
    base_url = "https://idoxpa.westminster.gov.uk"
    search_url = f"{base_url}/online-applications/search.do"
    submit_url = f"{base_url}/online-applications/simpleSearchResults.do?action=firstPage"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Search terms that we know return actual monitoring applications
    search_terms = [
        "monitoring",
        "tree monitoring", 
        "basement extension monitoring",
        "monitoring during construction",
        "subsidence monitoring",
        "noise monitoring",
        "vibration monitoring",
        "dust monitoring",
        "environmental monitoring"
    ]
    
    all_applications = []
    
    for search_term in search_terms:
        print(f"\n🔍 Searching: '{search_term}'")
        print("-" * 50)
        
        try:
            # Get search page and CSRF token
            response = session.get(search_url)
            if response.status_code != 200:
                print(f"   ❌ Can't access search page: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf'})
            if not csrf_input:
                print("   ❌ No CSRF token found")
                continue
                
            csrf_token = csrf_input.get('value')
            
            # Build form data (exact structure we discovered)
            form_data = {
                '_csrf': csrf_token,
                'searchType': 'Application',
                'searchCriteria.caseStatus': '',
                'searchCriteria.simpleSearchString': search_term,
                'searchCriteria.simpleSearch': 'true'
            }
            
            # Submit search
            session.headers['Referer'] = search_url
            search_response = session.post(submit_url, data=form_data, timeout=15)
            
            print(f"   📊 Response: {search_response.status_code}")
            
            if search_response.status_code == 200:
                content_lower = search_response.text.lower()
                
                if "too many results found" in content_lower:
                    print("   ⚠️ Too many results - trying more specific term")
                    continue
                    
                elif "no results" in content_lower or "no applications found" in content_lower:
                    print("   📭 No results found")
                    continue
                    
                # Parse results using the correct structure
                results_soup = BeautifulSoup(search_response.content, 'html.parser')
                
                # Find the results list: <ul id="searchresults">
                results_ul = results_soup.find('ul', id='searchresults')
                
                if not results_ul:
                    print("   ❓ No results list found")
                    continue
                    
                # Find all result items: <li class="searchresult">
                result_items = results_ul.find_all('li', class_='searchresult')
                
                if not result_items:
                    print("   📭 No result items found")
                    continue
                    
                print(f"   🎉 Found {len(result_items)} applications!")
                
                # Parse each result
                for i, item in enumerate(result_items, 1):
                    try:
                        # Get the main link with description
                        link = item.find('a', class_='summaryLink')
                        if not link:
                            continue
                            
                        app_url = link.get('href', '')
                        if app_url and not app_url.startswith('http'):
                            app_url = f"{base_url}{app_url}"
                            
                        # Get description from the div inside the link
                        desc_div = link.find('div')
                        description = desc_div.get_text(strip=True) if desc_div else ""
                        
                        # Get address
                        address_p = item.find('p', class_='address')
                        address = address_p.get_text(strip=True) if address_p else ""
                        
                        # Get metadata (reference, dates, status)
                        meta_p = item.find('p', class_='metaInfo')
                        reference = ""
                        received_date = ""
                        status = ""
                        
                        if meta_p:
                            meta_text = meta_p.get_text()
                            
                            # Extract reference number
                            ref_match = re.search(r'Ref\. No:\s*([^\|]+)', meta_text)
                            if ref_match:
                                reference = ref_match.group(1).strip()
                                
                            # Extract received date
                            received_match = re.search(r'Received:\s*([^\|]+)', meta_text)
                            if received_match:
                                received_date = received_match.group(1).strip()
                                
                            # Extract status
                            status_match = re.search(r'Status:\s*(.+?)(?:\s|$)', meta_text)
                            if status_match:
                                status = status_match.group(1).strip()
                        
                        # Check for monitoring keywords in description and address
                        monitoring_keywords = [
                            'monitoring', 'noise', 'vibration', 'dust', 'subsidence',
                            'environmental', 'acoustic', 'sound', 'tree monitoring',
                            'construction management', 'arboricultural', 'supervision'
                        ]
                        
                        combined_text = f"{description} {address}".lower()
                        found_keywords = [kw for kw in monitoring_keywords if kw in combined_text]
                        
                        application = {
                            'reference': reference,
                            'address': address,
                            'description': description,
                            'status': status,
                            'received_date': received_date,
                            'url': app_url,
                            'search_term': search_term,
                            'borough': 'Westminster',
                            'keywords': found_keywords,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        all_applications.append(application)
                        
                        # Show progress
                        if found_keywords:
                            print(f"      🎯 {i}. {reference}: {', '.join(found_keywords)}")
                        else:
                            print(f"      📋 {i}. {reference}: (no specific keywords)")
                            
                    except Exception as e:
                        print(f"      ❌ Error parsing item {i}: {str(e)[:30]}")
                        continue
                        
            elif search_response.status_code == 403:
                print("   🚫 Blocked (403)")
                
            else:
                print(f"   ❌ Error: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:50]}")
            
        time.sleep(3)  # Be polite between searches
    
    return all_applications

def main():
    applications = scrape_westminster_monitoring()
    
    print("\n\n🎯 FINAL RESULTS")
    print("=" * 80)
    
    if applications:
        print(f"📊 Total applications found: {len(applications)}")
        
        # Filter for those with monitoring keywords
        monitoring_apps = [app for app in applications if app['keywords']]
        non_monitoring_apps = [app for app in applications if not app['keywords']]
        
        if monitoring_apps:
            print(f"\n🎉 {len(monitoring_apps)} APPLICATIONS WITH MONITORING KEYWORDS:")
            print("=" * 60)
            
            for i, app in enumerate(monitoring_apps, 1):
                print(f"\n{i}. 📋 {app['reference']} ({app['status']})")
                print(f"   🏠 Address: {app['address']}")
                print(f"   📝 Description: {app['description'][:100]}{'...' if len(app['description']) > 100 else ''}")
                print(f"   🎯 Keywords: {', '.join(app['keywords'])}")
                print(f"   📅 Received: {app['received_date']}")
                print(f"   🔗 URL: {app['url']}")
                print(f"   🔍 Found via: '{app['search_term']}'")
        
        if non_monitoring_apps:
            print(f"\n📋 {len(non_monitoring_apps)} other applications found (no specific monitoring keywords)")
            
        print(f"\n🚀 SUCCESS! Westminster scraper is fully operational!")
        print(f"📈 Can be extended to other boroughs using same approach")
        
    else:
        print("❌ No applications found")
        
    return applications

if __name__ == "__main__":
    results = main() 