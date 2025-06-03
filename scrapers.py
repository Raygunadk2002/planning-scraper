"""
Web scrapers for London Borough Planning Portals
Contains scraper classes for each borough's planning application portal
"""

import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import re
import os

import requests
from bs4 import BeautifulSoup

# Try to import Selenium - optional dependency
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS, SCRAPING_CONFIG
from utils import ScrapingUtils, TextProcessor, ValidationUtils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for borough scrapers with live monitoring support"""
    
    def __init__(self, borough_name: str, activity_logger=None):
        self.borough_name = borough_name
        self.config = BOROUGHS_CONFIG[borough_name]
        self.scraping_utils = ScrapingUtils()
        self.applications = []
        self.activity_logger = activity_logger  # For live activity logging
    
    def log_activity(self, message: str, level: str = "info"):
        """Log activity for live monitoring"""
        if self.activity_logger:
            try:
                self.activity_logger(message, self.borough_name, level)
            except Exception as e:
                logger.error(f"Error in activity logging: {e}")
        
        # Also log to standard logger
        if level == "error":
            logger.error(f"[{self.borough_name}] {message}")
        elif level == "warning":
            logger.warning(f"[{self.borough_name}] {message}")
        else:
            logger.info(f"[{self.borough_name}] {message}")
    
    def scrape_applications(self, keywords: List[str] = None) -> List[Dict]:
        """Main method to scrape applications - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement scrape_applications")
    
    def search_keyword(self, keyword: str) -> List[Dict]:
        """Search for applications containing a specific keyword - MUST be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement search_keyword")
    
    def parse_application_details(self, application_element) -> Optional[Dict]:
        """Parse application details from HTML element"""
        raise NotImplementedError("Subclasses must implement parse_application_details")

class IdoxScraper(BaseScraper):
    """Scraper for Idox-based planning portals (Camden, Westminster, H&F, Tower Hamlets)"""
    
    def __init__(self, borough_name: str, activity_logger=None):
        super().__init__(borough_name, activity_logger)
        self.base_url = self.config['base_url']
        self.search_url = self.config['search_url']
        self.log_activity(f"🏗️ Initialized Idox scraper for {borough_name}")
        self.log_activity(f"🌐 Base URL: {self.base_url}")
        self.log_activity(f"🔍 Search URL: {self.search_url}")
    
    def scrape_applications(self, keywords: List[str] = None) -> List[Dict]:
        """Scrape applications from Idox-based portal"""
        if keywords is None:
            keywords = MONITORING_KEYWORDS
        
        all_applications = []
        
        for keyword in keywords:
            logger.info(f"Searching {self.borough_name} for keyword: {keyword}")
            try:
                keyword_apps = self.search_keyword(keyword)
                all_applications.extend(keyword_apps)
                logger.info(f"Found {len(keyword_apps)} applications for '{keyword}' in {self.borough_name}")
            except Exception as e:
                logger.error(f"Error searching for '{keyword}' in {self.borough_name}: {e}")
        
        # Remove duplicates based on project_id
        unique_applications = {}
        for app in all_applications:
            project_id = app.get('project_id')
            if project_id and project_id not in unique_applications:
                unique_applications[project_id] = app
        
        final_applications = list(unique_applications.values())
        logger.info(f"Total unique applications found in {self.borough_name}: {len(final_applications)}")
        
        return final_applications
    
    def search_keyword(self, keyword: str) -> List[Dict]:
        """Search for a specific keyword in the Idox portal with live monitoring"""
        applications = []
        
        self.log_activity(f"🔍 Starting keyword search: '{keyword}'")
        
        try:
            # Prepare search form data
            self.log_activity(f"📝 Preparing search form data for '{keyword}'")
            search_data = {
                'searchType': 'Application',
                'searchCriteria.applicationNumber': '',
                'searchCriteria.applicantName': '',
                'searchCriteria.developmentAddress': '',
                'searchCriteria.proposal': keyword,
                'searchCriteria.ward': '',
                'searchCriteria.parish': '',
                'searchCriteria.postcode': '',
                'searchCriteria.receivedDateFrom': '',
                'searchCriteria.receivedDateTo': '',
                'searchCriteria.decisionDateFrom': '',
                'searchCriteria.decisionDateTo': '',
                'action': 'search'
            }
            
            # Perform search
            self.log_activity(f"🌐 Making POST request to {self.search_url}")
            response = self.scraping_utils.post_request_with_session_init(
                self.search_url,
                search_data,
                urlparse(self.base_url).netloc
            )
            
            if not response:
                self.log_activity(f"❌ No response received from {self.borough_name} search", "warning")
                return applications
            
            self.log_activity(f"✅ Received response ({response.status_code}), parsing HTML...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search results
            results_table = soup.find('table', {'class': 'searchresults'}) or soup.find('table', id='searchresults')
            
            if not results_table:
                self.log_activity(f"⚠️ No results table found for '{keyword}'", "warning")
                return applications
            
            # Parse each result row
            result_rows = results_table.find_all('tr')[1:]  # Skip header row
            self.log_activity(f"📊 Found {len(result_rows)} result rows to process")
            
            processed_count = 0
            max_pages = SCRAPING_CONFIG['max_pages_per_borough']
            
            for i, row in enumerate(result_rows[:max_pages]):
                try:
                    self.log_activity(f"📄 Processing row {i+1}/{min(len(result_rows), max_pages)}")
                    app_data = self.parse_application_row(row, keyword)
                    if app_data:
                        applications.append(app_data)
                        processed_count += 1
                        self.log_activity(f"✅ Successfully processed application: {app_data.get('project_id', 'Unknown ID')}")
                    else:
                        self.log_activity(f"⏭️ Skipped row {i+1} (no valid data or keywords)")
                except Exception as e:
                    self.log_activity(f"❌ Error processing row {i+1}: {str(e)}", "error")
                    continue
            
            self.log_activity(f"🎉 Completed search for '{keyword}': {processed_count} applications found")
            
        except Exception as e:
            self.log_activity(f"💥 Critical error searching for '{keyword}': {str(e)}", "error")
        
        return applications
    
    def parse_application_row(self, row, search_keyword: str) -> Optional[Dict]:
        """Parse a single application row from search results with live monitoring"""
        try:
            cells = row.find_all('td')
            if len(cells) < 4:
                return None
            
            # Extract basic information
            app_link = cells[0].find('a')
            if not app_link:
                return None
            
            project_id = TextProcessor.clean_text(app_link.text)
            if not ValidationUtils.is_valid_project_id(project_id):
                return None
            
            application_url = urljoin(self.base_url, app_link.get('href', ''))
            
            # Get other details
            address = TextProcessor.clean_text(cells[1].text) if len(cells) > 1 else ""
            title = TextProcessor.clean_text(cells[2].text) if len(cells) > 2 else ""
            
            self.log_activity(f"🔗 Processing application {project_id}: {title[:50]}...")
            
            # Extract date (usually in last column)
            date_text = TextProcessor.clean_text(cells[-1].text)
            submission_date = TextProcessor.parse_date(date_text)
            
            # Get full application details
            self.log_activity(f"📄 Fetching full details for {project_id}")
            full_text = self.get_application_details(application_url)
            
            # Detect keywords in full text
            detected_keywords = TextProcessor.detect_keywords(full_text)
            
            # Only include if monitoring keywords are found
            if not detected_keywords:
                self.log_activity(f"⏭️ No monitoring keywords found in {project_id}")
                return None
            
            self.log_activity(f"🎯 Found keywords in {project_id}: {', '.join(detected_keywords)}")
            
            application_data = {
                'project_id': project_id,
                'borough': self.borough_name,
                'title': title,
                'address': address,
                'submission_date': submission_date,
                'application_url': application_url,
                'detected_keywords': detected_keywords,
                'source_url': self.search_url
            }
            
            return ValidationUtils.validate_application_data(application_data)
            
        except Exception as e:
            self.log_activity(f"❌ Error parsing application row: {str(e)}", "error")
            return None
    
    def get_application_details(self, application_url: str) -> str:
        """Get full application details from individual application page with live monitoring"""
        try:
            self.log_activity(f"🌐 Fetching details from: {application_url[:60]}...")
            
            response = self.scraping_utils.rate_limited_request(
                application_url,
                domain=urlparse(self.base_url).netloc
            )
            
            if not response:
                self.log_activity(f"❌ No response from application details page", "warning")
                return ""
            
            self.log_activity(f"✅ Retrieved application details page ({len(response.content)} bytes)")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text from main content areas
            content_areas = [
                soup.find('div', {'class': 'content'}),
                soup.find('div', {'id': 'main'}),
                soup.find('div', {'class': 'main-content'}),
                soup.find('main'),
                soup.body
            ]
            
            full_text = ""
            for area in content_areas:
                if area:
                    full_text = area.get_text(separator=' ', strip=True)
                    break
            
            self.log_activity(f"📝 Extracted {len(full_text)} characters of text content")
            return TextProcessor.clean_text(full_text)
            
        except Exception as e:
            self.log_activity(f"❌ Error getting application details: {str(e)}", "error")
            return ""

class SouthwarkScraper(BaseScraper):
    """Scraper for Southwark planning portal (may have different structure)"""
    
    def __init__(self, borough_name: str = "Southwark", activity_logger=None):
        super().__init__(borough_name, activity_logger)
        self.base_url = self.config['base_url']
        self.search_url = self.config['search_url']
        self.log_activity(f"🏗️ Initialized Southwark scraper")
        self.log_activity(f"🌐 Base URL: {self.base_url}")
    
    def scrape_applications(self, keywords: List[str] = None) -> List[Dict]:
        """Scrape applications from Southwark portal"""
        if keywords is None:
            keywords = MONITORING_KEYWORDS
        
        all_applications = []
        
        for keyword in keywords:
            logger.info(f"Searching Southwark for keyword: {keyword}")
            try:
                keyword_apps = self.search_keyword(keyword)
                all_applications.extend(keyword_apps)
                logger.info(f"Found {len(keyword_apps)} applications for '{keyword}' in Southwark")
            except Exception as e:
                logger.error(f"Error searching for '{keyword}' in Southwark: {e}")
        
        # Remove duplicates
        unique_applications = {}
        for app in all_applications:
            project_id = app.get('project_id')
            if project_id and project_id not in unique_applications:
                unique_applications[project_id] = app
        
        final_applications = list(unique_applications.values())
        logger.info(f"Total unique applications found in Southwark: {len(final_applications)}")
        
        return final_applications
    
    def search_keyword(self, keyword: str) -> List[Dict]:
        """Search for applications in Southwark using similar Idox approach with live monitoring"""
        applications = []
        
        self.log_activity(f"🔍 Starting Southwark search for: '{keyword}'")
        
        try:
            search_data = {
                'searchType': 'Application',
                'searchCriteria.proposal': keyword,
                'action': 'search'
            }
            
            self.log_activity(f"🌐 Making POST request to Southwark portal")
            response = self.scraping_utils.post_request_with_session_init(
                self.search_url,
                search_data,
                urlparse(self.base_url).netloc
            )
            
            if not response:
                self.log_activity(f"❌ No response from Southwark search", "warning")
                return applications
            
            self.log_activity(f"✅ Received response, parsing results...")
            soup = BeautifulSoup(response.content, 'html.parser')
            results_table = soup.find('table', {'class': 'searchresults'})
            
            if results_table:
                result_rows = results_table.find_all('tr')[1:]
                self.log_activity(f"📊 Found {len(result_rows)} result rows in Southwark")
                
                for i, row in enumerate(result_rows[:SCRAPING_CONFIG['max_pages_per_borough']]):
                    try:
                        self.log_activity(f"📄 Processing Southwark row {i+1}")
                        app_data = self.parse_application_row(row, keyword)
                        if app_data:
                            applications.append(app_data)
                            self.log_activity(f"✅ Added Southwark application: {app_data.get('project_id')}")
                    except Exception as e:
                        self.log_activity(f"❌ Error processing Southwark row {i+1}: {str(e)}", "error")
                        continue
            else:
                self.log_activity(f"⚠️ No results table found in Southwark response", "warning")
        
        except Exception as e:
            self.log_activity(f"💥 Critical error in Southwark search: {str(e)}", "error")
        
        self.log_activity(f"🎉 Southwark search completed: {len(applications)} applications")
        return applications
    
    def parse_application_row(self, row, search_keyword: str) -> Optional[Dict]:
        """Parse Southwark application row - similar to Idox"""
        try:
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            app_link = cells[0].find('a')
            if not app_link:
                return None
            
            project_id = TextProcessor.clean_text(app_link.text)
            if not ValidationUtils.is_valid_project_id(project_id):
                return None
            
            application_url = urljoin(self.base_url, app_link.get('href', ''))
            address = TextProcessor.clean_text(cells[1].text) if len(cells) > 1 else ""
            title = TextProcessor.clean_text(cells[2].text) if len(cells) > 2 else ""
            
            # Get full details and detect keywords
            full_text = self.get_application_details(application_url)
            detected_keywords = TextProcessor.detect_keywords(full_text)
            
            if not detected_keywords:
                return None
            
            application_data = {
                'project_id': project_id,
                'borough': self.borough_name,
                'title': title,
                'address': address,
                'submission_date': None,  # Will be parsed from details if available
                'application_url': application_url,
                'detected_keywords': detected_keywords,
                'source_url': self.search_url
            }
            
            return ValidationUtils.validate_application_data(application_data)
            
        except Exception as e:
            logger.error(f"Error parsing Southwark application row: {e}")
            return None
    
    def get_application_details(self, application_url: str) -> str:
        """Get full application details from Southwark application page"""
        try:
            response = self.scraping_utils.rate_limited_request(
                application_url,
                domain=urlparse(self.base_url).netloc
            )
            
            if not response:
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            full_text = soup.get_text(separator=' ', strip=True)
            return TextProcessor.clean_text(full_text)
            
        except Exception as e:
            logger.error(f"Error getting Southwark application details: {e}")
            return ""

class SeleniumScraper(BaseScraper):
    """Selenium-based scraper for JavaScript-heavy portals"""
    
    def __init__(self, borough_name: str, activity_logger=None):
        super().__init__(borough_name, activity_logger)
        self.driver = None
        if SELENIUM_AVAILABLE:
            self.log_activity(f"🤖 Setting up Selenium WebDriver for {borough_name}")
            self.setup_driver()
        else:
            self.log_activity(f"⚠️ Selenium not available for {borough_name}", "warning")
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium dependencies not available")
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-tools')
            chrome_options.add_argument('--no-zygote')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={SCRAPING_CONFIG["user_agent"]}')
            
            # Try to use system chrome first (for cloud deployments)
            chrome_binary_locations = [
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser', 
                '/usr/bin/google-chrome',
                '/opt/google/chrome/chrome'
            ]
            
            for binary in chrome_binary_locations:
                if os.path.exists(binary):
                    chrome_options.binary_location = binary
                    break
            
            try:
                # Try using ChromeDriverManager first
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            except Exception:
                # Fallback to system chromedriver
                self.driver = webdriver.Chrome(options=chrome_options)
                
            self.driver.set_page_load_timeout(SCRAPING_CONFIG['timeout'])
            logger.info(f"Selenium driver setup complete for {self.borough_name}")
            
        except Exception as e:
            logger.error(f"Error setting up Selenium driver: {e}")
            self.driver = None
    
    def scrape_applications(self, keywords: List[str] = None) -> List[Dict]:
        """Scrape applications using Selenium"""
        if not SELENIUM_AVAILABLE:
            logger.warning(f"Selenium not available for {self.borough_name}. Returning empty results.")
            return []
            
        if not self.driver:
            logger.error("Selenium driver not available")
            return []
        
        if keywords is None:
            keywords = MONITORING_KEYWORDS
        
        all_applications = []
        
        for keyword in keywords:
            logger.info(f"Searching {self.borough_name} with Selenium for: {keyword}")
            try:
                keyword_apps = self.search_keyword_selenium(keyword)
                all_applications.extend(keyword_apps)
            except Exception as e:
                logger.error(f"Selenium search error for '{keyword}': {e}")
        
        # Remove duplicates
        unique_applications = {}
        for app in all_applications:
            project_id = app.get('project_id')
            if project_id and project_id not in unique_applications:
                unique_applications[project_id] = app
        
        return list(unique_applications.values())
    
    def search_keyword_selenium(self, keyword: str) -> List[Dict]:
        """Search using Selenium for JavaScript-rendered content"""
        applications = []
        
        try:
            self.driver.get(self.config['search_url'])
            time.sleep(2)
            
            # Look for search form elements
            search_input = None
            possible_selectors = [
                "input[name*='proposal']",
                "input[name*='description']",
                "input[id*='search']",
                "textarea[name*='proposal']"
            ]
            
            for selector in possible_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if search_input:
                search_input.clear()
                search_input.send_keys(keyword)
                
                # Find and click search button
                search_button = None
                button_selectors = [
                    "input[type='submit'][value*='Search']",
                    "button[type='submit']",
                    "input[value='Search']"
                ]
                
                for selector in button_selectors:
                    try:
                        search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if search_button:
                    search_button.click()
                    
                    # Wait for results
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    
                    # Parse results
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    applications = self.parse_selenium_results(soup, keyword)
        
        except Exception as e:
            logger.error(f"Selenium search error: {e}")
        
        return applications
    
    def parse_selenium_results(self, soup: BeautifulSoup, keyword: str) -> List[Dict]:
        """Parse search results from Selenium page source"""
        applications = []
        
        try:
            results_table = soup.find('table', {'class': 'searchresults'})
            if not results_table:
                return applications
            
            result_rows = results_table.find_all('tr')[1:]  # Skip header
            
            for row in result_rows:
                try:
                    app_data = self.parse_selenium_row(row, keyword)
                    if app_data:
                        applications.append(app_data)
                except Exception as e:
                    logger.error(f"Error parsing Selenium row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing Selenium results: {e}")
        
        return applications
    
    def parse_selenium_row(self, row, keyword: str) -> Optional[Dict]:
        """Parse individual result row from Selenium"""
        # Similar to Idox parsing logic
        try:
            cells = row.find_all('td')
            if len(cells) < 3:
                return None
            
            app_link = cells[0].find('a')
            if not app_link:
                return None
            
            project_id = TextProcessor.clean_text(app_link.text)
            if not ValidationUtils.is_valid_project_id(project_id):
                return None
            
            application_url = urljoin(self.config['base_url'], app_link.get('href', ''))
            address = TextProcessor.clean_text(cells[1].text) if len(cells) > 1 else ""
            title = TextProcessor.clean_text(cells[2].text) if len(cells) > 2 else ""
            
            # Basic keyword detection (full details would require additional requests)
            full_text = f"{title} {address}".lower()
            detected_keywords = TextProcessor.detect_keywords(full_text)
            
            if not detected_keywords:
                return None
            
            application_data = {
                'project_id': project_id,
                'borough': self.borough_name,
                'title': title,
                'address': address,
                'submission_date': None,
                'application_url': application_url,
                'detected_keywords': detected_keywords,
                'source_url': self.config['search_url']
            }
            
            return ValidationUtils.validate_application_data(application_data)
            
        except Exception as e:
            logger.error(f"Error parsing Selenium row: {e}")
            return None
    
    def close(self):
        """Close Selenium driver"""
        if self.driver:
            self.driver.quit()
            logger.info(f"Selenium driver closed for {self.borough_name}")

def create_scraper(borough_name: str, activity_logger=None) -> BaseScraper:
    """Factory function to create appropriate scraper for each borough with activity logging"""
    if borough_name in ["Camden", "Westminster", "Hammersmith & Fulham", "Tower Hamlets"]:
        return IdoxScraper(borough_name, activity_logger)
    elif borough_name == "Southwark":
        return SouthwarkScraper(borough_name, activity_logger)
    else:
        # Fallback to Selenium scraper for unknown portals
        return SeleniumScraper(borough_name, activity_logger) 