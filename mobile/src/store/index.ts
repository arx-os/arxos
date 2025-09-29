/**
 * Redux Store Configuration
 * Centralized state management for ArxOS Mobile
 */

import {configureStore} from '@reduxjs/toolkit';
import {persistStore, persistReducer} from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {combineReducers} from '@reduxjs/toolkit';

// Import reducers
import authReducer from './slices/authSlice';
import equipmentReducer from './slices/equipmentSlice';
import syncReducer from './slices/syncSlice';
import arReducer from './slices/arSlice';
import settingsReducer from './slices/settingsSlice';

// Persist configuration
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'settings'], // Only persist auth and settings
  blacklist: ['sync', 'ar'], // Don't persist sync and AR state
};

// Root reducer
const rootReducer = combineReducers({
  auth: authReducer,
  equipment: equipmentReducer,
  sync: syncReducer,
  ar: arReducer,
  settings: settingsReducer,
});

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: __DEV__,
});

// Persistor
export const persistor = persistStore(store);

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Hooks
export {useAppDispatch, useAppSelector} from './hooks';
