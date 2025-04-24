from crewai import Agent, Task, Crew, Process
import logging
import json
import time
import uuid

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
        query = data.get('query', '')
        process_id = data.get('process_id', str(uuid.uuid4()))
        
        if not content:
            self.emit_log("⚠️ No content provided for analysis")
            return {'error': 'No content provided for analysis'}
        
        # Analyze the structure of records to understand what we're working with
        record_count = len(content)
        self.emit_log(f"Analyzing {record_count} records...")
        
        # Extract all text for analysis
        all_feedback = []
        for record in content:
            # For text-based records
            if 'text' in record:
                all_feedback.append(record['text'])
            # For email records that might have a message field
            elif 'message' in record:
                all_feedback.append(record['message'])
            # For records with multiple fields, look for likely feedback content
            else:
                # Check common feedback field names
                for field in ['feedback', 'content', 'description', 'comment', 'issue', 'complaint']:
                    if field in record and record[field]:
                        all_feedback.append(str(record[field]))
                        break
                else:
                    # If no matching field, use all values concatenated
                    record_str = ' '.join(str(val) for val in record.values() if val)
                    all_feedback.append(record_str)
        
        # Prepare samples for analysis (limit to avoid token issues)
        sample_size = min(50, len(all_feedback))
        samples = all_feedback[:sample_size]
        
        self.emit_log(f"Processing {sample_size} feedback samples...")
        
        # Create the scout task
        scout_task = Task(
            description=f"""
            Analyze the following user feedback to identify key patterns and insights.
            
            User Query: "{query}"
            
            Feedback Data:
            ```
            {samples}
            ```
            
            Your task is to:
            1. Identify the main types of issues present in the feedback
            2. Determine the priority or criticality of each issue type
            3. Extract key information that can help in resolving these issues
            4. Note any common themes or patterns across the feedback
            
            Format your response as a detailed JSON object with the following structure:
            {{
                "issue_types": [
                    {{
                        "type": "Type of issue (e.g., billing, technical, support)",
                        "examples": ["Example 1", "Example 2"],
                        "priority": "High/Medium/Low",
                        "key_details": "Important details related to this issue type"
                    }}
                ],
                "common_themes": ["Theme 1", "Theme 2"],
                "overall_sentiment": "Positive/Negative/Neutral",
                "summary": "Overall summary of the findings"
            }}
            """,
            agent=self.agent,
            expected_output="Detailed analysis of user feedback in structured JSON format"
        )
        
        try:
            # Execute the task
            self.emit_log("Scout Agent is analyzing feedback...")
            crew = Crew(
                agents=[self.agent],
                tasks=[scout_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Run the analysis
            result = crew.kickoff()

            print("[scout_task]",scout_task.description)
            
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
                'record_count': record_count,
                'scout_analysis': parsed_result
            }
            
            self.emit_log("Scout analysis complete")
            return final_result
            
        except Exception as e:
            self.emit_log(f"⚠️ Error in Scout analysis: {str(e)}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'process_id': process_id
            }