# Arxos AI Ingestion Implementation Plan

## Executive Summary
Transition Arxos from manual computer vision wall extraction to AI-powered ingestion using OpenAI Vision API and specialized parsers. This approach will enable accurate conversion of PDF, IFC, HEIC/JPEG, and LiDAR files into the Arxos Building Information Model.

## Current State Assessment

### What We Built (To Be Preserved)
1. **Core Arxos BIM Viewer** (`arxos_complete.html`)
   - Canvas-based rendering engine
   - Pan/zoom navigation
   - ArxObject data structure
   - Grid display system
   - Status: ✅ **KEEP AS-IS**

2. **Manual Wall Extraction** (`wall_extraction_engine.js`)
   - Hough transform implementation
   - Edge detection algorithms
   - Status: ⚠️ **ARCHIVE BUT DON'T DELETE**
   - Action: Move to `/archive/manual_extraction/` folder
   - Reason: May be useful for offline/fallback scenarios

3. **Test Interfaces** 
   - `photo_ingestion.html` - Initial photo upload interface
   - `arxos_unified.html` - Simplified BIM viewer
   - Status: 📁 **ARCHIVE**
   - Action: Move to `/archive/prototypes/`

## Implementation Phases

### Phase 0: Clean Up & Stabilize (Week 1)
**Goal:** Ensure current system is stable before adding AI

#### Tasks:
1. **Archive Manual Extraction Work**
   ```bash
   mkdir -p archive/manual_extraction
   mkdir -p archive/prototypes
   mv wall_extraction_engine.js archive/manual_extraction/
   mv photo_ingestion.html archive/prototypes/
   mv arxos_unified.html archive/prototypes/
   ```

2. **Create Feature Flag System**
   ```javascript
   // config.js
   const ARXOS_CONFIG = {
     ingestion: {
       useAI: true,  // Toggle between AI and manual
       aiProvider: 'openai', // 'openai', 'google', 'azure'
       fallbackToManual: false
     }
   };
   ```

3. **Stub Out AI Integration Points**
   ```javascript
   // arxos_complete.html - Add this to existing file
   async processWithAI(file) {
     if (!ARXOS_CONFIG.ingestion.useAI) {
       return this.processWithManualExtraction(file);
     }
     // AI processing will go here
     throw new Error('AI processing not yet implemented');
   }
   ```

### Phase 1: OpenAI Integration (Week 2-3)
**Goal:** Implement OpenAI Vision API for photo/PDF processing

#### Prerequisites:
- OpenAI API key
- Backend service for API key security

#### Tasks:

1. **Create Backend API Service**
   ```go
   // core/backend/handlers/ai_ingestion.go
   package handlers
   
   type AIIngestionHandler struct {
     openAIKey string
     db *sql.DB
   }
   
   func (h *AIIngestionHandler) ProcessImage(w http.ResponseWriter, r *http.Request) {
     // 1. Receive image from frontend
     // 2. Call OpenAI Vision API
     // 3. Parse response to ArxObjects
     // 4. Return ArxObjects to frontend
   }
   ```

2. **Create AI Service Module**
   ```javascript
   // ai_ingestion_service.js
   class AIIngestionService {
     async processFloorPlan(file) {
       const formData = new FormData();
       formData.append('file', file);
       formData.append('prompt', this.getFloorPlanPrompt());
       
       const response = await fetch('/api/v1/ai/ingest', {
         method: 'POST',
         body: formData
       });
       
       return await response.json(); // Returns ArxObjects
     }
     
     getFloorPlanPrompt() {
       return `Analyze this floor plan image and extract:
       1. All walls as line segments with start/end coordinates
       2. Room boundaries and dimensions
       3. Room labels and numbers
       4. Doors and windows with positions
       Return as JSON with coordinate system where top-left is (0,0)`;
     }
   }
   ```

3. **Update Frontend Integration**
   ```javascript
   // In arxos_complete.html
   async handlePhotoUpload(event) {
     const file = event.target.files[0];
     if (!file) return;
     
     this.showLoading('Processing with AI...');
     
     try {
       const aiService = new AIIngestionService();
       const arxObjects = await aiService.processFloorPlan(file);
       this.arxObjects = arxObjects;
       this.fitToView();
       this.updateStats();
     } catch (error) {
       console.error('AI processing failed:', error);
       // Fallback logic here if needed
     } finally {
       this.hideLoading();
     }
   }
   ```

### Phase 2: IFC Parser Integration (Week 3-4)
**Goal:** Direct IFC to ArxObject conversion

#### Tasks:

1. **Integrate web-ifc Library**
   ```html
   <!-- Add to arxos_complete.html -->
   <script src="https://cdn.jsdelivr.net/npm/web-ifc@0.0.36/web-ifc-api.js"></script>
   ```

2. **Create IFC Parser Service**
   ```javascript
   // ifc_parser_service.js
   class IFCParserService {
     async parseIFC(file) {
       const ifcAPI = new WebIFC.IfcAPI();
       await ifcAPI.Init();
       
       const data = await file.arrayBuffer();
       const modelID = await ifcAPI.OpenModel(data);
       
       // Extract walls, slabs, spaces
       const walls = await this.extractWalls(ifcAPI, modelID);
       const spaces = await this.extractSpaces(ifcAPI, modelID);
       
       // Convert to ArxObjects
       return this.convertToArxObjects(walls, spaces);
     }
   }
   ```

### Phase 3: LiDAR Processing (Week 4-5)
**Goal:** Support for LiDAR/3D scan ingestion

#### Options:
1. **Apple RoomPlan** (iOS only)
   - On-device processing
   - Exports USDZ format
   - Convert USDZ → ArxObjects

2. **Polycam API** (Cross-platform)
   - Cloud processing
   - REST API available
   - Subscription required

3. **Open3D** (Open source)
   - Self-hosted processing
   - More complex setup

#### Implementation:
```javascript
// lidar_service.js
class LiDARService {
  async processLiDARScan(file) {
    if (this.isIOSDevice() && file.type === 'usdz') {
      return this.processRoomPlan(file);
    } else {
      return this.processWithPolycam(file);
    }
  }
}
```

### Phase 4: Production Readiness (Week 5-6)
**Goal:** Error handling, caching, optimization

#### Tasks:

1. **Error Handling & Fallbacks**
   ```javascript
   async processFile(file) {
     try {
       return await this.processWithAI(file);
     } catch (aiError) {
       console.warn('AI processing failed, trying fallback', aiError);
       
       if (ARXOS_CONFIG.ingestion.fallbackToManual) {
         return await this.processWithManualExtraction(file);
       }
       
       throw new Error('Unable to process file');
     }
   }
   ```

2. **Caching Layer**
   ```javascript
   // Cache processed results to avoid re-processing
   const fileHash = await this.hashFile(file);
   const cached = await this.cache.get(fileHash);
   if (cached) return cached;
   ```

3. **Progress Indicators**
   ```javascript
   this.updateProgress('Uploading file...', 20);
   this.updateProgress('AI analyzing floor plan...', 50);
   this.updateProgress('Converting to BIM...', 80);
   this.updateProgress('Rendering...', 100);
   ```

## API Keys & Security

### Required API Keys:
1. **OpenAI API** - For Vision API
2. **Polycam API** (optional) - For LiDAR processing
3. **Google Cloud** (optional) - For Document AI fallback

### Security Implementation:
```javascript
// NEVER expose API keys in frontend
// Always proxy through backend

// Backend: core/backend/.env
OPENAI_API_KEY=sk-...
POLYCAM_API_KEY=...

// Backend validates and forwards requests
```

## Testing Strategy

### Test Files Needed:
1. Simple rectangular floor plan (PDF)
2. Complex multi-room floor plan (JPEG)
3. Photo of paper floor plan (HEIC)
4. Sample IFC file
5. LiDAR scan output (USDZ or PLY)

### Test Cases:
```javascript
describe('AI Ingestion', () => {
  test('Processes simple floor plan', async () => {
    const result = await ingest('simple_floor.pdf');
    expect(result.walls).toHaveLength(4); // Rectangle
  });
  
  test('Handles complex school layout', async () => {
    const result = await ingest('mclane_school.jpg');
    expect(result.rooms).toBeGreaterThan(20);
  });
  
  test('Falls back gracefully on AI failure', async () => {
    mockAPIFailure();
    const result = await ingest('test.jpg');
    expect(result.source).toBe('manual_extraction');
  });
});
```

## Migration Checklist

### Before Starting:
- [ ] Backup current working code
- [ ] Document current ArxObject structure
- [ ] Obtain API keys
- [ ] Set up backend API proxy

### Phase 0 Completion:
- [ ] Manual extraction archived
- [ ] Feature flags implemented
- [ ] Existing BIM viewer stable

### Phase 1 Completion:
- [ ] OpenAI Vision integrated
- [ ] Backend API secure
- [ ] Photo upload working

### Phase 2 Completion:
- [ ] IFC parser integrated
- [ ] Direct IFC → ArxObject working

### Phase 3 Completion:
- [ ] LiDAR processing available
- [ ] At least one method working (RoomPlan or Polycam)

### Phase 4 Completion:
- [ ] Error handling complete
- [ ] Caching implemented
- [ ] All file types supported

## Risk Mitigation

### Risks:
1. **API Rate Limits** 
   - Mitigation: Implement caching, queue system

2. **API Costs**
   - Mitigation: Cache results, offer manual option for high volume

3. **Accuracy Issues**
   - Mitigation: Allow manual correction UI post-ingestion

4. **API Downtime**
   - Mitigation: Manual extraction fallback

## Success Metrics

### Target Performance:
- Photo → BIM: < 5 seconds
- PDF → BIM: < 3 seconds  
- IFC → BIM: < 2 seconds
- Accuracy: > 90% of walls detected
- Room labels: > 95% accuracy

## Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize phases** based on user needs
3. **Obtain API keys** for chosen services
4. **Begin Phase 0** cleanup and stabilization

---

## Appendix: File Structure After Implementation

```
/arxos
├── core/
│   ├── backend/
│   │   ├── handlers/
│   │   │   ├── ai_ingestion.go      # NEW
│   │   │   └── ifc_parser.go        # NEW
│   └── ingestion/
│       ├── ai_service.js            # NEW
│       ├── ifc_service.js           # NEW
│       └── lidar_service.js         # NEW
├── frontend/
│   └── web/
│       ├── arxos_complete.html      # UPDATED
│       └── static/
│           └── js/
│               └── arxos-core.js    # UPDATED
├── archive/
│   ├── manual_extraction/
│   │   └── wall_extraction_engine.js
│   └── prototypes/
│       ├── photo_ingestion.html
│       └── arxos_unified.html
└── config/
    └── config.js                     # NEW
```