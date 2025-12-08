# Archived Mobile Documentation

**Status:** Archived  
**Date:** December 8, 2025  
**Reason:** Strategic pivot to WASM PWA-only approach

---

## Context

This directory contains documentation for native mobile app development (Android/iOS) that was previously planned for ArxOS. As of December 8, 2025, the project has pivoted to focus exclusively on **WASM PWA (Progressive Web App)** deployment.

## Why Archived?

**Decision:** Focus on WASM PWA instead of native mobile apps

**Rationale:**
- **Single codebase:** Rust → WASM works across all platforms via browser
- **No platform gatekeeping:** No app store submission required
- **Faster development:** Avoid platform-specific build complexity (Android Studio, Xcode)
- **Broader compatibility:** Works on any device with a modern browser
- **Offline capability:** Service workers enable offline functionality
- **Lower maintenance:** No FFI bindings, no platform-specific UI frameworks

**Trade-offs:**
- ❌ No access to native device APIs (camera, GPS, etc.)
- ❌ Requires modern browser (Chrome/Firefox/Safari 2020+)
- ✅ But these limitations are acceptable for ArxOS's terminal-first use case

## Archived Documents

This directory contains:
- `ANDROID.md` - Android native app development guide
- `IOS_*.md` - iOS integration plans and FFI status
- `ANDROID_AR_*.md` - AR feature integration plans
- `MOBILE_FFI_INTEGRATION.md` - Foreign Function Interface design
- `MOBILE_GAME_INTEGRATION.md` - Gamification on mobile platforms
- `MOBILE_CI_CD.md` - Mobile CI/CD pipeline
- `README_MOBILE_FFI_TESTS.md` - Mobile FFI test documentation
- `README_ANDROID_AR_TESTS.md` - Android AR test documentation

## Current Approach

**WASM PWA Architecture:**
- **Terminal emulation:** xterm.js in browser
- **3D visualization:** WebGL via Bevy WASM target
- **Offline support:** Service workers cache assets
- **Installable:** Add to home screen on mobile devices
- **Cross-platform:** Single binary deployed via static hosting

**Browser Requirements:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Modern mobile browsers (2020+)

## Future Considerations

Native mobile apps may be revisited if:
1. **Use cases emerge** requiring native device APIs (camera for AR scans, GPS for outdoor facilities)
2. **User demand** specifically requests app store distribution
3. **Vendor partnerships** require native integration
4. **Performance** constraints require native rendering

Until then, WASM PWA provides the best balance of:
- Development velocity
- Platform reach
- Maintenance burden
- User experience

---

## Related Documentation

- **Current Architecture:** `docs/TECHNICAL_DESIGN_NEXT_FEATURES.md`
- **WASM Deployment:** `docs/web/` (if created)
- **Browser Compatibility:** `docs/QUICK_START_GUIDE.md`
- **Development Plan:** `docs/development/GEOMETRY_ENHANCEMENT_PLAN.md`

---

**Archived By:** Development Team  
**Decision Document:** AD-001 in `GEOMETRY_ENHANCEMENT_PLAN.md`
