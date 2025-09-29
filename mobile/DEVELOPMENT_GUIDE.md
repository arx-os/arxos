# ArxOS Mobile Development Guide

## 🚀 Getting Started

### Prerequisites
- Node.js >= 16.0.0
- React Native CLI
- Xcode (for iOS development)
- Android Studio (for Android development)
- CocoaPods (for iOS dependencies)

### Installation

1. **Install dependencies:**
   ```bash
   cd /Users/joelpate/repos/arxos/mobile
   npm install
   ```

2. **Install iOS dependencies (Mac only):**
   ```bash
   cd ios && pod install && cd ..
   ```

3. **Start Metro bundler:**
   ```bash
   npm start
   ```

4. **Run on iOS:**
   ```bash
   npm run ios
   ```

5. **Run on Android:**
   ```bash
   npm run android
   ```

## 🏗️ Architecture Overview

### Core Principles
- **Offline-First**: All data operations work offline with sync when online
- **Type Safety**: Full TypeScript coverage with strict type checking
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Security**: Secure token storage using device keychain
- **Performance**: Optimized for mobile with efficient caching and lazy loading

### Project Structure
```
src/
├── config/           # Environment configuration
├── constants/        # App-wide constants
├── navigation/       # Navigation configuration
├── screens/          # Screen components
├── services/         # Business logic services
├── store/            # Redux state management
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── __tests__/        # Test files
```

## 🔧 Development Workflow

### 1. Environment Setup
- Copy `env.example` to `.env` and configure your settings
- Set up your ArxOS backend API endpoint
- Configure development vs production settings

### 2. Code Standards
- **TypeScript**: Use strict typing, avoid `any` types
- **ESLint**: Follow the configured linting rules
- **Prettier**: Use consistent code formatting
- **Testing**: Write tests for all new functionality

### 3. Git Workflow
- Create feature branches from `main`
- Write descriptive commit messages
- Run tests before committing
- Create pull requests for code review

## 📱 Core Features

### Authentication
- JWT token-based authentication
- Secure token storage in device keychain
- Automatic token refresh
- Biometric authentication support

### Equipment Management
- CRUD operations for equipment
- Offline-first data storage
- Photo capture and upload
- Search and filtering

### Augmented Reality
- ARKit/ARCore integration
- Spatial anchor management
- Equipment visualization in AR
- Real-time data overlay

### Data Synchronization
- Offline-first architecture
- Automatic sync when online
- Conflict resolution
- Retry logic with exponential backoff

## 🧪 Testing

### Running Tests
```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Test Structure
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test service interactions
- **E2E Tests**: Test complete user workflows

### Coverage Requirements
- Branches: 80%
- Functions: 80%
- Lines: 80%
- Statements: 80%

## 🔒 Security

### Data Protection
- Sensitive data stored in device keychain
- API communication over HTTPS
- Input validation and sanitization
- Secure token handling

### Permissions
- Camera access for photo capture
- Location access for AR features
- Storage access for offline data
- Network access for API communication

## 📊 Performance

### Optimization Strategies
- Lazy loading of screens and components
- Image optimization and caching
- Efficient database queries
- Memory management
- Battery optimization

### Monitoring
- Performance metrics tracking
- Error logging and reporting
- User analytics
- Crash reporting

## 🚀 Deployment

### Build Process
```bash
# Build for iOS
npm run build:ios

# Build for Android
npm run build:android

# Build for both platforms
npm run build
```

### App Store Preparation
- Update version numbers
- Generate app icons and splash screens
- Configure app permissions
- Test on physical devices
- Submit for review

## 🐛 Debugging

### Debug Tools
- React Native Debugger
- Flipper integration
- Console logging with structured data
- Error boundary components
- Performance profiling

### Common Issues
- **Metro bundler issues**: Clear cache with `npm start -- --reset-cache`
- **iOS build issues**: Clean build folder and reinstall pods
- **Android build issues**: Clean gradle cache and rebuild
- **Permission issues**: Check device settings and app permissions

## 📚 Resources

### Documentation
- [React Native Documentation](https://reactnative.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [React Navigation Documentation](https://reactnavigation.org/)

### Tools
- [React Native Debugger](https://github.com/jhen0409/react-native-debugger)
- [Flipper](https://fbflipper.com/)
- [React Native Performance](https://github.com/facebook/react-native-performance)

## 🤝 Contributing

### Code Review Process
1. Create feature branch
2. Implement changes with tests
3. Run linting and tests
4. Create pull request
5. Address review feedback
6. Merge to main

### Best Practices
- Write self-documenting code
- Add comments for complex logic
- Follow naming conventions
- Keep functions small and focused
- Use meaningful variable names

## 📞 Support

### Getting Help
- Check existing issues in the repository
- Create new issue with detailed description
- Include error logs and reproduction steps
- Provide device and OS information

### Contact
- Project maintainer: [Your Name]
- Email: [your-email@example.com]
- Slack: #arxos-mobile

---

**Happy Coding! 🎉**
