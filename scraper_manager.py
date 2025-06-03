"""
Scraper Manager Module
Coordinates scraping across all London boroughs and manages the overall process
"""

import logging
import threading
import time
from typing import List, Dict, Optional, Callable
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
    """Manages the scraping process across all boroughs with real-time status tracking"""
    
    def __init__(self, db_path: str = None, progress_callback: Callable = None):
        self.database = PlanningDatabase(db_path)
        self.scrapers = {}
        self.scraping_status = {}
        self.is_running = False
        self.current_progress = {}  # Track current keyword being searched per borough
        self.progress_callback = progress_callback  # Callback for UI updates
        
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
                    'applications_found': 0,
                    'current_keyword': None,
                    'keywords_completed': 0,
                    'total_keywords': 0,
                    'start_time': None
                }
                self.current_progress[borough_name] = {
                    'current_keyword': None,
                    'keyword_index': 0,
                    'total_keywords': 0
                }
                logger.info(f"Scraper initialized for {borough_name}")
            except Exception as e:
                logger.error(f"Failed to initialize scraper for {borough_name}: {e}")
                self.scraping_status[borough_name] = {
                    'status': 'error',
                    'last_run': None,
                    'last_error': str(e),
                    'applications_found': 0,
                    'current_keyword': None,
                    'keywords_completed': 0,
                    'total_keywords': 0,
                    'start_time': None
                }
    
    def update_progress(self, borough_name: str, keyword: str = None, keyword_index: int = 0, total_keywords: int = 0):
        """Update progress tracking for real-time display"""
        if borough_name in self.current_progress:
            self.current_progress[borough_name].update({
                'current_keyword': keyword,
                'keyword_index': keyword_index,
                'total_keywords': total_keywords
            })
            
            # Also update scraping status
            if borough_name in self.scraping_status:
                self.scraping_status[borough_name].update({
                    'current_keyword': keyword,
                    'keywords_completed': keyword_index,
                    'total_keywords': total_keywords
                })
            
            # Call progress callback if provided (for UI updates)
            if self.progress_callback:
                try:
                    self.progress_callback(borough_name, keyword, keyword_index, total_keywords)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def scrape_single_borough(self, borough_name: str, keywords: List[str] = None) -> Dict:
        """Scrape a single borough and return results with progress tracking"""
        if borough_name not in self.scrapers:
            logger.error(f"No scraper available for {borough_name}")
            return {'success': False, 'error': 'No scraper available'}
        
        if keywords is None:
            keywords = MONITORING_KEYWORDS
            
        scraper = self.scrapers[borough_name]
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting scraping for {borough_name} with {len(keywords)} keywords")
            
            # Update status to running
            self.scraping_status[borough_name].update({
                'status': 'running',
                'start_time': start_time.isoformat(),
                'total_keywords': len(keywords),
                'keywords_completed': 0,
                'current_keyword': None
            })
            
            # Perform scraping with progress tracking
            all_applications = []
            
            for i, keyword in enumerate(keywords):
                if not self.is_running and len(keywords) > 1:  # Allow stopping mid-process
                    break
                    
                logger.info(f"Searching {borough_name} for keyword '{keyword}' ({i+1}/{len(keywords)})")
                
                # Update progress
                self.update_progress(borough_name, keyword, i, len(keywords))
                
                try:
                    # Get applications for this keyword
                    keyword_apps = scraper.search_keyword(keyword) if hasattr(scraper, 'search_keyword') else []
                    all_applications.extend(keyword_apps)
                    
                    logger.info(f"Found {len(keyword_apps)} applications for '{keyword}' in {borough_name}")
                    
                    # Small delay between keywords to be polite
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error searching for '{keyword}' in {borough_name}: {e}")
                    continue
                finally:
                    # Update progress
                    self.update_progress(borough_name, keyword, i + 1, len(keywords))
            
            # Remove duplicates based on project_id
            unique_applications = {}
            for app in all_applications:
                project_id = app.get('project_id')
                if project_id and project_id not in unique_applications:
                    unique_applications[project_id] = app
            
            final_applications = list(unique_applications.values())
            
            # Store results in database
            total_count, new_count = self.database.bulk_insert_applications(final_applications)
            
            # Update status to completed
            self.scraping_status[borough_name].update({
                'status': 'completed',
                'last_run': start_time.isoformat(),
                'last_error': None,
                'applications_found': len(final_applications),
                'current_keyword': None,
                'keywords_completed': len(keywords)
            })
            
            # Clear progress
            self.update_progress(borough_name, None, len(keywords), len(keywords))
            
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
                'total_found': len(final_applications),
                'new_applications': new_count,
                'keywords_searched': len(keywords),
                'duration': (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error scraping {borough_name}: {e}")
            
            # Update status with error
            self.scraping_status[borough_name].update({
                'status': 'error',
                'last_run': start_time.isoformat(),
                'last_error': str(e),
                'applications_found': 0,
                'current_keyword': None
            })
            
            # Clear progress
            self.update_progress(borough_name, None, 0, len(keywords) if keywords else 0)
            
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
        """Get current status of all scrapers with detailed progress information"""
        # Get database statistics
        db_stats = self.database.get_statistics()
        
        # Calculate overall progress if scraping is running
        overall_progress = 0
        if self.is_running and self.scraping_status:
            total_boroughs = len(self.scraping_status)
            completed_boroughs = len([
                status for status in self.scraping_status.values() 
                if status.get('status') in ['completed', 'error']
            ])
            overall_progress = (completed_boroughs / total_boroughs) * 100 if total_boroughs > 0 else 0
        
        # Enhanced borough status with progress details
        enhanced_borough_status = {}
        for borough_name, status in self.scraping_status.items():
            enhanced_status = status.copy()
            
            # Add progress percentage for individual borough
            if status.get('total_keywords', 0) > 0:
                keyword_progress = (status.get('keywords_completed', 0) / status['total_keywords']) * 100
                enhanced_status['progress_percentage'] = round(keyword_progress, 1)
            else:
                enhanced_status['progress_percentage'] = 0
            
            # Add time elapsed if currently running
            if status.get('status') == 'running' and status.get('start_time'):
                try:
                    start_time = datetime.fromisoformat(status['start_time'])
                    elapsed_seconds = (datetime.now() - start_time).total_seconds()
                    enhanced_status['elapsed_time'] = round(elapsed_seconds, 1)
                    enhanced_status['elapsed_formatted'] = f"{int(elapsed_seconds // 60):02d}:{int(elapsed_seconds % 60):02d}"
                except:
                    enhanced_status['elapsed_time'] = 0
                    enhanced_status['elapsed_formatted'] = "00:00"
            
            # Add current progress info
            if borough_name in self.current_progress:
                enhanced_status.update(self.current_progress[borough_name])
            
            enhanced_borough_status[borough_name] = enhanced_status
        
        return {
            'is_running': self.is_running,
            'boroughs': enhanced_borough_status,
            'total_boroughs': len(self.scrapers),
            'overall_progress': round(overall_progress, 1),
            'database_stats': db_stats,
            'active_scrapers': len([
                status for status in self.scraping_status.values() 
                if status.get('status') == 'running'
            ]),
            'completed_scrapers': len([
                status for status in self.scraping_status.values() 
                if status.get('status') == 'completed'
            ]),
            'error_scrapers': len([
                status for status in self.scraping_status.values() 
                if status.get('status') == 'error'
            ]),
            'current_keywords': list(set([
                status.get('current_keyword') 
                for status in self.scraping_status.values() 
                if status.get('current_keyword')
            ])),
            'last_updated': datetime.now().isoformat()
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