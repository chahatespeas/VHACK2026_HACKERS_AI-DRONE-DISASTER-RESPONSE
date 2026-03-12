// --- ASEAN Region Data ---
const regions = {
    manila: { lat: 14.5995, lng: 120.9842, name: "Manila, Philippines (Typhoon Zone)" },
    jakarta: { lat: -6.2088, lng: 106.8456, name: "Jakarta, Indonesia (Earthquake Zone)" },
    kl: { lat: 3.1390, lng: 101.6869, name: "Kuala Lumpur, Malaysia (Flood Zone)" }
};

let currentRegion = regions.manila;
let missionActive = false;
let simulationInterval;
let stats = { found: 0, aided: 0 };

// --- Initialize Map ---
const map = L.map('map').setView([currentRegion.lat, currentRegion.lng], 14);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CARTO'
}).addTo(map);

// --- Icons ---
const baseIcon = L.divIcon({ className: 'custom-base', iconSize: [40, 40], html: 'BASE' });
const droneIcon = L.divIcon({ className: 'custom-drone', iconSize: [14, 14] });
const survivorSosIcon = L.divIcon({ className: 'custom-survivor-sos', iconSize: [18, 18] });
const survivorAidedIcon = L.divIcon({ className: 'custom-survivor-aided', iconSize: [14, 14] });

let baseMarker;
let droneMarkers = {};
let survivorMarkers = {};

// CHANGED HERE: IDs are now 1, 2, 3
let drones = [
    { id: '1', lat: 0, lng: 0, battery: 100, state: 'idle', targetId: null },
    { id: '2', lat: 0, lng: 0, battery: 85, state: 'idle', targetId: null },
    { id: '3', lat: 0, lng: 0, battery: 90, state: 'idle', targetId: null }
];
let survivors = [];

// UI Elements
const startBtn = document.getElementById('start-btn');
const regionSelect = document.getElementById('region-select');
const batteryContainer = document.getElementById('battery-levels');

function changeRegion() {
    if(missionActive) {
        alert("Cannot change region while mission is active!");
        return;
    }
    currentRegion = regions[regionSelect.value];
    map.flyTo([currentRegion.lat, currentRegion.lng], 14);
    logAction(`Satellite recalibrated to ${currentRegion.name}.`);
}

function startMission() {
    missionActive = true;
    startBtn.disabled = true;
    startBtn.innerText = "MISSION ACTIVE";
    regionSelect.disabled = true;
    
    baseMarker = L.marker([currentRegion.lat, currentRegion.lng], {icon: baseIcon}).addTo(map);

    // Generate random survivors around the city
    for(let i=1; i<=5; i++) {
        survivors.push({ 
            id: i, 
            lat: currentRegion.lat + (Math.random() - 0.5) * 0.04, 
            lng: currentRegion.lng + (Math.random() - 0.5) * 0.04, 
            status: 'hidden' // hidden -> detected -> aided
        });
    }

    drones.forEach(drone => {
        drone.lat = currentRegion.lat;
        drone.lng = currentRegion.lng;
        droneMarkers[drone.id] = L.marker([drone.lat, drone.lng], {icon: droneIcon}).addTo(map);
    });

    logAction("Executing MCP Tool: get_network_drones()");
    setTimeout(() => {
        logThought(`Command Agent initialized. Discovered 3 drones. Initiating thermal sweep of ${currentRegion.name}.`);
        simulationInterval = setInterval(runSimulationTick, 1000); 
    }, 1500);
}

function runSimulationTick() {
    // 1. Randomly "Detect" survivors (Simulating thermal scan)
    survivors.forEach(surv => {
        if (surv.status === 'hidden' && Math.random() > 0.96) {
            surv.status = 'detected';
            stats.found++;
            document.getElementById('stat-found').innerText = stats.found;
            logAlert(`Thermal signature detected! Survivor #${surv.id} located at GPS [${surv.lat.toFixed(3)}, ${surv.lng.toFixed(3)}].`);
            survivorMarkers[surv.id] = L.marker([surv.lat, surv.lng], {icon: survivorSosIcon}).addTo(map);
        }
    });

    // 2. Drone Logic
    drones.forEach(drone => {
        drone.battery -= Math.random() * 1.5; 

        if (drone.battery <= 20 && drone.state !== 'returning') {
            drone.state = 'returning';
            drone.targetId = null;
            logThought(`Drone ${drone.id} battery low. Executing return protocol.`);
        }

        if (drone.state === 'returning') {
            drone.lat += (currentRegion.lat - drone.lat) * 0.1;
            drone.lng += (currentRegion.lng - drone.lng) * 0.1;
            if (Math.abs(drone.lat - currentRegion.lat) < 0.001) drone.battery = 100; 
        } else {
            // Find a detected survivor that needs aid
            let target = survivors.find(s => s.status === 'detected');
            
            if (target) {
                // Fly towards survivor
                drone.lat += (target.lat - drone.lat) * 0.1;
                drone.lng += (target.lng - drone.lng) * 0.1;

                // If close enough, deploy aid!
                if (Math.abs(drone.lat - target.lat) < 0.002 && Math.abs(drone.lng - target.lng) < 0.002) {
                    target.status = 'aided';
                    stats.aided++;
                    document.getElementById('stat-aid').innerText = stats.aided;
                    
                    // Change map icon to Blue (Safe)
                    map.removeLayer(survivorMarkers[target.id]);
                    survivorMarkers[target.id] = L.marker([target.lat, target.lng], {icon: survivorAidedIcon}).addTo(map);
                    
                    logThought(`Drone ${drone.id} has reached Survivor #${target.id}.`);
                    logAction(`Executing MCP Tool: deploy_aid_payload() via Drone ${drone.id}`);
                    addLog(`✅ Aid successfully delivered to Survivor #${target.id}.`, 'success');
                }
            } else {
                // Random search pattern
                drone.lat += (Math.random() - 0.5) * 0.005;
                drone.lng += (Math.random() - 0.5) * 0.005;
            }
        }
        droneMarkers[drone.id].setLatLng([drone.lat, drone.lng]);
    });

    updateTelemetry();
}

function updateTelemetry() {
    batteryContainer.innerHTML = '';
    drones.forEach(drone => {
        let bat = Math.floor(drone.battery);
        let color = bat > 50 ? 'var(--safe)' : (bat > 20 ? '#fbbf24' : 'var(--danger)');
        // CHANGED HERE: The label now reads "Drone 1" instead of "[ID: 1]"
        batteryContainer.innerHTML += `
            <div class="battery-item">
                <div class="battery-label"><span>Drone ${drone.id}</span><span>${bat}%</span></div>
                <div class="battery-bar-bg"><div class="battery-bar-fill" style="width: ${bat}%; background: ${color}"></div></div>
            </div>`;
    });
}

function logThought(msg) { addLog(`🧠 [Reasoning] ${msg}`, 'thought'); }
function logAction(msg) { addLog(`⚡ [Action] ${msg}`, 'action'); }
function logAlert(msg) { addLog(`🚨 [ALERT] ${msg}`, 'alert'); }

function addLog(message, type) {
    const el = document.createElement('div');
    el.className = `log ${type}`;
    el.innerText = `> ${message}`;
    document.getElementById('log-container').appendChild(el);
    document.getElementById('log-container').scrollTop = document.getElementById('log-container').scrollHeight;
}