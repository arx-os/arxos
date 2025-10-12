/**
 * Settings Screen
 * App configuration and preferences
 */

import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  setAREnabled,
  setAutoSync,
  setBiometricEnabled,
  setCameraQuality,
  setDebugMode,
  setLightEstimation,
  setPlaneDetection,
  setPushNotifications,
  setSyncInterval,
  setTheme,
} from '@/store/slices/settingsSlice';
import React from 'react';
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export const SettingsScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const settings = useAppSelector(state => state.settings);

  const handleThemeChange = (theme: 'light' | 'dark' | 'auto') => {
    dispatch(setTheme(theme));
  };

  const handleAutoSyncChange = (value: boolean) => {
    dispatch(setAutoSync(value));
  };

  const handleSyncIntervalChange = (interval: number) => {
    dispatch(setSyncInterval(interval));
  };

  const handleAREnabledChange = (value: boolean) => {
    dispatch(setAREnabled(value));
  };

  const handlePlaneDetectionChange = (value: boolean) => {
    dispatch(setPlaneDetection(value));
  };

  const handleLightEstimationChange = (value: boolean) => {
    dispatch(setLightEstimation(value));
  };

  const handleCameraQualityChange = (quality: 'low' | 'medium' | 'high') => {
    dispatch(setCameraQuality(quality));
  };

  const handleBiometricEnabledChange = (value: boolean) => {
    dispatch(setBiometricEnabled(value));
  };

  const handlePushNotificationsChange = (value: boolean) => {
    dispatch(setPushNotifications(value));
  };

  const handleDebugModeChange = (value: boolean) => {
    dispatch(setDebugMode(value));
  };

  const getSyncIntervalText = (interval: number) => {
    const minutes = interval / 60000;
    if (minutes < 60) {
      return `${minutes}m`;
    }
    const hours = minutes / 60;
    return `${hours}h`;
  };

  const renderSettingItem = (
    title: string,
    subtitle: string,
    icon: string,
    onPress?: () => void,
    rightComponent?: React.ReactNode
  ) => (
    <TouchableOpacity
      style={styles.settingItem}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingLeft}>
        <Icon name={icon} size={24} color="#666666" />
        <View style={styles.settingText}>
          <Text style={styles.settingTitle}>{title}</Text>
          <Text style={styles.settingSubtitle}>{subtitle}</Text>
        </View>
      </View>
      {rightComponent || (onPress && <Icon name="chevron-right" size={24} color="#cccccc" />)}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* App Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Settings</Text>

          {renderSettingItem(
            'Theme',
            'Choose your preferred theme',
            'palette',
            () => {
              // NOTE: Theme picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.theme}</Text>
          )}

          {renderSettingItem(
            'Language',
            'Select your language',
            'language',
            () => {
              // NOTE: Language picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.language}</Text>
          )}

          {renderSettingItem(
            'Font Size',
            'Adjust text size',
            'text-fields',
            () => {
              // NOTE: Font size picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.fontSize}</Text>
          )}
        </View>

        {/* Sync Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sync Settings</Text>

          {renderSettingItem(
            'Auto Sync',
            'Automatically sync data when online',
            'sync',
            undefined,
            <Switch
              value={settings.autoSync}
              onValueChange={handleAutoSyncChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.autoSync ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Sync Interval',
            'How often to sync data',
            'schedule',
            () => {
              // NOTE: Sync interval picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{getSyncIntervalText(settings.syncInterval)}</Text>
          )}

          {renderSettingItem(
            'Max Retries',
            'Maximum sync retry attempts',
            'refresh',
            () => {
              // NOTE: Retry count picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.maxRetries}</Text>
          )}
        </View>

        {/* AR Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AR Settings</Text>

          {renderSettingItem(
            'AR Enabled',
            'Enable augmented reality features',
            'view-in-ar',
            undefined,
            <Switch
              value={settings.arEnabled}
              onValueChange={handleAREnabledChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.arEnabled ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Plane Detection',
            'Detect horizontal and vertical planes',
            'layers',
            undefined,
            <Switch
              value={settings.planeDetection}
              onValueChange={handlePlaneDetectionChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.planeDetection ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Light Estimation',
            'Estimate lighting conditions',
            'lightbulb',
            undefined,
            <Switch
              value={settings.lightEstimation}
              onValueChange={handleLightEstimationChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.lightEstimation ? 'white' : '#f4f3f4'}
            />
          )}
        </View>

        {/* Camera Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Camera Settings</Text>

          {renderSettingItem(
            'Photo Quality',
            'Quality of captured photos',
            'camera-alt',
            () => {
              // NOTE: Photo quality picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.cameraQuality}</Text>
          )}

          {renderSettingItem(
            'Auto Focus',
            'Automatically focus camera',
            'center-focus-strong',
            undefined,
            <Switch
              value={settings.autoFocus}
              onValueChange={(value) => {
                // NOTE: Auto focus setting persistence - Future enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.autoFocus ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Flash Enabled',
            'Use flash when taking photos',
            'flash-on',
            undefined,
            <Switch
              value={settings.flashEnabled}
              onValueChange={(value) => {
                // NOTE: Flash setting persistence - Future enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.flashEnabled ? 'white' : '#f4f3f4'}
            />
          )}
        </View>

        {/* Security Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Security Settings</Text>

          {renderSettingItem(
            'Biometric Authentication',
            'Use fingerprint or face ID',
            'fingerprint',
            undefined,
            <Switch
              value={settings.biometricEnabled}
              onValueChange={handleBiometricEnabledChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.biometricEnabled ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Auto Lock Timeout',
            'Lock app after inactivity',
            'lock',
            () => {
              // NOTE: Network timeout picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.autoLockTimeout / 60000}m</Text>
          )}

          {renderSettingItem(
            'Require Password on Startup',
            'Ask for password when app starts',
            'security',
            undefined,
            <Switch
              value={settings.requirePasswordOnStartup}
              onValueChange={(value) => {
                // NOTE: Password on startup - Future security enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.requirePasswordOnStartup ? 'white' : '#f4f3f4'}
            />
          )}
        </View>

        {/* Notification Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notification Settings</Text>

          {renderSettingItem(
            'Push Notifications',
            'Receive push notifications',
            'notifications',
            undefined,
            <Switch
              value={settings.pushNotifications}
              onValueChange={handlePushNotificationsChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.pushNotifications ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Email Notifications',
            'Receive email notifications',
            'email',
            undefined,
            <Switch
              value={settings.emailNotifications}
              onValueChange={(value) => {
                // NOTE: Email notifications - Future enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.emailNotifications ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Sync Notifications',
            'Notify about sync status',
            'sync',
            undefined,
            <Switch
              value={settings.syncNotifications}
              onValueChange={(value) => {
                // NOTE: Sync notifications - Future enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.syncNotifications ? 'white' : '#f4f3f4'}
            />
          )}
        </View>

        {/* Debug Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Debug Settings</Text>

          {renderSettingItem(
            'Debug Mode',
            'Enable debug logging and features',
            'bug-report',
            undefined,
            <Switch
              value={settings.debugMode}
              onValueChange={handleDebugModeChange}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.debugMode ? 'white' : '#f4f3f4'}
            />
          )}

          {renderSettingItem(
            'Log Level',
            'Set logging verbosity',
            'assignment',
            () => {
              // NOTE: Log level picker modal - Future enhancement
            },
            <Text style={styles.settingValue}>{settings.logLevel}</Text>
          )}

          {renderSettingItem(
            'Performance Monitoring',
            'Monitor app performance',
            'speed',
            undefined,
            <Switch
              value={settings.performanceMonitoring}
              onValueChange={(value) => {
                // NOTE: Performance monitoring toggle - Future enhancement
              }}
              trackColor={{ false: '#e0e0e0', true: '#007AFF' }}
              thumbColor={settings.performanceMonitoring ? 'white' : '#f4f3f4'}
            />
          )}
        </View>

        {/* App Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Information</Text>

          {renderSettingItem(
            'Version',
            'App version and build',
            'info',
            () => {
              // NOTE: Version info modal - Future enhancement
            },
            <Text style={styles.settingValue}>0.1.0</Text>
          )}

          {renderSettingItem(
            'About',
            'Learn more about ArxOS',
            'help',
            () => {
              // TODO: Show about screen
            }
          )}

          {renderSettingItem(
            'Privacy Policy',
            'View privacy policy',
            'privacy-tip',
            () => {
              // TODO: Show privacy policy
            }
          )}

          {renderSettingItem(
            'Terms of Service',
            'View terms of service',
            'description',
            () => {
              // TODO: Show terms of service
            }
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: 'white',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    padding: 20,
    paddingBottom: 12,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 16,
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    color: '#333333',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#666666',
  },
  settingValue: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: 'bold',
  },
});
