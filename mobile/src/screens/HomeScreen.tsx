/**
 * Home Screen
 * Main dashboard showing equipment overview and quick actions
 */

import React, {useEffect, useCallback, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useNavigation} from '@react-navigation/native';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {fetchEquipment} from '@/store/slices/equipmentSlice';
import {syncData} from '@/store/slices/syncSlice';
import {Logger} from "../utils/logger";
import {errorHandler} from '../utils/errorHandler';

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation();
  const dispatch = useAppDispatch();
  const {user} = useAppSelector(state => state.auth);
  const {equipment, isLoading} = useAppSelector(state => state.equipment);
  const logger = new Logger('HomeScreen');
  const {isOnline, lastSync, pendingUpdates} = useAppSelector(state => state.sync);
  
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    // Load equipment data on mount
    if (user?.organizationId) {
      logger.info('Loading equipment data', {organizationId: user.organizationId});
      dispatch(fetchEquipment(user.organizationId));
    }
  }, [dispatch, user?.organizationId]);
  
  const handleSync = useCallback(async () => {
    try {
      logger.info('Manual sync triggered');
      await dispatch(syncData());
    } catch (error) {
      logger.error('Sync failed', error as Error);
      errorHandler.handleError(error as Error, 'HomeScreen');
      Alert.alert('Sync Failed', 'Failed to sync data. Please try again.');
    }
  }, [dispatch]);
  
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      if (user?.organizationId) {
        await dispatch(fetchEquipment(user.organizationId));
      }
      await dispatch(syncData());
    } catch (error) {
      logger.error('Refresh failed', error as Error);
      errorHandler.handleError(error as Error, 'HomeScreen');
    } finally {
      setRefreshing(false);
    }
  }, [dispatch, user?.organizationId]);
  
  const getStatusCount = (status: string) => {
    return equipment.filter(eq => eq.status === status).length;
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
      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.userName}>{user?.fullName || user?.username}</Text>
        </View>
        
        {/* Status Cards */}
        <View style={styles.statusContainer}>
          <View style={styles.statusCard}>
            <Icon name="check-circle" size={24} color="#4CAF50" />
            <Text style={styles.statusNumber}>{getStatusCount('normal')}</Text>
            <Text style={styles.statusLabel}>Normal</Text>
          </View>
          
          <View style={styles.statusCard}>
            <Icon name="warning" size={24} color="#FF9800" />
            <Text style={styles.statusNumber}>{getStatusCount('needs-repair')}</Text>
            <Text style={styles.statusLabel}>Needs Repair</Text>
          </View>
          
          <View style={styles.statusCard}>
            <Icon name="error" size={24} color="#F44336" />
            <Text style={styles.statusNumber}>{getStatusCount('failed')}</Text>
            <Text style={styles.statusLabel}>Failed</Text>
          </View>
        </View>
        
        {/* Quick Actions */}
        <View style={styles.actionsContainer}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('Equipment' as never)}
            >
              <Icon name="search" size={32} color="#007AFF" />
              <Text style={styles.actionLabel}>Search Equipment</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('AR' as never)}
            >
              <Icon name="view-in-ar" size={32} color="#007AFF" />
              <Text style={styles.actionLabel}>AR View</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => navigation.navigate('Camera' as never)}
            >
              <Icon name="camera-alt" size={32} color="#007AFF" />
              <Text style={styles.actionLabel}>Take Photo</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.actionButton}
              onPress={handleSync}
              disabled={!isOnline}
            >
              <Icon name="sync" size={32} color={isOnline ? "#007AFF" : "#999999"} />
              <Text style={[styles.actionLabel, !isOnline && styles.disabledText]}>
                Sync Data
              </Text>
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Sync Status */}
        <View style={styles.syncContainer}>
          <Text style={styles.sectionTitle}>Sync Status</Text>
          
          <View style={styles.syncInfo}>
            <View style={styles.syncRow}>
              <Text style={styles.syncLabel}>Status:</Text>
              <Text style={[styles.syncValue, {color: isOnline ? '#4CAF50' : '#F44336'}]}>
                {isOnline ? 'Online' : 'Offline'}
              </Text>
            </View>
            
            <View style={styles.syncRow}>
              <Text style={styles.syncLabel}>Last Sync:</Text>
              <Text style={styles.syncValue}>{getLastSyncText()}</Text>
            </View>
            
            <View style={styles.syncRow}>
              <Text style={styles.syncLabel}>Pending Updates:</Text>
              <Text style={styles.syncValue}>{pendingUpdates}</Text>
            </View>
          </View>
        </View>
        
        {/* Recent Equipment */}
        <View style={styles.recentContainer}>
          <Text style={styles.sectionTitle}>Recent Equipment</Text>
          
          {isLoading ? (
            <Text style={styles.loadingText}>Loading equipment...</Text>
          ) : equipment.length === 0 ? (
            <Text style={styles.emptyText}>No equipment found</Text>
          ) : (
            equipment.slice(0, 5).map((eq) => (
              <TouchableOpacity
                key={eq.id}
                style={styles.equipmentItem}
                onPress={() => (navigation as any).navigate('EquipmentDetail', {equipmentId: eq.id})}
              >
                <View style={styles.equipmentInfo}>
                  <Text style={styles.equipmentName}>{eq.name}</Text>
                  <Text style={styles.equipmentLocation}>
                    {eq.floorId || 'N/A'} - {eq.roomId || 'N/A'}
                  </Text>
                </View>
                <View style={styles.equipmentStatus}>
                  <Text style={[styles.statusText, {color: getStatusColor(eq.status)}]}>
                    {eq.status}
                  </Text>
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'normal':
      return '#4CAF50';
    case 'needs-repair':
      return '#FF9800';
    case 'failed':
      return '#F44336';
    default:
      return '#999999';
  }
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
    padding: 20,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  greeting: {
    fontSize: 16,
    color: '#666666',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 4,
  },
  statusContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-between',
  },
  statusCard: {
    flex: 1,
    backgroundColor: 'white',
    padding: 16,
    marginHorizontal: 4,
    borderRadius: 8,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statusNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 8,
  },
  statusLabel: {
    fontSize: 12,
    color: '#666666',
    marginTop: 4,
  },
  actionsContainer: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 16,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionButton: {
    width: '48%',
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionLabel: {
    fontSize: 14,
    color: '#333333',
    marginTop: 8,
    textAlign: 'center',
  },
  disabledText: {
    color: '#999999',
  },
  syncContainer: {
    padding: 20,
  },
  syncInfo: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  syncRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  syncLabel: {
    fontSize: 14,
    color: '#666666',
  },
  syncValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333333',
  },
  recentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingText: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  emptyText: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  equipmentItem: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  equipmentInfo: {
    flex: 1,
  },
  equipmentName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
  },
  equipmentLocation: {
    fontSize: 14,
    color: '#666666',
    marginTop: 2,
  },
  equipmentStatus: {
    alignItems: 'flex-end',
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
});
