# Arxos Mobile AR Application

## Overview

React Native augmented reality application for visualizing and managing building equipment in physical space.

## Quick Start

```bash
# Install dependencies
npm install

# iOS setup
cd ios && pod install && cd ..

# Run on iOS
npm run ios

# Run on Android  
npm run android
```

## Project Structure

```
mobile/
├── src/
│   ├── App.tsx              # App entry point
│   ├── components/          # Reusable components
│   │   ├── ar/             # AR-specific components
│   │   ├── common/         # Common UI components
│   │   └── forms/          # Form components
│   ├── screens/            # Screen components
│   ├── services/           # API and business logic
│   │   ├── api/           # API client and endpoints
│   │   ├── ar/            # AR services
│   │   └── sync/          # Offline sync
│   ├── contexts/          # React contexts
│   ├── hooks/             # Custom hooks
│   ├── navigation/        # Navigation configuration
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
├── ios/                   # iOS native code
├── android/               # Android native code
└── package.json          # Dependencies

```

## Available Scripts

- `npm start` - Start Metro bundler
- `npm run ios` - Run on iOS simulator
- `npm run android` - Run on Android emulator
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run type-check` - Check TypeScript types

## Documentation

- [Setup Guide](../docs/MOBILE_SETUP.md)
- [AR Development](../docs/MOBILE_AR.md)
- [API Specification](../docs/AR_API_SPEC.md)
- [Database Schema](../docs/AR_DATABASE_SCHEMA.md)

## Requirements

- Node.js 18+
- React Native 0.72+
- iOS 14+ or Android API 24+
- Physical device for AR testing

## License

MIT