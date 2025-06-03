#!/usr/bin/env python3
"""
Debug Westminster search results HTML structure
"""

import requests
from bs4 import BeautifulSoup

def debug_westminster_results():
    print("🔍 DEBUGGING WESTMINSTER SEARCH RESULTS")
    print("=" * 60)
    
    base_url = "https://idoxpa.westminster.gov.uk"
    search_url = f"{base_url}/online-applications/search.do"
    submit_url = f"{base_url}/online-applications/simpleSearchResults.do?action=firstPage"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    # Use a search term that we know returns results
    search_term = "basement extension monitoring"
    
    try:
        # Get CSRF token
        response = session.get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
        
        # Submit search
        form_data = {
            '_csrf': csrf_token,
            'searchType': 'Application',
            'searchCriteria.caseStatus': '',
            'searchCriteria.simpleSearchString': search_term,
            'searchCriteria.simpleSearch': 'true'
        }
        
        session.headers['Referer'] = search_url
        search_response = session.post(submit_url, data=form_data)
        
        print(f"Search term: '{search_term}'")
        print(f"Response code: {search_response.status_code}")
        
        if search_response.status_code == 200:
            soup = BeautifulSoup(search_response.content, 'html.parser')
            
            # Save full HTML for analysis
            with open('debug_results.html', 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            print("✅ Full HTML saved to debug_results.html")
            
            # Analyze structure
            print("\n📋 HTML STRUCTURE ANALYSIS:")
            
            # Check for common result indicators
            content_lower = search_response.text.lower()
            
            if "no results" in content_lower:
                print("❌ Contains 'no results'")
            elif "too many results" in content_lower:
                print("⚠️ Contains 'too many results'")
            elif "application" in content_lower:
                print("✅ Contains 'application' - likely has results")
                
            # Look for tables
            tables = soup.find_all('table')
            print(f"\n📊 Found {len(tables)} tables:")
            
            for i, table in enumerate(tables, 1):
                print(f"\nTable {i}:")
                rows = table.find_all('tr')
                print(f"  Rows: {len(rows)}")
                
                if rows:
                    # Analyze first row (header)
                    header_cells = rows[0].find_all(['th', 'td'])
                    print(f"  Header cells: {len(header_cells)}")
                    
                    if header_cells:
                        headers = [cell.get_text(strip=True) for cell in header_cells]
                        print(f"  Headers: {headers}")
                        
                    # Analyze data rows
                    if len(rows) > 1:
                        data_row = rows[1]
                        data_cells = data_row.find_all(['td', 'th'])
                        print(f"  First data row cells: {len(data_cells)}")
                        
                        if data_cells:
                            for j, cell in enumerate(data_cells[:5]):  # First 5 cells
                                cell_text = cell.get_text(strip=True)[:50]
                                cell_links = cell.find_all('a')
                                print(f"    Cell {j+1}: '{cell_text}' (links: {len(cell_links)})")
                                
                # Check table attributes
                table_id = table.get('id', 'no-id')
                table_class = table.get('class', 'no-class')
                print(f"  ID: {table_id}")
                print(f"  Class: {table_class}")
                
            # Look for divs that might contain results
            print("\n📦 Looking for result divs:")
            result_divs = soup.find_all('div', class_=lambda x: x and ('result' in str(x).lower() or 'search' in str(x).lower()))
            print(f"Found {len(result_divs)} potential result divs")
            
            for div in result_divs[:3]:  # First 3
                div_class = div.get('class', [])
                div_text = div.get_text(strip=True)[:100]
                print(f"  Div class: {div_class}")
                print(f"  Text: {div_text}...")
                
            # Look for specific application references
            print("\n🔍 Looking for application references:")
            app_refs = soup.find_all(text=lambda text: text and any(
                char.isdigit() for char in text
            ) and len(text) > 5 and len(text) < 50)
            
            for ref in app_refs[:10]:  # First 10
                ref_clean = ref.strip()
                if ref_clean and not ref_clean.isspace():
                    print(f"  Potential ref: '{ref_clean}'")
                    
        else:
            print(f"❌ Error response: {search_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_westminster_results() 