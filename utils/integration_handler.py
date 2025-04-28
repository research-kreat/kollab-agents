import os
import json
import logging
import time
import requests
from typing import Dict, List, Any, Tuple, Optional
import tempfile
import csv
import pandas as pd

logger = logging.getLogger(__name__)

class IntegrationHandler:
    """Handles integrations with external data sources"""
    
    def __init__(self):
        """Initialize the integration handler"""
        self.temp_dir = tempfile.mkdtemp()
        
    def process_connected_sources(self, sources_data: Dict[str, Any]) -> Tuple[List[Dict], str]:
        """
        Process data from connected sources
        
        Args:
            sources_data: Dictionary containing connected sources data
            
        Returns:
            Tuple of (processed_content, file_type)
        """
        logger.info(f"Processing data from {len(sources_data)} connected sources")
        
        all_records = []
        file_type = "csv"  # Default file type
        
        for source, source_data in sources_data.items():
            try:
                # In a real implementation, this would make API calls to the connected services
                # For now, we'll simulate with sample data
                source_records, source_file_type = self._get_sample_data_for_source(source, source_data)
                
                # Append records and use last file type
                all_records.extend(source_records)
                file_type = source_file_type
                
                logger.info(f"Retrieved {len(source_records)} records from {source}")
            except Exception as e:
                logger.error(f"Error retrieving data from {source}: {str(e)}")
        
        logger.info(f"Total records from connected sources: {len(all_records)}")
        return all_records, file_type
    
    def _get_sample_data_for_source(self, source: str, source_data: Dict) -> Tuple[List[Dict], str]:
        """
        Generate sample data for a source
        
        Args:
            source: Source identifier (gdrive, slack, etc.)
            source_data: Data about the source connection
            
        Returns:
            Tuple of (records, file_type)
        """
        # Get files selected for this source
        files = source_data.get('files', [])
        
        # Create sample data based on source type and filenames
        records = []
        
        # Default file type
        file_type = "csv"
        
        # Simulate different data types based on source
        if source == 'gdrive':
            for file in files:
                if 'Survey' in file:
                    records.extend(self._generate_survey_data(15))
                elif 'Reviews' in file:
                    records.extend(self._generate_review_data(10))
                elif 'Tickets' in file:
                    records.extend(self._generate_ticket_data(20))
                elif 'Consolidated' in file:
                    records.extend(self._generate_consolidated_feedback(25))
        
        elif source == 'slack':
            records.extend(self._generate_chat_data(20, source='slack'))
        
        elif source == 'teams':
            records.extend(self._generate_chat_data(15, source='teams'))
            
            for file in files:
                if '.xlsx' in file or '.csv' in file:
                    if 'Feedback' in file:
                        records.extend(self._generate_survey_data(10))
                    elif 'Issue' in file:
                        records.extend(self._generate_ticket_data(12))
        
        elif source == 'skype':
            records.extend(self._generate_chat_data(10, source='skype'))
        
        elif source == 'jira':
            for file in files:
                if 'Bugs' in file:
                    records.extend(self._generate_ticket_data(18, issue_type='bug'))
                elif 'Feature' in file:
                    records.extend(self._generate_ticket_data(12, issue_type='feature'))
                elif 'Customer' in file:
                    records.extend(self._generate_ticket_data(15, issue_type='feedback'))
                elif '.csv' in file:
                    records.extend(self._generate_consolidated_feedback(20))
        
        elif source == 'dropbox':
            for file in files:
                if 'Feedback' in file:
                    records.extend(self._generate_survey_data(10))
                elif 'Reviews' in file:
                    records.extend(self._generate_review_data(8))
                elif 'Tickets' in file or 'Issues' in file:
                    records.extend(self._generate_ticket_data(15))
                elif 'Consolidated' in file:
                    records.extend(self._generate_consolidated_feedback(20))
        
        else:
            # Generic sample data
            records.extend(self._generate_consolidated_feedback(15))
        
        return records, file_type
    
    def _generate_survey_data(self, count: int) -> List[Dict]:
        """Generate sample survey data"""
        questions = [
            "How satisfied are you with our product?",
            "How likely are you to recommend our product to others?",
            "What features would you like to see improved?",
            "How would you rate our customer support?",
            "What issues did you encounter while using our product?"
        ]
        
        ratings = ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"]
        ratings_numeric = [1, 2, 3, 4, 5]
        
        records = []
        
        for i in range(count):
            # Generate a mix of positive and negative feedback
            sentiment = i % 5  # 0-4 range
            satisfaction = ratings[sentiment]
            rating = ratings_numeric[sentiment]
            
            # Generate different feedback based on sentiment
            if sentiment <= 1:  # Negative feedback
                feedback = [
                    "The product is too slow and crashes frequently",
                    "I couldn't get the feature to work properly",
                    "The interface is confusing and hard to navigate",
                    "Customer support was unhelpful and slow to respond",
                    "Many bugs in the latest update"
                ][i % 5]
            elif sentiment == 2:  # Neutral feedback
                feedback = [
                    "Product works okay but could be improved",
                    "Some features are good, others need work",
                    "Interface is acceptable but not intuitive",
                    "Support response was average",
                    "Works most of the time with occasional issues"
                ][i % 5]
            else:  # Positive feedback
                feedback = [
                    "Love the product, very intuitive and useful",
                    "Great features, especially the new dashboard",
                    "The interface is clean and easy to use",
                    "Support team was very helpful and responsive",
                    "Works flawlessly on all my devices"
                ][i % 5]
            
            record = {
                "survey_id": f"SRV{1000 + i}",
                "user_id": f"USER{5000 + i}",
                "user_email": f"user{i}@example.com",
                "location": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"][i % 5],
                "question": questions[i % 5],
                "rating": rating,
                "satisfaction": satisfaction,
                "feedback": feedback,
                "timestamp": self._generate_timestamp(i)
            }
            records.append(record)
        
        return records
    
    def _generate_review_data(self, count: int) -> List[Dict]:
        """Generate sample product review data"""
        records = []
        
        for i in range(count):
            # Generate a mix of positive and negative reviews
            sentiment = i % 5  # 0-4 range
            rating = sentiment + 1  # 1-5 rating
            
            # Generate different review text based on sentiment
            if rating <= 2:  # Negative reviews
                review = [
                    "Disappointing product with many flaws. The app crashes frequently and loses my data.",
                    "Very frustrated with this product. Customer service is terrible and the software has too many bugs.",
                    "Waste of money. The interface is confusing and key features don't work properly.",
                    "Had high hopes but this product doesn't deliver. The performance is sluggish and unreliable."
                ][i % 4]
            elif rating == 3:  # Neutral reviews
                review = [
                    "Average product. Some good features but also some annoying bugs that need to be fixed.",
                    "Works okay but nothing special. Would be better with improvements to the UI.",
                    "Decent product but overpriced for what it offers. Needs more features to justify the cost."
                ][i % 3]
            else:  # Positive reviews
                review = [
                    "Excellent product! Very intuitive and has all the features I need.",
                    "Great experience overall. The interface is clean and the performance is solid.",
                    "Outstanding software. Has saved me hours of work and the support team is fantastic.",
                    "Best in class. Very reliable and the recent updates have made it even better."
                ][i % 4]
            
            platform = ["App Store", "Google Play", "Website", "Email Survey"][i % 4]
            version = f"v{2 + (i % 3)}.{i % 10}"
            
            record = {
                "review_id": f"REV{2000 + i}",
                "user_name": f"Reviewer{i}",
                "platform": platform,
                "version": version,
                "rating": rating,
                "review_text": review,
                "timestamp": self._generate_timestamp(i)
            }
            records.append(record)
        
        return records
    
    def _generate_ticket_data(self, count: int, issue_type: str = None) -> List[Dict]:
        """Generate sample support ticket data"""
        statuses = ["Open", "In Progress", "Resolved", "Closed"]
        priorities = ["Low", "Medium", "High", "Critical"]
        types = ["Bug", "Feature Request", "Question", "Feedback"]
        
        if issue_type:
            issue_type = issue_type.capitalize()
            types = [t for t in types if issue_type in t] or types
        
        records = []
        
        for i in range(count):
            status = statuses[i % len(statuses)]
            priority = priorities[i % len(priorities)]
            ticket_type = types[i % len(types)]
            
            # Generate subject and description based on ticket type
            if ticket_type == "Bug":
                subjects = [
                    "Application crashes when exporting large files",
                    "Cannot save changes in profile settings",
                    "Search feature returns incorrect results",
                    "Login fails intermittently",
                    "Data not syncing between devices"
                ]
                descriptions = [
                    "When I try to export files larger than 10MB, the application crashes without warning.",
                    "Every time I try to save changes to my profile settings, I get an error message.",
                    "The search feature is not working correctly. It returns unrelated results or misses obvious matches.",
                    "I'm frequently unable to log in, getting 'Invalid credentials' even though I know my password is correct.",
                    "Changes made on my phone are not appearing on my desktop app, even after waiting for hours."
                ]
            elif ticket_type == "Feature Request":
                subjects = [
                    "Add dark mode option",
                    "Need ability to export to PDF",
                    "Request for bulk editing feature",
                    "Allow customizable dashboards",
                    "Add integration with Google Calendar"
                ]
                descriptions = [
                    "Please add a dark mode option to reduce eye strain when using the app at night.",
                    "Would like the ability to export reports as PDF files for sharing with clients.",
                    "Need a way to edit multiple items at once to save time when making similar changes.",
                    "Would be great if we could customize the dashboard to show the metrics most relevant to our workflow.",
                    "Please add integration with Google Calendar so appointments can be synced automatically."
                ]
            elif ticket_type == "Question":
                subjects = [
                    "How to reset password?",
                    "Where to find export options?",
                    "Is there a limit on number of users?",
                    "How to set up email notifications?",
                    "Can I use the app offline?"
                ]
                descriptions = [
                    "I forgot my password and need to reset it. Where is the reset option?",
                    "I need to export my data but can't find the export button. Please advise.",
                    "Is there a limit on how many user accounts I can create in my organization?",
                    "I'd like to receive notifications when new comments are added. How do I set this up?",
                    "Does the app work offline, or do I need an internet connection to use it?"
                ]
            else:  # Feedback
                subjects = [
                    "UI is confusing for new users",
                    "Love the new dashboard feature",
                    "App is too slow on older devices",
                    "Great customer support experience",
                    "Suggestion for improving the mobile app"
                ]
                descriptions = [
                    "As a new user, I found the interface quite confusing. It took me a while to figure out basic functions.",
                    "Just wanted to say I love the new dashboard feature. It's made my workflow much more efficient.",
                    "The app is getting very slow on my older device. It used to work fine but recent updates seem to have made it sluggish.",
                    "Had a great experience with your support team. They resolved my issue quickly and were very helpful.",
                    "The mobile app could be improved by adding the same features available in the desktop version."
                ]
            
            subject_index = i % len(subjects)
            
            record = {
                "ticket_id": f"TCK{3000 + i}",
                "customer_name": f"Customer{i}",
                "customer_email": f"customer{i}@example.com",
                "status": status,
                "priority": priority,
                "type": ticket_type,
                "subject": subjects[subject_index],
                "description": descriptions[subject_index],
                "created_at": self._generate_timestamp(i),
                "updated_at": self._generate_timestamp(i, offset_days=i % 3)
            }
            records.append(record)
        
        return records
    
    def _generate_chat_data(self, count: int, source: str = "slack") -> List[Dict]:
        """Generate sample chat conversation data"""
        records = []
        
        channels = {
            "slack": ["customer-feedback", "support-tickets", "product-discussions"],
            "teams": ["Customer Support Team", "Product Team", "Feedback"],
            "skype": ["Support Team", "Customer Feedback Group", "Product Team"]
        }
        
        channel_list = channels.get(source, ["general"])
        
        # Create conversation threads
        for i in range(count // 3 + 1):  # Create several conversation threads
            channel = channel_list[i % len(channel_list)]
            
            # Each thread has multiple messages
            for j in range(3):  # 3 messages per thread
                msg_index = i * 3 + j
                if msg_index >= count:
                    break
                    
                is_customer = j == 0  # First message in thread is from customer
                
                if is_customer:
                    # Customer messages - questions, issues, feedback
                    messages = [
                        "I've been having trouble with the export feature. It crashes whenever I try to export a large file.",
                        "The new update is causing the app to freeze frequently. Is anyone else experiencing this?",
                        "Is there a way to customize the dashboard? I can't find this option anywhere.",
                        "The mobile app is missing key features that are available on desktop. Very frustrating!",
                        "Search functionality isn't working properly. It's not finding relevant results.",
                        "Love the new UI design, but the performance seems to have gotten worse. Pages load slower now."
                    ]
                    sender = f"Customer{i}"
                    sender_email = f"customer{i}@example.com"
                else:
                    # Support or team member responses
                    if j == 1:
                        # First response
                        messages = [
                            "I'm sorry to hear you're experiencing issues. Can you tell me what size file you're trying to export?",
                            "Thanks for reporting this. We're investigating the freezing issue. What device and OS version are you using?",
                            "You can customize the dashboard by clicking the gear icon in the top right corner. Let me know if you need more help.",
                            "We're working on bringing feature parity to the mobile app. Which specific features are you missing?",
                            "I'll look into the search issue. Can you give me an example of a search term that's not working correctly?",
                            "Thanks for the feedback on the new UI! We're aware of some performance issues and working on optimizations."
                        ]
                    else:
                        # Follow-up response
                        messages = [
                            "We've identified the issue with exporting large files and a fix will be included in the next update.",
                            "Our team has reproduced the freezing bug and we're working on a fix. Should be resolved in the next few days.",
                            "I'm glad you found the customization options! Let us know if you have any other questions.",
                            "Thanks for the details. I've added your request for these features to our product roadmap.",
                            "We've found the issue with the search function and deployed a fix. Please try again and let us know if it's working now.",
                            "The performance optimization update will be released next week. Thank you for your patience!"
                        ]
                    
                    sender = f"Support{j}"
                    sender_email = f"support{j}@company.com"
                
                message = messages[i % len(messages)]
                
                record = {
                    "message_id": f"MSG{4000 + msg_index}",
                    "channel": channel,
                    "thread_id": f"THREAD{1000 + i}",
                    "sender": sender,
                    "sender_email": sender_email,
                    "is_customer": is_customer,
                    "message": message,
                    "timestamp": self._generate_timestamp(msg_index)
                }
                records.append(record)
        
        return records
    
    def _generate_consolidated_feedback(self, count: int) -> List[Dict]:
        """Generate a mix of different feedback types"""
        records = []
        
        # Get some of each type of feedback
        survey_count = count // 3
        review_count = count // 3
        ticket_count = count - survey_count - review_count
        
        records.extend(self._generate_survey_data(survey_count))
        records.extend(self._generate_review_data(review_count))
        records.extend(self._generate_ticket_data(ticket_count))
        
        return records
    
    def _generate_timestamp(self, index: int, offset_days: int = 0) -> str:
        """Generate a timestamp string, with more recent entries for lower indices"""
        now = time.time()
        # Go back in time based on index (newer entries first)
        # Add some randomness to make it more realistic
        offset = (index * 3600 * 12) + (offset_days * 3600 * 24)  # Hours and days offset
        timestamp = now - offset
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    
    def save_to_temp_file(self, records: List[Dict], file_type: str = "csv") -> str:
        """
        Save records to a temporary file
        
        Args:
            records: List of record dictionaries
            file_type: File type/extension to save as
            
        Returns:
            Path to the temporary file
        """
        if not records:
            raise ValueError("No records to save")
        
        # Create a unique filename
        filename = f"temp_data_{int(time.time())}.{file_type}"
        file_path = os.path.join(self.temp_dir, filename)
        
        if file_type == "csv":
            # Save as CSV using pandas for proper handling
            df = pd.DataFrame(records)
            df.to_csv(file_path, index=False)
        elif file_type == "json":
            # Save as JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2)
        else:
            # Default to CSV for unsupported types
            df = pd.DataFrame(records)
            df.to_csv(file_path, index=False)
        
        logger.info(f"Saved {len(records)} records to {file_path}")
        return file_path