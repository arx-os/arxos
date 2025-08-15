// Process Alafia Elementary School IDF locations
// This script extracts the network infrastructure from the floor plan

const alafiaNetworkInfrastructure = {
    building: {
        name: "Alafia Elementary School",
        address: "3835 Culbreath Dr, Valrico, Florida",
        code: "School Code: 0271",
        totalRooms: 50, // Approximate from plan
    },
    
    // Main Distribution Frame - the network core
    mdf: {
        id: "MDF-300c",
        location: "Room 300c",
        type: "MDF",
        system: "network",
        coordinates: { x: -20, y: 30 }, // Approximate from plan
        properties: {
            rackUnits: 42,
            estimatedPorts: 24, // Uplinks to IDFs
            powerRequirement: "60A",
            ups: true,
            cooling: "dedicated",
            fibersOut: 4, // One to each IDF
        }
    },
    
    // Intermediate Distribution Frames
    idfs: [
        {
            id: "IDF-516",
            location: "Room 516 area",
            type: "IDF",
            system: "network",
            coordinates: { x: -80, y: 60 },
            properties: {
                servesRooms: ["516", "517", "518", "519", "520"],
                rackUnits: 12,
                switchPorts: 48,
                powerRequirement: "20A",
                uplinkTo: "MDF-300c",
                cableType: "Single-mode fiber",
                estimatedDrops: 120
            }
        },
        {
            id: "IDF-507a",
            location: "Room 507a",
            type: "IDF", 
            system: "network",
            coordinates: { x: -70, y: 0 },
            properties: {
                servesRooms: ["501", "502", "503", "504", "505", "506", "507", "508"],
                rackUnits: 20,
                switchPorts: 96,
                powerRequirement: "30A",
                uplinkTo: "MDF-300c",
                cableType: "Single-mode fiber",
                estimatedDrops: 200
            }
        },
        {
            id: "IDF-606a",
            location: "Room 606a",
            type: "IDF",
            system: "network",
            coordinates: { x: 0, y: -40 },
            properties: {
                servesRooms: ["601", "602", "603", "604", "605", "606", "607", "608", "609", "610"],
                rackUnits: 20,
                switchPorts: 96,
                powerRequirement: "30A",
                uplinkTo: "MDF-300c",
                cableType: "Single-mode fiber",
                estimatedDrops: 240
            }
        },
        {
            id: "IDF-800b",
            location: "Room 800b",
            type: "IDF",
            system: "network",
            coordinates: { x: 40, y: 50 },
            properties: {
                servesRooms: ["801", "802", "803", "804", "805", "806", "807", "808", "809", "810"],
                rackUnits: 20,
                switchPorts: 96,
                powerRequirement: "30A",
                uplinkTo: "MDF-300c",
                cableType: "Single-mode fiber",
                estimatedDrops: 250
            }
        }
    ],
    
    // Network Topology
    topology: {
        architecture: "Hub and Spoke",
        core: "MDF-300c",
        spokes: ["IDF-516", "IDF-507a", "IDF-606a", "IDF-800b"],
        estimatedTotalDrops: 810,
        estimatedAccessPoints: 50, // ~1 per classroom
        vlans: {
            administrative: 10,
            academic: 20,
            guest: 30,
            security: 40,
            voip: 50,
            iot: 60
        }
    },
    
    // Valuable insights for different stakeholders
    insights: {
        forInsurance: {
            criticalAssets: 5,
            estimatedReplacementCost: 250000,
            redundancy: "None - single point of failure at MDF",
            businessContinuityRisk: "High - no redundant paths"
        },
        forMaintenance: {
            equipmentAge: "Unknown - needs audit",
            nextRefresh: "Typical 5-7 year cycle",
            monthlyCheckpoints: [
                "Verify cooling in MDF/IDF rooms",
                "Check UPS battery status",
                "Review port utilization",
                "Cable management audit"
            ]
        },
        forUpgrades: {
            recommendations: [
                "Add redundant fiber path between MDF and IDFs",
                "Upgrade to 10G uplinks",
                "Add environmental monitoring",
                "Implement PoE+ for modern APs and cameras"
            ]
        }
    }
};

// Convert to ArxObjects for database
function convertToArxObjects(infrastructure) {
    const objects = [];
    
    // Add MDF
    objects.push({
        type: infrastructure.mdf.type,
        system: infrastructure.mdf.system,
        x: infrastructure.mdf.coordinates.x,
        y: infrastructure.mdf.coordinates.y,
        z: 0,
        scaleMin: 1,
        scaleMax: 1000,
        properties: {
            ...infrastructure.mdf.properties,
            id: infrastructure.mdf.id,
            location: infrastructure.mdf.location
        }
    });
    
    // Add IDFs
    infrastructure.idfs.forEach(idf => {
        objects.push({
            type: idf.type,
            system: idf.system,
            x: idf.coordinates.x,
            y: idf.coordinates.y,
            z: 0,
            scaleMin: 1,
            scaleMax: 1000,
            properties: {
                ...idf.properties,
                id: idf.id,
                location: idf.location
            }
        });
    });
    
    // Add connections (topology)
    infrastructure.idfs.forEach(idf => {
        objects.push({
            type: "fiber_run",
            system: "network",
            fromId: infrastructure.mdf.id,
            toId: idf.id,
            properties: {
                cableType: idf.properties.cableType,
                purpose: "IDF Uplink",
                bandwidth: "1Gbps", // Current
                capacity: "10Gbps"  // Potential
            }
        });
    });
    
    return objects;
}

// Display the extracted data
console.log("Alafia Elementary Network Infrastructure:");
console.log("==========================================");
console.log(`MDF: ${alafiaNetworkInfrastructure.mdf.id} in ${alafiaNetworkInfrastructure.mdf.location}`);
console.log(`IDFs: ${alafiaNetworkInfrastructure.idfs.length} distributed across building`);
console.log(`Total network drops: ~${alafiaNetworkInfrastructure.topology.estimatedTotalDrops}`);
console.log(`Estimated replacement cost: $${alafiaNetworkInfrastructure.insights.forInsurance.estimatedReplacementCost.toLocaleString()}`);

// Export for use
if (typeof module !== 'undefined') {
    module.exports = {
        alafiaNetworkInfrastructure,
        convertToArxObjects
    };
}