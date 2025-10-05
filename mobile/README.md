# ArxOS Mobile

ArxOS Mobile is a React Native application that serves as the mobile interface for the ArxOS building management system. It provides bidirectional data input capabilities through AR/text interfaces, enabling field technicians to interact with building equipment and systems.

## Features

- **Equipment Management**: View, search, and update equipment status
- **Augmented Reality**: AR visualization and spatial anchor management
- **Camera Integration**: Photo capture for equipment documentation
- **Offline Support**: Work offline with automatic sync when online
- **Real-time Sync**: Bidirectional data synchronization with the main ArxOS system
- **Location Services**: GPS tracking for equipment positioning
- **Push Notifications**: Real-time updates and alerts

## Architecture

The app follows a clean architecture pattern with:

- **Presentation Layer**: React Native screens and components
- **Business Logic Layer**: Redux store and services
- **Data Layer**: SQLite local storage and API services
- **Infrastructure Layer**: Device capabilities and external services

## Tech Stack

- **React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe development
- **Redux Toolkit**: State management
- **React Navigation**: Navigation handling
- **SQLite**: Local data storage
- **ARKit/ARCore**: Augmented Reality support
- **Axios**: HTTP client
- **React Native Vector Icons**: Icon library

## Dependencies

### Core Dependencies

- **React Native**: 0.73.6
- **TypeScript**: 5.3.3
- **React**: 18.3.1
- **Node.js**: 20+

### Mobile-Specific Dependencies

- **@react-native-async-storage/async-storage**: 1.21.0
- **@react-native-community/geolocation**: 3.2.0
- **react-native-camera**: 4.2.1
- **react-native-geolocation-service**: 5.3.1
- **react-native-image-picker**: 7.1.0
- **react-native-push-notification**: 8.1.1
- **react-native-sqlite-storage**: 6.0.1
- **react-native-vector-icons**: 10.0.3

### Development Dependencies

- **@types/react**: 18.3.1
- **@types/react-native**: 0.73.0
- **@typescript-eslint/eslint-plugin**: 6.21.0
- **@typescript-eslint/parser**: 6.21.0
- **eslint**: 8.57.0
- **eslint-plugin-react**: 7.34.1
- **eslint-plugin-react-hooks**: 4.6.0
- **eslint-plugin-react-native**: 4.1.0

## Project Structure

```
src/
├── components/          # Reusable UI components
├── screens/            # Screen components
├── navigation/         # Navigation configuration
├── store/             # Redux store and slices
├── services/          # Business logic services
├── types/             # TypeScript type definitions
├── utils/             # Utility functions
├── constants/         # Application constants
└── App.tsx            # Main app component
```

## Getting Started

### Prerequisites

- **Node.js 20+** - [Download](https://nodejs.org/)
- **React Native CLI** - `npm install -g @react-native-community/cli`
- **iOS**: Xcode 15+ and iOS Simulator
- **Android**: Android Studio and Android SDK
- **CocoaPods** (iOS only) - `sudo gem install cocoapods`

### Installation

```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos/mobile

# Install dependencies
npm install

# iOS setup (macOS only)
cd ios && pod install && cd ..

# Start Metro bundler
npm start
```

### Running the App

```bash
# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on both platforms
npm run start:ios
npm run start:android
```

### Building for Production

```bash
# Build for iOS
npm run build:ios

# Build for Android
npm run build:android

# Build for both platforms
npm run build:all
```

### Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Troubleshooting

#### Common Issues

1. **Metro bundler issues**
   ```bash
   # Clear Metro cache
   npm start -- --reset-cache
   
   # Clear npm cache
   npm cache clean --force
   ```

2. **iOS build issues**
   ```bash
   # Clean iOS build
   cd ios && xcodebuild clean && cd ..
   
   # Reinstall pods
   cd ios && pod deintegrate && pod install && cd ..
   ```

3. **Android build issues**
   ```bash
   # Clean Android build
   cd android && ./gradlew clean && cd ..
   
   # Clear Gradle cache
   cd android && ./gradlew cleanBuildCache && cd ..
   ```

4. **TypeScript errors**
   ```bash
   # Check TypeScript configuration
   npx tsc --noEmit
   
   # Update type definitions
   npm install --save-dev @types/react @types/react-native
   ```

#### Performance Optimization

- **Enable Hermes** (Android): Already enabled in `android/app/build.gradle`
- **Enable Flipper** (Development): Configured in `ios/Podfile`
- **Bundle Analysis**: Use `npm run analyze` to analyze bundle size

### Development Workflow

1. **Start development server**: `npm start`
2. **Run on device**: `npm run ios` or `npm run android`
3. **Test changes**: Use hot reload for instant feedback
4. **Debug**: Use React Native Debugger or Flipper
5. **Test**: Run `npm test` before committing

### Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Ensure TypeScript compilation passes
5. Test on both iOS and Android platforms

## Development

### Code Style

The project uses ESLint and Prettier for code formatting. Run:

```bash
npm run lint
npm run lint:fix
```

### Testing

Run tests with:

```bash
npm test
```

### Building

#### Android
```bash
npm run build:android
```

#### iOS
```bash
npm run build:ios
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
API_BASE_URL=http://localhost:8080/api/v1
DEBUG_MODE=true
```

### API Configuration

The app connects to the main ArxOS API. Update the API base URL in `src/constants/index.ts` or use environment variables.

## Features Overview

### Equipment Management

- Browse equipment by building, floor, and room
- Search equipment by name, type, or status
- Update equipment status with photos and notes
- View equipment specifications and history

### Augmented Reality

- AR visualization of equipment in 3D space
- Spatial anchor creation and management
- AR-based equipment identification
- Real-time AR data synchronization

### Camera Integration

- High-quality photo capture
- Photo compression and optimization
- Automatic photo upload to equipment records
- Gallery management

### Offline Support

- Local SQLite database for offline data
- Automatic sync when connection is restored
- Conflict resolution for data updates
- Offline queue management

### Sync System

- Real-time bidirectional synchronization
- Conflict resolution strategies
- Retry mechanisms for failed syncs
- Progress tracking and error handling

## API Integration

The mobile app integrates with the main ArxOS API through:

- **Authentication**: JWT-based authentication
- **Equipment API**: CRUD operations for equipment
- **Spatial API**: AR anchor management
- **Sync API**: Data synchronization endpoints
- **File API**: Photo and document upload

## Security

- JWT token authentication
- Biometric authentication support
- Secure local storage
- API request encryption
- Certificate pinning

## Performance

- Image optimization and compression
- Lazy loading of components
- Efficient state management
- Memory usage optimization
- Battery usage optimization

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `npx react-native start --reset-cache`
2. **iOS build issues**: Clean build folder in Xcode
3. **Android build issues**: Run `cd android && ./gradlew clean`
4. **Permission issues**: Check device permissions in settings

### Debug Mode

Enable debug mode by setting `DEBUG_MODE=true` in your environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.