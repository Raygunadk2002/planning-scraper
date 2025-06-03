#!/usr/bin/env python3
"""
Analyze Westminster form fields to find correct field names
"""

import requests
from bs4 import BeautifulSoup

def analyze_form():
    # Try multiple Westminster URLs
    urls_to_try = [
        'https://idoxpa.westminster.gov.uk/online-applications/search.do',
        'https://idoxpa.westminster.gov.uk/online-applications/search.do?action=simple&searchType=Application',
        'https://idoxpa.westminster.gov.uk/online-applications/simpleSearchResults.do?action=firstPage',
        'https://idoxpa.westminster.gov.uk/online-applications/advancedSearchResults.do?action=firstPage'
    ]
    
    print('🔍 WESTMINSTER FORM FIELD ANALYSIS')
    print('=' * 50)
    
    for url in urls_to_try:
        print(f'\n📍 Trying: {url}')
        
        try:
            response = requests.get(url, timeout=10)
            print(f'   Status: {response.status_code}')
            
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            forms = soup.find_all('form')
            print(f'   Forms found: {len(forms)}')
            
            for i, form in enumerate(forms, 1):
                print(f'\n   📋 FORM {i}:')
                action = form.get('action', 'no-action')
                method = form.get('method', 'GET')
                print(f'      Action: {action}')
                print(f'      Method: {method}')
                
                # Find all input fields
                inputs = form.find_all(['input', 'textarea', 'select'])
                print(f'      Fields: {len(inputs)}')
                
                # Look for proposal/description fields
                proposal_fields = []
                for inp in inputs:
                    field_name = inp.get('name', '')
                    field_type = inp.get('type', inp.name)
                    field_id = inp.get('id', '')
                    placeholder = inp.get('placeholder', '')
                    
                    # Check if this looks like a proposal field
                    if any(keyword in field_name.lower() for keyword in ['proposal', 'description', 'detail']):
                        proposal_fields.append({
                            'name': field_name,
                            'type': field_type,
                            'id': field_id,
                            'placeholder': placeholder
                        })
                        
                if proposal_fields:
                    print(f'      ✅ PROPOSAL FIELDS FOUND:')
                    for field in proposal_fields:
                        print(f'         {field["type"]}: name="{field["name"]}" id="{field["id"]}"')
                        if field['placeholder']:
                            print(f'         placeholder: "{field["placeholder"]}"')
                            
                    # Test with this form
                    print(f'\n      🧪 TESTING FORM SUBMISSION:')
                    return test_form_submission(url, form, proposal_fields[0])
                else:
                    # Show all fields for analysis
                    print(f'      📝 All fields:')
                    for inp in inputs[:8]:  # First 8 fields
                        field_name = inp.get('name', 'unnamed')
                        field_type = inp.get('type', inp.name)
                        print(f'         {field_type}: {field_name}')
                        
        except Exception as e:
            print(f'   ❌ Error: {str(e)[:40]}')
    
    print('\n❌ No suitable forms found')
    return False

def test_form_submission(url, form, proposal_field):
    """Test submitting the form with 'rear extension'"""
    
    print(f'      Testing with field: {proposal_field["name"]}')
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': url
        })
        
        # Build form data
        form_data = {}
        
        # Add hidden fields
        hidden_fields = form.find_all('input', {'type': 'hidden'})
        for field in hidden_fields:
            name = field.get('name')
            value = field.get('value')
            if name and value:
                form_data[name] = value
        
        # Add the proposal
        form_data[proposal_field['name']] = 'rear extension'
        
        # Add submit button
        submit_btn = form.find('input', {'type': 'submit'})
        if submit_btn:
            submit_name = submit_btn.get('name', 'submit')
            submit_value = submit_btn.get('value', 'Search')
            form_data[submit_name] = submit_value
        
        # Get form action
        action = form.get('action', '')
        if action and not action.startswith('http'):
            from urllib.parse import urljoin
            submit_url = urljoin(url, action)
        else:
            submit_url = url
            
        print(f'      Submitting to: {submit_url}')
        print(f'      Form data: {len(form_data)} fields')
        
        # Submit
        response = session.post(submit_url, data=form_data, timeout=15)
        print(f'      Response: {response.status_code}')
        
        if response.status_code == 200:
            content = response.text.lower()
            if 'too many results' in content:
                print(f'      🎉 SUCCESS! Too many results (exactly like manual test)')
                return True
            elif 'no results' in content:
                print(f'      📭 No results found')
            elif 'application' in content and 'reference' in content:
                print(f'      🎉 SUCCESS! Results found')
                return True
            else:
                print(f'      ❓ Unknown response')
        elif response.status_code == 403:
            print(f'      🚫 Blocked (403)')
        else:
            print(f'      ❌ Error: {response.status_code}')
            
    except Exception as e:
        print(f'      ❌ Exception: {str(e)[:40]}')
        
    return False

if __name__ == "__main__":
    success = analyze_form()
    if success:
        print('\n🎉 BREAKTHROUGH! Found working form submission method!')
    else:
        print('\n📋 Analysis complete - may need Selenium for this site') 