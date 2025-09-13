import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppNavigator } from './navigation/AppNavigator';
import { AuthProvider } from './contexts/AuthContext';
import { ARProvider } from './contexts/ARContext';

const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <AuthProvider>
          <ARProvider>
            <AppNavigator />
          </ARProvider>
        </AuthProvider>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;