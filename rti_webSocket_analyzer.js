// RTI WebSocket and Checkbox Analyzer
// Run this in the browser console on the diagnostics page

console.log("RTI WebSocket Analyzer Loaded");
console.log("This script will help you understand checkbox behavior and WebSocket subscriptions");

// Store all discovered data
window.rtiAnalysis = {
    checkboxes: [],
    websocketMessages: [],
    subscriptions: [],
    variables: {}
};

// Function to analyze all checkboxes on the page
function analyzeCheckboxes() {
    console.log("\n=== ANALYZING CHECKBOXES ===");
    
    // Wait for Vue.js to load content
    setTimeout(() => {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        console.log(`Found ${checkboxes.length} checkboxes`);
        
        window.rtiAnalysis.checkboxes = [];
        
        checkboxes.forEach((checkbox, index) => {
            const analysis = {
                index: index,
                id: checkbox.id || '',
                name: checkbox.name || '',
                value: checkbox.value || '',
                className: checkbox.className || '',
                checked: checkbox.checked,
                parentText: '',
                parentHTML: '',
                dataAttributes: {},
                possibleVariableId: null
            };
            
            // Get parent element info
            if (checkbox.parentElement) {
                analysis.parentText = checkbox.parentElement.textContent.trim();
                analysis.parentHTML = checkbox.parentElement.outerHTML.substring(0, 300);
            }
            
            // Get data attributes
            for (let attr of checkbox.attributes) {
                if (attr.name.startsWith('data-')) {
                    analysis.dataAttributes[attr.name] = attr.value;
                }
            }
            
            // Try to extract variable ID from text or attributes
            const text = analysis.parentText + ' ' + checkbox.value + ' ' + checkbox.id;
            const idMatch = text.match(/\b(\d+)\b/g);
            if (idMatch) {
                analysis.possibleVariableId = idMatch[0];
            }
            
            window.rtiAnalysis.checkboxes.push(analysis);
            
            console.log(`Checkbox ${index}: ${analysis.parentText.substring(0, 60)}...`);
            if (analysis.possibleVariableId) {
                console.log(`  Possible Variable ID: ${analysis.possibleVariableId}`);
            }
        });
        
        console.log(`\nAnalyzed ${window.rtiAnalysis.checkboxes.length} checkboxes`);
        
    }, 2000); // Wait 2 seconds for Vue.js to load
}

// Function to monitor WebSocket messages
function monitorWebSocketMessages() {
    console.log("\n=== MONITORING WEBSOCKET MESSAGES ===");
    
    // Override WebSocket to intercept messages
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(...args) {
        const ws = new originalWebSocket(...args);
        console.log(`WebSocket created: ${args[0]}`);
        
        ws.addEventListener('message', function(event) {
            try {
                const data = JSON.parse(event.data);
                window.rtiAnalysis.websocketMessages.push({
                    timestamp: new Date().toISOString(),
                    data: data
                });
                
                console.log(`\n--- WebSocket Message ---`);
                console.log(JSON.stringify(data, null, 2));
                
                // Check if it's a subscription message
                if (data.type === 'Subscribe' && data.resource === 'Sysvar') {
                    const varId = data.value.id;
                    const status = data.value.status;
                    console.log(`📡 Subscription: Variable ${varId} = ${status}`);
                    
                    window.rtiAnalysis.subscriptions.push({
                        variableId: varId,
                        status: status,
                        timestamp: new Date().toISOString()
                    });
                }
                
                // Check if it's a system variable response
                if (data.messageType === 'Sysvar') {
                    const varId = data.sysvarid;
                    const varValue = data.sysvarval;
                    console.log(`📊 Variable Update: ${varId} = ${varValue}`);
                    
                    window.rtiAnalysis.variables[varId] = {
                        id: varId,
                        value: varValue,
                        timestamp: new Date().toISOString()
                    };
                }
                
            } catch (e) {
                console.log(`Non-JSON WebSocket message: ${event.data}`);
            }
        });
        
        ws.addEventListener('open', function() {
            console.log('WebSocket connection opened');
        });
        
        ws.addEventListener('close', function() {
            console.log('WebSocket connection closed');
        });
        
        ws.addEventListener('error', function(error) {
            console.log('WebSocket error:', error);
        });
        
        return ws;
    };
    
    console.log("WebSocket interceptor installed");
}

// Function to monitor checkbox changes
function monitorCheckboxChanges() {
    console.log("\n=== MONITORING CHECKBOX CHANGES ===");
    
    // Wait for checkboxes to load
    setTimeout(() => {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        console.log(`Monitoring ${checkboxes.length} checkboxes`);
        
        checkboxes.forEach((checkbox, index) => {
            checkbox.addEventListener('change', function() {
                console.log(`\n🔄 CHECKBOX ${index} CHANGED`);
                console.log(`ID: ${this.id}`);
                console.log(`Name: ${this.name}`);
                console.log(`Value: ${this.value}`);
                console.log(`Checked: ${this.checked}`);
                console.log(`Parent Text: ${this.parentElement ? this.parentElement.textContent.trim() : 'N/A'}`);
                
                // Try to find associated variable ID
                const parentText = this.parentElement ? this.parentElement.textContent : '';
                const valueMatch = parentText.match(/\b(\d+)\b/);
                if (valueMatch) {
                    console.log(`🔍 Possible Variable ID: ${valueMatch[1]}`);
                }
                
                // Check for data attributes that might contain the variable ID
                for (let attr of this.attributes) {
                    if (attr.name.startsWith('data-')) {
                        console.log(`📋 ${attr.name}: ${attr.value}`);
                    }
                }
            });
        });
        
    }, 3000); // Wait 3 seconds for Vue.js to load
}

// Function to simulate checkbox clicks
function simulateCheckboxClicks() {
    console.log("\n=== SIMULATING CHECKBOX CLICKS ===");
    
    setTimeout(() => {
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        console.log(`Clicking ${checkboxes.length} checkboxes...`);
        
        checkboxes.forEach((checkbox, index) => {
            console.log(`\n--- Clicking Checkbox ${index} ---`);
            console.log(`Text: ${checkbox.parentElement ? checkbox.parentElement.textContent.trim() : 'N/A'}`);
            
            // Click the checkbox
            checkbox.click();
            
            // Wait a moment for WebSocket messages
            setTimeout(() => {
                console.log(`✓ Checkbox ${index} clicked`);
            }, 500);
        });
        
    }, 3000);
}

// Function to export all analysis data
function exportAnalysisData() {
    const data = {
        timestamp: new Date().toISOString(),
        checkboxes: window.rtiAnalysis.checkboxes,
        websocketMessages: window.rtiAnalysis.websocketMessages,
        subscriptions: window.rtiAnalysis.subscriptions,
        variables: window.rtiAnalysis.variables
    };
    
    console.log("\n=== EXPORT DATA ===");
    console.log(JSON.stringify(data, null, 2));
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(() => {
            console.log("✓ Analysis data copied to clipboard");
        });
    }
    
    return data;
}

// Function to show summary
function showSummary() {
    console.log("\n=== ANALYSIS SUMMARY ===");
    console.log(`Checkboxes found: ${window.rtiAnalysis.checkboxes.length}`);
    console.log(`WebSocket messages: ${window.rtiAnalysis.websocketMessages.length}`);
    console.log(`Subscriptions made: ${window.rtiAnalysis.subscriptions.length}`);
    console.log(`Variables discovered: ${Object.keys(window.rtiAnalysis.variables).length}`);
    
    if (Object.keys(window.rtiAnalysis.variables).length > 0) {
        console.log("\nVariables:");
        Object.values(window.rtiAnalysis.variables).forEach(variable => {
            console.log(`  ${variable.id}: ${variable.value}`);
        });
    }
}

// Auto-start analysis
console.log("\n=== STARTING ANALYSIS ===");
analyzeCheckboxes();
monitorWebSocketMessages();
monitorCheckboxChanges();

console.log("\n=== AVAILABLE FUNCTIONS ===");
console.log("- analyzeCheckboxes() - Analyze all checkboxes");
console.log("- monitorCheckboxChanges() - Monitor checkbox changes");
console.log("- simulateCheckboxClicks() - Click all checkboxes");
console.log("- exportAnalysisData() - Export all analysis data");
console.log("- showSummary() - Show analysis summary");

console.log("\n=== INSTRUCTIONS ===");
console.log("1. Wait for the page to fully load (checkboxes should appear)");
console.log("2. Click checkboxes manually and watch console output");
console.log("3. Check Network tab for WebSocket messages");
console.log("4. Run showSummary() to see what was discovered");
console.log("5. Run exportAnalysisData() to get all data");


