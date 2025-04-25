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
                
                # Add tags if present
                if 'tags' in issue and issue['tags']:
                    formatted_text.append(f"     Tags: {', '.join(issue['tags'])}")
                
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

    def generate_final_report(self, analyst_insights, scout_analysis, query, metadata):
        """
        Generate final report from analyst insights and scout analysis
        
        Args:
            analyst_insights: Dict containing analyst insights
            scout_analysis: Dict containing scout analysis
            query: Original query string
            metadata: Metadata about the analysis
            
        Returns:
            Dict containing final report
        """
        self.emit_log("Generating final report...")
        
        # Extract issues from analyst team assignments
        issues = []
        
        if 'team_assignments' in analyst_insights:
            for assignment in analyst_insights['team_assignments']:
                # Find the matching issue in scout analysis for tags
                tags = []
                if 'issue_type' in assignment and scout_analysis.get('issue_types'):
                    for scout_issue in scout_analysis.get('issue_types', []):
                        if scout_issue.get('type') == assignment.get('issue_type'):
                            tags = scout_issue.get('tags', [])
                            break
                
                issue = {
                    'issue_type': assignment.get('issue_type', 'Unknown Issue'),
                    'description': assignment.get('resolution_strategy', 'No description available'),
                    'responsible_team': assignment.get('responsible_team', 'Unassigned'),
                    'criticality': assignment.get('criticality', 'Medium'),
                    'recommended_actions': assignment.get('recommended_actions', []),
                    'resolution_strategy': assignment.get('resolution_strategy', 'No strategy provided'),
                    'sources': assignment.get('sources', []),
                    'tags': tags,
                    'timeline': self._determine_timeline(assignment.get('criticality', 'Medium'))
                }
                issues.append(issue)
        
        # Build implementation plan based on issue criticality
        implementation_plan = {
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': []
        }
        
        for issue in issues:
            timeline = issue.get('timeline', 'short-term')
            
            # Take first action from each issue based on timeline
            if issue.get('recommended_actions'):
                action = f"{issue.get('issue_type')} - {issue.get('recommended_actions')[0]}"
                
                if timeline == 'immediate':
                    implementation_plan['immediate_actions'].append(action)
                elif timeline == 'short-term':
                    implementation_plan['short_term_actions'].append(action)
                else:
                    implementation_plan['long_term_actions'].append(action)
        
        # Generate cross-team initiatives from analyst insights
        cross_team_initiatives = []
        
        if 'cross_team_recommendations' in analyst_insights and analyst_insights['cross_team_recommendations']:
            for i, recommendation in enumerate(analyst_insights['cross_team_recommendations']):
                initiative = {
                    'name': f"Initiative {i+1}",
                    'description': recommendation,
                    'teams_involved': self._extract_teams_from_text(recommendation),
                }
                cross_team_initiatives.append(initiative)
        
        # Build executive summary
        executive_summary = scout_analysis.get('summary', 'No summary available')
        if len(executive_summary) < 100 and 'overall_sentiment' in scout_analysis:
            executive_summary += f" Overall sentiment is {scout_analysis['overall_sentiment'].lower()}."
        
        # Final report structure
        final_report = {
            'executive_summary': executive_summary,
            'issues': issues,
            'cross_team_initiatives': cross_team_initiatives,
            'implementation_plan': implementation_plan
        }
        
        return final_report
        
    def _determine_timeline(self, criticality):
        """Determine timeline based on criticality"""
        criticality = criticality.lower() if criticality else 'medium'
        
        if criticality == 'critical':
            return 'immediate'
        elif criticality == 'high':
            return 'immediate'
        elif criticality == 'medium':
            return 'short-term'
        else:
            return 'long-term'
            
    def _extract_teams_from_text(self, text):
        """Extract potential team names from recommendation text"""
        common_teams = ['Product', 'Engineering', 'Support', 'QA', 'Marketing', 
                      'Sales', 'Design', 'Customer Success', 'Operations', 'Finance']
        
        found_teams = []
        for team in common_teams:
            if team.lower() in text.lower():
                found_teams.append(team)
        
        # If no teams found, add product and engineering as defaults
        if not found_teams:
            found_teams = ['Product', 'Engineering']
            
        return found_teams
        
    def process_analyst_query(self, scout_results):
        """
        Process data with the Analyst Agent and generate final report
        
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
        company_id = scout_results.get('company_id', 'default_company')
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
                    analyst_insights = json.loads(json_str)
                else:
                    analyst_insights = {"error": "Could not extract JSON from response"}
                    
            except json.JSONDecodeError:
                self.emit_log("⚠️ Error parsing JSON from LLM response")
                analyst_insights = {"error": "Invalid JSON format in response"}
            
            # Generate final report directly (replacing orchestrator)
            final_report = self.generate_final_report(
                analyst_insights=analyst_insights,
                scout_analysis=scout_analysis,
                query=query,
                metadata=metadata
            )
            
            # Add metadata to the result
            final_result = {
                'process_id': process_id,
                'company_id': company_id,
                'timestamp': int(time.time()),
                'query': query,
                'scout_analysis': scout_analysis,
                'metadata': metadata if metadata else {
                    'record_count': scout_results.get('record_count', 0)
                },
                'analyst_insights': analyst_insights,
                'final_report': final_report
            }
            
            self.emit_log("Analysis and report generation complete")
            return final_result
            
        except Exception as e:
            self.emit_log(f"⚠️ Error in Analyst processing: {str(e)}")
            return {
                'error': f'Analysis failed: {str(e)}',
                'process_id': process_id,
                'company_id': company_id
            }