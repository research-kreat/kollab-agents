from crewai import Agent, Task, Crew, Process
import logging
import json
import time

class AnalystAgent:
    def __init__(self, socket_instance=None):
        """Initialize the Analyst Agent"""
        # Store SocketIO instance for emitting events
        self.socketio = socket_instance
        
        # Initialize CrewAI Agent for deeper analysis
        self.agent = Agent(
            role="Feedback Analysis Expert",
            goal="Determine responsible teams and actionable recommendations based on feedback analysis",
            backstory="You are a senior analyst specializing in interpreting customer feedback and transforming it into actionable insights for organizations.",
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
        
    def emit_log(self, message):
        """Emits a log message to the client via socket.io"""
        print(f"ANALYST: {message}")
        if self.socketio:
            self.socketio.emit('analyst_log', {'message': message})

    def process_analyst_query(self, scout_results):
        """
        Process data with the Analyst Agent
        
        Args:
            scout_results: Dict containing results from the Scout Agent
            
        Returns:
            Dict containing analyst insights and recommendations
        """
        self.emit_log("Starting Analyst Agent processing...")
        
        if 'error' in scout_results:
            self.emit_log(f"⚠️ Error received from Scout Agent: {scout_results['error']}")
            return scout_results
        
        process_id = scout_results.get('process_id', 'unknown')
        query = scout_results.get('query', '')
        scout_analysis = scout_results.get('scout_analysis', {})
        
        # Create the analyst task
        analyst_task = Task(
            description=f"""
            Based on the following Scout Agent analysis, determine which internal teams should handle each issue, 
            recommend specific actions, and propose resolution strategies.
            
            User Query: "{query}"
            
            Scout Analysis:
            ```
            {json.dumps(scout_analysis, indent=2)}
            ```
            
            Your task is to:
            
            1. For each issue type identified, determine the internal team(s) (support, technical, billing, product, etc.) 
               that should be responsible for addressing it
               
            2. Recommend specific actions that each team should take to resolve the issues
            
            3. Assess the criticality of each issue (Critical, High, Medium, Low) based on:
               - Impact on user experience
               - Potential business impact
               - Urgency of resolution
               - Number of users affected
               
            4. Propose a comprehensive resolution strategy for each issue
            
            Format your response as a detailed JSON object with the following structure:
            {{
                "team_assignments": [
                    {{
                        "issue_type": "Type of issue from scout analysis",
                        "responsible_team": "Primary team responsible",
                        "supporting_teams": ["Team 1", "Team 2"],
                        "criticality": "Critical/High/Medium/Low",
                        "recommended_actions": [
                            "Specific action 1",
                            "Specific action 2"
                        ],
                        "resolution_strategy": "Detailed approach to resolving this issue"
                    }}
                ],
                "cross_team_recommendations": [
                    "Recommendation 1",
                    "Recommendation 2"
                ],
                "prioritization": [
                    {{
                        "issue_type": "Most critical issue type",
                        "reason": "Why this should be addressed first"
                    }},
                    {{
                        "issue_type": "Second most critical issue type",
                        "reason": "Why this should be addressed next"
                    }}
                ]
            }}
            """,
            agent=self.agent,
            expected_output="Detailed analysis and recommendations in structured JSON format"
        )
        
        try:
            # Execute the task
            self.emit_log("Analyst Agent is evaluating scout findings...")
            crew = Crew(
                agents=[self.agent],
                tasks=[analyst_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Run the analysis
            result = crew.kickoff()

            print("[analyst_task]",analyst_task.description)
            
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
                'scout_analysis': scout_analysis,
                'analyst_insights': parsed_result
            }
            
            self.emit_log("Analyst evaluation complete")
            return final_result
            
        except Exception as e:
            self.emit_log(f"⚠️ Error in Analyst processing: {str(e)}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'process_id': process_id
            }