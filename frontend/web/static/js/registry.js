let objectTypesRegistry = null;
let behaviorProfilesRegistry = null;

async function fetchRegistries() {
  const [objTypesRes, behaviorRes] = await Promise.all([
    fetch('/api/object-types'),
    fetch('/api/behavior-profiles')
  ]);
  objectTypesRegistry = await objTypesRes.json();
  behaviorProfilesRegistry = await behaviorRes.json();
}

function getObjectTypesRegistry() {
  return objectTypesRegistry;
}

function getBehaviorProfilesRegistry() {
  return behaviorProfilesRegistry;
}

// Generate an object ID from building, floor, system, type, and instance (zero-padded to 3 digits)
function generateObjectId(building, floor, system, type, instance) {
  // Example: TCHS_L2_E_Receptacle_015
  const instanceStr = String(instance).padStart(3, '0');
  return `${building}_${floor}_${system}_${type}_${instanceStr}`;
}

// Validate an object ID using the backend regex
function isValidObjectId(id) {
  // Regex: ^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$
  const pattern = /^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$/;
  return pattern.test(id);
}

// Get the next available instance number for a given context (stub: client-side only)
function getNextInstanceNumber(objects, { building, floor, system, type }) {
  // Filter objects matching the context
  const regex = new RegExp(`^${building}_${floor}_${system}_${type}_(\\d{3})$`);
  let maxInstance = 0;
  for (const obj of objects) {
    const match = obj.id && obj.id.match(regex);
    if (match) {
      const instanceNum = parseInt(match[1], 10);
      if (instanceNum > maxInstance) maxInstance = instanceNum;
    }
  }
  return maxInstance + 1;
}

export { fetchRegistries, getObjectTypesRegistry, getBehaviorProfilesRegistry, generateObjectId, isValidObjectId, getNextInstanceNumber }; 