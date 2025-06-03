#!/usr/bin/env python3
"""
Selenium-based scraper with human-like behavior to bypass anti-bot protection
"""

import time
import random
from datetime import datetime, timedelta
import re

# Try to import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available. Install with: pip install selenium")

from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS

class HumanLikeScraper:
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required for this scraper")
            
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome with human-like behavior"""
        chrome_options = Options()
        
        # Make browser look more human
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Human-like window size
        chrome_options.add_argument('--window-size=1366,768')
        
        # Realistic user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Selenium driver initialized with human-like settings")
            
        except Exception as e:
            print(f"❌ Error setting up Selenium: {e}")
            self.driver = None
    
    def human_delay(self, min_sec=1, max_sec=3):
        """Add human-like delays"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def human_type(self, element, text):
        """Type text with human-like pauses"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def search_borough_selenium(self, borough_name, keyword="extension"):
        """Search a borough using Selenium with human-like behavior"""
        if not self.driver:
            print("❌ Selenium driver not available")
            return []
            
        print(f"\n🤖 SELENIUM SEARCH: {borough_name} for '{keyword}'")
        print("=" * 60)
        
        config = BOROUGHS_CONFIG[borough_name]
        search_url = config['search_url']
        
        try:
            # Navigate to search page
            print(f"🌐 Navigating to: {search_url}")
            self.driver.get(search_url)
            self.human_delay(2, 4)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("✅ Page loaded, looking for search form...")
            
            # Look for search input fields
            search_inputs = [
                "input[name*='proposal']",
                "input[name*='description']", 
                "input[id*='proposal']",
                "input[id*='description']",
                "textarea[name*='proposal']",
                "textarea[name*='description']"
            ]
            
            search_element = None
            for selector in search_inputs:
                try:
                    search_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found search input: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not search_element:
                print("❌ No search input found")
                return []
            
            # Human-like interaction with the form
            print(f"📝 Filling search form with '{keyword}'...")
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_element)
            self.human_delay(1, 2)
            
            # Click and clear field
            search_element.click()
            self.human_delay(0.5, 1)
            search_element.clear()
            self.human_delay(0.5, 1)
            
            # Type with human-like behavior
            self.human_type(search_element, keyword)
            self.human_delay(1, 2)
            
            # Find submit button
            submit_buttons = [
                "input[type='submit'][value*='Search']",
                "button[type='submit']",
                "input[value*='Search']",
                "button:contains('Search')"
            ]
            
            submit_element = None
            for selector in submit_buttons:
                try:
                    submit_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found submit button: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not submit_element:
                print("❌ No submit button found")
                return []
            
            # Human-like submission
            print("🚀 Submitting search...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_element)
            self.human_delay(1, 2)
            
            # Move mouse to button and click (more human-like)
            ActionChains(self.driver).move_to_element(submit_element).pause(0.5).click().perform()
            
            # Wait for results
            print("⏳ Waiting for search results...")
            self.human_delay(3, 6)
            
            # Check if we got results or were blocked
            page_source = self.driver.page_source.lower()
            
            if "forbidden" in page_source or "403" in page_source:
                print("❌ Still blocked by anti-bot protection")
                return []
            
            if "no results" in page_source or "no applications found" in page_source:
                print("⚠️ No applications found for this keyword")
                return []
            
            # Look for results table
            try:
                results_table = self.driver.find_element(By.CSS_SELECTOR, "table.searchresults, table[class*='result'], table[id*='result']")
                print("✅ Found results table!")
                
                # Parse results
                applications = self.parse_results_selenium(results_table, borough_name)
                return applications
                
            except NoSuchElementException:
                print("❌ No results table found")
                return []
            
        except Exception as e:
            print(f"❌ Error during Selenium search: {str(e)[:60]}")
            return []
    
    def parse_results_selenium(self, table, borough_name):
        """Parse results from Selenium table element"""
        applications = []
        
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"📊 Found {len(rows)} rows in results table")
            
            for i, row in enumerate(rows[1:6]):  # Skip header, check first 5 results
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 3:
                        continue
                    
                    # Extract application data
                    app_link = cells[0].find_element(By.TAG_NAME, "a")
                    app_ref = app_link.text.strip()
                    app_url = app_link.get_attribute("href")
                    
                    address = cells[1].text.strip()
                    description = cells[2].text.strip()
                    
                    print(f"   📋 Row {i+1}: {app_ref} - {description[:40]}...")
                    
                    # Check for keywords
                    combined_text = f"{description} {address}".lower()
                    found_keywords = [kw for kw in MONITORING_KEYWORDS if kw.lower() in combined_text]
                    
                    if found_keywords:
                        print(f"      🎯 KEYWORD MATCH! {', '.join(found_keywords)}")
                        
                        applications.append({
                            'app_ref': app_ref,
                            'borough': borough_name,
                            'description': description,
                            'address': address,
                            'app_url': app_url,
                            'keywords': found_keywords,
                            'source': 'selenium_search',
                            'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                except Exception as e:
                    print(f"      ❌ Error parsing row {i+1}: {str(e)[:30]}")
                    continue
            
        except Exception as e:
            print(f"❌ Error parsing results table: {e}")
        
        return applications
    
    def run_selenium_search(self, test_keywords=None):
        """Run Selenium search across all boroughs"""
        if not self.driver:
            print("❌ Selenium driver not available")
            return []
        
        if test_keywords is None:
            test_keywords = ["extension", "house", "application"]  # Start with common terms
        
        print("🤖 SELENIUM ANTI-BOT BYPASS SCRAPER")
        print("Using human-like behavior to bypass blocking")
        print("=" * 80)
        
        all_results = []
        
        for borough_name in list(BOROUGHS_CONFIG.keys())[:2]:  # Test first 2 boroughs
            print(f"\n🏛️ Testing {borough_name}...")
            
            for keyword in test_keywords:
                try:
                    results = self.search_borough_selenium(borough_name, keyword)
                    all_results.extend(results)
                    
                    if results:
                        print(f"✅ Found {len(results)} applications for '{keyword}'")
                        break  # Found results, no need to try other keywords
                    else:
                        print(f"⚠️ No results for '{keyword}', trying next keyword...")
                        
                    self.human_delay(5, 10)  # Wait between searches
                    
                except Exception as e:
                    print(f"❌ Error searching {borough_name} for '{keyword}': {e}")
                    
            self.human_delay(10, 15)  # Longer wait between boroughs
        
        print("\n\n🎯 SELENIUM RESULTS")
        print("=" * 80)
        
        if all_results:
            print(f"🎉 SUCCESS! Found {len(all_results)} applications with Selenium:")
            
            for i, app in enumerate(all_results, 1):
                print(f"\n{i}. 📋 {app['app_ref']} ({app['borough']})")
                print(f"   Description: {app['description'][:60]}...")
                print(f"   Keywords: {', '.join(app['keywords'])}")
                print(f"   URL: {app['app_url']}")
        else:
            print("❌ No applications found with Selenium approach")
            print("Possible reasons:")
            print("- Still blocked by advanced anti-bot protection")
            print("- No recent applications contain the test keywords")
            print("- May need to solve CAPTCHA manually")
        
        return all_results
    
    def close(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            print("🚪 Selenium driver closed")

def run_selenium_bypass():
    """Run the Selenium bypass approach"""
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not available. Install with:")
        print("   pip install selenium")
        print("   And install ChromeDriver")
        return []
    
    scraper = None
    try:
        scraper = HumanLikeScraper()
        results = scraper.run_selenium_search()
        return results
    except Exception as e:
        print(f"❌ Error running Selenium scraper: {e}")
        return []
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    results = run_selenium_bypass() 