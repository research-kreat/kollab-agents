from crewai import Agent, Task, Crew, Process
import logging
import json
import time

class OrchestratorAgent:
    def __init__(self, socket_instance=None):
        """Initialize the Orchestrator Agent"""
        # Store SocketIO instance for emitting events
        self.socketio = socket_instance
        
        # Initialize CrewAI Agent for orchestration
        self.agent = Agent(
            role="Analysis Orchestrator",
            goal="Create a cohesive, actionable final report based on individual agent findings",
            backstory="You are a strategic manager who synthesizes information from multiple sources to create clear, concise action plans.",
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
        
    def emit_log(self, message):
        """Emits a log message to the client via socket.io"""
        print(f"ORCHESTRATOR: {message}")
        if self.socketio:
            self.socketio.emit('orchestrator_log', {'message': message})

    def format_analysis_for_prompt(self, analysis_data):
        """Format analysis data in a more readable way for LLM consumption"""
        formatted_text = []
        
        # Handle issue types
        if 'issue_types' in analysis_data:
            formatted_text.append("ISSUE TYPES:")
            for idx, issue in enumerate(analysis_data.get('issue_types', []), 1):
                formatted_text.append(f"  {idx}. Type: {issue.get('type', 'Unknown')}")
                formatted_text.append(f"     Priority: {issue.get('priority', 'Unknown')}")
                if issue.get('key_details'):
                    formatted_text.append(f"     Details: {issue.get('key_details')}")
                if issue.get('examples') and len(issue.get('examples')) > 0:
                    formatted_text.append(f"     Example: {issue.get('examples')[0]}")
                formatted_text.append("")
        
        # Handle common themes
        if 'common_themes' in analysis_data and analysis_data['common_themes']:
            formatted_text.append("COMMON THEMES:")
            for theme in analysis_data.get('common_themes', []):
                formatted_text.append(f"  • {theme}")
            formatted_text.append("")
            
        # Handle summary and sentiment
        if 'summary' in analysis_data:
            formatted_text.append(f"SUMMARY: {analysis_data.get('summary', 'No summary available')}")
            
        if 'overall_sentiment' in analysis_data:
            formatted_text.append(f"SENTIMENT: {analysis_data.get('overall_sentiment', 'Unknown')}")
            
        return "\n".join(formatted_text)
    
    def format_insights_for_prompt(self, insights_data):
        """Format insights data in a more readable way for LLM consumption"""
        formatted_text = []
        
        # Handle team assignments
        if 'team_assignments' in insights_data:
            formatted_text.append("TEAM ASSIGNMENTS:")
            for idx, assignment in enumerate(insights_data.get('team_assignments', []), 1):
                formatted_text.append(f"  {idx}. Issue: {assignment.get('issue_type', 'Unknown')}")
                formatted_text.append(f"     Team: {assignment.get('responsible_team', 'Unassigned')}")
                formatted_text.append(f"     Criticality: {assignment.get('criticality', 'Unknown')}")
                
                if assignment.get('recommended_actions'):
                    formatted_text.append("     Actions:")
                    for action in assignment.get('recommended_actions', [])[:3]:  # Limit to first 3 actions
                        formatted_text.append(f"       • {action}")
                
                if assignment.get('resolution_strategy'):
                    formatted_text.append(f"     Strategy: {assignment.get('resolution_strategy')[:100]}...")  # Limit length
                
                formatted_text.append("")
        
        # Handle cross-team recommendations
        if 'cross_team_recommendations' in insights_data and insights_data['cross_team_recommendations']:
            formatted_text.append("CROSS-TEAM RECOMMENDATIONS:")
            for rec in insights_data.get('cross_team_recommendations', [])[:5]:  # Limit to first 5
                formatted_text.append(f"  • {rec}")
            formatted_text.append("")
            
        # Handle prioritization
        if 'prioritization' in insights_data and insights_data['prioritization']:
            formatted_text.append("PRIORITIZATION:")
            for idx, priority in enumerate(insights_data.get('prioritization', []), 1):
                formatted_text.append(f"  {idx}. {priority.get('issue_type', 'Unknown')}")
                if priority.get('reason'):
                    formatted_text.append(f"     Reason: {priority.get('reason')}")
            
        return "\n".join(formatted_text)

    def orchestrate_analysis(self, analyst_results, original_query):
        """
        Orchestrate and finalize the analysis based on analyst results
        
        Args:
            analyst_results: Dict containing results from the Analyst Agent
            original_query: The original user query
            
        Returns:
            Dict containing final orchestrated insights and recommendations
        """
        self.emit_log("Starting final orchestration...")
        
        if 'error' in analyst_results:
            self.emit_log(f"⚠️ Error received from Analyst Agent: {analyst_results['error']}")
            return analyst_results
        
        process_id = analyst_results.get('process_id', 'unknown')
        scout_analysis = analyst_results.get('scout_analysis', {})
        analyst_insights = analyst_results.get('analyst_insights', {})
        
        # Format the data for better LLM consumption
        formatted_scout_analysis = self.format_analysis_for_prompt(scout_analysis)
        formatted_analyst_insights = self.format_insights_for_prompt(analyst_insights)
        
        # Create the orchestrator task
        orchestrator_task = Task(
            description=f"""
            Synthesize the following scout analysis and analyst insights into a clear, actionable final report.
            
            Original User Query: "{original_query}"
            
            SCOUT ANALYSIS:
            {formatted_scout_analysis}
            
            ANALYST INSIGHTS:
            {formatted_analyst_insights}
            
            Your task is to:
            
            1. Create a comprehensive executive summary
            
            2. Format all insights and recommendations into a clear, structured format
            
            3. Ensure all recommendations are specific, actionable, and assigned to appropriate teams
            
            4. Prioritize issues by criticality and impact
            
            5. Add an implementation timeline suggestion based on criticality
            
            Format your response as a detailed JSON object with the following structure:
            {{
                "executive_summary": "Brief summary of key findings and most critical actions",
                "issues": [
                    {{
                        "issue_type": "Type of issue",
                        "description": "Description of the issue based on feedback",
                        "responsible_team": "Primary team responsible",
                        "criticality": "Critical/High/Medium/Low",
                        "impact": "Description of business and user impact",
                        "recommended_actions": [
                            "Specific action 1",
                            "Specific action 2"
                        ],
                        "resolution_strategy": "Overall strategy for addressing this issue",
                        "timeline": "Suggested timeline for resolution (immediate, short-term, long-term)"
                    }}
                ],
                "cross_team_initiatives": [
                    {{
                        "name": "Initiative name",
                        "description": "Description of cross-team initiative",
                        "teams_involved": ["Team 1", "Team 2"],
                        "expected_outcome": "What success looks like"
                    }}
                ],
                "implementation_plan": {{
                    "immediate_actions": ["Action 1", "Action 2"],
                    "short_term_actions": ["Action 1", "Action 2"],
                    "long_term_actions": ["Action 1", "Action 2"]
                }}
            }}
            """,
            agent=self.agent,
            expected_output="Comprehensive final report in structured JSON format"
        )
        
        try:
            # Execute the task
            self.emit_log("Orchestrator is preparing final report...")
            crew = Crew(
                agents=[self.agent],
                tasks=[orchestrator_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Run the orchestration
            result = crew.kickoff()
            print("[orchestrator_task]",orchestrator_task.description)

            
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
                'query': original_query,
                'final_report': parsed_result
            }
            
            self.emit_log("Orchestration complete")
            return final_result
            
        except Exception as e:
            self.emit_log(f"⚠️ Error in Orchestration: {str(e)}")
            return {
                'error': f'Orchestration failed: {str(e)}',
                'process_id': process_id
            }