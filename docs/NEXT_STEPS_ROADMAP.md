# ArxOS Next Steps Roadmap

**Date:** October 12, 2025
**Status:** Post TODO Cleanup - Ready for Feature Development

## Current State Summary

✅ **Code Quality:** 100% TODO-free, fully compiling, all tests passing
✅ **Documentation:** Organized and indexed
✅ **Architecture:** Clean, maintainable, well-structured

## 4 Priority Features - Implementation Plan

### Priority 1: IFC Import 🏗️

**Current State:**
- ✅ IFCUseCase with parsing logic implemented
- ✅ IfcOpenShell service integration
- ✅ IFC validation and metadata extraction
- ⚠️ Basic entity extraction (buildings, spaces, equipment counts)
- ❌ Full building data conversion (IFC → Domain entities)
- ❌ Equipment relationship mapping from IFC

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

**Current State:**
- ✅ Mobile API handlers implemented
- ✅ Equipment list/detail endpoints
- ✅ Spatial data structures defined
- ⚠️ AR metadata placeholders (no real anchor integration)
- ❌ Spatial anchor storage and retrieval
- ❌ Point cloud data capture
- ❌ AR session management

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

**Current State:**
- ✅ RBAC system implemented
- ✅ JWT authentication with refresh tokens
- ✅ Permission middleware on routes
- ✅ User/organization management
- ✅ Session tracking
- ⚠️ Limited role definitions (need more granular permissions)
- ❌ Real-time collaboration features
- ❌ Activity feed and notifications

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

**Current State:**
- ✅ Hybrid graph model implemented (item_relationships table)
- ✅ Equipment domain with category/subtype/parent
- ✅ Relationship repository with recursive CTEs
- ✅ Graph traversal queries (upstream/downstream)
- ✅ System templates (YAML configs for 7 systems)
- ✅ API endpoints for relationship CRUD
- ❌ Template instantiation logic
- ❌ System validation rules
- ❌ Visual topology rendering

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

## Implementation Order Recommendation

### Phase 1 (Immediate - Week 1-2): **Equipment Systems** ✅
*Why First:* Just implemented, needs validation and testing before moving on.

- Complete template instantiation
- Test with real electrical system
- Validate graph traversal queries
- Document template creation

### Phase 2 (Near-term - Week 3-4): **IFC Import** 🏗️
*Why Second:* Foundational data source, enables testing other features with real data.

- Full entity extraction
- Geometry processing
- Property mapping
- Test with sample IFC files

### Phase 3 (Mid-term - Week 5-7): **Multi-User Support** 👥
*Why Third:* Enables team collaboration before field deployment.

- Enhanced RBAC
- Real-time collaboration
- Activity feed
- Team management

### Phase 4 (Long-term - Week 8-12): **Mobile App** 📱
*Why Last:* Most complex, requires backend features to be solid first.

- AR anchor integration
- Spatial data capture
- Mobile UI development
- Field testing

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

