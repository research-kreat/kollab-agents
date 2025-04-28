import os
import json
import logging
import time
import requests
from typing import Dict, List, Any, Tuple, Optional, Union
import tempfile
import csv
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class IntegrationHandler:
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        
    def process_connected_sources(self, sources_data: Dict[str, Any]) -> Tuple[List[Dict], str]:
        logger.info(f"Processing data from {len(sources_data)} connected sources")
        
        all_records = []
        file_type = "csv"  # Default file type
        
        for source_name, source_data in sources_data.items():
            try:
                source_records, source_file_type = self.fetch_source_data(source_name, source_data)
                all_records.extend(source_records)
                file_type = source_file_type
                logger.info(f"Retrieved {len(source_records)} records from {source_name}")
            except Exception as e:
                logger.error(f"Error retrieving data from {source_name}: {str(e)}")
        
        logger.info(f"Total records from connected sources: {len(all_records)}")
        return all_records, file_type
    
    def fetch_source_data(self, source_name: str, source_data: Dict) -> Tuple[List[Dict], str]:
        files = source_data.get('files', [])
        
        if not files:
            logger.warning(f"No files selected for source {source_name}")
            return [], "csv"
        
        if source_name == 'gdrive':
            return self.process_gdrive_source(files, source_data)
        elif source_name == 'slack':
            return self.process_slack_source(files, source_data)
        elif source_name == 'teams':
            return self.process_teams_source(files, source_data)
        elif source_name == 'skype':
            return self.process_skype_source(files, source_data)
        elif source_name == 'jira':
            return self.process_jira_source(files, source_data)
        elif source_name == 'dropbox':
            return self.process_dropbox_source(files, source_data)
        else:
            logger.warning(f"Unknown source type: {source_name}")
            return [], "csv"
    
    def process_gdrive_source(self, files: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process files from Google Drive using API
        records = []
        file_type = "csv"
        
        for file_name in files:
            file_extension = Path(file_name).suffix.lower()
            file_records = []
            
            if file_extension == '.csv':
                file_records = self.process_csv_file(file_name, source_data)
            elif file_extension in ['.xlsx', '.xls']:
                file_records = self.process_excel_file(file_name, source_data)
            elif file_extension == '.json':
                file_records = self.process_json_file(file_name, source_data)
            elif file_extension == '.docx':
                file_records = self.process_docx_file(file_name, source_data)
            elif file_extension == '.txt':
                file_records = self.process_text_file(file_name, source_data)
            else:
                logger.warning(f"Unsupported file type for {file_name}")
                
            records.extend(file_records)
            
        return records, file_type
    
    def process_slack_source(self, channels: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process Slack channels using Slack API
        records = []
        file_type = "text"
        
        for channel in channels:
            channel_records = self.fetch_slack_channel_messages(channel, source_data)
            records.extend(channel_records)
            
        return records, file_type
    
    def process_teams_source(self, teams_resources: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process Microsoft Teams resources using Graph API
        records = []
        file_type = "text"
        
        for resource in teams_resources:
            if resource.endswith(('.xlsx', '.csv')):
                if resource.endswith('.xlsx'):
                    resource_records = self.process_excel_file(resource, source_data)
                else:
                    resource_records = self.process_csv_file(resource, source_data)
            else:
                resource_records = self.fetch_teams_channel_messages(resource, source_data)
                
            records.extend(resource_records)
            
        return records, file_type
    
    def process_skype_source(self, conversations: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process Skype conversations using Skype API
        records = []
        file_type = "text"
        
        for conversation in conversations:
            conversation_records = self.fetch_skype_conversation_messages(conversation, source_data)
            records.extend(conversation_records)
            
        return records, file_type
    
    def process_jira_source(self, resources: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process Jira issues using Jira API
        records = []
        file_type = "json"
        
        for resource in resources:
            if resource.endswith('.csv'):
                resource_records = self.process_csv_file(resource, source_data)
            else:
                resource_records = self.fetch_jira_issues(resource, source_data)
                
            records.extend(resource_records)
            
        return records, file_type
    
    def process_dropbox_source(self, files: List[str], source_data: Dict) -> Tuple[List[Dict], str]:
        # Process Dropbox files using Dropbox API
        records = []
        file_type = "csv"
        
        for file_name in files:
            file_extension = Path(file_name).suffix.lower()
            file_records = []
            
            if file_extension == '.csv':
                file_records = self.process_csv_file(file_name, source_data)
            elif file_extension in ['.xlsx', '.xls']:
                file_records = self.process_excel_file(file_name, source_data)
            elif file_extension == '.json':
                file_records = self.process_json_file(file_name, source_data)
            elif file_extension == '.docx':
                file_records = self.process_docx_file(file_name, source_data)
            elif file_extension == '.txt':
                file_records = self.process_text_file(file_name, source_data)
            else:
                logger.warning(f"Unsupported file type for {file_name}")
                
            records.extend(file_records)
            
        return records, file_type
    
    # File Processing Methods
    
    def process_csv_file(self, file_path: str, source_data: Dict) -> List[Dict]:
        logger.info(f"Processing CSV file: {file_path}")
        
        try:
            local_path = self.download_file(file_path, source_data)
            df = pd.read_csv(local_path)
            records = df.to_dict('records')
            
            if os.path.exists(local_path):
                os.remove(local_path)
                
            return records
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            return []
    
    def process_excel_file(self, file_path: str, source_data: Dict) -> List[Dict]:
        logger.info(f"Processing Excel file: {file_path}")
        
        try:
            local_path = self.download_file(file_path, source_data)
            df = pd.read_excel(local_path)
            records = df.to_dict('records')
            
            if os.path.exists(local_path):
                os.remove(local_path)
                
            return records
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {str(e)}")
            return []
    
    def process_json_file(self, file_path: str, source_data: Dict) -> List[Dict]:
        logger.info(f"Processing JSON file: {file_path}")
        
        try:
            local_path = self.download_file(file_path, source_data)
            
            with open(local_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = [data] if isinstance(data, dict) else data
                
            if os.path.exists(local_path):
                os.remove(local_path)
                
            return records
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {str(e)}")
            return []
    
    def process_docx_file(self, file_path: str, source_data: Dict) -> List[Dict]:
        logger.info(f"Processing DOCX file: {file_path}")
        
        try:
            local_path = self.download_file(file_path, source_data)
            import docx
            
            doc = docx.Document(local_path)
            content = []
            
            for para in doc.paragraphs:
                if para.text.strip():  # Skip empty paragraphs
                    content.append(para.text)
            
            records = [{'text': '\n'.join(content)}]
            
            if os.path.exists(local_path):
                os.remove(local_path)
                
            return records
        except Exception as e:
            logger.error(f"Error processing DOCX file {file_path}: {str(e)}")
            return []
    
    def process_text_file(self, file_path: str, source_data: Dict) -> List[Dict]:
        logger.info(f"Processing text file: {file_path}")
        
        try:
            local_path = self.download_file(file_path, source_data)
            
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            
            if ',' in lines[0]:
                try:
                    reader = csv.reader(lines)
                    headers = next(reader)
                    records = []
                    
                    for row in reader:
                        if len(row) == len(headers):
                            record = {headers[i]: row[i] for i in range(len(headers))}
                            records.append(record)
                    
                    if records:
                        if os.path.exists(local_path):
                            os.remove(local_path)
                        return records
                except:
                    pass  # If CSV parsing fails, continue with text processing
            
            records = [{'text': content}]
            
            if os.path.exists(local_path):
                os.remove(local_path)
                
            return records
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return []
    
    # API-specific fetch methods
    
    def fetch_slack_channel_messages(self, channel_name: str, source_data: Dict) -> List[Dict]:
        # Placeholder for Slack API integration
        logger.info(f"Fetching messages from Slack channel: {channel_name}")
        return []
    
    def fetch_teams_channel_messages(self, channel_name: str, source_data: Dict) -> List[Dict]:
        # Placeholder for Microsoft Teams API integration
        logger.info(f"Fetching messages from Teams channel: {channel_name}")
        return []
    
    def fetch_skype_conversation_messages(self, conversation_name: str, source_data: Dict) -> List[Dict]:
        # Placeholder for Skype API integration
        logger.info(f"Fetching messages from Skype conversation: {conversation_name}")
        return []
    
    def fetch_jira_issues(self, project_name: str, source_data: Dict) -> List[Dict]:
        # Placeholder for Jira API integration
        logger.info(f"Fetching issues from Jira project: {project_name}")
        return []
    
    def download_file(self, remote_path: str, source_data: Dict) -> str:
        # Generate a temporary local file path for the downloaded file
        source_type = source_data.get('source_type', 'unknown')
        logger.info(f"Downloading file {remote_path} from {source_type}")
        
        filename = os.path.basename(remote_path)
        local_path = os.path.join(self.temp_dir, f"{int(time.time())}_{filename}")
        
        # Placeholder for actual API download logic
        with open(local_path, 'w') as f:
            f.write('')
            
        return local_path
    
    def normalize_text_output(self, records: List[Dict]) -> List[Dict]:
        # Ensure all records have a consistent 'text' field
        normalized = []
        text_fields = ['text', 'content', 'message', 'feedback', 'description', 'comments', 'body']
        
        for record in records:
            normalized_record = record.copy()
            
            if 'text' not in normalized_record:
                for field in text_fields:
                    if field in normalized_record and normalized_record[field]:
                        normalized_record['text'] = normalized_record[field]
                        break
                else:
                    normalized_record['text'] = ' '.join(str(value) for value in normalized_record.values() if value)
            
            normalized.append(normalized_record)
            
        return normalized
        
    def get_source_file_structure(self, source_type: str) -> List[Dict]:
        # Get file structure from the appropriate source
        logger.info(f"Getting file structure for source: {source_type}")
        
        if source_type == 'gdrive':
            return self._get_gdrive_structure()
        elif source_type == 'slack':
            return self._get_slack_structure()
        elif source_type == 'teams':
            return self._get_teams_structure()
        elif source_type == 'skype':
            return self._get_skype_structure()
        elif source_type == 'jira':
            return self._get_jira_structure()
        elif source_type == 'dropbox':
            return self._get_dropbox_structure()
        else:
            return [{"type": "file", "name": "Sample Data.csv"}]
    
    def _get_gdrive_structure(self) -> List[Dict]:
        # Sample Google Drive file structure
        return [
            {"type": "folder", "name": "Feedback", "children": [
                {"type": "file", "name": "Customer Survey 2024.csv"},
                {"type": "file", "name": "App Reviews Q1.xlsx"},
                {"type": "file", "name": "Support Tickets March.csv"}
            ]},
            {"type": "folder", "name": "Reports", "children": [
                {"type": "file", "name": "User Feedback Summary.docx"},
                {"type": "file", "name": "Issue Tracking 2024.xlsx"}
            ]},
            {"type": "file", "name": "Product Feedback Consolidated.csv"}
        ]
    
    def _get_slack_structure(self) -> List[Dict]:
        # Sample Slack channel structure
        return [
            {"type": "folder", "name": "Channels", "children": [
                {"type": "file", "name": "customer-feedback"},
                {"type": "file", "name": "support-tickets"},
                {"type": "file", "name": "product-discussions"}
            ]},
            {"type": "folder", "name": "Direct Messages", "children": [
                {"type": "file", "name": "Support Team"},
                {"type": "file", "name": "Customer Success"}
            ]}
        ]
    
    def _get_teams_structure(self) -> List[Dict]:
        # Sample Microsoft Teams structure
        return [
            {"type": "folder", "name": "Teams", "children": [
                {"type": "file", "name": "Customer Support Team"},
                {"type": "file", "name": "Product Team"}
            ]},
            {"type": "folder", "name": "Channels", "children": [
                {"type": "file", "name": "Feedback"},
                {"type": "file", "name": "Bug Reports"}
            ]},
            {"type": "folder", "name": "Files", "children": [
                {"type": "file", "name": "Customer Feedback.xlsx"},
                {"type": "file", "name": "Issue Tracker.csv"}
            ]}
        ]
    
    def _get_skype_structure(self) -> List[Dict]:
        # Sample Skype conversation structure
        return [
            {"type": "folder", "name": "Group Chats", "children": [
                {"type": "file", "name": "Support Team"},
                {"type": "file", "name": "Customer Feedback Group"}
            ]},
            {"type": "folder", "name": "Recent Chats", "children": [
                {"type": "file", "name": "Enterprise Customers"},
                {"type": "file", "name": "Product Team"}
            ]}
        ]
    
    def _get_jira_structure(self) -> List[Dict]:
        # Sample Jira project structure
        return [
            {"type": "folder", "name": "Projects", "children": [
                {"type": "file", "name": "Customer Support"},
                {"type": "file", "name": "Product Development"}
            ]},
            {"type": "folder", "name": "Issues", "children": [
                {"type": "file", "name": "Bugs"},
                {"type": "file", "name": "Feature Requests"},
                {"type": "file", "name": "Customer Feedback"}
            ]},
            {"type": "folder", "name": "Reports", "children": [
                {"type": "file", "name": "Issue Summary.csv"},
                {"type": "file", "name": "Customer Satisfaction.csv"}
            ]}
        ]
    
    def _get_dropbox_structure(self) -> List[Dict]:
        # Sample Dropbox file structure
        return [
            {"type": "folder", "name": "Feedback", "children": [
                {"type": "file", "name": "Customer Feedback 2024.csv"},
                {"type": "file", "name": "Product Reviews.xlsx"}
            ]},
            {"type": "folder", "name": "Support", "children": [
                {"type": "file", "name": "Tickets.csv"},
                {"type": "file", "name": "Customer Issues.xlsx"}
            ]},
            {"type": "file", "name": "Consolidated Feedback.csv"}
        ]