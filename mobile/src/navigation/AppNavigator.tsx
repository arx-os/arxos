/**
 * Main App Navigator
 * Handles navigation between different screens
 */

import React, {useEffect} from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createDrawerNavigator} from '@react-navigation/drawer';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {RootStackParamList} from '@/types/navigation';
import {useAppSelector} from '@/store/hooks';
import {authService} from '../services/authService';
import {logger} from '../utils/logger';
import {errorHandler} from '../utils/errorHandler';

// Import screens
import {HomeScreen} from '@/screens/HomeScreen';
import {EquipmentScreen} from '@/screens/EquipmentScreen';
import {EquipmentDetailScreen} from '@/screens/EquipmentDetailScreen';
import {ARScreen} from '@/screens/ARScreen';
import {CameraScreen} from '@/screens/CameraScreen';
import {SettingsScreen} from '@/screens/SettingsScreen';
import {LoginScreen} from '@/screens/LoginScreen';
import {ProfileScreen} from '@/screens/ProfileScreen';
import {SyncScreen} from '@/screens/SyncScreen';
import {OfflineScreen} from '@/screens/OfflineScreen';
import {LoadingScreen} from '@/screens/LoadingScreen';

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

// Tab Navigator
const TabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({route}) => ({
        tabBarIcon: ({focused, color, size}) => {
          let iconName: string;
          
          switch (route.name) {
            case 'Home':
              iconName = 'home';
              break;
            case 'Equipment':
              iconName = 'build';
              break;
            case 'AR':
              iconName = 'view-in-ar';
              break;
            case 'Camera':
              iconName = 'camera-alt';
              break;
            case 'Settings':
              iconName = 'settings';
              break;
            default:
              iconName = 'help';
          }
          
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: {
          backgroundColor: 'white',
          borderTopWidth: 1,
          borderTopColor: '#e0e0e0',
        },
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Home',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Equipment"
        component={EquipmentScreen}
        options={{
          title: 'Equipment',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="AR"
        component={ARScreen}
        options={{
          title: 'AR',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Camera"
        component={CameraScreen}
        options={{
          title: 'Camera',
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          headerShown: false,
        }}
      />
    </Tab.Navigator>
  );
};

// Drawer Navigator
const DrawerNavigator: React.FC = () => {
  return (
    <Drawer.Navigator
      screenOptions={{
        headerShown: false,
        drawerStyle: {
          backgroundColor: 'white',
          width: 280,
        },
        drawerActiveTintColor: '#007AFF',
        drawerInactiveTintColor: 'gray',
      }}
    >
      <Drawer.Screen
        name="Main"
        component={TabNavigator}
        options={{
          title: 'ArxOS Mobile',
          drawerIcon: ({color, size}) => (
            <Icon name="home" size={size} color={color} />
          ),
        }}
      />
      <Drawer.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
          drawerIcon: ({color, size}) => (
            <Icon name="person" size={size} color={color} />
          ),
        }}
      />
      <Drawer.Screen
        name="Sync"
        component={SyncScreen}
        options={{
          title: 'Sync Status',
          drawerIcon: ({color, size}) => (
            <Icon name="sync" size={size} color={color} />
          ),
        }}
      />
    </Drawer.Navigator>
  );
};

// Main App Navigator
export const AppNavigator: React.FC = () => {
  const {isAuthenticated, isLoading} = useAppSelector(state => state.auth);
  const {isOnline} = useAppSelector(state => state.sync);
  
  // Initialize authentication state on app start
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        logger.info('Initializing authentication state', {}, 'AppNavigator');
        await authService.initializeAuth();
      } catch (error) {
        logger.error('Failed to initialize authentication', error, 'AppNavigator');
        errorHandler.handleError(error, 'AppNavigator');
      }
    };

    initializeAuth();
  }, []);
  
  // Show loading screen while checking auth status
  if (isLoading) {
    return <LoadingScreen />;
  }
  
  // Show offline screen if not online
  if (!isOnline) {
    logger.info('App is offline, showing offline screen', {}, 'AppNavigator');
    return (
      <Stack.Navigator screenOptions={{headerShown: false}}>
        <Stack.Screen name="Offline" component={OfflineScreen} />
      </Stack.Navigator>
    );
  }
  
  // Show login screen if not authenticated
  if (!isAuthenticated) {
    logger.info('User not authenticated, showing login screen', {}, 'AppNavigator');
    return (
      <Stack.Navigator screenOptions={{headerShown: false}}>
        <Stack.Screen name="Login" component={LoginScreen} />
      </Stack.Navigator>
    );
  }
  
  // Show main app if authenticated
  logger.info('User authenticated, showing main app', {}, 'AppNavigator');
  return (
    <Stack.Navigator screenOptions={{headerShown: false}}>
      <Stack.Screen name="Main" component={DrawerNavigator} />
      <Stack.Screen
        name="EquipmentDetail"
        component={EquipmentDetailScreen}
        options={{
          title: 'Equipment Details',
          headerShown: true,
          headerBackTitle: 'Back',
        }}
      />
    </Stack.Navigator>
  );
};
