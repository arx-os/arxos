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

- Node.js 16+
- React Native CLI
- iOS Simulator (Mac) or Android Emulator
- Xcode (iOS development)
- Android Studio (Android development)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Install iOS dependencies (Mac only):
   ```bash
   cd ios && pod install && cd ..
   ```

4. Start the Metro bundler:
   ```bash
   npm start
   ```

5. Run on iOS:
   ```bash
   npm run ios
   ```

6. Run on Android:
   ```bash
   npm run android
   ```

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