document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements - Dashboard
    const ticketCards = document.querySelectorAll('.ticket-card');
    const statusFilter = document.getElementById('status-filter');
    const searchInput = document.getElementById('search-input');
    const ticketsContainer = document.querySelector('.tickets-container');
    
    // DOM Elements - Task Details Section
    const taskDetailsSection = document.getElementById('task-details-section');
    const taskDetailTitle = document.getElementById('task-detail-title');
    const taskSummary = document.getElementById('task-summary');
    const taskList = document.getElementById('task-list');
    const taskTimeline = document.getElementById('task-timeline');
    const initiativesList = document.getElementById('initiatives-list');
    const closeTaskDetailsBtn = document.getElementById('close-task-details');
    const taskCountNew = document.getElementById('task-count-new');
    const taskCountProcessing = document.getElementById('task-count-processing');
    const taskCountResolved = document.getElementById('task-count-resolved');
    
    // DOM Elements - Modal
    const analysisModal = document.getElementById('analysis-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalLoading = document.getElementById('modal-loading');
    const modalContent = document.getElementById('modal-content');
    const modalSummary = document.getElementById('modal-summary');
    const modalIssuesList = document.getElementById('modal-issues-list');
    const modalTimeline = document.getElementById('modal-timeline');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalDownloadBtn = document.getElementById('modal-download-btn');
    const closeModalBtn = document.querySelector('.close-modal');
    
    // Variables
    let currentCompanyId = document.querySelector('.dashboard-header h2').textContent.trim().toLowerCase().replace(/\s+/g, '_');
    let currentTicketId = null;
    let currentAnalysisData = null;
    
    // Event Listeners
    
    // Filtering and Searching
    statusFilter.addEventListener('change', filterTickets);
    searchInput.addEventListener('input', filterTickets);
    
    // Apply filter to tickets based on status and search
    function filterTickets() {
        const statusValue = statusFilter.value;
        const searchValue = searchInput.value.toLowerCase();
        
        ticketCards.forEach(card => {
            const status = card.dataset.status;
            const title = card.querySelector('.ticket-title').textContent.toLowerCase();
            const summary = card.querySelector('.ticket-summary').textContent.toLowerCase();
            const ticketId = card.querySelector('.ticket-id').textContent.toLowerCase();
            
            // Check if matches both filter criteria
            const statusMatch = statusValue === 'all' || status === statusValue;
            const searchMatch = searchValue === '' || 
                title.includes(searchValue) || 
                summary.includes(searchValue) || 
                ticketId.includes(searchValue);
            
            // Show/hide based on match
            card.style.display = (statusMatch && searchMatch) ? 'block' : 'none';
        });
        
        // Check if no results and show message
        const visibleCards = Array.from(ticketCards).filter(card => card.style.display !== 'none');
        if (visibleCards.length === 0) {
            let noResultsEl = document.querySelector('.no-results');
            if (!noResultsEl) {
                noResultsEl = document.createElement('div');
                noResultsEl.className = 'no-results';
                noResultsEl.innerHTML = `
                    <i class="fas fa-search"></i>
                    <p>No matching tickets found</p>
                `;
                ticketsContainer.appendChild(noResultsEl);
            }
            noResultsEl.style.display = 'flex';
        } else {
            const noResultsEl = document.querySelector('.no-results');
            if (noResultsEl) {
                noResultsEl.style.display = 'none';
            }
        }
    }
    
    // Add click event to all ticket cards to show manage tasks panel
    document.querySelectorAll('.spread-tasks-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const ticketId = this.dataset.ticketId;
            showTaskDetails(ticketId);
        });
    });
    
    // Close task details panel
    closeTaskDetailsBtn.addEventListener('click', function() {
        taskDetailsSection.style.display = 'none';
    });
    
    // Modal close buttons
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }
    
    // When the user clicks anywhere outside the modal, close it
    window.addEventListener('click', function(event) {
        if (event.target === analysisModal) {
            closeModal();
        }
    });
    
    // Download JSON button in modal
    if (modalDownloadBtn) {
        modalDownloadBtn.addEventListener('click', function() {
            if (!currentAnalysisData) return;
            
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentAnalysisData, null, 2));
            const downloadAnchor = document.createElement('a');
            downloadAnchor.setAttribute("href", dataStr);
            downloadAnchor.setAttribute("download", `ticket-${currentTicketId}.json`);
            document.body.appendChild(downloadAnchor);
            downloadAnchor.click();
            downloadAnchor.remove();
        });
    }
    
    // Functions
    
    // Show task details panel for a specific ticket
    function showTaskDetails(ticketId) {
        currentTicketId = ticketId;
        
        // Show loading state
        taskDetailsSection.style.display = 'block';
        taskDetailTitle.textContent = `Loading Tasks for Ticket #${ticketId.substring(0, 8)}...`;
        taskSummary.textContent = 'Loading...';
        taskList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading tasks...</div>';
        taskTimeline.innerHTML = '';
        initiativesList.innerHTML = '';
        
        // Reset task counters
        taskCountNew.textContent = '0';
        taskCountProcessing.textContent = '0';
        taskCountResolved.textContent = '0';
        
        // Fetch analysis data
        fetch(`/db/analysis/${currentCompanyId}/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (!data.success || !data.data) {
                    throw new Error(data.error || 'Failed to load analysis data');
                }
                
                // Store the data for later use
                currentAnalysisData = data.data;
                
                // Update panel title
                taskDetailTitle.textContent = `Tasks for Ticket #${ticketId.substring(0, 8)}`;
                
                // Populate task details panel
                renderTaskDetails(data.data);
            })
            .catch(error => {
                taskSummary.textContent = 'Error loading analysis';
                taskList.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            });
    }
    
    // Render task details in the task panel
    function renderTaskDetails(analysis) {
        // Clear existing content
        taskList.innerHTML = '';
        taskTimeline.innerHTML = '';
        initiativesList.innerHTML = '';
        
        // Set summary
        if (analysis.final_report && analysis.final_report.executive_summary) {
            taskSummary.textContent = analysis.final_report.executive_summary;
        } else {
            taskSummary.textContent = 'No summary available for this analysis.';
        }
        
        // If there are no issues, show a message
        if (!analysis.final_report || !analysis.final_report.issues || analysis.final_report.issues.length === 0) {
            taskList.innerHTML = '<div class="no-tasks">No tasks found in this analysis</div>';
            return;
        }
        
        // Get issues and add status counters
        const issues = analysis.final_report.issues;
        let statusCounts = {
            'new': 0,
            'processing': 0,
            'resolved': 0
        };
        
        // Process each issue as a task
        issues.forEach((issue, index) => {
            const status = issue.status || 'new';
            
            // Update status counters
            if (status in statusCounts) {
                statusCounts[status]++;
            }
            
            // Create the task card
            const taskCard = document.createElement('div');
            taskCard.className = `task-card status-${status}`;
            taskCard.dataset.taskIndex = index;
            
            // Determine badge class based on criticality
            const badgeClass = `badge-${issue.criticality ? issue.criticality.toLowerCase() : 'medium'}`;
            
            // Build source list HTML if sources exist
            let sourcesHtml = '';
            if (issue.sources && issue.sources.length > 0) {
                sourcesHtml = `
                    <div class="task-sources">
                        <h5>User Reports:</h5>
                        <ul class="sources-list">
                            ${issue.sources.slice(0, 2).map(source => `<li>${source}</li>`).join('')}
                            ${issue.sources.length > 2 ? `<li>+${issue.sources.length - 2} more reports</li>` : ''}
                        </ul>
                    </div>
                `;
            }
            
            // Build tags HTML if tags exist
            let tagsHtml = '';
            if (issue.tags && issue.tags.length > 0) {
                tagsHtml = `
                    <div class="task-tags">
                        ${issue.tags.map(tag => `<span class="task-tag">${tag}</span>`).join('')}
                    </div>
                `;
            }
            
            taskCard.innerHTML = `
                <div class="task-header">
                    <h4 class="task-title">${issue.issue_type || 'Untitled Task'}</h4>
                    <div class="task-meta">
                        <span class="task-badge ${badgeClass}">${issue.criticality || 'Medium'}</span>
                        <span class="task-team">${issue.responsible_team || 'Unassigned'}</span>
                    </div>
                </div>
                <div class="task-body">
                    <p class="task-description">${issue.description || 'No description available'}</p>
                    ${tagsHtml}
                    ${sourcesHtml}
                </div>
                <div class="task-actions">
                    <select class="task-status-select" data-ticket-id="${currentTicketId}" data-task-index="${index}">
                        <option value="new" ${status === 'new' ? 'selected' : ''}>New</option>
                        <option value="processing" ${status === 'processing' ? 'selected' : ''}>In Progress</option>
                        <option value="resolved" ${status === 'resolved' ? 'selected' : ''}>Resolved</option>
                    </select>
                    <button class="view-task-btn" data-task-index="${index}">
                        <i class="fas fa-eye"></i> Details
                    </button>
                </div>
            `;
            
            taskList.appendChild(taskCard);
        });
        
        // Update status counters
        taskCountNew.textContent = statusCounts.new;
        taskCountProcessing.textContent = statusCounts.processing;
        taskCountResolved.textContent = statusCounts.resolved;
        
        // Add implementation timeline if available
        if (analysis.final_report && analysis.final_report.implementation_plan) {
            renderImplementationPlan(analysis.final_report.implementation_plan, taskTimeline);
        } else {
            taskTimeline.innerHTML = '<p>No implementation plan available</p>';
        }
        
        // Add cross-team initiatives if available
        if (analysis.final_report && analysis.final_report.cross_team_initiatives) {
            renderInitiatives(analysis.final_report.cross_team_initiatives);
        } else {
            initiativesList.innerHTML = '<p>No cross-team initiatives identified</p>';
        }
        
        // Add event listeners to status selects
        document.querySelectorAll('.task-status-select').forEach(select => {
            select.addEventListener('change', function() {
                updateTaskStatus(
                    this.dataset.ticketId,
                    parseInt(this.dataset.taskIndex),
                    this.value
                );
            });
        });
        
        // Add event listeners to view details buttons
        document.querySelectorAll('.view-task-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const taskIndex = parseInt(this.dataset.taskIndex);
                showTaskModal(issues[taskIndex], taskIndex);
            });
        });
    }
    
    // Render implementation plan
    function renderImplementationPlan(plan, container) {
        // Clear existing content
        container.innerHTML = '';
        
        // Immediate Actions
        if (plan.immediate_actions && plan.immediate_actions.length > 0) {
            const immediateSection = document.createElement('div');
            immediateSection.className = 'timeline-section';
            immediateSection.innerHTML = `
                <h4><i class="fas fa-bolt"></i> Immediate Actions</h4>
                <ul class="timeline-items">
                    ${plan.immediate_actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            `;
            container.appendChild(immediateSection);
        }
        
        // Short Term Actions
        if (plan.short_term_actions && plan.short_term_actions.length > 0) {
            const shortTermSection = document.createElement('div');
            shortTermSection.className = 'timeline-section';
            shortTermSection.innerHTML = `
                <h4><i class="fas fa-calendar-alt"></i> Short Term Actions (1-4 weeks)</h4>
                <ul class="timeline-items">
                    ${plan.short_term_actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            `;
            container.appendChild(shortTermSection);
        }
        
        // Long Term Actions
        if (plan.long_term_actions && plan.long_term_actions.length > 0) {
            const longTermSection = document.createElement('div');
            longTermSection.className = 'timeline-section';
            longTermSection.innerHTML = `
                <h4><i class="fas fa-calendar-check"></i> Long Term Actions (1-3 months)</h4>
                <ul class="timeline-items">
                    ${plan.long_term_actions.map(action => `<li>${action}</li>`).join('')}
                </ul>
            `;
            container.appendChild(longTermSection);
        }
        
        // If no timeline data
        if (container.children.length === 0) {
            container.innerHTML = '<p>No implementation plan available</p>';
        }
    }
    
    // Render initiatives
    function renderInitiatives(initiatives) {
        // Clear existing content
        initiativesList.innerHTML = '';
        
        if (!initiatives || initiatives.length === 0) {
            initiativesList.innerHTML = '<p>No cross-team initiatives identified</p>';
            return;
        }
        
        // Add each initiative
        initiatives.forEach(initiative => {
            const initiativeCard = document.createElement('div');
            initiativeCard.className = 'initiative-card';
            
            // Get teams involved
            let teamsHtml = '';
            if (initiative.teams && initiative.teams.length > 0) {
                teamsHtml = `
                    <div class="initiative-teams">
                        <h5>Teams Involved:</h5>
                        <div class="teams-list">
                            ${initiative.teams.map(team => `<span class="team-badge">${team}</span>`).join('')}
                        </div>
                    </div>
                `;
            }
            
            initiativeCard.innerHTML = `
                <h4 class="initiative-title">${initiative.name || 'Untitled Initiative'}</h4>
                <p class="initiative-description">${initiative.description || 'No description available'}</p>
                ${teamsHtml}
                <div class="initiative-timeline">
                    <span class="initiative-timeframe">${initiative.timeframe || 'Timeline not specified'}</span>
                    <span class="initiative-priority">Priority: ${initiative.priority || 'Medium'}</span>
                </div>
            `;
            
            initiativesList.appendChild(initiativeCard);
        });
    }
    
    // Update task status via API
    function updateTaskStatus(ticketId, taskIndex, newStatus) {
        // Send status update request
        fetch('/db/task/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_id: currentCompanyId,
                ticket_id: ticketId,
                task_index: taskIndex,
                status: newStatus
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                throw new Error(data.error || 'Failed to update task status');
            }
            
            // Update the UI to reflect the change
            const taskCard = document.querySelector(`.task-card[data-task-index="${taskIndex}"]`);
            if (taskCard) {
                // Remove old status class and add new one
                taskCard.className = taskCard.className.replace(/status-\w+/, `status-${newStatus}`);
            }
            
            // Update the status counts
            if (data.counts) {
                taskCountNew.textContent = data.counts.new || 0;
                taskCountProcessing.textContent = data.counts.processing || 0;
                taskCountResolved.textContent = data.counts.resolved || 0;
            }
            
            // Also update the main dashboard ticket status indicators if available
            const ticketCard = document.querySelector(`.ticket-card[data-ticket-id="${ticketId}"]`);
            if (ticketCard && data.counts) {
                const taskCountsEl = ticketCard.querySelector('.ticket-task-status');
                if (taskCountsEl) {
                    const newCount = taskCountsEl.querySelector('.task-count.new');
                    const processingCount = taskCountsEl.querySelector('.task-count.processing');
                    const resolvedCount = taskCountsEl.querySelector('.task-count.resolved');
                    
                    if (newCount) newCount.textContent = data.counts.new || 0;
                    if (processingCount) processingCount.textContent = data.counts.processing || 0;
                    if (resolvedCount) resolvedCount.textContent = data.counts.resolved || 0;
                }
            }
        })
        .catch(error => {
            alert(`Error updating task status: ${error.message}`);
            // Reset the select to previous value
            const select = document.querySelector(`.task-status-select[data-task-index="${taskIndex}"]`);
            if (select) {
                select.value = currentAnalysisData.final_report.issues[taskIndex].status || 'new';
            }
        });
    }
    
    // Show task details in modal
    function showTaskModal(task, taskIndex) {
        if (!task) return;
        
        // Update modal title
        modalTitle.textContent = `Task Details: ${task.issue_type || 'Untitled Task'}`;
        
        // Show loading state
        modalLoading.style.display = 'block';
        modalContent.style.display = 'none';
        
        // Show the modal
        analysisModal.style.display = 'block';
        
        // Prepare the modal content
        modalSummary.textContent = task.description || 'No description available';
        
        // Create detailed task view
        const detailedTask = document.createElement('div');
        detailedTask.className = 'detailed-task';
        
        // Determine badge class based on criticality
        const badgeClass = `badge-${task.criticality ? task.criticality.toLowerCase() : 'medium'}`;
        
        // Build source list HTML if sources exist
        let sourcesHtml = '';
        if (task.sources && task.sources.length > 0) {
            sourcesHtml = `
                <div class="task-section">
                    <h5>User Reports:</h5>
                    <ul class="sources-list">
                        ${task.sources.map(source => `<li>${source}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Build tags HTML if tags exist
        let tagsHtml = '';
        if (task.tags && task.tags.length > 0) {
            tagsHtml = `
                <div class="task-tags">
                    ${task.tags.map(tag => `<span class="task-tag">${tag}</span>`).join('')}
                </div>
            `;
        }
        
        // Build actions HTML if actions exist
        let actionsHtml = '';
        if (task.recommended_actions && task.recommended_actions.length > 0) {
            actionsHtml = `
                <div class="task-section">
                    <h5>Recommended Actions:</h5>
                    <ul class="actions-list">
                        ${task.recommended_actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        detailedTask.innerHTML = `
            <div class="task-header">
                <div class="task-meta">
                    <span class="task-badge ${badgeClass}">${task.criticality || 'Medium'}</span>
                    <span class="task-team">Team: ${task.responsible_team || 'Unassigned'}</span>
                    <span class="task-status status-${task.status || 'new'}">Status: ${(task.status || 'new').toUpperCase()}</span>
                </div>
                ${tagsHtml}
            </div>
            
            ${actionsHtml}
            
            <div class="task-section">
                <h5>Resolution Strategy:</h5>
                <p>${task.resolution_strategy || 'No resolution strategy specified'}</p>
            </div>
            
            <div class="task-section">
                <h5>Timeline:</h5>
                <p>${task.timeline || 'No timeline specified'}</p>
            </div>
            
            ${sourcesHtml}
        `;
        
        // Clear existing issues and add the detailed task
        modalIssuesList.innerHTML = '';
        modalIssuesList.appendChild(detailedTask);
        
        // Hide loading and show content
        modalLoading.style.display = 'none';
        modalContent.style.display = 'block';
    }
    
    // Close the modal
    function closeModal() {
        analysisModal.style.display = 'none';
    }
});