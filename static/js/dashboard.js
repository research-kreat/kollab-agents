document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const statusFilter = document.getElementById('status-filter');
    const searchInput = document.getElementById('search-input');
    const ticketCards = document.querySelectorAll('.ticket-card');
    const spreadTasksButtons = document.querySelectorAll('.spread-tasks-btn');
    const statusOptions = document.querySelectorAll('.status-option');
    const analysisModal = document.getElementById('analysis-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalLoading = document.getElementById('modal-loading');
    const modalContent = document.getElementById('modal-content');
    const modalSummary = document.getElementById('modal-summary');
    const modalIssuesList = document.getElementById('modal-issues-list');
    const modalTimeline = document.getElementById('modal-timeline');
    const modalDownloadBtn = document.getElementById('modal-download-btn');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const closeModalBtn = document.querySelector('.close-modal');
    
    // Task Details Elements
    const taskDetailsSection = document.getElementById('task-details-section');
    const taskDetailTitle = document.getElementById('task-detail-title');
    const taskSummary = document.getElementById('task-summary');
    const taskList = document.getElementById('task-list');
    const taskTimeline = document.getElementById('task-timeline');
    const initiativesList = document.getElementById('initiatives-list');
    const closeTaskDetailsBtn = document.getElementById('close-task-details');
    
    // Current company ID (from URL or default)
    const companyId = getCompanyId();
    let currentTicketId = null;
    let currentAnalysisData = null;
    
    // Spread tasks button handling
    spreadTasksButtons.forEach(button => {
        button.addEventListener('click', function() {
            const ticketId = this.getAttribute('data-ticket-id');
            loadTaskDetails(ticketId);
        });
    });
    
    // Close task details
    if (closeTaskDetailsBtn) {
        closeTaskDetailsBtn.addEventListener('click', function() {
            taskDetailsSection.style.display = 'none';
        });
    }
    
    // Status update options
    statusOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            
            const ticketId = this.getAttribute('data-ticket-id');
            const newStatus = this.getAttribute('data-status');
            
            updateTicketStatus(ticketId, newStatus);
        });
    });
    
    // Filter tickets by status
    statusFilter.addEventListener('change', function() {
        filterTickets();
    });
    
    // Search tickets
    searchInput.addEventListener('input', function() {
        filterTickets();
    });
    
    // Close modal
    closeModalBtn.addEventListener('click', closeAnalysisModal);
    modalCloseBtn.addEventListener('click', closeAnalysisModal);
    
    // Modal download button
    modalDownloadBtn.addEventListener('click', function() {
        if (currentTicketId) {
            downloadAnalysis(currentTicketId);
        }
    });
    
    // Close modal if clicked outside
    window.addEventListener('click', function(e) {
        if (e.target === analysisModal) {
            closeAnalysisModal();
        }
    });
    
    // Helper function to get company ID from URL or use default
    function getCompanyId() {
        // Try to extract from URL path
        const pathParts = window.location.pathname.split('/');
        const dashboardIndex = pathParts.indexOf('dashboard');
        
        if (dashboardIndex !== -1 && pathParts.length > dashboardIndex + 1) {
            return pathParts[dashboardIndex + 1];
        }
        
        // Fallback to default
        return 'default_company';
    }
    
    // Filter tickets based on status and search query
    function filterTickets() {
        const statusValue = statusFilter.value;
        const searchQuery = searchInput.value.toLowerCase();
        
        ticketCards.forEach(card => {
            const cardStatus = card.getAttribute('data-status');
            const cardTitle = card.querySelector('.ticket-title').textContent.toLowerCase();
            const cardSummary = card.querySelector('.ticket-summary').textContent.toLowerCase();
            
            const statusMatch = statusValue === 'all' || cardStatus === statusValue;
            const searchMatch = !searchQuery || 
                                cardTitle.includes(searchQuery) || 
                                cardSummary.includes(searchQuery);
            
            if (statusMatch && searchMatch) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    // Load task details and display them
    function loadTaskDetails(ticketId) {
        // Store current ticket ID
        currentTicketId = ticketId;
        
        // Show loading state
        taskList.innerHTML = '<div class="loading-tasks"><i class="fas fa-spinner fa-spin"></i> Loading tasks...</div>';
        taskDetailsSection.style.display = 'block';
        taskDetailTitle.textContent = `Tasks for Ticket #${ticketId.substring(0, 8)}`;
        
        // Fetch analysis details
        fetch(`/api/analysis/${companyId}/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentAnalysisData = data.data;
                    renderTaskDetails(data.data);
                } else {
                    showTaskError(data.error || 'Failed to load task details');
                }
            })
            .catch(error => {
                showTaskError('Error loading tasks: ' + error);
            });
    }
    
    // Show error in task details
    function showTaskError(message) {
        taskList.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
        taskTimeline.innerHTML = '';
        initiativesList.innerHTML = '';
        taskSummary.textContent = 'Failed to load task details';
    }
    
    // Render task details from analysis data
    function renderTaskDetails(analysis) {
        // Render summary
        taskSummary.textContent = analysis.final_report?.executive_summary || 'No summary available';
        
        // Render tasks/issues
        renderTaskList(analysis.final_report?.issues || []);
        
        // Render implementation plan
        renderTaskImplementationPlan(analysis.final_report?.implementation_plan || {});
        
        // Render cross-team initiatives
        renderInitiatives(analysis.final_report?.cross_team_initiatives || []);
        
        // Scroll to task details
        taskDetailsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Render task list
    function renderTaskList(tasks) {
        taskList.innerHTML = '';
        
        if (tasks.length === 0) {
            taskList.innerHTML = '<p>No tasks found</p>';
            return;
        }
        
        tasks.forEach(task => {
            const taskCard = document.createElement('div');
            taskCard.className = 'task-card';
            
            // Determine badge class based on criticality
            const badgeClass = `badge-${task.criticality ? task.criticality.toLowerCase() : 'medium'}`;
            
            // Build source list HTML if sources exist
            let sourcesHtml = '';
            if (task.sources && task.sources.length > 0) {
                sourcesHtml = `
                    <h5>User Reports:</h5>
                    <ul class="sources-list">
                        ${task.sources.map(source => `<li>${source}</li>`).join('')}
                    </ul>
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
            
            // Build recommended actions
            let actionsHtml = '';
            if (task.recommended_actions && task.recommended_actions.length > 0) {
                actionsHtml = `
                    <h5>Recommended Actions:</h5>
                    <ul class="actions-list">
                        ${task.recommended_actions.map(action => `<li>${action}</li>`).join('')}
                    </ul>
                `;
            }
            
            taskCard.innerHTML = `
                <div class="task-header">
                    <h4 class="task-title">${task.issue_type || 'Untitled Task'}</h4>
                    <span class="task-badge ${badgeClass}">${task.criticality || 'Medium'}</span>
                </div>
                <div class="task-body">
                    <p class="task-description">${task.description || 'No description available'}</p>
                    <p class="task-team"><strong>Team:</strong> ${task.responsible_team || 'Unassigned'}</p>
                    ${tagsHtml}
                    ${actionsHtml}
                    ${sourcesHtml}
                    <p><strong>Resolution Strategy:</strong> ${task.resolution_strategy || 'Not specified'}</p>
                    <p><strong>Timeline:</strong> ${task.timeline || 'Not specified'}</p>
                </div>
            `;
            
            taskList.appendChild(taskCard);
        });
    }
    
    // Render implementation plan for tasks
    function renderTaskImplementationPlan(plan) {
        taskTimeline.innerHTML = '';
        
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
            taskTimeline.appendChild(immediateSection);
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
            taskTimeline.appendChild(shortTermSection);
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
            taskTimeline.appendChild(longTermSection);
        }
        
        // If no timeline data
        if (taskTimeline.children.length === 0) {
            taskTimeline.innerHTML = '<p>No implementation plan available</p>';
        }
    }
    
    // Render cross-team initiatives
    function renderInitiatives(initiatives) {
        initiativesList.innerHTML = '';
        
        if (initiatives.length === 0) {
            initiativesList.innerHTML = '<p>No cross-team initiatives found</p>';
            return;
        }
        
        initiatives.forEach(initiative => {
            const initiativeCard = document.createElement('div');
            initiativeCard.className = 'initiative-card';
            
            // Build teams list
            let teamsHtml = '';
            if (initiative.teams_involved && initiative.teams_involved.length > 0) {
                teamsHtml = `
                    <p class="teams-involved"><strong>Teams Involved:</strong></p>
                    <div class="teams-list">
                        ${initiative.teams_involved.map(team => `<span class="team-tag">${team}</span>`).join('')}
                    </div>
                `;
            }
            
            initiativeCard.innerHTML = `
                <div class="initiative-header">
                    <h4 class="initiative-title">${initiative.name || 'Untitled Initiative'}</h4>
                </div>
                <div class="initiative-body">
                    <p class="initiative-description">${initiative.description || 'No description available'}</p>
                    ${teamsHtml}
                </div>
            `;
            
            initiativesList.appendChild(initiativeCard);
        });
    }
    
    // Open analysis modal and load details
    function openAnalysisModal(ticketId) {
        // Store current ticket ID
        currentTicketId = ticketId;
        
        // Reset and show modal
        modalTitle.textContent = `Analysis #${ticketId.substring(0, 8)}`;
        modalLoading.style.display = 'block';
        modalContent.style.display = 'none';
        analysisModal.style.display = 'block';
        
        // Fetch analysis details
        fetch(`/api/analysis/${companyId}/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderAnalysisDetails(data.data);
                } else {
                    showError(data.error || 'Failed to load analysis details');
                }
            })
            .catch(error => {
                showError('Error loading analysis: ' + error);
            })
            .finally(() => {
                modalLoading.style.display = 'none';
                modalContent.style.display = 'block';
            });
    }
    
    // Close the analysis modal
    function closeAnalysisModal() {
        analysisModal.style.display = 'none';
        currentTicketId = null;
    }
    
    // Update ticket status
    function updateTicketStatus(ticketId, newStatus) {
        fetch(`/api/analysis/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_id: companyId,
                ticket_id: ticketId,
                status: newStatus
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update UI status
                const card = document.querySelector(`.ticket-card[data-ticket-id="${ticketId}"]`);
                if (card) {
                    card.setAttribute('data-status', newStatus);
                    const statusElement = card.querySelector('.ticket-status');
                    statusElement.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
                    statusElement.className = `ticket-status status-${newStatus}`;
                }
            } else {
                alert('Failed to update status: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            alert('Error updating status: ' + error);
        });
    }
    
    // Download analysis as JSON
    function downloadAnalysis(ticketId) {
        fetch(`/api/analysis/${companyId}/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data.data, null, 2));
                    const downloadAnchor = document.createElement('a');
                    downloadAnchor.setAttribute("href", dataStr);
                    downloadAnchor.setAttribute("download", `analysis-${ticketId}.json`);
                    document.body.appendChild(downloadAnchor);
                    downloadAnchor.click();
                    downloadAnchor.remove();
                } else {
                    alert('Failed to download: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                alert('Error downloading analysis: ' + error);
            });
    }
    
    // Show error in modal
    function showError(message) {
        modalSummary.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
        modalIssuesList.innerHTML = '';
        modalTimeline.innerHTML = '';
    }
    
    // Render analysis details in modal
    function renderAnalysisDetails(analysis) {
        // Render summary
        modalSummary.textContent = analysis.final_report?.executive_summary || 'No summary available';
        
        // Render issues
        renderIssues(analysis.final_report?.issues || []);
        
        // Render implementation plan
        renderImplementationPlan(analysis.final_report?.implementation_plan || {});
    }
    
    // Render issues in modal
    function renderIssues(issues) {
        modalIssuesList.innerHTML = '';
        
        if (issues.length === 0) {
            modalIssuesList.innerHTML = '<p>No issues found</p>';
            return;
        }
        
        issues.forEach(issue => {
            const issueCard = document.createElement('div');
            issueCard.className = 'issue-card';
            
            // Determine badge class based on criticality
            const badgeClass = `badge-${issue.criticality ? issue.criticality.toLowerCase() : 'medium'}`;
            
            // Build source list HTML if sources exist
            let sourcesHtml = '';
            if (issue.sources && issue.sources.length > 0) {
                sourcesHtml = `
                    <h5>User Reports:</h5>
                    <ul class="sources-list">
                        ${issue.sources.map(source => `<li>${source}</li>`).join('')}
                    </ul>
                `;
            }
            
            // Build tags HTML if tags exist
            let tagsHtml = '';
            if (issue.tags && issue.tags.length > 0) {
                tagsHtml = `
                    <div class="issue-tags">
                        ${issue.tags.map(tag => `<span class="issue-tag">${tag}</span>`).join('')}
                    </div>
                `;
            }
            
            issueCard.innerHTML = `
                <div class="issue-header">
                    <h4 class="issue-title">${issue.issue_type || 'Untitled Issue'}</h4>
                    <span class="issue-badge ${badgeClass}">${issue.criticality || 'Medium'}</span>
                </div>
                <div class="issue-body">
                    <p class="issue-description">${issue.description || 'No description available'}</p>
                    <p class="issue-team"><strong>Team:</strong> ${issue.responsible_team || 'Unassigned'}</p>
                    ${tagsHtml}
                    ${sourcesHtml}
                    <h5>Recommended Actions:</h5>
                    <ul class="actions-list">
                        ${(issue.recommended_actions || []).map(action => `<li>${action}</li>`).join('')}
                    </ul>
                    
                    <p><strong>Resolution Strategy:</strong> ${issue.resolution_strategy || 'Not specified'}</p>
                    <p><strong>Timeline:</strong> ${issue.timeline || 'Not specified'}</p>
                </div>
            `;
            
            modalIssuesList.appendChild(issueCard);
        });
    }
    
    // Render implementation plan
    function renderImplementationPlan(plan) {
        modalTimeline.innerHTML = '';
        
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
            modalTimeline.appendChild(immediateSection);
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
            modalTimeline.appendChild(shortTermSection);
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
            modalTimeline.appendChild(longTermSection);
        }
        
        // If no timeline data
        if (modalTimeline.children.length === 0) {
            modalTimeline.innerHTML = '<p>No implementation plan available</p>';
        }
    }
});