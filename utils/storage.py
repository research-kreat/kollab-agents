import os
import json
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Handles file-based storage operations for analysis results
    """
    def __init__(self, storage_dir="process_data"):
        """Initialize with a storage directory path"""
        self.storage_dir = storage_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # Create directories for companies if needed
        companies_dir = os.path.join(self.storage_dir, "companies")
        Path(companies_dir).mkdir(exist_ok=True)
        
    def _get_company_dir(self, company_id):
        """Get the directory for a specific company"""
        company_dir = os.path.join(self.storage_dir, "companies", company_id)
        Path(company_dir).mkdir(exist_ok=True)
        return company_dir
    
    def save_analysis(self, analysis_data, company_id, ticket_id=None):
        """
        Save analysis data to a JSON file
        
        Args:
            analysis_data: Dict containing analysis results
            company_id: Company identifier for organizing data
            ticket_id: Optional ticket identifier, generated if not provided
            
        Returns:
            Dict with status and ticket_id
        """
        try:
            # Generate ticket ID if not provided
            if not ticket_id:
                timestamp = int(time.time())
                ticket_id = f"{company_id}_{timestamp}"
            
            # Ensure company directory exists
            company_dir = self._get_company_dir(company_id)
            
            # Add status field if not present
            if 'status' not in analysis_data:
                analysis_data['status'] = 'new'
                
            # Add metadata if not present
            if 'metadata' not in analysis_data:
                analysis_data['metadata'] = {}
                
            # Add save timestamp
            analysis_data['metadata']['saved_at'] = int(time.time())
            analysis_data['ticket_id'] = ticket_id
            analysis_data['company_id'] = company_id
            
            # Initialize task status if not present in issues
            if 'final_report' in analysis_data and 'issues' in analysis_data['final_report']:
                for issue in analysis_data['final_report']['issues']:
                    if 'status' not in issue:
                        issue['status'] = 'new'
            
            # Save to file
            file_path = os.path.join(company_dir, f"{ticket_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2)
                
            logger.info(f"Saved analysis to {file_path}")
            return {
                'success': True,
                'ticket_id': ticket_id,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_analysis(self, company_id, ticket_id):
        """
        Retrieve a specific analysis by ticket ID
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket identifier
            
        Returns:
            Dict containing the analysis data or error
        """
        try:
            company_dir = self._get_company_dir(company_id)
            file_path = os.path.join(company_dir, f"{ticket_id}.json")
            
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'Analysis not found'}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                
            return {
                'success': True,
                'data': analysis_data
            }
            
        except Exception as e:
            logger.error(f"Error retrieving analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_analyses(self, company_id):
        """
        Get all analyses for a company
        
        Args:
            company_id: Company identifier
            
        Returns:
            List of analysis summary objects
        """
        try:
            company_dir = self._get_company_dir(company_id)
            analyses = []
            
            # List all JSON files in the company directory
            for file_name in os.listdir(company_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(company_dir, file_name)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                        
                    # Count tasks by status
                    task_status_counts = {'new': 0, 'processing': 0, 'resolved': 0}
                    if 'final_report' in analysis_data and 'issues' in analysis_data['final_report']:
                        for issue in analysis_data['final_report']['issues']:
                            status = issue.get('status', 'new')
                            if status in task_status_counts:
                                task_status_counts[status] += 1
                    
                    # Calculate overall status based on task statuses
                    total_tasks = sum(task_status_counts.values())
                    if total_tasks == 0:
                        overall_status = analysis_data.get('status', 'new')
                    elif task_status_counts['resolved'] == total_tasks:
                        overall_status = 'resolved'
                    elif task_status_counts['new'] == total_tasks:
                        overall_status = 'new'
                    else:
                        overall_status = 'processing'
                    
                    # Create a summary object with key information
                    summary = {
                        'ticket_id': analysis_data.get('ticket_id', file_name.replace('.json', '')),
                        'created_at': analysis_data.get('metadata', {}).get('saved_at', 0),
                        'status': overall_status,  # Use calculated overall status
                        'task_status_counts': task_status_counts,
                        'query': analysis_data.get('query', 'No query available'),
                        'summary': analysis_data.get('final_report', {}).get('executive_summary', 'No summary available'),
                        'issue_count': len(analysis_data.get('final_report', {}).get('issues', [])),
                    }
                    
                    analyses.append(summary)
            
            # Sort by creation date, newest first
            analyses.sort(key=lambda x: x['created_at'], reverse=True)
            return {
                'success': True,
                'data': analyses
            }
            
        except Exception as e:
            logger.error(f"Error retrieving analyses: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_analysis_status(self, company_id, ticket_id, new_status):
        """
        Update the status of an analysis
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket identifier
            new_status: New status value
            
        Returns:
            Dict with operation status
        """
        try:
            # Get the current analysis
            result = self.get_analysis(company_id, ticket_id)
            if not result['success']:
                return result
                
            analysis_data = result['data']
            
            # Update the status
            analysis_data['status'] = new_status
            analysis_data['metadata']['updated_at'] = int(time.time())
            
            # Save the updated analysis
            company_dir = self._get_company_dir(company_id)
            file_path = os.path.join(company_dir, f"{ticket_id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2)
                
            return {
                'success': True,
                'ticket_id': ticket_id,
                'status': new_status
            }
            
        except Exception as e:
            logger.error(f"Error updating analysis status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def update_task_status(self, company_id, ticket_id, task_index, new_status):
        """
        Update the status of a specific task within an analysis
        
        Args:
            company_id: Company identifier
            ticket_id: Ticket identifier
            task_index: Index of the task to update
            new_status: New status value for the task
            
        Returns:
            Dict with operation status
        """
        try:
            # Get the current analysis
            result = self.get_analysis(company_id, ticket_id)
            if not result['success']:
                return result
                
            analysis_data = result['data']
            
            # Update task status
            if ('final_report' in analysis_data and 
                'issues' in analysis_data['final_report'] and 
                task_index < len(analysis_data['final_report']['issues'])):
                
                analysis_data['final_report']['issues'][task_index]['status'] = new_status
                
                # Recalculate overall status
                task_count = len(analysis_data['final_report']['issues'])
                resolved_count = sum(1 for issue in analysis_data['final_report']['issues'] 
                                    if issue.get('status') == 'resolved')
                new_count = sum(1 for issue in analysis_data['final_report']['issues'] 
                               if issue.get('status') == 'new')
                
                if resolved_count == task_count:
                    analysis_data['status'] = 'resolved'
                elif new_count == task_count:
                    analysis_data['status'] = 'new'
                else:
                    analysis_data['status'] = 'processing'
                
                # Update timestamp
                analysis_data['metadata']['updated_at'] = int(time.time())
                
                # Save the updated analysis
                company_dir = self._get_company_dir(company_id)
                file_path = os.path.join(company_dir, f"{ticket_id}.json")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_data, f, indent=2)
                    
                return {
                    'success': True,
                    'ticket_id': ticket_id,
                    'task_index': task_index,
                    'task_status': new_status,
                    'overall_status': analysis_data['status']
                }
            else:
                return {
                    'success': False,
                    'error': 'Task not found in analysis'
                }
                
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }