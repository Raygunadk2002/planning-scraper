"""
Scraper Manager Module
Coordinates scraping across all London boroughs and manages the overall process
"""

import logging
import threading
import time
from typing import List, Dict, Optional
from datetime import datetime
import concurrent.futures

from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS
from database import PlanningDatabase
from scrapers import create_scraper
from utils import ValidationUtils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingManager:
    """Manages the scraping process across all boroughs"""
    
    def __init__(self, db_path: str = None):
        self.database = PlanningDatabase(db_path)
        self.scrapers = {}
        self.scraping_status = {}
        self.is_running = False
        
    def initialize_scrapers(self):
        """Initialize scrapers for all configured boroughs"""
        logger.info("Initializing scrapers for all boroughs...")
        
        for borough_name in BOROUGHS_CONFIG.keys():
            try:
                scraper = create_scraper(borough_name)
                self.scrapers[borough_name] = scraper
                self.scraping_status[borough_name] = {
                    'status': 'initialized',
                    'last_run': None,
                    'last_error': None,
                    'applications_found': 0
                }
                logger.info(f"Scraper initialized for {borough_name}")
            except Exception as e:
                logger.error(f"Failed to initialize scraper for {borough_name}: {e}")
                self.scraping_status[borough_name] = {
                    'status': 'error',
                    'last_run': None,
                    'last_error': str(e),
                    'applications_found': 0
                }
    
    def scrape_single_borough(self, borough_name: str, keywords: List[str] = None) -> Dict:
        """Scrape a single borough and return results"""
        if borough_name not in self.scrapers:
            logger.error(f"No scraper available for {borough_name}")
            return {'success': False, 'error': 'No scraper available'}
        
        scraper = self.scrapers[borough_name]
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting scraping for {borough_name}")
            self.scraping_status[borough_name]['status'] = 'running'
            
            # Perform scraping
            applications = scraper.scrape_applications(keywords)
            
            # Store results in database
            total_count, new_count = self.database.bulk_insert_applications(applications)
            
            # Update status
            self.scraping_status[borough_name].update({
                'status': 'completed',
                'last_run': start_time.isoformat(),
                'last_error': None,
                'applications_found': len(applications)
            })
            
            # Log scraping session
            self.database.log_scraping_session(
                borough=borough_name,
                records_found=total_count,
                records_new=new_count,
                status='success'
            )
            
            logger.info(f"Completed scraping for {borough_name}: {new_count} new out of {total_count} total")
            
            return {
                'success': True,
                'borough': borough_name,
                'total_found': len(applications),
                'new_applications': new_count,
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error scraping {borough_name}: {e}")
            
            # Update status with error
            self.scraping_status[borough_name].update({
                'status': 'error',
                'last_run': start_time.isoformat(),
                'last_error': str(e),
                'applications_found': 0
            })
            
            # Log error
            self.database.log_scraping_session(
                borough=borough_name,
                records_found=0,
                records_new=0,
                status='error',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'borough': borough_name,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
        
        finally:
            if hasattr(scraper, 'close'):
                scraper.close()
    
    def scrape_all_boroughs(self, keywords: List[str] = None, max_workers: int = 3) -> List[Dict]:
        """Scrape all boroughs using threading for efficiency"""
        if not self.scrapers:
            self.initialize_scrapers()
        
        self.is_running = True
        results = []
        
        logger.info(f"Starting scraping for all {len(self.scrapers)} boroughs...")
        
        # Use ThreadPoolExecutor to scrape multiple boroughs concurrently
        # but limit concurrent workers to avoid overwhelming servers
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks
            future_to_borough = {
                executor.submit(self.scrape_single_borough, borough, keywords): borough
                for borough in self.scrapers.keys()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_borough):
                borough = future_to_borough[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Scraping completed for {borough}: {result}")
                except Exception as e:
                    logger.error(f"Scraping failed for {borough}: {e}")
                    results.append({
                        'success': False,
                        'borough': borough,
                        'error': str(e)
                    })
        
        self.is_running = False
        
        # Summary
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        total_new = sum(r.get('new_applications', 0) for r in successful)
        total_found = sum(r.get('total_found', 0) for r in successful)
        
        logger.info(f"Scraping summary: {len(successful)} successful, {len(failed)} failed")
        logger.info(f"Total applications: {total_new} new out of {total_found} found")
        
        return results
    
    def scrape_specific_boroughs(self, borough_names: List[str], keywords: List[str] = None) -> List[Dict]:
        """Scrape specific boroughs"""
        if not self.scrapers:
            self.initialize_scrapers()
        
        results = []
        
        for borough_name in borough_names:
            if borough_name in self.scrapers:
                result = self.scrape_single_borough(borough_name, keywords)
                results.append(result)
            else:
                logger.warning(f"Scraper not available for {borough_name}")
                results.append({
                    'success': False,
                    'borough': borough_name,
                    'error': 'Scraper not available'
                })
        
        return results
    
    def get_scraping_status(self) -> Dict:
        """Get current status of all scrapers"""
        return {
            'is_running': self.is_running,
            'boroughs': self.scraping_status.copy(),
            'total_boroughs': len(self.scrapers),
            'database_stats': self.database.get_statistics()
        }
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_running = False
        logger.info("Scraping stop requested")
    
    def cleanup(self):
        """Clean up resources"""
        for scraper in self.scrapers.values():
            if hasattr(scraper, 'close'):
                try:
                    scraper.close()
                except Exception as e:
                    logger.error(f"Error closing scraper: {e}")
        
        self.scrapers.clear()
        logger.info("Scrapers cleaned up")

class ScheduledScraper:
    """Handles scheduled scraping operations"""
    
    def __init__(self, scraping_manager: ScrapingManager):
        self.manager = scraping_manager
        self.scheduler_running = False
        self.schedule_interval = 3600  # 1 hour in seconds
        
    def start_scheduled_scraping(self, interval_seconds: int = 3600):
        """Start scheduled scraping at regular intervals"""
        self.schedule_interval = interval_seconds
        self.scheduler_running = True
        
        def scheduled_run():
            while self.scheduler_running:
                try:
                    logger.info("Starting scheduled scraping...")
                    results = self.manager.scrape_all_boroughs()
                    
                    # Log summary
                    successful = sum(1 for r in results if r.get('success'))
                    logger.info(f"Scheduled scraping completed: {successful}/{len(results)} successful")
                    
                except Exception as e:
                    logger.error(f"Error in scheduled scraping: {e}")
                
                # Wait for next scheduled run
                time.sleep(self.schedule_interval)
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=scheduled_run, daemon=True)
        scheduler_thread.start()
        logger.info(f"Scheduled scraping started with {interval_seconds}s interval")
    
    def stop_scheduled_scraping(self):
        """Stop scheduled scraping"""
        self.scheduler_running = False
        logger.info("Scheduled scraping stopped")

# Convenience functions for standalone usage
def scrape_all_boroughs(keywords: List[str] = None) -> List[Dict]:
    """Convenience function to scrape all boroughs"""
    manager = ScrapingManager()
    try:
        return manager.scrape_all_boroughs(keywords)
    finally:
        manager.cleanup()

def scrape_borough(borough_name: str, keywords: List[str] = None) -> Dict:
    """Convenience function to scrape a single borough"""
    manager = ScrapingManager()
    try:
        manager.initialize_scrapers()
        return manager.scrape_single_borough(borough_name, keywords)
    finally:
        manager.cleanup()

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        borough = sys.argv[1]
        if borough in BOROUGHS_CONFIG:
            result = scrape_borough(borough)
            print(f"Scraping result for {borough}: {result}")
        else:
            print(f"Unknown borough: {borough}")
    else:
        results = scrape_all_boroughs()
        print(f"Scraping completed. Results: {results}") 