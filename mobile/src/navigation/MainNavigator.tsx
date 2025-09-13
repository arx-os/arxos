import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { HomeScreen } from '../screens/main/HomeScreen';
import { BuildingListScreen } from '../screens/main/BuildingListScreen';
import { ARViewScreen } from '../screens/ar/ARViewScreen';
import { SettingsScreen } from '../screens/main/SettingsScreen';

export type MainStackParamList = {
  Home: undefined;
  BuildingList: undefined;
  ARView: { floorPlanId?: string };
  Settings: undefined;
};

const Stack = createStackNavigator<MainStackParamList>();

export const MainNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      initialRouteName="Home"
      screenOptions={{
        headerStyle: {
          backgroundColor: '#4A90E2',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Stack.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ title: 'ArxOS' }}
      />
      <Stack.Screen 
        name="BuildingList" 
        component={BuildingListScreen}
        options={{ title: 'Buildings' }}
      />
      <Stack.Screen 
        name="ARView" 
        component={ARViewScreen}
        options={{ 
          title: 'AR View',
          headerShown: false
        }}
      />
      <Stack.Screen 
        name="Settings" 
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Stack.Navigator>
  );
};