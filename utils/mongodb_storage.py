import time
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class MongoDBStorage:
    """
    Handles MongoDB storage operations for analysis results
    """
    def __init__(self, connection_string="mongodb://localhost:27017/", database_name="KollabAgentic"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection URI
            database_name: Name of database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()
        
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB database: {self.database_name}")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def save_analysis(self, analysis_data, company_id, ticket_id=None):
        """
        Save analysis data to MongoDB
        
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
            
            # Create a clean copy without any ObjectId that might be present
            # This ensures we don't have serialization issues later
            analysis_data_clean = self._ensure_serializable(analysis_data)
            
            # Check if a document for this ticket_id already exists
            existing_doc = self.db.companies_tickets.find_one({"ticket_id": ticket_id})
            
            if existing_doc:
                # Update existing document
                result = self.db.companies_tickets.update_one(
                    {"ticket_id": ticket_id},
                    {"$set": analysis_data_clean}
                )
                logger.info(f"Updated existing analysis in MongoDB, ticket_id: {ticket_id}")
            else:
                # Insert new document
                result = self.db.companies_tickets.insert_one(analysis_data_clean)
                logger.info(f"Saved new analysis to MongoDB, ticket_id: {ticket_id}")
            
            return {
                'success': True,
                'ticket_id': ticket_id
            }
            
        except PyMongoError as e:
            logger.error(f"Error saving analysis to MongoDB: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _ensure_serializable(self, data):
        """
        Recursively process a dictionary to ensure all values are JSON serializable
        
        Args:
            data: Dict or list to process
            
        Returns:
            Dict or list with all values being JSON serializable
        """
        if isinstance(data, dict):
            return {k: self._ensure_serializable(v) for k, v in data.items() if k != '_id'}
        elif isinstance(data, list):
            return [self._ensure_serializable(item) for item in data]
        elif isinstance(data, ObjectId):
            return str(data)  # Convert ObjectId to string
        else:
            return data

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
            # Find document by ticket_id
            analysis_data = self.db.companies_tickets.find_one(
                {"ticket_id": ticket_id, "company_id": company_id},
                {"_id": 0}  # Exclude MongoDB _id from results
            )
            
            if not analysis_data:
                return {'success': False, 'error': 'Analysis not found'}
                
            return {
                'success': True,
                'data': analysis_data
            }
            
        except PyMongoError as e:
            logger.error(f"Error retrieving analysis from MongoDB: {str(e)}")
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
            # Find all documents for this company_id
            cursor = self.db.companies_tickets.find(
                {"company_id": company_id},
                {"_id": 0}  # Exclude MongoDB _id from results
            )
            
            analyses = []
            
            for analysis_data in cursor:
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
                    'ticket_id': analysis_data.get('ticket_id'),
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
            
        except PyMongoError as e:
            logger.error(f"Error retrieving analyses from MongoDB: {str(e)}")
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
            # Update the document status
            result = self.db.companies_tickets.update_one(
                {"ticket_id": ticket_id, "company_id": company_id},
                {
                    "$set": {
                        "status": new_status,
                        "metadata.updated_at": int(time.time())
                    }
                }
            )
            
            if result.matched_count == 0:
                return {'success': False, 'error': 'Analysis not found'}
                
            return {
                'success': True,
                'ticket_id': ticket_id,
                'status': new_status
            }
            
        except PyMongoError as e:
            logger.error(f"Error updating analysis status in MongoDB: {str(e)}")
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
                
                # Update task status in our local copy
                analysis_data['final_report']['issues'][task_index]['status'] = new_status
                
                # Prepare update operation
                update_field = f"final_report.issues.{task_index}.status"
                update_op = {
                    "$set": {
                        update_field: new_status,
                        "metadata.updated_at": int(time.time())
                    }
                }
                
                # Recalculate overall status
                task_count = len(analysis_data['final_report']['issues'])
                resolved_count = sum(1 for issue in analysis_data['final_report']['issues'] 
                                    if issue.get('status') == 'resolved')
                new_count = sum(1 for issue in analysis_data['final_report']['issues'] 
                               if issue.get('status') == 'new')
                
                if resolved_count == task_count:
                    overall_status = 'resolved'
                elif new_count == task_count:
                    overall_status = 'new'
                else:
                    overall_status = 'processing'
                
                # Add overall status to update operation
                update_op["$set"]["status"] = overall_status
                
                # Execute update in MongoDB
                update_result = self.db.companies_tickets.update_one(
                    {"ticket_id": ticket_id, "company_id": company_id},
                    update_op
                )
                
                if update_result.matched_count == 0:
                    return {'success': False, 'error': 'Analysis not found'}
                
                # Calculate task counts for response
                task_counts = {
                    'new': sum(1 for issue in analysis_data['final_report']['issues'] 
                              if issue.get('status') == 'new'),
                    'processing': sum(1 for issue in analysis_data['final_report']['issues'] 
                                     if issue.get('status') == 'processing'),
                    'resolved': sum(1 for issue in analysis_data['final_report']['issues'] 
                                   if issue.get('status') == 'resolved')
                }
                
                return {
                    'success': True,
                    'ticket_id': ticket_id,
                    'task_index': task_index,
                    'task_status': new_status,
                    'overall_status': overall_status,
                    'counts': task_counts
                }
            else:
                return {
                    'success': False,
                    'error': 'Task not found in analysis'
                }
                
        except PyMongoError as e:
            logger.error(f"Error updating task status in MongoDB: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }