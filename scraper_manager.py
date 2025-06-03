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
    """Manages the scraping process across all boroughs with ultra-granular real-time status tracking"""
    
    def __init__(self, db_path: str = None, progress_callback: Callable = None):
        self.database = PlanningDatabase(db_path)
        self.scrapers = {}
        self.scraping_status = {}
        self.is_running = False
        self.current_progress = {}  # Track current keyword being searched per borough
        self.progress_callback = progress_callback  # Callback for UI updates
        self.live_activity = []  # Store live activity logs
        self.url_tracking = {}  # Track current URLs being accessed
        
    def log_activity(self, message: str, borough: str = None, level: str = "info"):
        """Log activity with timestamp for real-time display"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'borough': borough,
            'level': level,
            'full_timestamp': datetime.now().isoformat()
        }
        
        self.live_activity.append(log_entry)
        
        # Keep only last 100 entries to prevent memory issues
        if len(self.live_activity) > 100:
            self.live_activity = self.live_activity[-100:]
        
        # Also log to standard logger
        if level == "error":
            logger.error(f"[{borough or 'SYSTEM'}] {message}")
        elif level == "warning":
            logger.warning(f"[{borough or 'SYSTEM'}] {message}")
        else:
            logger.info(f"[{borough or 'SYSTEM'}] {message}")
    
    def update_url_tracking(self, borough_name: str, current_url: str = None, action: str = None):
        """Track current URL being accessed for real-time display"""
        if borough_name not in self.url_tracking:
            self.url_tracking[borough_name] = {}
        
        self.url_tracking[borough_name].update({
            'current_url': current_url,
            'action': action,
            'last_updated': datetime.now().isoformat()
        })
        
        # Log the activity
        if current_url and action:
            self.log_activity(f"{action}: {current_url}", borough_name)
    
    def initialize_scrapers(self):
        """Initialize scrapers for all configured boroughs"""
        self.log_activity("🔧 Initializing scrapers for all boroughs...")
        
        for borough_name in BOROUGHS_CONFIG.keys():
            try:
                self.log_activity(f"Creating scraper instance...", borough_name)
                
                # Pass the log_activity method as the activity logger
                scraper = create_scraper(borough_name, activity_logger=self.log_activity)
                self.scrapers[borough_name] = scraper
                
                self.scraping_status[borough_name] = {
                    'status': 'initialized',
                    'last_run': None,
                    'last_error': None,
                    'applications_found': 0,
                    'current_keyword': None,
                    'keywords_completed': 0,
                    'total_keywords': 0,
                    'start_time': None,
                    'requests_made': 0,
                    'pages_processed': 0,
                    'current_phase': 'idle'
                }
                self.current_progress[borough_name] = {
                    'current_keyword': None,
                    'keyword_index': 0,
                    'total_keywords': 0
                }
                
                self.log_activity(f"✅ Scraper initialized successfully", borough_name)
                
            except Exception as e:
                self.log_activity(f"❌ Failed to initialize scraper: {str(e)}", borough_name, "error")
                self.scraping_status[borough_name] = {
                    'status': 'error',
                    'last_run': None,
                    'last_error': str(e),
                    'applications_found': 0,
                    'current_keyword': None,
                    'keywords_completed': 0,
                    'total_keywords': 0,
                    'start_time': None,
                    'requests_made': 0,
                    'pages_processed': 0,
                    'current_phase': 'error'
                }
        
        self.log_activity(f"🎯 All scrapers initialized. Ready to begin scraping.")
    
    def update_progress(self, borough_name: str, keyword: str = None, keyword_index: int = 0, total_keywords: int = 0, phase: str = None):
        """Update progress tracking for real-time display"""
        if borough_name in self.current_progress:
            self.current_progress[borough_name].update({
                'current_keyword': keyword,
                'keyword_index': keyword_index,
                'total_keywords': total_keywords
            })
            
            # Also update scraping status
            if borough_name in self.scraping_status:
                updates = {
                    'current_keyword': keyword,
                    'keywords_completed': keyword_index,
                    'total_keywords': total_keywords
                }
                if phase:
                    updates['current_phase'] = phase
                
                self.scraping_status[borough_name].update(updates)
            
            # Log progress update
            if keyword:
                progress_pct = (keyword_index / total_keywords * 100) if total_keywords > 0 else 0
                self.log_activity(f"📊 Progress: {keyword_index}/{total_keywords} ({progress_pct:.1f}%) - {keyword}", borough_name)
            
            # Call progress callback if provided (for UI updates)
            if self.progress_callback:
                try:
                    self.progress_callback(borough_name, keyword, keyword_index, total_keywords)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def scrape_single_borough(self, borough_name: str, keywords: List[str] = None) -> Dict:
        """Scrape a single borough with ultra-detailed progress tracking"""
        if borough_name not in self.scrapers:
            error_msg = f"No scraper available for {borough_name}"
            self.log_activity(error_msg, borough_name, "error")
            return {'success': False, 'error': error_msg}
        
        if keywords is None:
            keywords = MONITORING_KEYWORDS
            
        scraper = self.scrapers[borough_name]
        start_time = datetime.now()
        
        self.log_activity(f"🚀 Starting scraping session with {len(keywords)} keywords", borough_name)
        
        try:
            # Update status to running
            self.scraping_status[borough_name].update({
                'status': 'running',
                'start_time': start_time.isoformat(),
                'total_keywords': len(keywords),
                'keywords_completed': 0,
                'current_keyword': None,
                'requests_made': 0,
                'pages_processed': 0,
                'current_phase': 'starting'
            })
            
            # Get base configuration for URL tracking
            config = BOROUGHS_CONFIG[borough_name]
            base_url = config['base_url']
            search_url = config['search_url']
            
            self.log_activity(f"🌐 Target portal: {base_url}", borough_name)
            self.log_activity(f"🔍 Search endpoint: {search_url}", borough_name)
            
            self.update_progress(borough_name, None, 0, len(keywords), "initializing")
            
            # Perform scraping with progress tracking
            all_applications = []
            
            for i, keyword in enumerate(keywords):
                if not self.is_running and len(keywords) > 1:  # Allow stopping mid-process
                    self.log_activity(f"⏹️ Stop signal received, terminating scraping", borough_name, "warning")
                    break
                    
                self.log_activity(f"🔍 Starting search for keyword: '{keyword}' ({i+1}/{len(keywords)})", borough_name)
                self.update_progress(borough_name, keyword, i, len(keywords), "searching")
                
                # Update URL tracking for the search
                self.update_url_tracking(borough_name, search_url, f"Searching for '{keyword}'")
                
                try:
                    # Get applications for this keyword with detailed tracking
                    self.log_activity(f"📝 Preparing search form data for '{keyword}'", borough_name)
                    
                    # Track the actual scraping call
                    if hasattr(scraper, 'search_keyword'):
                        self.log_activity(f"🕷️ Executing search request...", borough_name)
                        
                        # The scraper will now log its own detailed activity
                        keyword_apps = scraper.search_keyword(keyword)
                        
                        # Update request counter (scrapers will report their own requests)
                        if borough_name in self.scraping_status:
                            self.scraping_status[borough_name]['requests_made'] += 1
                        
                        self.log_activity(f"✅ Search completed. Found {len(keyword_apps)} applications for '{keyword}'", borough_name)
                        
                        # Update URL tracking for each application processed
                        for idx, app in enumerate(keyword_apps):
                            app_id = app.get('project_id', f'app_{idx}')
                            app_url = app.get('application_url', '')
                            
                            if app_url:
                                self.update_url_tracking(borough_name, app_url, f"Processed {app_id}")
                                
                                # Brief pause to show URL tracking
                                time.sleep(0.2)
                                
                                if borough_name in self.scraping_status:
                                    self.scraping_status[borough_name]['pages_processed'] += 1
                        
                        all_applications.extend(keyword_apps)
                        
                    else:
                        self.log_activity(f"⚠️ Scraper does not support keyword search", borough_name, "warning")
                    
                    # Small delay between keywords to be polite
                    self.log_activity(f"😴 Waiting 1 second before next keyword (rate limiting)", borough_name)
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"❌ Error searching for '{keyword}': {str(e)}"
                    self.log_activity(error_msg, borough_name, "error")
                    continue
                finally:
                    # Update progress
                    self.update_progress(borough_name, keyword, i + 1, len(keywords), "processing")
            
            # Process results
            self.log_activity(f"🔄 Processing {len(all_applications)} total applications", borough_name)
            self.update_progress(borough_name, None, len(keywords), len(keywords), "deduplicating")
            
            # Remove duplicates based on project_id
            unique_applications = {}
            for app in all_applications:
                project_id = app.get('project_id')
                if project_id and project_id not in unique_applications:
                    unique_applications[project_id] = app
                else:
                    self.log_activity(f"🔄 Duplicate found: {project_id}", borough_name)
            
            final_applications = list(unique_applications.values())
            self.log_activity(f"✨ Deduplicated to {len(final_applications)} unique applications", borough_name)
            
            # Store results in database
            self.log_activity(f"💾 Saving results to database...", borough_name)
            self.update_progress(borough_name, None, len(keywords), len(keywords), "saving")
            
            total_count, new_count = self.database.bulk_insert_applications(final_applications)
            
            self.log_activity(f"✅ Database updated: {new_count} new out of {total_count} total", borough_name)
            
            # Update status to completed
            self.scraping_status[borough_name].update({
                'status': 'completed',
                'last_run': start_time.isoformat(),
                'last_error': None,
                'applications_found': len(final_applications),
                'current_keyword': None,
                'keywords_completed': len(keywords),
                'current_phase': 'completed'
            })
            
            # Clear progress and URL tracking
            self.update_progress(borough_name, None, len(keywords), len(keywords), "completed")
            self.update_url_tracking(borough_name, None, "Completed")
            
            # Log scraping session
            self.database.log_scraping_session(
                borough=borough_name,
                records_found=total_count,
                records_new=new_count,
                status='success'
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            self.log_activity(f"🎉 Scraping completed successfully in {duration:.1f} seconds", borough_name)
            
            return {
                'success': True,
                'borough': borough_name,
                'total_found': len(final_applications),
                'new_applications': new_count,
                'keywords_searched': len(keywords),
                'duration': duration,
                'requests_made': self.scraping_status[borough_name].get('requests_made', 0),
                'pages_processed': self.scraping_status[borough_name].get('pages_processed', 0)
            }
            
        except Exception as e:
            error_msg = f"💥 Critical error during scraping: {str(e)}"
            self.log_activity(error_msg, borough_name, "error")
            
            # Update status with error
            self.scraping_status[borough_name].update({
                'status': 'error',
                'last_run': start_time.isoformat(),
                'last_error': str(e),
                'applications_found': 0,
                'current_keyword': None,
                'current_phase': 'error'
            })
            
            # Clear progress and URL tracking
            self.update_progress(borough_name, None, 0, len(keywords) if keywords else 0, "error")
            self.update_url_tracking(borough_name, None, "Error occurred")
            
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
            self.log_activity(f"🧹 Cleaning up scraper resources", borough_name)
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
        """Get current status of all scrapers with detailed progress information and live activity"""
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
            
            # Add URL tracking info
            if borough_name in self.url_tracking:
                enhanced_status['url_info'] = self.url_tracking[borough_name]
            
            enhanced_borough_status[borough_name] = enhanced_status
        
        # Get recent live activity (last 20 entries for UI)
        recent_activity = self.live_activity[-20:] if self.live_activity else []
        
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
            'live_activity': recent_activity,
            'url_tracking': self.url_tracking,
            'total_requests_made': sum(
                status.get('requests_made', 0) 
                for status in self.scraping_status.values()
            ),
            'total_pages_processed': sum(
                status.get('pages_processed', 0) 
                for status in self.scraping_status.values()
            ),
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