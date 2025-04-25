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
                if issue.get('sources') and len(issue.get('sources')) > 0:
                    formatted_text.append(f"     User Reports: {len(issue.get('sources'))} reports")
                    for i, source in enumerate(issue.get('sources')[:3], 1):  # List the first 3 sources
                        formatted_text.append(f"       {i}. {source}")
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
                
                # Add supporting teams if present
                if assignment.get('supporting_teams') and len(assignment.get('supporting_teams')) > 0:
                    formatted_text.append(f"     Supporting Teams: {', '.join(assignment.get('supporting_teams'))}")
                
                formatted_text.append(f"     Criticality: {assignment.get('criticality', 'Unknown')}")
                
                if assignment.get('recommended_actions'):
                    formatted_text.append("     Actions:")
                    for action in assignment.get('recommended_actions', []):
                        formatted_text.append(f"       • {action}")
                
                if assignment.get('resolution_strategy'):
                    strategy_text = assignment.get('resolution_strategy')
                    # If strategy is very long, truncate it
                    if len(strategy_text) > 150:
                        strategy_text = strategy_text[:150] + "..."
                    formatted_text.append(f"     Strategy: {strategy_text}")
                
                # Add user reports/sources if present
                if assignment.get('sources') and len(assignment.get('sources')) > 0:
                    formatted_text.append(f"     User Reports: {len(assignment.get('sources'))} reports")
                    for i, source in enumerate(assignment.get('sources')[:2], 1):  # List the first 2 sources
                        formatted_text.append(f"       {i}. {source}")
                
                formatted_text.append("")
        
        # Handle cross-team recommendations
        if 'cross_team_recommendations' in insights_data and insights_data['cross_team_recommendations']:
            formatted_text.append("CROSS-TEAM RECOMMENDATIONS:")
            for idx, rec in enumerate(insights_data.get('cross_team_recommendations', []), 1):
                formatted_text.append(f"  {idx}. {rec}")
            formatted_text.append("")
            
        # Handle prioritization
        if 'prioritization' in insights_data and insights_data['prioritization']:
            formatted_text.append("ISSUE PRIORITIZATION:")
            for idx, priority in enumerate(insights_data.get('prioritization', []), 1):
                formatted_text.append(f"  {idx}. Issue: {priority.get('issue_type', 'Unknown')}")
                if priority.get('reason'):
                    formatted_text.append(f"     Reason: {priority.get('reason')}")
                formatted_text.append("")
            
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
        metadata = analyst_results.get('metadata', {})
        
        # Format the data for better LLM consumption
        formatted_scout_analysis = self.format_analysis_for_prompt(scout_analysis)
        formatted_analyst_insights = self.format_insights_for_prompt(analyst_insights)
        
        # Create the orchestrator task with optimized prompt
        orchestrator_task = Task(
            description=f"""
            Create a final actionable report based on the following feedback analysis.
            
            Query: "{original_query}"
            
            Context: {metadata.get('record_count', 0)} records analyzed. 
            {metadata.get('avg_feedback_length', 0)} avg chars.
            
            SCOUT ANALYSIS:
            {formatted_scout_analysis}
            
            ANALYST INSIGHTS:
            {formatted_analyst_insights}
            
            Task:
            1. Create an executive summary
            2. Structure issues with recommendations
            3. Ensure actions are specific and team-assigned
            4. Prioritize by criticality
            5. Include user reports/sources for each issue
            6. Add implementation timeline
            
            Format as JSON:
            {{
                "executive_summary": "Key findings summary",
                "issues": [
                    {{
                        "issue_type": "Issue name",
                        "description": "Issue description",
                        "responsible_team": "Primary team",
                        "criticality": "Critical/High/Medium/Low",
                        "impact": "Business and user impact",
                        "recommended_actions": ["Action 1", "Action 2"],
                        "resolution_strategy": "Strategy description",
                        "timeline": "immediate/short-term/long-term",
                        "sources": ["User report 1", "User report 2"]
                    }}
                ],
                "cross_team_initiatives": [
                    {{
                        "name": "Initiative name",
                        "description": "Initiative description",
                        "teams_involved": ["Team 1", "Team 2"],
                        "expected_outcome": "Success criteria"
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
            print("[orchestrator_task_PROMPT]",orchestrator_task.description)
            
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
                'metadata': metadata,
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