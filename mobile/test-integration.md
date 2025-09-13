# Mobile AR Integration Test Plan

## Overview
This document outlines the test plan for the ArxOS mobile AR integration.

## Test Cases

### 1. Authentication Flow
- [ ] User can log in with valid credentials
- [ ] Invalid credentials show appropriate error
- [ ] Token refresh works automatically
- [ ] User stays logged in after app restart
- [ ] Logout clears all stored tokens

### 2. Navigation Flow
- [ ] Home screen loads correctly after login
- [ ] Navigation to Buildings list works
- [ ] Navigation to AR view works
- [ ] Back navigation maintains state
- [ ] Settings screen is accessible

### 3. AR Functionality
- [ ] AR support detection works on device
- [ ] AR camera permission requests work
- [ ] AR scene initializes properly
- [ ] Floor plan data loads from API
- [ ] 3D objects render in AR space
- [ ] Object interaction (tap) works
- [ ] AR controls (exit) function properly

### 4. API Integration
- [ ] Building list loads from server
- [ ] Floor plan data fetches correctly
- [ ] Authentication tokens are sent with requests
- [ ] Error handling works for network issues
- [ ] Offline behavior is graceful

### 5. Type Safety
- [ ] No TypeScript compilation errors
- [ ] Props are correctly typed
- [ ] API responses match expected interfaces
- [ ] Navigation params are type-safe

## Manual Testing Steps

1. **Setup Environment**
   ```bash
   cd mobile
   npm install
   npx react-native run-ios  # or run-android
   ```

2. **Test Authentication**
   - Launch app
   - Verify login screen appears
   - Test login with valid/invalid credentials
   - Verify home screen after successful login

3. **Test Navigation**
   - Navigate through all screens
   - Verify smooth transitions
   - Test back button behavior

4. **Test AR Features**
   - Enable AR from home screen
   - Verify camera permission prompt
   - Test AR scene rendering
   - Interact with AR objects

5. **Test Error Handling**
   - Disconnect network during API calls
   - Test with invalid building IDs
   - Verify error messages are user-friendly

## Expected Results

- All screens render without crashes
- AR functionality works on supported devices
- API calls complete successfully
- Type checking passes without errors
- User experience is smooth and intuitive

## Known Limitations

- Requires physical device for AR testing
- Some dependencies may need version adjustments
- AR quality depends on device capabilities