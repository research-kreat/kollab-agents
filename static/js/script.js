document.addEventListener('DOMContentLoaded', function() {
    // Connect to Socket.IO
    const socket = io();
    
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const statusSection = document.getElementById('status-section');
    const statusMessages = document.getElementById('status-messages');
    const progressBar = document.getElementById('progress');
    const resultsSection = document.getElementById('results-section');
    const summaryContent = document.getElementById('summary-content');
    const issuesList = document.getElementById('issues-list');
    const timelineContainer = document.getElementById('timeline-container');
    const downloadJsonBtn = document.getElementById('download-json');
    const newAnalysisBtn = document.getElementById('new-analysis');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const companyIdInput = document.getElementById('company-id');
    const queryTextInput = document.getElementById('query-text');
    const saveAnalysisCheck = document.getElementById('save-analysis');
    const savedNotification = document.getElementById('saved-notification');
    const savedText = document.getElementById('saved-text');
    const viewDashboardLink = document.getElementById('view-dashboard-link');
    
    // Variables
    let uploadedFile = null;
    let analysisResults = null;
    let progressSteps = {
        'upload': { weight: 10, completed: false },
        'scout': { weight: 45, completed: false },
        'analyst': { weight: 45, completed: false }
    };
    
    // Socket.IO Event Listeners
    socket.on('connect', () => {
        addStatusMessage('Connected to server', 'system');
    });
    
    socket.on('disconnect', () => {
        addStatusMessage('Disconnected from server', 'error');
    });
    
    socket.on('status', (data) => {
        addStatusMessage(data.message);
        updateProgress(data.message);
    });
    
    socket.on('scout_log', (data) => {
        addStatusMessage(data.message, 'scout');
        updateProgress(data.message);
    });
    
    socket.on('analyst_log', (data) => {
        addStatusMessage(data.message, 'analyst');
        updateProgress(data.message);
    });
    
    // Try to load company ID from localStorage
    if (localStorage.getItem('companyId')) {
        companyIdInput.value = localStorage.getItem('companyId');
    }
    
    // File Input Handling
    fileInput.addEventListener('change', function(e) {
        if (fileInput.files.length > 0) {
            uploadedFile = fileInput.files[0];
            fileName.textContent = uploadedFile.name;
            fileLabel.style.display = 'none';
            fileInfo.style.display = 'flex';
            
            // Enable analyze button when file is selected
            analyzeBtn.disabled = false;
        }
    });
    
    // Remove File Button
    removeFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        uploadedFile = null;
        fileLabel.style.display = 'block';
        fileInfo.style.display = 'none';
        analyzeBtn.disabled = true;
    });
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!uploadedFile) {
            alert('Please select a file to analyze');
            return;
        }
        
        const companyId = companyIdInput.value.trim();
        if (!companyId) {
            alert('Please enter a Company ID');
            companyIdInput.focus();
            return;
        }
        
        // Save company ID to localStorage for next time
        localStorage.setItem('companyId', companyId);
        
        // Show status section
        statusSection.style.display = 'block';
        
        // Reset progress
        resetProgress();
        
        // Get custom query if provided
        const query = queryTextInput.value.trim() || 
                      "What are the key issues and actionable insights from this feedback?";
        
        // Create form data with all required parameters
        const formData = new FormData();
        formData.append('company_id', companyId);
        formData.append('query', query);
        formData.append('save_analysis', saveAnalysisCheck.checked);
        formData.append('file', uploadedFile);
        
        // Send to server
        addStatusMessage('Uploading and analyzing data...', 'system');
        analyzeBtn.disabled = true;
        
        fetch('/api/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Store results
            analysisResults = data;
            
            // Update progress to 100%
            Object.keys(progressSteps).forEach(step => {
                progressSteps[step].completed = true;
            });
            updateProgressBar();
            
            // Display results
            displayResults(data);
            
            // Show saved notification if saved
            if (data.saved && data.ticket_id) {
                savedNotification.style.display = 'block';
                savedText.textContent = `Analysis saved as Ticket #${data.ticket_id}`;
                viewDashboardLink.href = `/dashboard/${companyId}`;
            } else {
                savedNotification.style.display = 'none';
            }
            analyzeBtn.disabled = false;
        })
        .catch(error => {
            addStatusMessage(`Error: ${error.message}`, 'error');
            analyzeBtn.disabled = false;
        });
    });
    
    // Progress Bar Handling
    function resetProgress() {
        Object.keys(progressSteps).forEach(step => {
            progressSteps[step].completed = false;
        });
        updateProgressBar();
    }
    
    function updateProgress(message) {
        // Update progress based on message
        if (message.includes('Processing file') || message.includes('File processed') || 
            message.includes('Retrieving data')) {
            progressSteps.upload.completed = true;
        } else if (message.includes('Scout') || message.includes('scout')) {
            progressSteps.scout.completed = true;
        } else if (message.includes('Analyst') || message.includes('analyst')) {
            progressSteps.analyst.completed = true;
        }
        
        updateProgressBar();
    }
    
    function updateProgressBar() {
        let totalWeight = 0;
        let completedWeight = 0;
        
        Object.values(progressSteps).forEach(step => {
            totalWeight += step.weight;
            if (step.completed) {
                completedWeight += step.weight;
            }
        });
        
        const percentage = Math.round((completedWeight / totalWeight) * 100);
        progressBar.style.width = `${percentage}%`;
    }
    
    // Status Message Handling
    function addStatusMessage(message, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        statusMessages.appendChild(messageElement);
        statusMessages.scrollTop = statusMessages.scrollHeight;
    }
    
    // Display Results
    function displayResults(data) {
        // Show results section
        resultsSection.style.display = 'block';
        
        // Check if we have the final report
        if (!data.final_report) {
            addStatusMessage('Error: No final report data', 'error');
            return;
        }
        
        const report = data.final_report;
        
        // Executive Summary
        summaryContent.textContent = report.executive_summary || 'No summary available';
        
        // Issues List
        renderIssues(report.issues || []);
        
        // Implementation Plan
        renderImplementationPlan(report.implementation_plan || {});
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Render Issues
    function renderIssues(issues) {
        // Clear existing issues
        issuesList.innerHTML = '';
        
        // Filter issues based on active tab
        const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
        let filteredIssues = issues;
        
        if (activeTab !== 'all') {
            filteredIssues = issues.filter(issue => 
                issue.criticality && issue.criticality.toLowerCase() === activeTab.toLowerCase()
            );
        }
        
        // If no issues match the filter
        if (filteredIssues.length === 0) {
            const noIssues = document.createElement('div');
            noIssues.className = 'no-issues';
            noIssues.textContent = `No ${activeTab} priority issues found`;
            issuesList.appendChild(noIssues);
            return;
        }
        
        // Create issue cards
        filteredIssues.forEach(issue => {
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
            
            issuesList.appendChild(issueCard);
        });
    }
    
    // Render Implementation Plan
    function renderImplementationPlan(plan) {
        // Clear existing plan
        timelineContainer.innerHTML = '';
        
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
            timelineContainer.appendChild(immediateSection);
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
            timelineContainer.appendChild(shortTermSection);
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
            timelineContainer.appendChild(longTermSection);
        }
        
        // If no timeline data
        if (timelineContainer.children.length === 0) {
            timelineContainer.innerHTML = '<p>No implementation plan available</p>';
        }
    }
    
    // Tab Switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Re-render issues with the new filter
            if (analysisResults && analysisResults.final_report && analysisResults.final_report.issues) {
                renderIssues(analysisResults.final_report.issues);
            }
        });
    });
    
    // Download JSON Button
    downloadJsonBtn.addEventListener('click', function() {
        if (!analysisResults) return;
        
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(analysisResults, null, 2));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "feedback-analysis.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });
    
    // New Analysis Button
    newAnalysisBtn.addEventListener('click', function() {
        // Reset all inputs and state
        fileInput.value = '';
        fileLabel.style.display = 'block';
        fileInfo.style.display = 'none';
        queryTextInput.value = '';
        saveAnalysisCheck.checked = true;
        uploadedFile = null;
        analysisResults = null;
        analyzeBtn.disabled = true;
        
        // Hide results and status sections
        resultsSection.style.display = 'none';
        statusSection.style.display = 'none';
        savedNotification.style.display = 'none';
        
        // Clear status messages
        statusMessages.innerHTML = '<div class="message system">Ready to process your feedback</div>';
        
        // Reset progress
        resetProgress();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    // Drag and Drop Functionality for File Upload
    const fileUploadArea = document.querySelector('.file-upload');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        fileUploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        fileUploadArea.classList.add('highlighted');
    }
    
    function unhighlight() {
        fileUploadArea.classList.remove('highlighted');
    }
    
    fileUploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            // Trigger change event
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    }
});