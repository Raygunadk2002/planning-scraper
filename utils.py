"""
Utility functions for Planning Scraper Application
Contains helper functions for web scraping, text processing, and validation
"""

import time
import logging
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set
import re
from datetime import datetime, timedelta

from config import SCRAPING_CONFIG, MONITORING_KEYWORDS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingUtils:
    """Utility class for web scraping operations"""
    
    def __init__(self):
        self.request_counts = {}
        self.last_request_times = {}
        self.session = requests.Session()  # Use session for cookie persistence
        
        # Enhanced headers to look more like a real browser
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """Check if we can fetch the URL according to robots.txt"""
        if not SCRAPING_CONFIG['respect_robots_txt']:
            return True
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # Allow by default if robots.txt is not accessible
    
    def rate_limited_request(self, url: str, domain: str = None, **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited HTTP request"""
        if domain is None:
            domain = urlparse(url).netloc
        
        # Implement rate limiting
        if domain in self.last_request_times:
            time_since_last = time.time() - self.last_request_times[domain]
            if time_since_last < SCRAPING_CONFIG['request_delay']:
                sleep_time = SCRAPING_CONFIG['request_delay'] - time_since_last
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Check robots.txt
        if not self.can_fetch(url):
            logger.warning(f"Robots.txt disallows fetching {url}")
            return None
        
        # Make request with retries
        for attempt in range(SCRAPING_CONFIG['max_retries']):
            try:
                response = self.session.get(
                    url, 
                    timeout=SCRAPING_CONFIG['timeout'],
                    **kwargs
                )
                
                self.last_request_times[domain] = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = min(30, SCRAPING_CONFIG['request_delay'] * (2 ** attempt))
                    logger.warning(f"Rate limited by server, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < SCRAPING_CONFIG['max_retries'] - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def post_request(self, url: str, data: Dict, domain: str = None, **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited HTTP POST request"""
        if domain is None:
            domain = urlparse(url).netloc
        
        # Implement rate limiting
        if domain in self.last_request_times:
            time_since_last = time.time() - self.last_request_times[domain]
            if time_since_last < SCRAPING_CONFIG['request_delay']:
                sleep_time = SCRAPING_CONFIG['request_delay'] - time_since_last
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Make POST request with retries
        for attempt in range(SCRAPING_CONFIG['max_retries']):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    timeout=SCRAPING_CONFIG['timeout'],
                    **kwargs
                )
                
                self.last_request_times[domain] = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = min(30, SCRAPING_CONFIG['request_delay'] * (2 ** attempt))
                    logger.warning(f"Rate limited by server, waiting {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                logger.error(f"POST request error (attempt {attempt + 1}): {e}")
                if attempt < SCRAPING_CONFIG['max_retries'] - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

    def initialize_session_for_domain(self, domain: str, search_url: str) -> bool:
        """Initialize session by visiting the search page first to get cookies/tokens"""
        try:
            logger.info(f"Initializing session for {domain}")
            
            # Visit the main search page first to get session cookies
            base_url = f"https://{domain}"
            response = self.session.get(base_url, timeout=SCRAPING_CONFIG['timeout'])
            
            if response.status_code == 200:
                logger.info(f"Successfully visited {domain} homepage")
                
                # Now visit the search page to get any search-specific cookies/tokens
                time.sleep(2)  # Wait a bit to look more human
                search_response = self.session.get(search_url, timeout=SCRAPING_CONFIG['timeout'])
                
                if search_response.status_code == 200:
                    logger.info(f"Successfully visited search page for {domain}")
                    return True
                else:
                    logger.warning(f"Search page returned {search_response.status_code} for {domain}")
                    return False
            else:
                logger.warning(f"Homepage returned {response.status_code} for {domain}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing session for {domain}: {e}")
            return False
    
    def post_request_with_session_init(self, url: str, data: dict, domain: str) -> requests.Response:
        """Make POST request with session initialization if needed"""
        try:
            # First try to initialize session
            if domain not in self.last_request_times:
                logger.info(f"First request to {domain}, initializing session...")
                self.initialize_session_for_domain(domain, url)
            
            # Update headers for POST request
            post_headers = {
                'Referer': url,
                'Origin': f"https://{domain}",
                'Content-Type': 'application/x-www-form-urlencoded',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            }
            
            # Rate limiting
            if domain in self.last_request_times:
                time_since_last = time.time() - self.last_request_times[domain]
                if time_since_last < SCRAPING_CONFIG['request_delay']:
                    sleep_time = SCRAPING_CONFIG['request_delay'] - time_since_last
                    logger.info(f"Rate limiting: waiting {sleep_time:.1f}s for {domain}")
                    time.sleep(sleep_time)
            
            # Make the POST request
            logger.info(f"Making POST request to {url}")
            response = self.session.post(
                url, 
                data=data, 
                headers=post_headers,
                timeout=SCRAPING_CONFIG['timeout'],
                allow_redirects=True
            )
            
            self.last_request_times[domain] = time.time()
            
            logger.info(f"POST response: {response.status_code} from {domain}")
            
            if response.status_code in [403, 429]:
                logger.warning(f"Blocked by {domain} (status {response.status_code}). May need manual intervention.")
            
            return response
            
        except Exception as e:
            logger.error(f"POST request error: {e}")
            return None

class TextProcessor:
    """Utility class for text processing and keyword detection"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    @staticmethod
    def detect_keywords(text: str, keywords: List[str] = None) -> List[str]:
        """Detect monitoring keywords in text"""
        if not text:
            return []
        
        if keywords is None:
            keywords = MONITORING_KEYWORDS
        
        text_lower = text.lower()
        detected = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(keyword)
        
        return detected
    
    @staticmethod
    def extract_project_id(text: str) -> Optional[str]:
        """Extract project/application ID from text"""
        if not text:
            return None
        
        # Common patterns for planning application IDs
        patterns = [
            r'(?:Ref|Reference|Application|App)[\s:]*([A-Z0-9/\-\.]+)',
            r'([0-9]{2,4}/[0-9]{4,6}/?[A-Z]*)',
            r'([A-Z]{2,4}[0-9]{4,8})',
            r'([0-9]{8,12})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Parse various date formats and return ISO date string"""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = TextProcessor.clean_text(date_str)
        
        # Common date formats
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',      # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',      # DD-MM-YYYY or MM-DD-YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',      # YYYY-MM-DD
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',      # DD Month YYYY
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})'     # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle different formats
                    if pattern == date_patterns[2]:  # YYYY-MM-DD
                        year, month, day = groups
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif pattern in [date_patterns[0], date_patterns[1]]:  # DD/MM/YYYY or DD-MM-YYYY
                        day, month, year = groups
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif pattern == date_patterns[3]:  # DD Month YYYY
                        day, month_name, year = groups
                        month_names = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12',
                            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                            'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                            'oct': '10', 'nov': '11', 'dec': '12'
                        }
                        month_num = month_names.get(month_name.lower())
                        if month_num:
                            return f"{year}-{month_num}-{day.zfill(2)}"
                    elif pattern == date_patterns[4]:  # Month DD, YYYY
                        month_name, day, year = groups
                        month_names = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12'
                        }
                        month_num = month_names.get(month_name.lower())
                        if month_num:
                            return f"{year}-{month_num}-{day.zfill(2)}"
                            
                except (ValueError, IndexError):
                    continue
        
        return None

class ValidationUtils:
    """Utility class for data validation"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def is_valid_project_id(project_id: str) -> bool:
        """Check if project ID looks valid"""
        if not project_id or len(project_id) < 4:
            return False
        
        # Must contain some alphanumeric characters
        return bool(re.search(r'[A-Za-z0-9]', project_id))
    
    @staticmethod
    def validate_application_data(data: Dict) -> Dict:
        """Validate and clean application data"""
        validated = {}
        
        # Required fields
        required_fields = ['project_id', 'borough']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
            validated[field] = TextProcessor.clean_text(str(data[field]))
        
        # Optional fields with validation
        if 'title' in data:
            validated['title'] = TextProcessor.clean_text(data['title'])
        
        if 'address' in data:
            validated['address'] = TextProcessor.clean_text(data['address'])
        
        if 'submission_date' in data:
            parsed_date = TextProcessor.parse_date(data['submission_date'])
            validated['submission_date'] = parsed_date
        
        if 'application_url' in data:
            url = data['application_url']
            if ValidationUtils.is_valid_url(url):
                validated['application_url'] = url
        
        if 'source_url' in data:
            url = data['source_url']
            if ValidationUtils.is_valid_url(url):
                validated['source_url'] = url
        
        if 'detected_keywords' in data:
            validated['detected_keywords'] = data['detected_keywords']
        else:
            validated['detected_keywords'] = []
        
        return validated 