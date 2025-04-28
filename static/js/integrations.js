document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements for Integration
    const integrationIcons = document.querySelectorAll('.integration-icon');
    const connectedSources = document.getElementById('connected-sources');
    const integrationModal = document.getElementById('integration-modal');
    const sourceName = document.getElementById('source-name');
    const integrationLoading = document.getElementById('integration-loading');
    const integrationAuthForm = document.getElementById('integration-auth-form');
    const integrationSourceSelect = document.getElementById('integration-source-select');
    const sourceTree = document.getElementById('source-tree');
    const integrationCancelBtn = document.getElementById('integration-cancel-btn');
    const integrationConnectBtn = document.getElementById('integration-connect-btn');
    const oauthConnectBtn = document.getElementById('oauth-connect-btn');
    const closeModalBtn = document.querySelector('#integration-modal .close-modal');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // Variables
    let currentSource = null;
    let connectedSourcesList = {};
    
    // Checking for saved connections in localStorage
    loadSavedConnections();
    
    // Click event for integration icons
    integrationIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const source = this.getAttribute('data-source');
            if (source === 'more') {
                // Show more integrations options
                showMoreIntegrations();
                return;
            }
            
            // Open modal for the selected source
            openIntegrationModal(source);
        });
    });
    
    // Close modal
    closeModalBtn.addEventListener('click', closeIntegrationModal);
    integrationCancelBtn.addEventListener('click', closeIntegrationModal);
    
    // Close modal if clicked outside
    window.addEventListener('click', function(e) {
        if (e.target === integrationModal) {
            closeIntegrationModal();
        }
    });
    
    // OAuth connect button
    oauthConnectBtn.addEventListener('click', function() {
        // Show loading state
        integrationAuthForm.style.display = 'none';
        integrationLoading.style.display = 'block';
        
        // Simulate OAuth process
        simulateOAuth(currentSource);
    });
    
    // Connect button in modal
    integrationConnectBtn.addEventListener('click', function() {
        // Check which view is active
        if (integrationAuthForm.style.display !== 'none') {
            // Auth form is visible, handle credentials
            const username = document.getElementById('auth-username').value;
            const password = document.getElementById('auth-password').value;
            
            if (!username || !password) {
                alert('Please enter your credentials');
                return;
            }
            
            // Show loading state
            integrationAuthForm.style.display = 'none';
            integrationLoading.style.display = 'block';
            
            // Simulate authentication
            simulateAuth(currentSource, username, password);
        } else if (integrationSourceSelect.style.display !== 'none') {
            // Source selection is visible, handle selected files
            const selectedFiles = getSelectedFilesFromTree();
            
            if (selectedFiles.length === 0) {
                alert('Please select at least one file to import');
                return;
            }
            
            // Add connected source to the list
            addConnectedSource(currentSource, selectedFiles);
            
            // Close modal
            closeIntegrationModal();
            
            // Enable analyze button
            analyzeBtn.disabled = false;
        }
    });
    
    // Function to open integration modal
    function openIntegrationModal(source) {
        currentSource = source;
        
        // Set source name
        sourceName.textContent = getSourceDisplayName(source);
        
        // Reset modal state
        integrationLoading.style.display = 'none';
        integrationAuthForm.style.display = 'block';
        integrationSourceSelect.style.display = 'none';
        sourceTree.innerHTML = '';
        
        // Reset form fields
        document.getElementById('auth-username').value = '';
        document.getElementById('auth-password').value = '';
        
        // Show modal
        integrationModal.style.display = 'block';
    }
    
    // Function to close integration modal
    function closeIntegrationModal() {
        integrationModal.style.display = 'none';
        currentSource = null;
    }
    
    // Function to show more integrations
    function showMoreIntegrations() {
        alert('More integrations coming soon!');
    }
    
    // Function to simulate OAuth authentication
    function simulateOAuth(source) {
        // Simulate API delay
        setTimeout(() => {
            // Show source selection view
            integrationLoading.style.display = 'none';
            integrationSourceSelect.style.display = 'block';
            
            // Populate sample data
            populateSourceTree(source);
        }, 1500);
    }
    
    // Function to simulate credentials authentication
    function simulateAuth(source, username, password) {
        // Simulate API delay
        setTimeout(() => {
            // Show source selection view
            integrationLoading.style.display = 'none';
            integrationSourceSelect.style.display = 'block';
            
            // Populate sample data
            populateSourceTree(source);
            
            // Save connection if remember is checked
            if (document.getElementById('remember-auth').checked) {
                saveConnection(source, username);
            }
        }, 1500);
    }
    
    // Function to populate the source tree
    function populateSourceTree(source) {
        // Clear existing tree
        sourceTree.innerHTML = '';
        
        // Sample data structure based on source
        let sampleData;
        
        switch(source) {
            case 'gdrive':
                sampleData = [
                    { type: 'folder', name: 'Feedback', children: [
                        { type: 'file', name: 'Customer Survey 2024.csv' },
                        { type: 'file', name: 'App Reviews Q1.xlsx' },
                        { type: 'file', name: 'Support Tickets March.csv' }
                    ]},
                    { type: 'folder', name: 'Reports', children: [
                        { type: 'file', name: 'User Feedback Summary.docx' },
                        { type: 'file', name: 'Issue Tracking 2024.xlsx' }
                    ]},
                    { type: 'file', name: 'Product Feedback Consolidated.csv' }
                ];
                break;
                
            case 'slack':
                sampleData = [
                    { type: 'folder', name: 'Channels', children: [
                        { type: 'file', name: 'customer-feedback' },
                        { type: 'file', name: 'support-tickets' },
                        { type: 'file', name: 'product-discussions' }
                    ]},
                    { type: 'folder', name: 'Direct Messages', children: [
                        { type: 'file', name: 'Support Team' },
                        { type: 'file', name: 'Customer Success' }
                    ]}
                ];
                break;
                
            case 'teams':
                sampleData = [
                    { type: 'folder', name: 'Teams', children: [
                        { type: 'file', name: 'Customer Support Team' },
                        { type: 'file', name: 'Product Team' }
                    ]},
                    { type: 'folder', name: 'Channels', children: [
                        { type: 'file', name: 'Feedback' },
                        { type: 'file', name: 'Bug Reports' }
                    ]},
                    { type: 'folder', name: 'Files', children: [
                        { type: 'file', name: 'Customer Feedback.xlsx' },
                        { type: 'file', name: 'Issue Tracker.csv' }
                    ]}
                ];
                break;
                
            case 'skype':
                sampleData = [
                    { type: 'folder', name: 'Group Chats', children: [
                        { type: 'file', name: 'Support Team' },
                        { type: 'file', name: 'Customer Feedback Group' }
                    ]},
                    { type: 'folder', name: 'Recent Chats', children: [
                        { type: 'file', name: 'Enterprise Customers' },
                        { type: 'file', name: 'Product Team' }
                    ]}
                ];
                break;
                
            case 'jira':
                sampleData = [
                    { type: 'folder', name: 'Projects', children: [
                        { type: 'file', name: 'Customer Support' },
                        { type: 'file', name: 'Product Development' }
                    ]},
                    { type: 'folder', name: 'Issues', children: [
                        { type: 'file', name: 'Bugs' },
                        { type: 'file', name: 'Feature Requests' },
                        { type: 'file', name: 'Customer Feedback' }
                    ]},
                    { type: 'folder', name: 'Reports', children: [
                        { type: 'file', name: 'Issue Summary.csv' },
                        { type: 'file', name: 'Customer Satisfaction.csv' }
                    ]}
                ];
                break;
                
            case 'dropbox':
                sampleData = [
                    { type: 'folder', name: 'Feedback', children: [
                        { type: 'file', name: 'Customer Feedback 2024.csv' },
                        { type: 'file', name: 'Product Reviews.xlsx' }
                    ]},
                    { type: 'folder', name: 'Support', children: [
                        { type: 'file', name: 'Tickets.csv' },
                        { type: 'file', name: 'Customer Issues.xlsx' }
                    ]},
                    { type: 'file', name: 'Consolidated Feedback.csv' }
                ];
                break;
                
            default:
                sampleData = [
                    { type: 'file', name: 'Sample Feedback.csv' },
                    { type: 'file', name: 'Sample Issues.xlsx' }
                ];
        }
        
        // Render tree
        renderTree(sampleData, sourceTree);
    }
    
    // Function to render tree view
    function renderTree(data, container) {
        data.forEach(item => {
            if (item.type === 'folder') {
                // Create folder item
                const folderDiv = document.createElement('div');
                folderDiv.className = 'tree-item tree-folder';
                folderDiv.textContent = item.name;
                
                // Create folder content container
                const contentDiv = document.createElement('div');
                contentDiv.className = 'tree-folder-content';
                
                // Add click event to toggle folder
                folderDiv.addEventListener('click', function(e) {
                    e.stopPropagation();
                    this.classList.toggle('open');
                });
                
                // Recursively render children
                renderTree(item.children, contentDiv);
                
                container.appendChild(folderDiv);
                container.appendChild(contentDiv);
            } else {
                // Create file item with checkbox
                const fileDiv = document.createElement('div');
                fileDiv.className = 'tree-item tree-file';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = item.name;
                
                const label = document.createElement('label');
                label.textContent = item.name;
                
                fileDiv.appendChild(checkbox);
                fileDiv.appendChild(label);
                container.appendChild(fileDiv);
            }
        });
    }
    
    // Function to get selected files from tree
    function getSelectedFilesFromTree() {
        const checkboxes = sourceTree.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(checkbox => checkbox.value);
    }
    
    // Function to add connected source to the UI
    function addConnectedSource(source, files) {
        // Store source data
        connectedSourcesList[source] = {
            files: files,
            timestamp: new Date().getTime()
        };
        
        // Save to localStorage
        localStorage.setItem('connectedSources', JSON.stringify(connectedSourcesList));
        
        // Update UI
        updateConnectedSourcesUI();
    }
    
    // Function to update connected sources UI
    function updateConnectedSourcesUI() {
        // Clear container
        connectedSources.innerHTML = '';
        
        // Add each source
        for (const source in connectedSourcesList) {
            const sourceData = connectedSourcesList[source];
            const fileCount = sourceData.files.length;
            
            const sourceDiv = document.createElement('div');
            sourceDiv.className = 'connected-source';
            
            // Add icon based on source
            const icon = document.createElement('i');
            icon.className = getSourceIconClass(source);
            sourceDiv.appendChild(icon);
            
            // Add source name and file count
            const label = document.createElement('span');
            label.textContent = `${getSourceDisplayName(source)} (${fileCount} files)`;
            sourceDiv.appendChild(label);
            
            // Add remove button
            const removeBtn = document.createElement('span');
            removeBtn.className = 'remove-source';
            removeBtn.innerHTML = '<i class="fas fa-times-circle"></i>';
            removeBtn.setAttribute('data-source', source);
            removeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                removeConnectedSource(source);
            });
            sourceDiv.appendChild(removeBtn);
            
            connectedSources.appendChild(sourceDiv);
        }
        
        // Show or hide the container based on if we have sources
        if (Object.keys(connectedSourcesList).length > 0) {
            connectedSources.style.display = 'flex';
            // Enable analyze button
            analyzeBtn.disabled = false;
        } else {
            connectedSources.style.display = 'none';
            // Only disable analyze button if no file is selected
            if (!document.getElementById('file-info').style.display || 
                document.getElementById('file-info').style.display === 'none') {
                analyzeBtn.disabled = true;
            }
        }
    }
    
    // Function to remove connected source
    function removeConnectedSource(source) {
        delete connectedSourcesList[source];
        localStorage.setItem('connectedSources', JSON.stringify(connectedSourcesList));
        updateConnectedSourcesUI();
    }
    
    // Function to get source display name
    function getSourceDisplayName(source) {
        switch(source) {
            case 'gdrive': return 'Google Drive';
            case 'slack': return 'Slack';
            case 'teams': return 'Microsoft Teams';
            case 'skype': return 'Skype';
            case 'jira': return 'Jira';
            case 'dropbox': return 'Dropbox';
            default: return source.charAt(0).toUpperCase() + source.slice(1);
        }
    }
    
    // Function to get source icon class
    function getSourceIconClass(source) {
        switch(source) {
            case 'gdrive': return 'fab fa-google-drive';
            case 'slack': return 'fab fa-slack';
            case 'teams': return 'fab fa-microsoft';
            case 'skype': return 'fab fa-skype';
            case 'jira': return 'fab fa-jira';
            case 'dropbox': return 'fab fa-dropbox';
            default: return 'fas fa-external-link-alt';
        }
    }
    
    // Function to save connection
    function saveConnection(source, username) {
        // Store basic connection info (not the actual credentials for security reasons)
        const connections = JSON.parse(localStorage.getItem('savedConnections') || '{}');
        connections[source] = {
            username: username,
            lastConnected: new Date().toISOString()
        };
        localStorage.setItem('savedConnections', JSON.stringify(connections));
    }
    
    // Function to load saved connections
    function loadSavedConnections() {
        // Load connected sources
        const sources = JSON.parse(localStorage.getItem('connectedSources') || '{}');
        connectedSourcesList = sources;
        updateConnectedSourcesUI();
    }
    
    // Modify the existing form submission to include data from connected sources
    const originalSubmitHandler = document.getElementById('upload-form').onsubmit;
    document.getElementById('upload-form').onsubmit = function(e) {
        e.preventDefault();
        
        // Check if we have either a file or connected sources
        const hasFile = uploadedFile !== null;
        const hasSources = Object.keys(connectedSourcesList).length > 0;
        
        if (!hasFile && !hasSources) {
            alert('Please select a file or connect a data source');
            return;
        }
        
        // If we have connected sources, add them to the form data
        if (hasSources) {
            // Create form data
            const formData = new FormData();
            
            // Add company ID and query
            const companyId = document.getElementById('company-id').value.trim();
            formData.append('company_id', companyId);
            
            const query = document.getElementById('query-text').value.trim() || 
                          "What are the key issues and actionable insights from this feedback?";
            formData.append('query', query);
            
            // Add save_analysis checkbox value
            formData.append('save_analysis', document.getElementById('save-analysis').checked);
            
            // Add connected sources metadata
            formData.append('has_connected_sources', 'true');
            formData.append('connected_sources', JSON.stringify(connectedSourcesList));
            
            // Add file if selected
            if (hasFile) {
                formData.append('file', uploadedFile);
            }
            
            // Show status section
            document.getElementById('status-section').style.display = 'block';
            
            // Reset progress
            resetProgress();
            
            // Send request
            addStatusMessage('Retrieving data from connected sources...', 'system');
            analyzeBtn.disabled = true;
            
            fetch('/api/analyze-with-integrations', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Process response same as original handler
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
                    document.getElementById('saved-notification').style.display = 'block';
                    document.getElementById('saved-text').textContent = `Analysis saved as Ticket #${data.ticket_id.substring(0, 8)}`;
                    document.getElementById('view-dashboard-link').href = `/dashboard/${companyId}`;
                } else {
                    document.getElementById('saved-notification').style.display = 'none';
                }
                analyzeBtn.disabled = false;
            })
            .catch(error => {
                addStatusMessage(`Error: ${error.message}`, 'error');
                analyzeBtn.disabled = false;
            });
        } else {
            // Use original handler for file only
            if (typeof originalSubmitHandler === 'function') {
                originalSubmitHandler.call(this, e);
            }
        }
    };
    
    // Function to update the progress bar (borrowed from script.js)
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
        document.getElementById('progress').style.width = `${percentage}%`;
    }
    
    // Function to reset progress (borrowed from script.js)
    function resetProgress() {
        Object.keys(progressSteps).forEach(step => {
            progressSteps[step].completed = false;
        });
        updateProgressBar();
    }
    
    // Function to add status message (borrowed from script.js)
    function addStatusMessage(message, type = 'info') {
        const statusMessages = document.getElementById('status-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = message;
        
        statusMessages.appendChild(messageElement);
        statusMessages.scrollTop = statusMessages.scrollHeight;
    }
    
    // Function to display results (borrowed from script.js)
    function displayResults(data) {
        // Show results section
        document.getElementById('results-section').style.display = 'block';
        
        // Check if we have the final report
        if (!data.final_report) {
            addStatusMessage('Error: No final report data', 'error');
            return;
        }
        
        const report = data.final_report;
        
        // Executive Summary
        document.getElementById('summary-content').textContent = report.executive_summary || 'No summary available';
        
        // Issues List
        renderIssues(report.issues || []);
        
        // Implementation Plan
        renderImplementationPlan(report.implementation_plan || {});
        
        // Scroll to results
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    // These functions need to be re-declared to not rely on variables from script.js scope
    // Function to render issues (simplified from script.js)
    function renderIssues(issues) {
        // Implementation details omitted for brevity
        // This would be the same as the original script.js implementation
        if (window.renderIssues) {
            window.renderIssues(issues);
        }
    }
    
    // Function to render implementation plan (simplified from script.js)
    function renderImplementationPlan(plan) {
        // Implementation details omitted for brevity
        // This would be the same as the original script.js implementation
        if (window.renderImplementationPlan) {
            window.renderImplementationPlan(plan);
        }
    }
});