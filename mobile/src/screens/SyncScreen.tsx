/**
 * Sync Screen
 * Shows synchronization status and allows manual sync
 */

import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {syncData, retryFailedSync, clearSyncErrors} from '@/store/slices/syncSlice';
import {SyncQueueItem} from '@/types/sync';

export const SyncScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const {isOnline, lastSync, pendingUpdates, syncInProgress, syncErrors, queue} = useAppSelector(state => state.sync);
  const [refreshing, setRefreshing] = useState(false);
  
  const handleManualSync = async () => {
    try {
      await dispatch(syncData());
    } catch (error: any) {
      Alert.alert('Sync Failed', error.message);
    }
  };
  
  const handleRetryFailed = async (itemId: string) => {
    try {
      await dispatch(retryFailedSync(itemId));
    } catch (error: any) {
      Alert.alert('Retry Failed', error.message);
    }
  };
  
  const handleClearErrors = async () => {
    try {
      await dispatch(clearSyncErrors());
    } catch (error: any) {
      Alert.alert('Clear Failed', error.message);
    }
  };
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await handleManualSync();
    setRefreshing(false);
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
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#4CAF50';
      case 'failed':
        return '#F44336';
      case 'processing':
        return '#FF9800';
      case 'pending':
        return '#2196F3';
      default:
        return '#999999';
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'failed':
        return 'error';
      case 'processing':
        return 'sync';
      case 'pending':
        return 'schedule';
      default:
        return 'help';
    }
  };
  
  const renderSyncStatus = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Sync Status</Text>
      
      <View style={styles.statusContainer}>
        <View style={styles.statusItem}>
          <Icon
            name={isOnline ? 'wifi' : 'wifi-off'}
            size={24}
            color={isOnline ? '#4CAF50' : '#F44336'}
          />
          <Text style={styles.statusLabel}>Connection</Text>
          <Text style={[styles.statusValue, {color: isOnline ? '#4CAF50' : '#F44336'}]}>
            {isOnline ? 'Online' : 'Offline'}
          </Text>
        </View>
        
        <View style={styles.statusItem}>
          <Icon
            name={syncInProgress ? 'sync' : 'sync-problem'}
            size={24}
            color={syncInProgress ? '#FF9800' : '#4CAF50'}
          />
          <Text style={styles.statusLabel}>Sync Status</Text>
          <Text style={[styles.statusValue, {color: syncInProgress ? '#FF9800' : '#4CAF50'}]}>
            {syncInProgress ? 'In Progress' : 'Idle'}
          </Text>
        </View>
        
        <View style={styles.statusItem}>
          <Icon name="schedule" size={24} color="#666666" />
          <Text style={styles.statusLabel}>Last Sync</Text>
          <Text style={styles.statusValue}>{getLastSyncText()}</Text>
        </View>
        
        <View style={styles.statusItem}>
          <Icon name="pending" size={24} color="#2196F3" />
          <Text style={styles.statusLabel}>Pending</Text>
          <Text style={styles.statusValue}>{pendingUpdates}</Text>
        </View>
      </View>
    </View>
  );
  
  const renderSyncActions = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Sync Actions</Text>
      
      <TouchableOpacity
        style={[styles.actionButton, syncInProgress && styles.actionButtonDisabled]}
        onPress={handleManualSync}
        disabled={syncInProgress || !isOnline}
      >
        <Icon name="sync" size={24} color="white" />
        <Text style={styles.actionButtonText}>
          {syncInProgress ? 'Syncing...' : 'Sync Now'}
        </Text>
      </TouchableOpacity>
      
      {syncErrors.length > 0 && (
        <TouchableOpacity
          style={[styles.actionButton, styles.secondaryButton]}
          onPress={handleClearErrors}
        >
          <Icon name="clear" size={24} color="#007AFF" />
          <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>
            Clear Errors
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
  
  const renderSyncQueue = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Sync Queue ({queue.length})</Text>
      
      {queue.length === 0 ? (
        <View style={styles.emptyQueue}>
          <Icon name="check-circle" size={64} color="#4CAF50" />
          <Text style={styles.emptyQueueText}>All synced!</Text>
          <Text style={styles.emptyQueueSubtext}>
            No pending items in sync queue
          </Text>
        </View>
      ) : (
        <View style={styles.queueList}>
          {queue.map((item: SyncQueueItem) => (
            <View key={item.id} style={styles.queueItem}>
              <View style={styles.queueItemLeft}>
                <Icon
                  name={getStatusIcon(item.status)}
                  size={20}
                  color={getStatusColor(item.status)}
                />
                <View style={styles.queueItemText}>
                  <Text style={styles.queueItemTitle}>
                    {item.type.replace('_', ' ').toUpperCase()}
                  </Text>
                  <Text style={styles.queueItemSubtitle}>
                    Created: {new Date(item.createdAt).toLocaleString()}
                  </Text>
                  {item.error && (
                    <Text style={styles.queueItemError}>
                      Error: {item.error}
                    </Text>
                  )}
                </View>
              </View>
              
              {item.status === 'failed' && (
                <TouchableOpacity
                  style={styles.retryButton}
                  onPress={() => handleRetryFailed(item.id)}
                >
                  <Icon name="refresh" size={16} color="#007AFF" />
                </TouchableOpacity>
              )}
            </View>
          ))}
        </View>
      )}
    </View>
  );
  
  const renderSyncErrors = () => {
    if (syncErrors.length === 0) return null;
    
    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Sync Errors ({syncErrors.length})</Text>
        
        <View style={styles.errorsList}>
          {syncErrors.map((error, index) => (
            <View key={index} style={styles.errorItem}>
              <Icon name="error" size={20} color="#F44336" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ))}
        </View>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            colors={['#007AFF']}
            tintColor="#007AFF"
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderSyncStatus()}
        {renderSyncActions()}
        {renderSyncQueue()}
        {renderSyncErrors()}
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
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    padding: 20,
    paddingBottom: 12,
  },
  statusContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 20,
    paddingTop: 0,
  },
  statusItem: {
    width: '50%',
    alignItems: 'center',
    paddingVertical: 16,
  },
  statusLabel: {
    fontSize: 12,
    color: '#666666',
    marginTop: 8,
    marginBottom: 4,
  },
  statusValue: {
    fontSize: 14,
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
  emptyQueue: {
    alignItems: 'center',
    padding: 40,
  },
  emptyQueueText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyQueueSubtext: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
  },
  queueList: {
    padding: 20,
    paddingTop: 0,
  },
  queueItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  queueItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  queueItemText: {
    marginLeft: 12,
    flex: 1,
  },
  queueItemTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 2,
  },
  queueItemSubtitle: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 2,
  },
  queueItemError: {
    fontSize: 12,
    color: '#F44336',
  },
  retryButton: {
    padding: 8,
  },
  errorsList: {
    padding: 20,
    paddingTop: 0,
  },
  errorItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  errorText: {
    fontSize: 14,
    color: '#F44336',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
});
