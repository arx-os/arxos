# ArxOS Next Steps Roadmap

**Date:** October 12, 2025
**Status:** Integration Phase - Wiring Use Cases to Interfaces

## Reality Check - Current State Summary

⚠️ **Actual Completion:** 60-70% (architecture excellent, integration incomplete)
✅ **Code Quality:** Compiles successfully, ~15% test coverage
✅ **Documentation:** Now accurately reflects reality
✅ **Architecture:** Clean, maintainable, well-structured - **this is the strength**

### Status Legend:
- ✅ **Fully Functional** - Works end-to-end, tested
- ⚠️ **Partially Implemented** - Core logic exists, needs wiring/testing
- 🎭 **Placeholder** - Shows fake data or placeholder messages
- ❌ **Not Implemented** - Doesn't exist yet

**See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for detailed assessment and [`WIRING_PLAN.md`](WIRING_PLAN.md) for execution plan.**

## 4 Priority Features - Implementation Plan

### Priority 1: IFC Import 🏗️

**Status: ⚠️ 40% Complete - Core gap, needs full entity extraction**

**What Works:**
- ✅ IFCUseCase with parsing logic implemented
- ✅ IfcOpenShell service integration
- ✅ IFC validation and metadata extraction
- ✅ Entity counting (buildings, spaces, equipment counts)
- ✅ CLI command `arx import` calls real implementation

**What Doesn't Work:**
- 🎭 IFC import creates IFCFile record but not domain entities
- ❌ No Building/Floor/Room/Equipment creation from IFC
- ❌ No geometry/coordinate extraction
- ❌ No property mapping to equipment metadata
- ❌ No relationship preservation (spatial hierarchy lost)
- ❌ Equipment relationship mapping from IFC

**Wiring Required: 8-12 hours (see WIRING_PLAN.md "IFC Import Deep Dive")**

**Next Steps:**

1. **Enhanced Entity Extraction** (4-6 hours)
   - [ ] Map IfcBuilding → domain.Building with full metadata
   - [ ] Extract IfcBuildingStorey → domain.Floor with elevations
   - [ ] Convert IfcSpace → domain.Room with boundaries
   - [ ] Parse IfcProduct → domain.Equipment with properties
   - [ ] Handle IfcRelationships for spatial containment

2. **Geometry & Location Processing** (3-4 hours)
   - [ ] Extract 3D coordinates from IfcLocalPlacement
   - [ ] Convert IFC units to internal coordinate system
   - [ ] Generate bounding boxes for rooms and equipment
   - [ ] Store PostGIS geometries for spatial queries

3. **Property & Classification Mapping** (2-3 hours)
   - [ ] Extract Pset properties into domain.Equipment.Metadata
   - [ ] Map IFC types to equipment categories (electrical, HVAC, etc.)
   - [ ] Handle material assignments
   - [ ] Process classification references (Uniclass, Omniclass)

4. **Relationship Preservation** (3-4 hours)
   - [ ] Extract IfcRelConnectsElements → item_relationships
   - [ ] Map IfcRelContainedInSpatialStructure → parent_id
   - [ ] Preserve IfcRelDefinesByType for equipment templates
   - [ ] Store IfcRelAssignsToGroup for system membership

5. **Import Workflow Enhancement** (2-3 hours)
   - [ ] Add progress tracking for large IFC files
   - [ ] Implement transaction rollback on import failure
   - [ ] Generate import summary report
   - [ ] Create version commit after successful import

**Testing:**
- [ ] Test with AC20-FZK-Haus.ifc (sample file)
- [ ] Validate electrical equipment extraction
- [ ] Verify spatial hierarchy preservation
- [ ] Check property data integrity

**Estimated Total:** 14-20 hours

---

### Priority 2: Mobile App 📱

**Status: ⚠️ 50% Complete - Backend works, AR features need implementation**

**What Works:**
- ✅ Mobile auth endpoints (login, register, refresh, profile)
- ✅ Equipment list/detail endpoints functional
- ✅ Spatial query endpoints exist
- ✅ Building/floor/room CRUD via API
- ✅ Basic mobile UI structure

**What Doesn't Work:**
- 🎭 AR spatial anchor endpoints exist but storage incomplete
- 🎭 Mobile services have placeholder implementations (getUserProfile, changePassword)
- ❌ Spatial anchor persistence not implemented
- ❌ Point cloud data capture not implemented
- ❌ AR session management not implemented
- ❌ Offline sync queue defined but not functional

**Wiring Required: 16-21 hours backend + 20-30 hours mobile UI**

**Next Steps:**

1. **Spatial Anchor Integration** (4-5 hours)
   - [ ] Implement SpatialAnchorRepository
   - [ ] Create spatial_anchors CRUD operations
   - [ ] Link anchors to equipment via equipment_id
   - [ ] Store AR World Map data (ARKit/ARCore)
   - [ ] Handle anchor persistence and reload

2. **AR Session Management** (3-4 hours)
   - [ ] Create AR session tracking (start/stop/resume)
   - [ ] Store scanning progress and coverage
   - [ ] Handle multi-user AR collaboration metadata
   - [ ] Implement session recovery after interruption

3. **Point Cloud & Mesh Data** (3-4 hours)
   - [ ] Design point_clouds table schema
   - [ ] Store LiDAR scan data efficiently
   - [ ] Implement mesh generation pipeline
   - [ ] Add point cloud query by spatial bounds

4. **Mobile-Optimized Queries** (2-3 hours)
   - [ ] Implement spatial filtering (nearby equipment)
   - [ ] Add floor-level data loading
   - [ ] Create equipment search by AR scan
   - [ ] Optimize payload sizes for mobile bandwidth

5. **Data Collection Forms** (4-5 hours)
   - [ ] Create equipment inspection form API
   - [ ] Implement photo/document upload
   - [ ] Add work order creation endpoint
   - [ ] Store offline data for sync later

**React Native Work** (Mobile/TypeScript):
- [ ] AR camera view with equipment overlay
- [ ] Equipment detail form with photo capture
- [ ] Offline data queue management
- [ ] Sync indicator and conflict resolution UI

**Testing:**
- [ ] Test AR anchor persistence on iOS/Android
- [ ] Validate offline data queue
- [ ] Check equipment positioning accuracy
- [ ] Verify sync after network reconnection

**Estimated Total:** 16-21 hours (Backend only, +20-30 hours for mobile UI)

---

### Priority 3: Multi-User Support 👥

**Status: ✅ 75% Complete - Core auth works, collaboration features needed**

**What Works:**
- ✅ RBAC system fully implemented
- ✅ JWT authentication with refresh tokens
- ✅ Permission middleware on routes
- ✅ User/organization management (CRUD)
- ✅ Session tracking with login/logout
- ✅ Role-based access control enforced on API
- ✅ Multi-tenancy via organizations

**What Doesn't Work:**
- ⚠️ Limited role definitions (only basic roles)
- ❌ Real-time collaboration (WebSocket presence tracking)
- ❌ Activity feed not implemented
- ❌ User notifications system not implemented
- ❌ Team/group management beyond organizations
- ❌ Comment threads on equipment/rooms

**Wiring Required: 15-21 hours for collaboration features (can defer)**

**Next Steps:**

1. **Enhanced RBAC** (2-3 hours)
   - [ ] Define role hierarchy (Owner > Admin > Editor > Viewer > Guest)
   - [ ] Add permission templates for common roles
   - [ ] Implement resource-level permissions (building/floor access)
   - [ ] Add team/group permissions

2. **Real-Time Collaboration** (6-8 hours)
   - [ ] WebSocket presence tracking (who's online, where)
   - [ ] Collaborative editing indicators (locks/cursors)
   - [ ] Live change broadcasting
   - [ ] Conflict detection and resolution UI

3. **Activity Feed & Audit** (3-4 hours)
   - [ ] Activity stream API (recent changes by user)
   - [ ] User mention/notification system
   - [ ] Comment threads on equipment/rooms
   - [ ] Change history timeline

4. **Team Management** (2-3 hours)
   - [ ] Team/group creation and membership
   - [ ] Invite system (email invitations)
   - [ ] Access request workflow
   - [ ] Permission inheritance

5. **User Preferences & Profiles** (2-3 hours)
   - [ ] User profile management
   - [ ] Notification preferences
   - [ ] UI customization (theme, units, language)
   - [ ] Recent items and favorites

**Testing:**
- [ ] Test multi-user concurrent edits
- [ ] Validate permission enforcement
- [ ] Check notification delivery
- [ ] Verify conflict resolution

**Estimated Total:** 15-21 hours

---

### Priority 4: Equipment Systems ⚡

**Status: ✅ 85% Complete - Core topology works, templates need testing**

**What Works:**
- ✅ Hybrid graph model implemented (item_relationships table)
- ✅ Equipment domain with category/subtype/parent
- ✅ Relationship repository with recursive CTEs
- ✅ Graph traversal queries (upstream/downstream) functional
- ✅ System templates (YAML configs for 7 systems: electrical, HVAC, network, etc.)
- ✅ API endpoints for relationship CRUD working
- ✅ Equipment hierarchy queries via API

**What Doesn't Work:**
- ⚠️ Template instantiation logic exists but needs more testing
- ⚠️ System validation rules basic (needs enhancement)
- ❌ Visual topology rendering (frontend feature, not critical for backend)
- ❌ Bulk equipment operations need optimization

**Wiring Required: 14-19 hours for template testing and validation**

**Next Steps:**

1. **Template Instantiation** (3-4 hours)
   - [ ] Parse YAML system templates
   - [ ] Generate equipment hierarchy from template
   - [ ] Create relationships based on template rules
   - [ ] Assign IDs and spatial locations
   - [ ] Add to version control system

2. **System Validation** (2-3 hours)
   - [ ] Validate topology completeness
   - [ ] Check relationship type consistency
   - [ ] Verify electrical flow (no loops, proper grounding)
   - [ ] Validate HVAC zones and balancing
   - [ ] Network connectivity verification

3. **Bulk Equipment Operations** (2-3 hours)
   - [ ] Import equipment from CSV/Excel
   - [ ] Bulk update properties
   - [ ] Mass relationship creation
   - [ ] Equipment cloning with relationships

4. **System Analytics** (3-4 hours)
   - [ ] Calculate system statistics (total load, capacity)
   - [ ] Identify orphaned equipment (no parent)
   - [ ] Find incomplete systems
   - [ ] Generate system health reports

5. **Integration Testing** (4-5 hours)
   - [ ] Test electrical system creation from template
   - [ ] Validate network topology instantiation
   - [ ] Test HVAC zone configuration
   - [ ] Verify BAS point linkage to equipment
   - [ ] Check custodial/IT marker creation

**Documentation:**
- [ ] Create system template guide
- [ ] Document relationship types
- [ ] Write equipment hierarchy best practices
- [ ] Add system validation rules

**Testing:**
- [ ] Create full electrical distribution system
- [ ] Test network MDF → IDF → WAP hierarchy
- [ ] Validate HVAC air handler → VAV topology
- [ ] Verify equipment search by system

**Estimated Total:** 14-19 hours

---

## Implementation Order Recommendation (Updated for Reality)

### **NEW Priority: BAS CLI Wiring (Week 1) - CRITICAL**
**Why First:** Small, contained feature to prove wiring pattern. Builds confidence.
- Wire `arx bas list/unmapped/map/show` commands (10-14 hours)
- Tests the pattern for all other CLI wiring
- **Success Criteria:** All BAS commands work with real database data

### **Phase 1 (Week 2-3): IFC Import - CRITICAL** 🏗️
**Why Second:** Unblocks testing with real buildings. Core use case for Joel's workplace.
- Full entity extraction (8-12 hours)
- Extract Building/Floor/Room/Equipment from IFC
- Map geometry and properties
- Test with AC20-FZK-Haus.ifc
- **Success Criteria:** `arx import building.ifc` creates complete building in database

### **Phase 2 (Week 4-6): HTTP API Completion** 📡
**Why Third:** Mobile app and external integrations need these endpoints.
- Add BAS endpoints (8-10 hours)
- Add PR/Issue endpoints (14-18 hours)
- Add Version Control endpoints (6-8 hours)
- Test with Postman
- **Success Criteria:** 80%+ use case coverage via REST API

### **Phase 3 (Week 7-9): Testing & Validation** ✅
**Why Fourth:** Prove everything works together before adding more features.
- Add use case tests (20-30 hours)
- Add integration tests (10-15 hours)
- Test end-to-end workflows (10-15 hours)
- **Success Criteria:** 60%+ test coverage, core workflows proven

### **Phase 4 (Week 10-13): Mobile App Enhancement** 📱
**Why Fifth:** After backend is solid and tested.
- Complete AR anchor storage (4-5 hours)
- AR session management (3-4 hours)
- Offline sync implementation (6-8 hours)
- Mobile UI polish (20-30 hours)
- **Success Criteria:** Field-testable with AR features

### **Defer to Post-MVP:**
- ⏸️ Multi-User Collaboration (WebSocket, activity feed) - Core auth works
- ⏸️ Equipment Template Testing - Basics work, enhance later
- ⏸️ Remote Repository (clone/push/pull) - Not needed for single-workplace deployment

---

## Success Criteria

### IFC Import ✅
- [ ] Import AC20-FZK-Haus.ifc with 100% entity preservation
- [ ] Extract all equipment with properties
- [ ] Maintain spatial hierarchy
- [ ] Generate accurate building model

### Mobile App ✅
- [ ] Place AR anchor and persist location
- [ ] Scan equipment and retrieve data
- [ ] Submit inspection form offline
- [ ] Sync data when back online

### Multi-User ✅
- [ ] Two users edit same building simultaneously
- [ ] Changes appear in real-time
- [ ] Permissions enforced correctly
- [ ] Conflict resolved automatically

### Equipment Systems ✅
- [ ] Instantiate electrical system from template
- [ ] Traverse transformer → outlet path
- [ ] Validate system completeness
- [ ] Query "show all equipment fed by panel X"

---

## Resources & Tools

**IFC Development:**
- IfcOpenShell documentation
- Sample IFC files (AC20-FZK-Haus, Duplex_A_20110907)
- IFC4 specification reference

**Mobile Development:**
- React Native CLI
- Expo for AR testing
- TestFlight/Google Play internal testing

**Testing:**
- Integration test suite expansion
- E2E testing with real IFC data
- Mobile device testing (iOS/Android)
- Multi-user concurrency tests

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| IFC parsing errors | High | Extensive testing with diverse IFC files |
| AR anchor drift | Medium | Multiple anchor points, continuous calibration |
| Concurrent edit conflicts | Medium | Optimistic locking, conflict resolution UI |
| Mobile offline sync | High | Queue-based sync, conflict detection |
| Equipment graph complexity | Medium | Graph query optimization, caching |

---

## Next Immediate Actions

**Today/This Week:**
1. ✅ Complete equipment system testing
2. ✅ Validate relationship graph queries
3. ✅ Test system template instantiation
4. ✅ Document equipment topology usage

**This Month:**
1. IFC entity extraction enhancement
2. IFC geometry processing
3. Test with real building files
4. Generate first complete building model

**This Quarter:**
1. Complete all 4 priority features
2. Field test at workplace
3. Gather user feedback
4. Iterate based on real-world usage

---

**Status:** Ready to proceed with systematic feature implementation! 🚀

