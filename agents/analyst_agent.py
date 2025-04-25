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
            
    def format_scout_analysis(self, scout_analysis):
        """
        Format scout analysis data as readable text
        
        Args:
            scout_analysis: Dict containing the scout analysis results
            
        Returns:
            Formatted text representation of the scout analysis
        """
        formatted_text = []
        
        # Issue Types Section
        formatted_text.append("ISSUE TYPES IDENTIFIED:")
        if 'issue_types' in scout_analysis and scout_analysis['issue_types']:
            for i, issue in enumerate(scout_analysis['issue_types'], 1):
                formatted_text.append(f"  {i}. Type: {issue.get('type', 'Unknown issue type')}")
                formatted_text.append(f"     Priority: {issue.get('priority', 'Not specified')}")
                
                if 'key_details' in issue and issue['key_details']:
                    formatted_text.append(f"     Key Details: {issue['key_details']}")
                
                if 'examples' in issue and issue['examples']:
                    formatted_text.append("     Examples:")
                    for example in issue['examples']:
                        formatted_text.append(f"       - \"{example}\"")
                
                if 'sources' in issue and issue['sources']:
                    formatted_text.append("     User Reports:")
                    for source in issue['sources']:
                        formatted_text.append(f"       - \"{source}\"")
                
                formatted_text.append("")  # Empty line for separation
        else:
            formatted_text.append("  No specific issue types identified.")
            formatted_text.append("")
        
        # Common Themes Section
        formatted_text.append("COMMON THEMES:")
        if 'common_themes' in scout_analysis and scout_analysis['common_themes']:
            for i, theme in enumerate(scout_analysis['common_themes'], 1):
                formatted_text.append(f"  {i}. {theme}")
            formatted_text.append("")
        else:
            formatted_text.append("  No common themes identified.")
            formatted_text.append("")
        
        # Overall Sentiment Section
        formatted_text.append("OVERALL SENTIMENT:")
        sentiment = scout_analysis.get('overall_sentiment', 'Not specified')
        formatted_text.append(f"  {sentiment}")
        formatted_text.append("")
        
        # Summary Section
        formatted_text.append("SUMMARY:")
        summary = scout_analysis.get('summary', 'No summary provided')
        formatted_text.append(f"  {summary}")
        
        return "\n".join(formatted_text)

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
        metadata = scout_results.get('metadata', {})
        
        # Format the scout analysis as text
        formatted_scout_analysis = self.format_scout_analysis(scout_analysis)
        self.emit_log("Formatted scout analysis for better readability")
        
        # Create the analyst task with optimized prompt
        analyst_task = Task(
            description=f"""
            Analyze this feedback data and determine team responsibilities and action plans.
            
            Query: "{query}"
            
            Context: {scout_results.get('record_count', 0)} records analyzed. 
            
            Scout Analysis:
            ```
            {formatted_scout_analysis}
            ```
            
            Your task:
            1. Assign each issue to responsible team(s) (support, technical, billing, product, etc.)
            2. Recommend specific actions to resolve each issue
            3. Rate criticality (Critical/High/Medium/Low) based on user impact, business impact, urgency
            4. Provide resolution strategy for each issue
            5. Maintain the user reports/sources from the scout analysis
            
            Format as JSON:
            {{
                "team_assignments": [
                    {{
                        "issue_type": "Issue name",
                        "responsible_team": "Primary team",
                        "supporting_teams": ["Team 1", "Team 2"],
                        "criticality": "Critical/High/Medium/Low",
                        "recommended_actions": ["Action 1", "Action 2"],
                        "resolution_strategy": "Strategy description",
                        "sources": ["User report 1", "User report 2"]
                    }}
                ],
                "cross_team_recommendations": ["Recommendation 1", "Recommendation 2"],
                "prioritization": [
                    {{
                        "issue_type": "Most critical issue",
                        "reason": "Why address first"
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
            print("[analyst_task_PROMPT]",analyst_task.description)
            
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
                'metadata': metadata if metadata else {
                    'record_count': scout_results.get('record_count', 0)
                },
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