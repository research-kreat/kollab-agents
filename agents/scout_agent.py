from crewai import Agent, Task, Crew, Process
import logging
import json
import time
import uuid
import re
from collections import Counter

class ScoutAgent:
    def __init__(self, socket_instance=None):
        """Initialize the Scout Agent"""
        # Store SocketIO instance for emitting events
        self.socketio = socket_instance
        
        # Initialize CrewAI Agent for scouting/information gathering
        self.agent = Agent(
            role="Data Scout Specialist",
            goal="Extract key insights from user feedback to identify issue types and priorities",
            backstory="You are an expert at analyzing customer feedback and identifying common patterns and issues.",
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
        
    def emit_log(self, message):
        """Emits a log message to the client via socket.io"""
        print(f"SCOUT: {message}")
        if self.socketio:
            self.socketio.emit('scout_log', {'message': message})

    def clean_text(self, text):
        """Clean and normalize text for better analysis"""
        if not text:
            return ""
        text = str(text)
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespaces with single space
        text = text.replace('\r\n', '\n').replace('\r', '\n')  # Normalize line breaks
        return text.strip()  # Remove leading/trailing whitespace
    
    def extract_metadata(self, content):
        """Extract metadata and categorize feedback for better context"""
        metadata = {
            "categories": Counter(),
            "sources": Counter(),
            "avg_length": 0,
            "has_structured_fields": False,
            "field_statistics": Counter(),
            "users": Counter(),
            "user_location": Counter(),  # New field for user locations
            "potential_tags": Counter()   # New field to track potential tags
        }
        
        total_length = 0
        all_fields = set()
        
        # Common tag categories to look for
        tag_indicators = {
            'refund': ['refund', 'money back', 'return payment'],
            'replacement': ['replacement', 'replace', 'new product'],
            'update': ['update', 'upgrade', 'new version', 'software'],
            'bug': ['bug', 'error', 'crash', 'not working'],
            'feature': ['feature', 'add', 'missing', 'would be nice'],
            'usability': ['difficult', 'confusing', 'hard to use', 'not intuitive'],
            'performance': ['slow', 'lag', 'freeze', 'performance'],
            'billing': ['bill', 'charge', 'subscription', 'payment'],
            'support': ['support', 'help', 'service', 'contact'],
            'quality': ['quality', 'poor', 'bad', 'excellent', 'good']
        }
        
        for record in content:
            # Track fields
            record_fields = set(record.keys())
            all_fields.update(record_fields)
            for field in record_fields:
                metadata["field_statistics"][field] += 1
            
            # Look for categories and sources
            if "category" in record:
                metadata["categories"][str(record["category"])] += 1
            elif "type" in record:
                metadata["categories"][str(record["type"])] += 1
                
            if "source" in record:
                metadata["sources"][str(record["source"])] += 1
            elif "channel" in record:
                metadata["sources"][str(record["channel"])] += 1
            
            # Track users/usernames and location if available
            user_found = False
            for user_field in ["user", "username", "user_id", "customer", "customer_id", "name", "email"]:
                if user_field in record and record[user_field]:
                    metadata["users"][str(record[user_field])] += 1
                    user_found = True
                    break
            
            # Check for location information
            for location_field in ["location", "country", "city", "region", "address"]:
                if location_field in record and record[location_field]:
                    metadata["user_location"][str(record[location_field])] += 1
                    break
            
            # Calculate average text length and detect potential tags
            feedback_text = ""
            for field in ["text", "message", "feedback", "content", "description"]:
                if field in record and record[field]:
                    feedback_text = str(record[field])
                    
                    # Check for tag indicators in the text
                    feedback_lower = feedback_text.lower()
                    for tag, keywords in tag_indicators.items():
                        for keyword in keywords:
                            if keyword in feedback_lower:
                                metadata["potential_tags"][tag] += 1
                                break
                    
                    break
            
            total_length += len(feedback_text)
        
        # Set average length and structure info
        if content:
            metadata["avg_length"] = total_length / len(content)
        metadata["has_structured_fields"] = len(all_fields) > 2
        metadata["common_fields"] = [field for field, count in metadata["field_statistics"].most_common(5)]
        
        # Extract top potential tags
        metadata["suggested_tags"] = [tag for tag, count in metadata["potential_tags"].most_common(5)]
        
        return metadata

    def format_all_feedback(self, all_feedback, user_map=None, location_map=None, max_token_estimate=100000):
        """
        Format all feedback data without sampling, only cleaning whitespace
        
        Args:
            all_feedback: List of all feedback text
            user_map: Dictionary mapping feedback to usernames
            location_map: Dictionary mapping feedback to user locations
            max_token_estimate: Rough limit to ensure we don't exceed token limits
            
        Returns:
            Formatted string with all cleaned feedback
        """
        if not all_feedback:
            return "No feedback available for analysis."
            
        # Clean all feedback and remove any empty items
        cleaned_feedback = [self.clean_text(item) for item in all_feedback if item and self.clean_text(item)]
        
        # Format with numbers
        formatted_texts = []
        total_chars = 0
        char_limit = max_token_estimate * 4  # Rough estimate of chars per token
        
        for i, text in enumerate(cleaned_feedback, 1):
            metadata = ""
            if user_map and text in user_map and user_map[text]:
                metadata += f" (User: {user_map[text]})"
                
            if location_map and text in location_map and location_map[text]:
                metadata += f" (Location: {location_map[text]})"
                
            feedback_entry = f"Feedback {i}{metadata}: {text}"
            
            # Check if we're approaching token limit
            if total_chars + len(feedback_entry) > char_limit:
                formatted_texts.append(f"... (and {len(cleaned_feedback) - i + 1} more feedback items not shown due to size constraints)")
                break
            
            formatted_texts.append(feedback_entry)
            total_chars += len(feedback_entry)
        
        return "\n\n".join(formatted_texts)

    def process_scout_query(self, data):
        """
        Process data with the Scout Agent
        
        Args:
            data: Dict containing 'content', 'query', and 'process_id'
            
        Returns:
            Dict containing scout analysis results
        """
        self.emit_log("Starting Scout Agent analysis...")
        
        content = data.get('content', [])
        query = data.get('query', 'What are the key issues and actionable insights from this feedback?')
        process_id = data.get('process_id', str(uuid.uuid4()))
        company_id = data.get('company_id', 'default_company')
        
        if not content:
            self.emit_log("⚠️ No content provided for analysis")
            return {'error': 'No content provided for analysis'}
        
        # Analyze the structure of records and extract metadata
        record_count = len(content)
        metadata = self.extract_metadata(content)
        self.emit_log(f"Analyzing {record_count} feedback records...")
        
        # Build user and location maps
        user_feedback_map = {}
        location_feedback_map = {}
        
        # Extract all text for analysis
        all_feedback = []
        for record in content:
            feedback_text = None
            username = None
            location = None
            
            # Try to get username
            for user_field in ["user", "username", "user_id", "customer", "customer_id", "name", "email"]:
                if user_field in record and record[user_field]:
                    username = str(record[user_field])
                    break
            
            # Try to get location
            for location_field in ["location", "country", "city", "region", "address"]:
                if location_field in record and record[location_field]:
                    location = str(record[location_field])
                    break
            
            # For text-based records
            if 'text' in record:
                feedback_text = record['text']
            # For email records
            elif 'message' in record:
                feedback_text = record['message']
            # Check common feedback field names
            else:
                for field in ['feedback', 'content', 'description', 'comment', 'issue', 'complaint']:
                    if field in record and record[field]:
                        feedback_text = str(record[field])
                        break
                
                # If no matching field, use all values concatenated
                if not feedback_text:
                    record_str = ' '.join(str(val) for val in record.values() if val)
                    feedback_text = record_str
            
            # Clean and add the feedback
            if feedback_text:
                cleaned_text = self.clean_text(feedback_text)
                all_feedback.append(cleaned_text)
                
                # Map feedback to username and location if available
                if username:
                    user_feedback_map[cleaned_text] = username
                if location:
                    location_feedback_map[cleaned_text] = location
        
        # Format all feedback (no sampling, just whitespace cleaning)
        self.emit_log(f"Formatting {len(all_feedback)} feedback items...")
        formatted_feedback = self.format_all_feedback(all_feedback, user_feedback_map, location_feedback_map)
        
        # Create the scout task with enhanced prompt for tagging
        suggested_tags = ", ".join(metadata.get("suggested_tags", []))
        scout_task = Task(
            description=f"""
            Analyze all customer feedback to identify key patterns and insights.
            
            Query: "{query}"
            
            Context: {record_count} feedback records. Avg length: {int(metadata["avg_length"])} chars.
            {", ".join(metadata["common_fields"][:3])} are common fields.
            Suggested tags based on content: {suggested_tags}
            
            Complete Feedback Data:
            {formatted_feedback}
            
            Task:
            1. Identify issue types with priorities (Critical/High/Medium/Low)
            2. Extract examples and key details for each issue
            3. Include sources with customer details where available
            4. Tag each issue with relevant categories (e.g. refund, replacement, update, bug, feature, etc.)
            5. Note common themes and overall sentiment
            6. Provide a summary of findings
            
            Format as JSON:
            {{
                "issue_types": [
                    {{
                        "type": "Issue name",
                        "examples": ["Example 1", "Example 2"],
                        "priority": "High/Medium/Low",
                        "key_details": "Important details",
                        "sources": ["User John from New York is facing battery drainage via Chat", "Battery issue reported by multiple customers via Slack", "Amaan Edwards via Social media"],
                        "tags": ["refund", "replacement", "bug"]
                    }}
                ],
                "common_themes": ["Theme 1", "Theme 2"],
                "overall_sentiment": "Positive/Negative/Neutral",
                "summary": "Overall summary"
            }}
            """,
            agent=self.agent,
            expected_output="Detailed analysis of user feedback in structured JSON format"
        )
        
        try:
            # Execute the task
            self.emit_log("Scout Agent is analyzing all feedback...")
            crew = Crew(
                agents=[self.agent],
                tasks=[scout_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Run the analysis
            result = crew.kickoff()
            print("[scout_task_PROMPT]", scout_task.description)
            
            # Parse the JSON response
            try:
                # Extract JSON from the response if it's embedded
                result_str = str(result)
                json_start = result_str.find('{')
                json_end = result_str.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = result_str[json_start:json_end]
                    parsed_result = json.loads(json_str)
                else:
                    parsed_result = {"error": "Could not extract JSON from response"}
                    
            except json.JSONDecodeError:
                self.emit_log("⚠️ Error parsing JSON from LLM response")
                parsed_result = {"error": "Invalid JSON format in response"}
                
            # Add metadata to the result
            final_result = {
                'process_id': process_id,
                'timestamp': int(time.time()),
                'query': query,
                'company_id': company_id,
                'record_count': record_count,
                'metadata': {
                    'avg_feedback_length': int(metadata["avg_length"]),
                    'common_fields': metadata["common_fields"],
                    'has_structured_data': metadata["has_structured_fields"],
                    'suggested_tags': metadata.get("suggested_tags", []),
                    'top_locations': [loc for loc, count in metadata.get("user_location", {}).most_common(3)]
                },
                'scout_analysis': parsed_result
            }
            
            self.emit_log("Scout analysis complete")
            return final_result
            
        except Exception as e:
            self.emit_log(f"⚠️ Error in Scout analysis: {str(e)}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'process_id': process_id,
                'company_id': company_id
            }