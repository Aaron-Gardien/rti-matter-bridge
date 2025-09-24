// RTI Matterbridge Integration Driver
// Discovers and controls RTI system variables via WebSocket and integrates with Matterbridge

// Configuration
var g_moduleId = "RTI-MATTER";
var g_serverAddress = Config.Get("RTIServerAddress").toString();
var g_serverPort = parseInt(Config.Get("RTIServerPort"), 10);
var g_websocketEndpoint = Config.Get("WebSocketEndpoint").toString();
var g_startVariableID = parseInt(Config.Get("StartVariableID"), 10);
var g_endVariableID = parseInt(Config.Get("EndVariableID"), 10);
var g_discoveryTimeout = parseInt(Config.Get("DiscoveryTimeout"), 10);
var g_autoDiscover = Config.Get("AutoDiscoverVariables") == "true";
var g_debug = Config.Get("EnableTrace") == "true";

// Matterbridge Configuration
var g_matterbridgeEnabled = Config.Get("MatterbridgeEnabled") == "true";
var g_matterbridgeURL = Config.Get("MatterbridgeURL").toString();
var g_matterbridgeToken = Config.Get("MatterbridgeToken").toString();
var g_matterbridgeChannel = Config.Get("MatterbridgeChannel").toString();

// Global variables
var g_http = null;
var g_connected = false;
var g_discoveredVariables = {};
var g_activeSubscriptions = {};
var g_messageCount = 0;
var g_discoveryInProgress = false;

// Initialize driver
function Initialize()
{
    dbgPrint("RTI HomeKit Bridge Driver Initializing...");
    
    // Create HTTP object with WebSocket support
    g_http = new HTTP(OnCommHttpRx);
    g_http.OnConnectFunc = OnCommHttpConnect;
    g_http.OnDisconnectFunc = OnCommHttpDisconnect;
    g_http.OnConnectFailedFunc = OnCommHttpConnectFailed;
    g_http.OnWebsocketUpgradeOKFunc = OnCommWebsocketUpgradeOK;
    g_http.OnWebsocketUpgradeFailedFunc = OnCommWebsocketUpgradeFailed;
    g_http.WebsocketVersion = 13;
    g_http.UseHandleInCallbacks = true;
    
    // Initialize system variables
    ConnectionStateChange(0);
    VariablesDiscoveredChange(0);
    MessagesReceivedChange(0);
    SubscriptionsActiveChange(0);
    
    // Connect to RTI system
    Connect();
}

// Helper functions
function dbgPrint(msg)
{
    if (g_debug)
    {
        System.Print(g_moduleId + ": " + msg + "\r\n");
    }
}

function ConnectionStateChange(state)
{
    SetVariable("ConnectionState", state);
    SetVariable("ConnectionState00", state == 0);
    SetVariable("ConnectionState01", state == 1);
}

function VariablesDiscoveredChange(count)
{
    SetVariable("VariablesDiscovered", count);
}

function MessagesReceivedChange(count)
{
    SetVariable("MessagesReceived", count);
}

function SubscriptionsActiveChange(count)
{
    SetVariable("SubscriptionsActive", count);
}

function LastDiscoveryTimeChange()
{
    var now = new Date();
    var timeString = now.getFullYear() + "-" + 
                    String(now.getMonth() + 1).padStart(2, '0') + "-" + 
                    String(now.getDate()).padStart(2, '0') + " " + 
                    String(now.getHours()).padStart(2, '0') + ":" + 
                    String(now.getMinutes()).padStart(2, '0') + ":" + 
                    String(now.getSeconds()).padStart(2, '0');
    SetVariable("LastDiscoveryTime", timeString);
}

function LastWebSocketMessageChange(message)
{
    SetVariable("LastWebSocketMessage", message);
}

// WebSocket event handlers
function OnCommHttpConnect(connectionId)
{
    dbgPrint("HTTP Connected, upgrading to WebSocket...");
    g_http.UpgradeWebsocket();
}

function OnCommHttpDisconnect(connectionId)
{
    dbgPrint("WebSocket Disconnected");
    g_connected = false;
    ConnectionStateChange(0);
}

function OnCommHttpConnectFailed(httpCode, connectionId)
{
    dbgPrint("Connection Failed: " + httpCode);
    g_connected = false;
    ConnectionStateChange(0);
}

function OnCommWebsocketUpgradeOK()
{
    dbgPrint("WebSocket Upgrade Successful!");
    g_connected = true;
    ConnectionStateChange(1);
    LastWebSocketMessageChange("WebSocket connection established");
    
    // RTI will automatically send all variables on boot
    // No need to manually discover - just wait for the data
    if (g_autoDiscover)
    {
        dbgPrint("Waiting for RTI boot variables...");
        LastWebSocketMessageChange("Waiting for RTI to send boot variables");
    }
}

function OnCommWebsocketUpgradeFailed(httpCode, connectionId)
{
    dbgPrint("WebSocket Upgrade Failed: " + httpCode);
    g_connected = false;
    ConnectionStateChange(0);
}

function OnCommHttpRx(data, connectionId)
{
    g_messageCount++;
    MessagesReceivedChange(g_messageCount);
    
    try
    {
        var message = JSON.parse(data);
        LastWebSocketMessageChange("Received: " + JSON.stringify(message));
        
        // Handle system variable updates
        if (message.messageType === "Sysvar")
        {
            var varId = message.sysvarid;
            var varValue = message.sysvarval;
            
            dbgPrint("Variable Update: " + varId + " = " + varValue);
            
            // Update discovered variables
            g_discoveredVariables[varId] = {
                id: varId,
                value: varValue,
                timestamp: new Date().getTime()
            };
            
            // Update system variable
            var sysVarName = "DiscoveredVar" + String(varId).padStart(3, '0');
            SetVariable(sysVarName, varValue);
            
            // Update variables discovered count
            VariablesDiscoveredChange(Object.keys(g_discoveredVariables).length);
            
            // Send to Matterbridge if enabled
            if (g_matterbridgeEnabled)
            {
                SendToMatterbridge("rti", "variable_update", {
                    variable_id: varId,
                    value: varValue,
                    timestamp: new Date().toISOString()
                });
            }
        }
        else if (message.messageType === "echo")
        {
            dbgPrint("Echo: " + message.message);
        }
    }
    catch (e)
    {
        dbgPrint("Error parsing WebSocket message: " + e.message);
        LastWebSocketMessageChange("Error parsing message: " + data);
    }
}

// Exported functions
function Connect()
{
    if (g_connected)
    {
        dbgPrint("Already connected");
        return;
    }
    
    dbgPrint("Connecting to ws://" + g_serverAddress + ":" + g_serverPort + g_websocketEndpoint);
    g_http.Open(g_serverAddress, g_serverPort);
}

function Disconnect()
{
    if (g_connected)
    {
        dbgPrint("Disconnecting...");
        g_http.Close();
        g_connected = false;
        ConnectionStateChange(0);
    }
}

function Reconnect()
{
    dbgPrint("Reconnecting...");
    Disconnect();
    setTimeout(function() {
        Connect();
    }, 2000);
}

function DiscoverVariables()
{
    if (!g_connected)
    {
        dbgPrint("Not connected to RTI system");
        return;
    }
    
    if (g_discoveryInProgress)
    {
        dbgPrint("Discovery already in progress");
        return;
    }
    
    dbgPrint("Starting variable discovery from " + g_startVariableID + " to " + g_endVariableID);
    g_discoveryInProgress = true;
    
    var currentId = g_startVariableID;
    
    function testNextVariable()
    {
        if (currentId > g_endVariableID)
        {
            g_discoveryInProgress = false;
            VariablesDiscoveredChange(Object.keys(g_discoveredVariables).length);
            LastDiscoveryTimeChange();
            dbgPrint("Variable discovery completed. Found " + Object.keys(g_discoveredVariables).length + " variables");
            return;
        }
        
        SubscribeToVariable(currentId);
        
        setTimeout(function() {
            UnsubscribeFromVariable(currentId);
            currentId++;
            setTimeout(testNextVariable, 500);
        }, g_discoveryTimeout * 1000);
    }
    
    testNextVariable();
}

function RefreshAllVariables()
{
    if (!g_connected)
    {
        dbgPrint("Not connected to RTI system");
        return;
    }
    
    dbgPrint("Refreshing all discovered variables...");
    
    for (var varId in g_discoveredVariables)
    {
        SubscribeToVariable(parseInt(varId));
    }
}

function ClearDiscoveredVariables()
{
    dbgPrint("Clearing discovered variables...");
    g_discoveredVariables = {};
    VariablesDiscoveredChange(0);
    
    // Clear system variables
    for (var i = g_startVariableID; i <= g_endVariableID; i++)
    {
        var sysVarName = "DiscoveredVar" + String(i).padStart(3, '0');
        SetVariable(sysVarName, "");
    }
}

function SubscribeToVariable(varId)
{
    if (!g_connected)
    {
        dbgPrint("Not connected to RTI system");
        return;
    }
    
    var message = {
        "type": "Subscribe",
        "resource": "Sysvar",
        "value": {"id": varId, "status": true}
    };
    
    g_http.Write(JSON.stringify(message));
    g_activeSubscriptions[varId] = true;
    SubscriptionsActiveChange(Object.keys(g_activeSubscriptions).length);
    
    dbgPrint("Subscribed to variable " + varId);
}

function UnsubscribeFromVariable(varId)
{
    if (!g_connected)
    {
        return;
    }
    
    var message = {
        "type": "Subscribe",
        "resource": "Sysvar",
        "value": {"id": varId, "status": false}
    };
    
    g_http.Write(JSON.stringify(message));
    delete g_activeSubscriptions[varId];
    SubscriptionsActiveChange(Object.keys(g_activeSubscriptions).length);
    
    dbgPrint("Unsubscribed from variable " + varId);
}

function TestVariableRange()
{
    dbgPrint("Testing variable range " + g_startVariableID + " to " + g_endVariableID);
    DiscoverVariables();
}

function StartHomeKitBridge()
{
    dbgPrint("HomeKit Bridge functionality would be implemented here");
    // This would start the Python HomeKit bridge
}

function StopHomeKitBridge()
{
    dbgPrint("Stopping HomeKit Bridge");
    // This would stop the Python HomeKit bridge
}

function ExportVariableMapping()
{
    var mapping = {
        timestamp: new Date().toISOString(),
        server: g_serverAddress + ":" + g_serverPort,
        variables: g_discoveredVariables
    };
    
    var jsonString = JSON.stringify(mapping, null, 2);
    dbgPrint("Variable Mapping Export:");
    dbgPrint(jsonString);
    
    // In a real implementation, this would save to a file
    LastWebSocketMessageChange("Variable mapping exported - check debug output");
}

function ShowConnectionStatus()
{
    var status = g_connected ? "Connected" : "Disconnected";
    dbgPrint("Connection Status: " + status);
    dbgPrint("Server: " + g_serverAddress + ":" + g_serverPort);
    dbgPrint("Active Subscriptions: " + Object.keys(g_activeSubscriptions).length);
    LastWebSocketMessageChange("Status: " + status);
}

function ShowDiscoveredVariables()
{
    dbgPrint("Discovered Variables:");
    for (var varId in g_discoveredVariables)
    {
        var varData = g_discoveredVariables[varId];
        dbgPrint("  ID " + varId + ": " + varData.value + " (updated " + new Date(varData.timestamp) + ")");
    }
    LastWebSocketMessageChange("Found " + Object.keys(g_discoveredVariables).length + " variables");
}

function ShowWebSocketLog()
{
    dbgPrint("WebSocket Messages Received: " + g_messageCount);
    dbgPrint("Last Message: " + GetVariable("LastWebSocketMessage"));
    LastWebSocketMessageChange("Log: " + g_messageCount + " messages received");
}

// Cleanup on driver shutdown
function Shutdown()
{
    dbgPrint("Driver shutting down...");
    Disconnect();
}

