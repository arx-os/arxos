# Mobile AR Application Setup Guide

## Prerequisites

Before setting up the Arxos Mobile AR application, ensure you have the following installed:

### Development Environment
- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher (comes with Node.js)
- **Git**: For version control
- **Code Editor**: VS Code recommended with React Native extensions

### Platform-Specific Requirements

#### iOS Development (macOS only)
- **Xcode**: 14.0 or higher (from Mac App Store)
- **CocoaPods**: 1.12.0 or higher
  ```bash
  sudo gem install cocoapods
  ```
- **iOS Device**: iPhone 6s or newer with iOS 14+ (for AR testing)
- **Apple Developer Account**: For device deployment ($99/year)

#### Android Development
- **Android Studio**: Latest stable version
- **JDK**: Version 11 or higher
- **Android SDK**: API Level 24+ (Android 7.0)
- **Android Device**: ARCore supported device for testing

## Initial Setup

### 1. Clone the Repository
```bash
git clone https://github.com/arxos/arxos.git
cd arxos
```

### 2. Create Mobile App Directory
```bash
mkdir mobile
cd mobile
```

### 3. Initialize React Native Project
```bash
npx react-native init ArxosAR --template react-native-template-typescript
cd ArxosAR
```

### 4. Install Core Dependencies
```bash
npm install \
  react-viro@2.23.0 \
  axios@^1.5.0 \
  @react-navigation/native@^6.1.0 \
  @react-navigation/stack@^6.3.0 \
  @react-native-async-storage/async-storage@^1.19.0 \
  react-native-sqlite-storage@^6.0.1 \
  react-native-voice@^3.2.4 \
  react-native-camera@^4.2.1 \
  react-native-permissions@^3.9.0 \
  react-native-vector-icons@^10.0.0 \
  react-native-keychain@^8.1.0
```

### 5. Install Development Dependencies
```bash
npm install --save-dev \
  @types/react@^18.2.0 \
  @types/react-native@^0.72.0 \
  @typescript-eslint/eslint-plugin@^6.0.0 \
  @typescript-eslint/parser@^6.0.0 \
  eslint@^8.0.0 \
  prettier@^3.0.0 \
  jest@^29.0.0 \
  @testing-library/react-native@^12.0.0 \
  detox@^20.0.0
```

## Platform Configuration

### iOS Setup

#### 1. Navigate to iOS Directory
```bash
cd ios
```

#### 2. Install CocoaPods Dependencies
```bash
pod install
```

#### 3. Configure Info.plist
Add the following permissions to `ios/ArxosAR/Info.plist`:

```xml
<key>NSCameraUsageDescription</key>
<string>ArxOS needs camera access for AR functionality</string>
<key>NSMicrophoneUsageDescription</key>
<string>ArxOS needs microphone access for voice commands</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>ArxOS uses location to find nearby equipment</string>
```

#### 4. Configure AR Capabilities
Open the project in Xcode:
```bash
open ArxosAR.xcworkspace
```

In Xcode:
1. Select your project in the navigator
2. Select your target
3. Go to "Signing & Capabilities"
4. Add "ARKit" capability

### Android Setup

#### 1. Update Android Manifest
Edit `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />

<application>
  <!-- Add ARCore meta-data -->
  <meta-data 
    android:name="com.google.ar.core" 
    android:value="required" />
</application>
```

#### 2. Update Gradle Configuration
Edit `android/app/build.gradle`:

```gradle
android {
    compileSdkVersion 33
    
    defaultConfig {
        minSdkVersion 24
        targetSdkVersion 33
    }
}

dependencies {
    implementation 'com.google.ar:core:1.39.0'
}
```

## Project Structure Setup

Create the following directory structure in your mobile app:

```bash
mkdir -p src/{components,screens,services,hooks,utils,navigation,types,assets}
mkdir -p src/components/{ar,common,forms}
mkdir -p src/services/{api,ar,sync}
```

### Create Base Configuration Files

#### 1. TypeScript Configuration
Create `tsconfig.json`:

```json
{
  "extends": "@tsconfig/react-native/tsconfig.json",
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@screens/*": ["src/screens/*"],
      "@services/*": ["src/services/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"]
    }
  }
}
```

#### 2. ESLint Configuration
Create `.eslintrc.js`:

```javascript
module.exports = {
  root: true,
  extends: [
    '@react-native-community',
    'plugin:@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  rules: {
    'react-native/no-inline-styles': 'off',
    '@typescript-eslint/no-unused-vars': 'warn',
  },
};
```

#### 3. Prettier Configuration
Create `.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

## Environment Configuration

### 1. Create Environment Files
Create `.env.development`:

```bash
API_BASE_URL=http://localhost:8080/api/v1
AR_SESSION_TIMEOUT=30000
OFFLINE_SYNC_INTERVAL=60000
ENABLE_VOICE_INPUT=true
```

Create `.env.production`:

```bash
API_BASE_URL=https://api.arxos.io/api/v1
AR_SESSION_TIMEOUT=30000
OFFLINE_SYNC_INTERVAL=60000
ENABLE_VOICE_INPUT=true
```

### 2. Install React Native Config
```bash
npm install react-native-config
cd ios && pod install
```

## Initial Code Setup

### 1. Create App Entry Point
Create `src/App.tsx`:

```typescript
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { AppNavigator } from './navigation/AppNavigator';
import { AuthProvider } from './contexts/AuthContext';
import { ARProvider } from './contexts/ARContext';

const App: React.FC = () => {
  return (
    <NavigationContainer>
      <AuthProvider>
        <ARProvider>
          <AppNavigator />
        </ARProvider>
      </AuthProvider>
    </NavigationContainer>
  );
};

export default App;
```

### 2. Update Index File
Update `index.js`:

```javascript
import { AppRegistry } from 'react-native';
import App from './src/App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
```

## Running the Application

### iOS
```bash
# Run on simulator
npx react-native run-ios

# Run on device
npx react-native run-ios --device "Your iPhone Name"
```

### Android
```bash
# Start Metro bundler
npx react-native start

# Run on emulator/device
npx react-native run-android
```

## Testing AR Features

### iOS Simulator Limitations
- AR features are NOT available in iOS Simulator
- Use a physical device for AR testing
- Enable Developer Mode on iOS 16+ devices

### Android Emulator AR
- Use Android Studio AVD with ARCore support
- Limited AR functionality compared to physical device

## Troubleshooting

### Common Issues

#### 1. Pod Installation Fails (iOS)
```bash
cd ios
pod deintegrate
pod install --repo-update
```

#### 2. Metro Bundler Issues
```bash
npx react-native start --reset-cache
```

#### 3. Build Failures
```bash
# iOS
cd ios && xcodebuild clean

# Android
cd android && ./gradlew clean
```

#### 4. AR Not Working
- Ensure device supports ARKit/ARCore
- Check camera permissions are granted
- Verify adequate lighting for AR tracking

## Next Steps

1. **Implement Core Services**: Set up API client and authentication
2. **Create AR Components**: Build AR session manager and equipment visualizers
3. **Add Offline Support**: Implement local database and sync queue
4. **Test on Devices**: Deploy to physical devices for AR testing
5. **Configure CI/CD**: Set up automated builds and testing

## Development Workflow

### Daily Development
```bash
# Start Metro bundler
npm start

# Run on iOS device
npm run ios:device

# Run on Android device
npm run android:device

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint
```

### Building for Testing

#### iOS TestFlight
```bash
cd ios
fastlane beta
```

#### Android Internal Testing
```bash
cd android
./gradlew bundleRelease
```

## Resources

- [React Native Documentation](https://reactnative.dev/docs/getting-started)
- [ViroReact Documentation](https://docs.viromedia.com/)
- [ARKit Documentation](https://developer.apple.com/arkit/)
- [ARCore Documentation](https://developers.google.com/ar)
- [React Navigation](https://reactnavigation.org/)

## Support

For setup issues:
- GitHub Issues: https://github.com/arxos/mobile-ar/issues
- Discord: https://discord.gg/arxos
- Email: mobile-support@arxos.io