// Configuration
const API_URL = "http://localhost:5000/api/status"; // Change to your backend URL
const USE_MOCK_DATA = true; // Set to false when connecting to real backend

let missionActive = false;
let pollingInterval;

// DOM Elements
const mapEl = document.getElementById('map');
const batteryContainer = document.getElementById('battery-levels');
const logContainer = document.getElementById('log-container');
const startBtn = document.getElementById('start-btn');

// Start Mission
function startMission() {
    missionActive = true;
    startBtn.disabled = true;
    startBtn.innerText = "Mission In Progress...";
    
    log("Mission initiated. Dispatching swarm...", "success");
    
    // In a real app, send a POST request to your backend here
    // fetch('http://localhost:5000/api/start', { method: 'POST' });

    pollingInterval = setInterval(fetchUpdates, 1000); // Fetch updates every second
}

// Fetch loop
async function fetchUpdates() {
    let data;
    if (USE_MOCK_DATA) {
        data = generateMockData();
    } else {
        try {
            const response = await fetch(API_URL);
            data = await response.json();
        } catch (error) {
            console.error("API Error:", error);
            log("Connection to backend lost.", "alert");
            return;
        }
    }
    
    updateMap(data.drones, data.survivors);
    updateTelemetry(data.drones);
    if(data.latestLog) log(data.latestLog.msg, data.latestLog.type);
}

// Map Rendering
function updateMap(drones, survivors) {
    // Render Survivors (assuming static for now)
    survivors.forEach(surv => {
        let el = document.getElementById(`surv-${surv.id}`);
        if (!el) {
            el = document.createElement('div');
            el.id = `surv-${surv.id}`;
            el.className = 'entity survivor';
            mapEl.appendChild(el);
        }
        el.style.left = `${surv.x}%`;
        el.style.top = `${surv.y}%`;
    });

    // Render Drones
    drones.forEach(drone => {
        let el = document.getElementById(`drone-${drone.id}`);
        if (!el) {
            el = document.createElement('div');
            el.id = `drone-${drone.id}`;
            el.className = 'entity drone';
            mapEl.appendChild(el);
        }
        // CSS transitions will automatically animate this movement
        el.style.left = `${drone.x}%`;
        el.style.top = `${drone.y}%`;
    });
}

// Telemetry Rendering
function updateTelemetry(drones) {
    batteryContainer.innerHTML = '';
    drones.forEach(drone => {
        const color = drone.battery > 50 ? 'var(--success)' : (drone.battery > 20 ? '#fbbf24' : 'var(--alert)');
        
        const html = `
            <div class="battery-item">
                <div class="battery-label">
                    <span>Drone ${drone.id}</span>
                    <span>${drone.battery}%</span>
                </div>
                <div class="battery-bar-bg">
                    <div class="battery-bar-fill" style="width: ${drone.battery}%; background-color: ${color}"></div>
                </div>
            </div>
        `;
        batteryContainer.innerHTML += html;
    });
}

// Agent Reasoning Logs
function log(message, type = "normal") {
    const el = document.createElement('div');
    el.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    el.innerHTML = `[${timestamp}] ${message}`;
    
    logContainer.appendChild(el);
    logContainer.scrollTop = logContainer.scrollHeight; // Auto-scroll
}

// ==========================================
// MOCK DATA GENERATOR (For Hackathon Demo)
// ==========================================
let mockDrones = [
    { id: 1, x: 10, y: 10, battery: 100 },
    { id: 2, x: 90, y: 10, battery: 100 },
    { id: 3, x: 50, y: 90, battery: 100 }
];
const mockSurvivors = [
    { id: 'A', x: 45, y: 45 },
    { id: 'B', x: 75, y: 80 }
];

function generateMockData() {
    // Move drones randomly towards center
    mockDrones.forEach(d => {
        d.x += (Math.random() - 0.3) * 5;
        d.y += (Math.random() - 0.3) * 5;
        d.battery -= Math.floor(Math.random() * 2);
        
        // Boundaries
        d.x = Math.max(0, Math.min(100, d.x));
        d.y = Math.max(0, Math.min(100, d.y));
    });

    // Random logs
    const logMessages = [
        "Drone 1: Scanning sector Alpha...",
        "Drone 2: Thermal anomaly detected.",
        "Agent: Rerouting Drone 3 to investigate anomaly.",
        "System: Optimal path calculated.",
        "Drone 1: Sector clear."
    ];
    
    let latestLog = null;
    if (Math.random() > 0.6) {
        latestLog = { 
            msg: logMessages[Math.floor(Math.random() * logMessages.length)],
            type: Math.random() > 0.8 ? "alert" : "normal"
        };
    }

    return { drones: mockDrones, survivors: mockSurvivors, latestLog };
}