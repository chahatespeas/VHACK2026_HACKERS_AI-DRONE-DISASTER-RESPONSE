// --- ASEAN Region Data (Real GPS Coordinates) ---
const regions = {
    manila: { lat: 14.5995, lng: 120.9842, name: "Manila, Philippines" },
    jakarta: { lat: -6.2088, lng: 106.8456, name: "Jakarta, Indonesia" },
    kl: { lat: 3.1390, lng: 101.6869, name: "Kuala Lumpur, Malaysia" }
};

let currentRegion = regions.manila; // Default
let missionActive = false;
let simulationInterval;

// --- Initialize Interactive Map ---
const map = L.map('map').setView([currentRegion.lat, currentRegion.lng], 13);
// Adding a super cool Dark Mode map layer!
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
}).addTo(map);

// --- Define Custom Glowing Icons ---
const baseIcon = L.divIcon({ className: 'custom-base', iconSize: [40, 40], html: 'BASE' });
const droneIcon = L.divIcon({ className: 'custom-drone', iconSize: [14, 14] });
const survivorIcon = L.divIcon({ className: 'custom-survivor', iconSize: [18, 18] });

// --- Map Entities ---
let baseMarker;
let droneMarkers = {};
let survivorMarkers = [];

let drones = [
    { id: 'Alpha', lat: 0, lng: 0, battery: 100, state: 'idle' },
    { id: 'Bravo', lat: 0, lng: 0, battery: 85, state: 'idle' },
    { id: 'Charlie', lat: 0, lng: 0, battery: 90, state: 'idle' }
];

let survivors = [];

// UI Elements
const startBtn = document.getElementById('start-btn');
const regionSelect = document.getElementById('region-select');
const batteryContainer = document.getElementById('battery-levels');
const logContainer = document.getElementById('log-container');

// Change Country Dropdown
function changeRegion() {
    if(missionActive) {
        alert("Cannot change region while mission is active!");
        regionSelect.value = Object.keys(regions).find(key => regions[key].name === currentRegion.name);
        return;
    }
    const selected = regionSelect.value;
    currentRegion = regions[selected];
    map.flyTo([currentRegion.lat, currentRegion.lng], 13); // Smooth fly animation
    logAction(`Satellite recalibrated to ${currentRegion.name}. Waiting for initialization.`);
}

function startMission() {
    missionActive = true;
    startBtn.disabled = true;
    startBtn.innerText = "MISSION ACTIVE";
    regionSelect.disabled = true; // Lock the dropdown
    
    // Set Base Station
    baseMarker = L.marker([currentRegion.lat, currentRegion.lng], {icon: baseIcon}).addTo(map);

    // Prepare Survivors
    survivors = [
        { id: 1, lat: currentRegion.lat + 0.02, lng: currentRegion.lng + 0.02, discovered: false },
        { id: 2, lat: currentRegion.lat - 0.03, lng: currentRegion.lng - 0.01, discovered: false }
    ];

    // Place Drones at Base
    drones.forEach(drone => {
        drone.lat = currentRegion.lat;
        drone.lng = currentRegion.lng;
        droneMarkers[drone.id] = L.marker([drone.lat, drone.lng], {icon: droneIcon}).addTo(map);
    });

    logAction("Executing MCP Tool: discover_active_drones()");
    setTimeout(() => {
        logThought(`I found 3 drones available on the edge network in ${currentRegion.name}. Deploying swarm.`);
        simulationInterval = setInterval(runSimulationTick, 1000); 
    }, 1000);
}

function runSimulationTick() {
    drones.forEach(drone => {
        drone.battery -= Math.random() * 2; 

        // AI Battery Management Logic
        if (drone.battery <= 20 && drone.state !== 'returning') {
            drone.state = 'returning';
            logThought(`Drone ${drone.id} battery is critical (${Math.floor(drone.battery)}%). Recalling to base.`);
            logAction(`execute: move_to(lat:${currentRegion.lat.toFixed(3)}, lng:${currentRegion.lng.toFixed(3)}) for Drone ${drone.id}`);
        }

        // AI Drone Movement Logic
        if (drone.state === 'returning') {
            // Fly back to base
            drone.lat += (currentRegion.lat - drone.lat) * 0.1;
            drone.lng += (currentRegion.lng - drone.lng) * 0.1;
            // Recharge if close enough
            if (Math.abs(drone.lat - currentRegion.lat) < 0.001) drone.battery = 100; 
        } else {
            drone.state = 'searching';
            // Random search pattern over the real city blocks
            drone.lat += (Math.random() - 0.5) * 0.005;
            drone.lng += (Math.random() - 0.5) * 0.005;
        }

        // Update visual marker on the map
        droneMarkers[drone.id].setLatLng([drone.lat, drone.lng]);
    });

    // Check if survivors are found
    survivors.forEach(surv => {
        if (!surv.discovered && Math.random() > 0.95) {
            surv.discovered = true;
            logAlert(`THERMAL SIGNATURE DETECTED at GPS [${surv.lat.toFixed(4)}, ${surv.lng.toFixed(4)}]`);
            L.marker([surv.lat, surv.lng], {icon: survivorIcon}).addTo(map);
        }
    });

    updateTelemetry();
}

function updateTelemetry() {
    batteryContainer.innerHTML = '';
    drones.forEach(drone => {
        let bat = Math.floor(drone.battery);
        let color = bat > 50 ? 'var(--safe)' : (bat > 20 ? '#fbbf24' : 'var(--danger)');
        
        batteryContainer.innerHTML += `
            <div class="battery-item">
                <div class="battery-label"><span>Drone ${drone.id}</span><span>${bat}%</span></div>
                <div class="battery-bar-bg">
                    <div class="battery-bar-fill" style="width: ${bat}%; background: ${color}"></div>
                </div>
            </div>`;
    });
}

function logThought(msg) { addLog(`🧠 Thinking: ${msg}`, 'thought'); }
function logAction(msg) { addLog(`⚡ Action: ${msg}`, 'action'); }
function logAlert(msg) { addLog(`🚨 ${msg}`, 'alert'); }

function addLog(message, type) {
    const el = document.createElement('div');
    el.className = `log ${type}`;
    el.innerText = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(el);
    logContainer.scrollTop = logContainer.scrollHeight;
}