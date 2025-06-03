#!/usr/bin/env python3
"""
Integrate Westminster monitoring applications into the main database
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from database import PlanningDatabase

def scrape_and_save_westminster():
    print("🎯 INTEGRATING WESTMINSTER MONITORING APPLICATIONS")
    print("Scraping and saving to main database")
    print("=" * 80)
    
    # Initialize database connection
    db = PlanningDatabase()
    
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
    
    # Search terms for monitoring applications
    search_terms = [
        "monitoring",
        "tree monitoring", 
        "noise monitoring",
        "environmental monitoring"
    ]
    
    saved_count = 0
    
    for search_term in search_terms:
        print(f"\n🔍 Processing: '{search_term}'")
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
            
            # Build form data
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
            
            if search_response.status_code != 200:
                print(f"   ❌ Search failed: {search_response.status_code}")
                continue
                
            content_lower = search_response.text.lower()
            
            if "too many results found" in content_lower:
                print("   ⚠️ Too many results - skipping")
                continue
                
            if "no results" in content_lower:
                print("   📭 No results found")
                continue
                
            # Parse results
            results_soup = BeautifulSoup(search_response.content, 'html.parser')
            results_ul = results_soup.find('ul', id='searchresults')
            
            if not results_ul:
                print("   ❓ No results list found")
                continue
                
            result_items = results_ul.find_all('li', class_='searchresult')
            
            if not result_items:
                print("   📭 No result items found")
                continue
                
            print(f"   🎉 Found {len(result_items)} applications!")
            
            # Process each result
            for i, item in enumerate(result_items, 1):
                try:
                    # Extract application data
                    link = item.find('a', class_='summaryLink')
                    if not link:
                        continue
                        
                    app_url = link.get('href', '')
                    if app_url and not app_url.startswith('http'):
                        app_url = f"{base_url}{app_url}"
                        
                    desc_div = link.find('div')
                    description = desc_div.get_text(strip=True) if desc_div else ""
                    
                    address_p = item.find('p', class_='address')
                    address = address_p.get_text(strip=True) if address_p else ""
                    
                    # Get metadata
                    meta_p = item.find('p', class_='metaInfo')
                    reference = ""
                    received_date = ""
                    status = ""
                    
                    if meta_p:
                        meta_text = meta_p.get_text()
                        
                        ref_match = re.search(r'Ref\. No:\s*([^\|]+)', meta_text)
                        if ref_match:
                            reference = ref_match.group(1).strip()
                            
                        received_match = re.search(r'Received:\s*([^\|]+)', meta_text)
                        if received_match:
                            received_date = received_match.group(1).strip()
                            
                        status_match = re.search(r'Status:\s*(.+?)(?:\s|$)', meta_text)
                        if status_match:
                            status = status_match.group(1).strip()
                    
                    # Check for monitoring keywords
                    monitoring_keywords = [
                        'monitoring', 'noise', 'vibration', 'dust', 'subsidence',
                        'environmental', 'acoustic', 'sound', 'tree monitoring',
                        'construction management', 'arboricultural', 'supervision'
                    ]
                    
                    combined_text = f"{description} {address}".lower()
                    found_keywords = [kw for kw in monitoring_keywords if kw in combined_text]
                    
                    if not found_keywords:
                        continue  # Skip applications without monitoring keywords
                    
                    # Save to database using correct method and field mapping
                    try:
                        application_data = {
                            'project_id': reference,
                            'borough': 'Westminster',
                            'title': description,
                            'address': address,
                            'submission_date': received_date,
                            'application_url': app_url,
                            'detected_keywords': found_keywords,
                            'source_url': base_url
                        }
                        
                        success = db.insert_planning_application(application_data)
                        
                        if success:
                            saved_count += 1
                            print(f"      ✅ {saved_count}. {reference}: {', '.join(found_keywords)}")
                        else:
                            print(f"      🔄 {reference}: Already exists (skipping)")
                        
                    except Exception as e:
                        print(f"      ❌ Error saving {reference}: {str(e)[:50]}")
                        
                except Exception as e:
                    print(f"      ❌ Error parsing item {i}: {str(e)[:30]}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:50]}")
            
        time.sleep(2)  # Be polite between searches
    
    print(f"\n\n🎯 INTEGRATION COMPLETE")
    print("=" * 40)
    print(f"✅ Successfully saved {saved_count} monitoring applications to database")
    print("🎉 Data now available in Streamlit dashboard!")
    
    return saved_count

if __name__ == "__main__":
    count = scrape_and_save_westminster()
    print(f"\n🚀 Ready! {count} Westminster monitoring applications integrated.") 