from flask import jsonify

# Import the centralized app configuration
from utils.app_config import socketio, logger, storage, scout, analyst

def process_with_agents(content, query, process_id, company_id, save_analysis):
    """
    Process content with Scout and Analyst agents
    
    Args:
        content: List of records to analyze
        query: Query string for analysis
        process_id: Unique ID for this analysis process
        company_id: Company identifier
        save_analysis: Whether to save the analysis
        
    Returns:
        JSON response with analysis results
    """
    try:
        # Step 2: Scout agent processing
        socketio.emit('status', {'message': 'Scout agent processing data...'})
        scout_results = scout.process_scout_query({
            'content': content,
            'query': query,
            'process_id': process_id,
            'company_id': company_id
        })

        if 'error' in scout_results:
            socketio.emit('status', {'message': f'Error in Scout analysis: {scout_results["error"]}'})
            return jsonify(scout_results), 500
        
        # Step 3: Analyst agent processing
        socketio.emit('status', {'message': 'Analyst agent reviewing findings...'})
        final_results = analyst.process_analyst_query(scout_results)
        
        # Initialize status for each issue
        if 'final_report' in final_results and 'issues' in final_results['final_report']:
            for issue in final_results['final_report']['issues']:
                issue['status'] = 'new'
        
        # Step 4: Save analysis if requested
        if save_analysis:
            save_result = storage.save_analysis(final_results, company_id)
            final_results['saved'] = save_result['success']
            if save_result['success']:
                final_results['ticket_id'] = save_result['ticket_id']
            else:
                logger.error(f"Failed to save analysis: {save_result['error']}")
        
        socketio.emit('status', {'message': 'Analysis complete'})
        return jsonify(final_results)
    
    except Exception as e:
        logger.error(f"Error in agent processing: {str(e)}")
        socketio.emit('status', {'message': f'Error: {str(e)}'})
        return jsonify({'error': str(e)}), 500