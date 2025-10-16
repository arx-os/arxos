/**
 * Offline Screen
 * Shows when the app is offline and provides offline functionality
 */

import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ScrollView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import NetInfo from '@react-native-community/netinfo';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {setOnlineStatus, syncQueue, loadSyncQueue} from '@/store/slices/syncSlice';

export const OfflineScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const {pendingUpdates, lastSync} = useAppSelector(state => state.sync);
  const [isCheckingConnection, setIsCheckingConnection] = useState(false);
  
  useEffect(() => {
    // Load sync queue on mount
    dispatch(loadSyncQueue());
    
    // Listen for network changes
    const unsubscribe = NetInfo.addEventListener(state => {
      dispatch(setOnlineStatus(state.isConnected || false));
    });
    
    return unsubscribe;
  }, [dispatch]);
  
  const handleCheckConnection = async () => {
    setIsCheckingConnection(true);
    try {
      const netInfo = await NetInfo.fetch();
      dispatch(setOnlineStatus(netInfo.isConnected || false));
      
      if (netInfo.isConnected) {
        Alert.alert('Connection Restored', 'You are now back online!');
      } else {
        Alert.alert('Still Offline', 'Please check your internet connection.');
      }
    } catch (error) {
      Alert.alert('Connection Check Failed', 'Unable to check connection status.');
    } finally {
      setIsCheckingConnection(false);
    }
  };
  
  const handleRetrySync = async () => {
    Alert.alert(
      'Retry Sync',
      'This will attempt to sync your data when you are back online.',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Retry',
          onPress: async () => {
            try {
              await dispatch(syncQueue());
              Alert.alert('Sync Complete', 'Your data has been synced successfully.');
            } catch (error: any) {
              Alert.alert('Sync Failed', error.message || 'Failed to sync data.');
            }
          },
        },
      ]
    );
  };
  
  const handleViewPendingUpdates = () => {
    Alert.alert(
      'Pending Updates',
      `You have ${pendingUpdates} pending updates that will sync when you are back online.`,
      [{text: 'OK'}]
    );
  };
  
  const getLastSyncText = () => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Icon name="wifi-off" size={64} color="#F44336" />
          <Text style={styles.title}>You're Offline</Text>
          <Text style={styles.subtitle}>
            Don't worry, you can still use the app. Your changes will sync when you're back online.
          </Text>
        </View>
        
        {/* Connection Status */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Connection Status</Text>
          
          <View style={styles.statusItem}>
            <Icon name="wifi-off" size={24} color="#F44336" />
            <View style={styles.statusText}>
              <Text style={styles.statusLabel}>Internet Connection</Text>
              <Text style={styles.statusValue}>Offline</Text>
            </View>
          </View>
          
          <View style={styles.statusItem}>
            <Icon name="sync" size={24} color="#FF9800" />
            <View style={styles.statusText}>
              <Text style={styles.statusLabel}>Sync Status</Text>
              <Text style={styles.statusValue}>Paused</Text>
            </View>
          </View>
          
          <View style={styles.statusItem}>
            <Icon name="schedule" size={24} color="#666666" />
            <View style={styles.statusText}>
              <Text style={styles.statusLabel}>Last Sync</Text>
              <Text style={styles.statusValue}>{getLastSyncText()}</Text>
            </View>
          </View>
          
          <View style={styles.statusItem}>
            <Icon name="pending" size={24} color="#2196F3" />
            <View style={styles.statusText}>
              <Text style={styles.statusLabel}>Pending Updates</Text>
              <Text style={styles.statusValue}>{pendingUpdates}</Text>
            </View>
          </View>
        </View>
        
        {/* Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Actions</Text>
          
          <TouchableOpacity
            style={[styles.actionButton, isCheckingConnection && styles.actionButtonDisabled]}
            onPress={handleCheckConnection}
            disabled={isCheckingConnection}
          >
            <Icon name="refresh" size={24} color="white" />
            <Text style={styles.actionButtonText}>
              {isCheckingConnection ? 'Checking...' : 'Check Connection'}
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={handleRetrySync}
          >
            <Icon name="sync" size={24} color="#007AFF" />
            <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
              Retry Sync
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={handleViewPendingUpdates}
          >
            <Icon name="list" size={24} color="#007AFF" />
            <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
              View Pending Updates
            </Text>
          </TouchableOpacity>
        </View>
        
        {/* Offline Features */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Available Offline</Text>
          
          <View style={styles.featureItem}>
            <Icon name="build" size={24} color="#4CAF50" />
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>View Equipment</Text>
              <Text style={styles.featureSubtitle}>
                Browse and view equipment information
              </Text>
            </View>
          </View>
          
          <View style={styles.featureItem}>
            <Icon name="camera-alt" size={24} color="#4CAF50" />
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Take Photos</Text>
              <Text style={styles.featureSubtitle}>
                Capture photos for equipment documentation
              </Text>
            </View>
          </View>
          
          <View style={styles.featureItem}>
            <Icon name="note-add" size={24} color="#4CAF50" />
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Add Notes</Text>
              <Text style={styles.featureSubtitle}>
                Add notes and comments to equipment
              </Text>
            </View>
          </View>
          
          <View style={styles.featureItem}>
            <Icon name="update" size={24} color="#4CAF50" />
            <View style={styles.featureText}>
              <Text style={styles.featureTitle}>Update Status</Text>
              <Text style={styles.featureSubtitle}>
                Update equipment status and information
              </Text>
            </View>
          </View>
        </View>
        
        {/* Tips */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Tips</Text>
          
          <View style={styles.tipItem}>
            <Icon name="lightbulb" size={20} color="#FF9800" />
            <Text style={styles.tipText}>
              Your changes are saved locally and will sync automatically when you're back online.
            </Text>
          </View>
          
          <View style={styles.tipItem}>
            <Icon name="lightbulb" size={20} color="#FF9800" />
            <Text style={styles.tipText}>
              You can continue working offline. All your data is safely stored on your device.
            </Text>
          </View>
          
          <View style={styles.tipItem}>
            <Icon name="lightbulb" size={20} color="#FF9800" />
            <Text style={styles.tipText}>
              Check your internet connection and try again. The app will automatically reconnect when available.
            </Text>
          </View>
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
  header: {
    backgroundColor: 'white',
    alignItems: 'center',
    padding: 40,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 24,
  },
  section: {
    backgroundColor: 'white',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    padding: 20,
    paddingBottom: 12,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  statusText: {
    marginLeft: 16,
    flex: 1,
  },
  statusLabel: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 2,
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
  },
  actionButton: {
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    margin: 20,
    marginTop: 0,
    borderRadius: 8,
  },
  actionButtonDisabled: {
    backgroundColor: '#cccccc',
  },
  secondaryButton: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  secondaryButtonText: {
    color: '#007AFF',
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  featureText: {
    marginLeft: 16,
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    color: '#333333',
    marginBottom: 2,
  },
  featureSubtitle: {
    fontSize: 14,
    color: '#666666',
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  tipText: {
    fontSize: 14,
    color: '#666666',
    marginLeft: 16,
    flex: 1,
    lineHeight: 20,
  },
});
