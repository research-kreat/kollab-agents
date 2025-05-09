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
    
    // OAuth connect button - direct connection without filling anything
    oauthConnectBtn.addEventListener('click', function() {
        // Show loading state
        integrationAuthForm.style.display = 'none';
        integrationLoading.style.display = 'block';
        
        // Simulate OAuth process
        simulateOAuth(currentSource);
    });
    
    // Connect button in modal (used after selecting files)
    integrationConnectBtn.addEventListener('click', function() {
        if (integrationSourceSelect.style.display !== 'none') {
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
            
            // Populate file tree
            populateSourceTree(source);
        }, 1500);
    }
    
    // Function to populate the source tree
    function populateSourceTree(source) {
        // Clear existing tree
        sourceTree.innerHTML = '';
        
        // Make API call to get source structure
        fetch(`/api/integrations/files?source=${source}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderTree(data.files, sourceTree);
                } else {
                    sourceTree.innerHTML = `<div class="error-message">${data.error || 'Failed to load files'}</div>`;
                }
            })
            .catch(error => {
                sourceTree.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            });
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
    
    // Function to load saved connections
    function loadSavedConnections() {
        // Load connected sources
        const sources = JSON.parse(localStorage.getItem('connectedSources') || '{}');
        connectedSourcesList = sources;
        updateConnectedSourcesUI();
    }
    
    // Expose the integration handler to the main script
    window.integrationHandler = {
        getConnectedSources: function() {
            return connectedSourcesList;
        },
        hasConnectedSources: function() {
            return Object.keys(connectedSourcesList).length > 0;
        }
    };
});