// Browser Console Script for RTI Variable Discovery
// Run this in the browser console while on the diagnostics page

console.log("RTI Variable Discovery Script Loaded");
console.log("Check the checkboxes on the page to discover variables");

// Store discovered variables
window.rtiVariables = {};

// Function to add a variable to our catalog
function addRTIVariable(id, name, value) {
    window.rtiVariables[id] = {
        id: id,
        name: name,
        value: value,
        discoveredAt: new Date().toISOString()
    };
    console.log(`✓ Variable ${id}: ${name} = ${value}`);
}

// Function to display all discovered variables
function listRTIVariables() {
    console.log("\n=== RTI VARIABLES DISCOVERED ===");
    const sorted = Object.values(window.rtiVariables).sort((a, b) => a.id - b.id);
    
    sorted.forEach(variable => {
        console.log(`ID ${variable.id.toString().padStart(3)}: ${variable.name}`);
        if (variable.value) {
            console.log(`       Value: ${variable.value}`);
        }
    });
    
    console.log(`\nTotal variables: ${sorted.length}`);
    return sorted;
}

// Function to export variables as JSON
function exportRTIVariables() {
    const data = {
        discoveredAt: new Date().toISOString(),
        variables: window.rtiVariables
    };
    
    const json = JSON.stringify(data, null, 2);
    console.log("=== EXPORT DATA ===");
    console.log(json);
    
    // Copy to clipboard if possible
    if (navigator.clipboard) {
        navigator.clipboard.writeText(json).then(() => {
            console.log("✓ Data copied to clipboard");
        });
    }
    
    return data;
}

// Function to generate HomeKit configuration
function generateHomeKitConfig() {
    const variables = Object.values(window.rtiVariables).sort((a, b) => a.id - b.id);
    
    const config = {
        rti_server: {
            host: "192.168.102.232",
            port: 80
        },
        homekit: {
            bridge_name: "RTI Bridge",
            port: 51826,
            setup_code: "123-45-678"
        },
        variables: variables.map(variable => ({
            id: variable.id,
            name: variable.name,
            type: "switch", // Default type
            homekit_type: "switch",
            description: `RTI Variable ${variable.id}`,
            current_value: variable.value
        }))
    };
    
    console.log("=== HOMEKIT CONFIG ===");
    console.log(JSON.stringify(config, null, 2));
    
    return config;
}

// Instructions
console.log("\n=== INSTRUCTIONS ===");
console.log("1. Check the checkboxes on the diagnostics page");
console.log("2. Watch the console for variable discoveries");
console.log("3. Use listRTIVariables() to see all discovered variables");
console.log("4. Use exportRTIVariables() to get JSON data");
console.log("5. Use generateHomeKitConfig() to create HomeKit config");
console.log("\n=== AVAILABLE FUNCTIONS ===");
console.log("- addRTIVariable(id, name, value)");
console.log("- listRTIVariables()");
console.log("- exportRTIVariables()");
console.log("- generateHomeKitConfig()");

// Try to intercept WebSocket messages if possible
if (window.WebSocket) {
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(...args) {
        const ws = new originalWebSocket(...args);
        
        ws.addEventListener('message', function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.messageType === 'Sysvar') {
                    const varId = data.sysvarid;
                    const varValue = data.sysvarval;
                    
                    // Try to find the variable name from the page
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    let varName = `Variable ${varId}`;
                    
                    for (let checkbox of checkboxes) {
                        if (checkbox.value == varId || checkbox.id == varId) {
                            const label = checkbox.parentElement.textContent.trim();
                            if (label) {
                                varName = label;
                                break;
                            }
                        }
                    }
                    
                    addRTIVariable(varId, varName, varValue);
                }
            } catch (e) {
                // Not JSON, ignore
            }
        });
        
        return ws;
    };
}

console.log("WebSocket interceptor installed. Check boxes to discover variables!");


