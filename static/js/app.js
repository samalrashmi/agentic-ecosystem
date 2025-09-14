// Agentic Ecosystem - Main JavaScript

// Global variables
let currentProjectId = null;
let websocket = null;
let agentStates = {
    'orchestrator-agent': 'sleeping',
    'ba-agent': 'sleeping',
    'architect-agent': 'sleeping',
    'developer-agent': 'sleeping',
    'tester-agent': 'sleeping'
};

// Initialize the page and set agents to idle state
async function initializePage() {
    console.log('Initializing page...');
    
    // Instead of fetching health status, assume all agents are ready
    // This is a temporary workaround while we fix the health endpoint
    Object.keys(agentStates).forEach(agentId => {
        updateAgentStatus(agentId, 'sleeping', 'Ready to work! 💤');
    });
    
    // Optional: Try to fetch health status anyway
    try {
        const response = await fetch('/agents/health');
        if (response.ok) {
            const data = await response.json();
            console.log('Agent health data:', data);
            
            // Update UI with actual health data if available
            if (data.agents) {
                Object.entries(data.agents).forEach(([agentType, agentInfo]) => {
                    const agentId = agentType.replace('_', '-') + '-agent';
                    let uiStatus = 'idle';
                    let message = 'Ready to work! 💤';
                    
                    if (agentInfo.status === 'working') {
                        uiStatus = 'working';
                        message = 'Working hard! 🎵';
                    } else if (!agentInfo.is_healthy) {
                        uiStatus = 'error';
                        message = 'Something went wrong! 😵';
                    }
                    
                    updateAgentStatus(agentId, uiStatus, message);
                });
            }
        } else {
            console.log('Health endpoint not available, using default idle state');
        }
    } catch (error) {
        console.log('Could not fetch health status, using default idle state:', error);
    }
}

// Form submission handler
function initializeFormHandler() {
    document.getElementById('projectForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const projectData = {
            specification: `Project Name: ${formData.get('name')}\n\nDescription: ${formData.get('description')}`,
            title: formData.get('name'),
            domain: "web-application" // You can make this dynamic later
        };

        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;
        submitBtn.textContent = '🚀 Creating Project...';

        try {
            const response = await fetch('/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData)
            });

            if (response.ok) {
                const result = await response.json();
                currentProjectId = result.project_id;
                
                showNotification('Project created successfully! 🎉', 'success');
                showProjectStatus(result.project_id);
                connectWebSocket();
                
                // Start the workflow with immediate status updates
                updateAgentStatus('orchestrator-agent', 'working', 'Coordinating the team! 🎵');
                updateProgress(10);
                document.getElementById('statusText').textContent = 'Project started! Orchestrator is coordinating the team...';
                
                // Simulate immediate workflow start (this would normally come from WebSocket)
                setTimeout(() => {
                    handleWebSocketMessage({
                        type: 'workflow_update',
                        stage: 'requirements_analysis'
                    });
                }, 2000);
                
                // Simulate complete workflow for demo
                simulateWorkflowProgress();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create project');
            }
        } catch (error) {
            showNotification('Error creating project: ' + error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Create Project';
        }
    });
}

// Project status functions
function showProjectStatus(projectId) {
    document.getElementById('projectId').textContent = `Project ID: ${projectId}`;
    document.getElementById('projectStatus').classList.remove('status-hidden');
    updateProgress(10);
}

function updateProgress(percentage) {
    document.getElementById('progressFill').style.width = percentage + '%';
}

// WebSocket functions
function connectWebSocket() {
    if (!currentProjectId) return;

    const clientId = 'web-client-' + Date.now();
    websocket = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    websocket.onopen = () => {
        console.log('WebSocket connected');
        showNotification('Connected to live updates! 📡', 'success');
    };

    websocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(() => {
            if (currentProjectId) {
                connectWebSocket();
            }
        }, 5000);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(message) {
    console.log('Received message:', message);

    // Update agent status based on message
    if (message.type === 'agent_status') {
        const agentId = message.agent_id.replace('_', '-');
        updateAgentStatus(agentId, message.status, message.message);
    }

    // Update progress based on workflow stage
    if (message.type === 'workflow_update') {
        const stage = message.stage;
        let progress = 10;
        let statusText = 'Working on your project...';

        // Mark previous agents as completed when moving to next stage
        switch (stage) {
            case 'requirements_analysis':
                progress = 25;
                statusText = 'Analyzing requirements... 📋';
                updateAgentStatus('orchestrator-agent', 'completed', 'Coordination complete! ✅');
                updateAgentStatus('ba-agent', 'working', 'Analyzing requirements! 🎵');
                break;
            case 'architecture_design':
                progress = 40;
                statusText = 'Designing architecture... 🏗️';
                updateAgentStatus('ba-agent', 'completed', 'Requirements analysis complete! ✅');
                updateAgentStatus('architect-agent', 'working', 'Designing the system! 🎵');
                break;
            case 'development':
                progress = 60;
                statusText = 'Writing code... 💻';
                updateAgentStatus('architect-agent', 'completed', 'Architecture design complete! ✅');
                updateAgentStatus('developer-agent', 'working', 'Coding away! 🎵');
                break;
            case 'testing':
                progress = 80;
                statusText = 'Testing the application... 🧪';
                updateAgentStatus('developer-agent', 'completed', 'Development complete! ✅');
                updateAgentStatus('tester-agent', 'working', 'Testing everything! 🎵');
                break;
            case 'completed':
                progress = 100;
                statusText = 'Project completed! 🎉';
                updateAgentStatus('tester-agent', 'completed', 'Testing complete! ✅');
                showNotification('🎉 Project completed successfully! All agents have finished their work.', 'success');
                showCompletionSummary();
                break;
        }

        updateProgress(progress);
        document.getElementById('statusText').textContent = statusText;
    }

    // Handle errors
    if (message.type === 'error') {
        const agentId = message.agent_id?.replace('_', '-');
        if (agentId) {
            updateAgentStatus(agentId, 'error', 'Something went wrong! 😠');
        }
        showNotification('Agent encountered an error: ' + message.message, 'error');
    }
}

// Agent status functions
function updateAgentStatus(agentId, status, statusText) {
    const agent = document.getElementById(agentId);
    if (!agent) return;

    const statusElement = agent.querySelector('.agent-status-text');

    // Remove all status classes from agent
    agent.classList.remove('sleeping', 'working', 'error', 'completed', 'active');
    
    // Add new status class to agent
    agent.classList.add(status);

    // Update status text and its classes
    if (statusElement) {
        statusElement.textContent = statusText;
        // Remove old status classes
        statusElement.classList.remove('status-sleeping', 'status-working', 'status-error', 'status-completed', 'status-active');
        // Add new status class
        statusElement.classList.add('status-' + status);
    }

    // Store current state
    agentStates[agentId] = status;
    
    console.log(`Updated ${agentId} to ${status}: ${statusText}`);
}

function setAllAgentsSleeping() {
    Object.keys(agentStates).forEach(agentId => {
        updateAgentStatus(agentId, 'completed', 'Work completed! ✅');
    });
}

// Notification functions
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.innerHTML = message; // Changed from textContent to innerHTML
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000); // Increased timeout for detailed messages
    }
}

// Demo and interaction functions
function simulateWorkflowProgress() {
    if (!currentProjectId) return;
    
    const stages = [
        { stage: 'requirements_analysis', delay: 4000 },
        { stage: 'architecture_design', delay: 8000 },
        { stage: 'development', delay: 12000 },
        { stage: 'testing', delay: 16000 },
        { stage: 'completed', delay: 20000 }
    ];
    
    stages.forEach(({ stage, delay }) => {
        setTimeout(() => {
            if (currentProjectId) { // Only continue if project is still active
                handleWebSocketMessage({
                    type: 'workflow_update',
                    stage: stage
                });
            }
        }, delay);
    });
}

function simulateAgentActivity() {
    setInterval(() => {
        // Random agent activity simulation when no real project is running
        if (!currentProjectId) {
            const agents = Object.keys(agentStates);
            const randomAgent = agents[Math.floor(Math.random() * agents.length)];
            
            if (Math.random() > 0.95) { // 5% chance
                updateAgentStatus(randomAgent, 'working', 'Just stretching! 🎵');
                setTimeout(() => {
                    updateAgentStatus(randomAgent, 'sleeping', 'Back to sleep... 😴');
                }, 2000);
            }
        }
    }, 5000);
}

function initializeAgentInteractions() {
    // Add some fun interactions
    document.querySelectorAll('.agent').forEach(agent => {
        agent.addEventListener('click', () => {
            const agentNameElement = agent.querySelector('.agent-name');
            if (agentNameElement) {
                const agentName = agentNameElement.textContent;
                showNotification(`${agentName} says hello! 👋`, 'success');
            }
        });
    });
}

// Workbench modal functions
function openWorkbench(agentName) {
    const modal = document.getElementById(`${agentName}-workbench`);
    if (modal) {
        modal.style.display = 'flex';
        loadArtifacts(agentName);
    }
}

function closeWorkbench(agentName) {
    const modal = document.getElementById(`${agentName}-workbench`);
    if (modal) {
        modal.style.display = 'none';
    }
}

async function loadArtifacts(agentName) {
    const workbenchBody = document.getElementById(`${agentName}-workbench-body`);
    if (!workbenchBody) return;

    // Show loading state
    workbenchBody.innerHTML = '<div class="loading-artifacts">⏳ Loading artifacts...</div>';

    try {
        const response = await fetch(`/api/artifacts/${agentName}`);
        if (!response.ok) {
            if (response.status === 404) {
                // No artifacts yet - this is normal for new agents
                workbenchBody.innerHTML = `
                    <div class="empty-workbench">
                        <h3>No artifacts yet</h3>
                        <p>The ${agentName} agent hasn't generated any artifacts yet</p>
                    </div>
                `;
                return;
            }
            throw new Error(`Failed to load artifacts: ${response.statusText}`);
        }

        const artifacts = await response.json();
        renderArtifacts(workbenchBody, artifacts, agentName);
    } catch (error) {
        console.error('Error loading artifacts:', error);
        workbenchBody.innerHTML = `
            <div class="error-state">
                <h3>⚠️ Failed to load artifacts</h3>
                <p>${error.message}</p>
                <button onclick="loadArtifacts('${agentName}')" class="retry-btn" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>
            </div>
        `;
    }
}

function renderArtifacts(container, artifacts, agentName) {
    if (!artifacts || artifacts.length === 0) {
        container.innerHTML = `
            <div class="empty-workbench">
                <h3>No artifacts yet</h3>
                <p>The ${agentName} agent hasn't generated any artifacts yet</p>
            </div>
        `;
        return;
    }

    const artifactsHtml = artifacts.map(artifact => `
        <div class="artifact-card">
            <div class="artifact-header">
                <div class="artifact-title">${artifact.title}</div>
                <div class="artifact-meta">
                    <span class="artifact-type">${artifact.type}</span>
                    <span class="artifact-date">${new Date(artifact.created_at).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="artifact-preview">
                ${artifact.preview || 'No preview available'}
            </div>
            <div class="artifact-actions">
                <button onclick="viewArtifact('${artifact.id}')" class="action-btn view-btn">👁️ View</button>
                <button onclick="downloadArtifact('${artifact.id}')" class="action-btn download-btn">📥 Download</button>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="artifacts-grid">
            ${artifactsHtml}
        </div>
    `;
}

async function viewArtifact(artifactId) {
    try {
        const response = await fetch(`/api/artifacts/view/${artifactId}`);
        if (!response.ok) {
            throw new Error('Failed to load artifact content');
        }

        const content = await response.text();
        
        // Create a modal to display the artifact content
        const viewModal = document.createElement('div');
        viewModal.className = 'artifact-view-modal';
        viewModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1001;
        `;
        
        viewModal.innerHTML = `
            <div class="artifact-view-content" style="
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 800px;
                max-height: 90%;
                display: flex;
                flex-direction: column;
            ">
                <div class="artifact-view-header" style="
                    padding: 20px;
                    border-bottom: 1px solid #e9ecef;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h3 style="margin: 0;">📄 Artifact Content</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
                </div>
                <div class="artifact-view-body" style="
                    padding: 20px;
                    overflow: auto;
                    flex: 1;
                ">
                    <pre style="
                        white-space: pre-wrap;
                        font-family: 'Courier New', monospace;
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 6px;
                        border: 1px solid #e9ecef;
                        margin: 0;
                    ">${content}</pre>
                </div>
            </div>
        `;
        document.body.appendChild(viewModal);
    } catch (error) {
        showNotification('Failed to load artifact content', 'error');
    }
}

async function downloadArtifact(artifactId) {
    try {
        const response = await fetch(`/api/artifacts/download/${artifactId}`);
        if (!response.ok) {
            throw new Error('Failed to download artifact');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `artifact_${artifactId}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Artifact downloaded successfully! 📥', 'success');
    } catch (error) {
        showNotification('Failed to download artifact', 'error');
    }
}

// Completion functions
function showCompletionSummary() {
    const summaryDiv = document.getElementById('completionSummary');
    if (summaryDiv) {
        summaryDiv.style.display = 'block';
    }
}

function downloadProjectArtifacts() {
    if (!currentProjectId) {
        showNotification('No project ID available for download', 'error');
        return;
    }
    
    // Create a simple download of project summary
    const projectSummary = {
        projectId: currentProjectId,
        completedAt: new Date().toISOString(),
        agents: Object.keys(agentStates).map(agentId => ({
            name: agentId.replace('-agent', '').replace('-', ' '),
            status: agentStates[agentId]
        })),
        artifactsLocation: `/out/project_${currentProjectId}/`
    };
    
    const blob = new Blob([JSON.stringify(projectSummary, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `project_${currentProjectId}_summary.json`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showNotification('📁 Project summary downloaded! Check the /out folder for all artifacts.', 'success');
}

function viewProjectSummary() {
    if (!currentProjectId) {
        showNotification('No project data available', 'error');
        return;
    }
    
    const summaryText = `
🎉 Project Completion Summary

Project ID: ${currentProjectId}
Completed: ${new Date().toLocaleString()}

Agent Status:
${Object.keys(agentStates).map(agentId => {
    const name = agentId.replace('-agent', '').replace('-', ' ').toUpperCase();
    const status = agentStates[agentId] === 'completed' ? '✅ COMPLETED' : '⏳ ' + agentStates[agentId].toUpperCase();
    return `• ${name}: ${status}`;
}).join('\n')}

All project artifacts have been saved to:
/out/project_${currentProjectId}/

This includes:
• Business requirements analysis
• System architecture design  
• Implementation plan & source code
• Test strategy & quality reports
`;

    alert(summaryText);
}

// Modal event handlers
function initializeModalHandlers() {
    // Close modals when clicking outside
    window.onclick = function(event) {
        if (event.target.classList.contains('workbench-modal')) {
            event.target.style.display = 'none';
        }
        if (event.target.classList.contains('artifact-view-modal')) {
            event.target.remove();
        }
    };
}

// Global state for mode
let currentMode = 'full'; // 'full' or 'ba-only'

// Mode switching functionality
function setMode(mode) {
    currentMode = mode;
    
    // Update button states
    document.getElementById('fullWorkflowMode').classList.toggle('active', mode === 'full');
    document.getElementById('baOnlyMode').classList.toggle('active', mode === 'ba-only');
    
    // Update form elements
    if (mode === 'ba-only') {
        document.getElementById('formTitle').textContent = '📋 Requirements Analysis';
        document.getElementById('descriptionLabel').textContent = 'Detailed Requirements:';
        document.getElementById('projectDescription').placeholder = 'Describe your requirements in detail. Include business objectives, user needs, functional requirements, constraints, and any specific business rules...';
        document.getElementById('domainGroup').style.display = 'none';
        document.getElementById('exportFormatGroup').style.display = 'block';
        document.getElementById('submitBtn').innerHTML = '📋 Generate Specification';
    } else {
        document.getElementById('formTitle').textContent = '📝 Project Specification';
        document.getElementById('descriptionLabel').textContent = 'Detailed Description:';
        document.getElementById('projectDescription').placeholder = 'Describe what you want to build in detail. Include features, target users, and any specific requirements...';
        document.getElementById('domainGroup').style.display = 'block';
        document.getElementById('exportFormatGroup').style.display = 'none';
        document.getElementById('submitBtn').innerHTML = '🚀 Create Project';
    }
}

// Enhanced form submission handler for both modes
function initializeEnhancedFormHandler() {
    document.getElementById('projectForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (currentMode === 'ba-only') {
            await handleBAOnlySubmission(e);
        } else {
            await handleFullWorkflowSubmission(e);
        }
    });
}

// BA-only submission handler with fallback to regular endpoint
async function handleBAOnlySubmission(e) {
    const formData = new FormData(e.target);
    const requestData = {
        title: formData.get('name'),
        requirements: formData.get('description'),
        export_format: formData.get('export_format') || 'markdown'
    };

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '🚀 Starting...';

    try {
        // Try streaming first, fallback to regular endpoint if it fails
        let finalResult = null;
        const startTime = Date.now();
        
        try {
            // Attempt streaming
            console.log('Attempting streaming endpoint...');
            finalResult = await handleStreamingRequest(requestData, submitBtn);
        } catch (streamError) {
            console.warn('Streaming failed, falling back to regular endpoint:', streamError);
            // Fallback to regular endpoint with progress simulation
            finalResult = await handleRegularRequest(requestData, submitBtn);
        }

        const endTime = Date.now();
        const processingTime = ((endTime - startTime) / 1000).toFixed(2);

        if (finalResult) {
            // Enhanced success notification with details
            const successMessage = `
                Specification generated successfully! 🎉<br>
                <small>
                    Processing time: ${processingTime}s | 
                    Tokens used: ${finalResult.token_count ? finalResult.token_count.toLocaleString() : 'N/A'} |
                    Status: ${finalResult.status || 'completed'}
                    ${finalResult.saved_files ? `<br>Generated ${finalResult.saved_files.length} files in ${finalResult.output_directory}` : ''}
                </small>
            `;
            showNotification(successMessage, 'success');
            displayBAResults(finalResult);
        } else {
            throw new Error('No result received');
        }

    } catch (error) {
        console.error('BA submission error:', error);
        const errorMessage = `
            Error generating specification ❌<br>
            <small>${error.message}</small>
        `;
        showNotification(errorMessage, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '📋 Generate Specification';
    }
}

// Handle streaming request
async function handleStreamingRequest(requestData, submitBtn) {
    const response = await fetch('/ba/specification/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalResult = null;

    while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer
        
        for (const line of lines) {
            if (line.trim() && line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    console.log('Received SSE data:', data);
                    
                    if (data.type === 'progress') {
                        submitBtn.textContent = data.message;
                        showNotification(`${data.message}`, 'info');
                    } else if (data.type === 'complete') {
                        finalResult = data.result;
                        console.log('Received final result:', finalResult);
                        break;
                    } else if (data.type === 'error') {
                        throw new Error(data.message);
                    }
                } catch (parseError) {
                    console.warn('Failed to parse SSE data:', parseError, 'Line:', line);
                }
            }
        }
        
        if (finalResult) break;
    }
    
    return finalResult;
}

// Handle regular request with simulated progress
async function handleRegularRequest(requestData, submitBtn) {
    const progressSteps = [
        '🚀 Initializing BA Agent...',
        '🧠 Analyzing requirements with Chain of Thought...',
        '📋 Generating functional specification...',
        '📝 Creating comprehensive Gherkin user stories...',
        '💾 Saving specification files...'
    ];
    
    let currentStep = 0;
    
    // Start progress simulation
    const progressInterval = setInterval(() => {
        if (currentStep < progressSteps.length) {
            submitBtn.textContent = progressSteps[currentStep];
            showNotification(progressSteps[currentStep], 'info');
            currentStep++;
        }
    }, 2000);
    
    try {
        const response = await fetch('/ba/specification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Unknown error');
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        clearInterval(progressInterval);
        throw error;
    }
}

// Display BA results
function displayBAResults(result) {
    const baResults = document.getElementById('baResults');
    const spec = result.specification;
    
    // Hide other sections
    document.getElementById('projectStatus').style.display = 'none';
    
    // Populate result data with enhanced information
    document.getElementById('baProjectName').textContent = spec.project_title || 'Generated Project';
    document.getElementById('baTimestamp').textContent = new Date(result.timestamp).toLocaleString();
    document.getElementById('baTokenCount').textContent = result.token_count.toLocaleString();
    
    // Add status and file information
    if (result.status) {
        const statusHtml = `
            <div class="status-info" style="margin: 10px 0; padding: 10px; border-radius: 5px; background: ${result.status === 'success' ? '#d4edda' : '#f8d7da'};">
                <strong>Status:</strong> <span style="color: ${result.status === 'success' ? '#155724' : '#721c24'};">${result.status.toUpperCase()}</span>
                ${result.output_directory ? `<br><strong>Output Directory:</strong> <code>${result.output_directory}</code>` : ''}
                ${result.saved_files && result.saved_files.length > 0 ? `
                    <br><strong>Generated Files:</strong>
                    <ul style="margin: 5px 0 0 20px;">
                        ${result.saved_files.map(file => `<li><code>${file}</code></li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        `;
        
        // Insert status info after the basic info
        const tokenCountElement = document.getElementById('baTokenCount').parentElement;
        tokenCountElement.insertAdjacentHTML('afterend', statusHtml);
    }
    
    // Populate executive summary (from chain of thought)
    const executiveSummary = document.getElementById('executiveSummary');
    if (spec.executive_summary) {
        executiveSummary.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${spec.executive_summary}</pre>`;
    } else {
        executiveSummary.textContent = 'Executive summary will be generated...';
    }
    
    // Populate functional requirements (from functional spec)
    const funcReqsDiv = document.getElementById('functionalReqs');
    if (spec.functional_requirements) {
        funcReqsDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${spec.functional_requirements}</pre>`;
    } else {
        funcReqsDiv.textContent = 'Functional requirements will be generated...';
    }
    
    // Populate user stories (from Gherkin template)
    const userStoriesDiv = document.getElementById('userStories');
    if (spec.user_stories) {
        userStoriesDiv.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${spec.user_stories}</pre>`;
    } else {
        userStoriesDiv.textContent = 'User stories will be generated...';
    }
    
    // Set up download handlers
    document.getElementById('downloadMarkdown').onclick = () => downloadSpecification(result.project_id, 'markdown');
    document.getElementById('downloadJson').onclick = () => downloadSpecification(result.project_id, 'json');
    
    // Show results
    baResults.style.display = 'block';
    baResults.scrollIntoView({ behavior: 'smooth' });
}

// Download specification
async function downloadSpecification(projectId, format) {
    try {
        const response = await fetch(`/ba/specification/${projectId}/export?format=${format}`);
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `specification_${projectId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showNotification(`Specification downloaded as ${format.toUpperCase()}! 📁`, 'success');
        } else {
            throw new Error('Failed to download specification');
        }
    } catch (error) {
        showNotification('Error downloading specification: ' + error.message, 'error');
    }
}

// Full workflow submission handler (existing functionality)
async function handleFullWorkflowSubmission(e) {
    const formData = new FormData(e.target);
    const projectData = {
        specification: `Project Name: ${formData.get('name')}\n\nDescription: ${formData.get('description')}`,
        title: formData.get('name'),
        domain: "web-application"
    };

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = '🚀 Creating Project...';

    try {
        const response = await fetch('/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(projectData)
        });

        if (response.ok) {
            const result = await response.json();
            currentProjectId = result.project_id;
            
            showNotification('Project created successfully! 🎉', 'success');
            showProjectStatus(result.project_id);
            connectWebSocket();
            
            // Hide BA results if showing
            document.getElementById('baResults').style.display = 'none';
            
            // Start the workflow with immediate status updates
            updateAgentStatus('orchestrator-agent', 'working', 'Coordinating the team! 🎵');
            updateProgress(10);
            document.getElementById('statusText').textContent = 'Project started! Orchestrator is coordinating the team...';
            
            // Simulate immediate workflow start
            setTimeout(() => {
                handleWebSocketMessage({
                    type: 'workflow_update',
                    stage: 'requirements_analysis'
                });
            }, 2000);
            
            // Simulate complete workflow for demo
            simulateWorkflowProgress();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to create project');
        }
    } catch (error) {
        showNotification('Error creating project: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Create Project';
    }
}

// Main initialization function
function initializeApp() {
    console.log('🚀 Initializing Agentic Ecosystem App...');
    
    // Initialize all components
    initializePage();
    initializeEnhancedFormHandler(); // Use enhanced form handler
    initializeAgentInteractions();
    initializeModalHandlers();
    
    // Start simulation
    simulateAgentActivity();
    
    console.log('✅ App initialized successfully!');
}

// Call initialization when page loads
document.addEventListener('DOMContentLoaded', initializeApp);
