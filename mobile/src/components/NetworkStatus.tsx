/**
 * Network Status Component
 * Shows network connectivity status throughout the app
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import NetInfo from '@react-native-community/netinfo';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setOnlineStatus } from '@/store/slices/syncSlice';

export interface NetworkStatusProps {
  showOfflineOnly?: boolean;
  position?: 'top' | 'bottom';
  style?: any;
}

export const NetworkStatus: React.FC<NetworkStatusProps> = ({
  showOfflineOnly = true,
  position = 'top',
  style,
}) => {
  const dispatch = useAppDispatch();
  const { isOnline, pendingUpdates } = useAppSelector(state => state.sync);
  const [slideAnim] = useState(new Animated.Value(-100));
  const [showStatus, setShowStatus] = useState(false);

  useEffect(() => {
    // Listen for network changes
    const unsubscribe = NetInfo.addEventListener(state => {
      const online = state.isConnected || false;
      dispatch(setOnlineStatus(online));
      
      // Show status when going offline or when there are pending updates
      if (!online || (!showOfflineOnly && pendingUpdates > 0)) {
        setShowStatus(true);
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start();
      } else if (online && showOfflineOnly) {
        // Hide after a delay when back online
        setTimeout(() => {
          Animated.timing(slideAnim, {
            toValue: -100,
            duration: 300,
            useNativeDriver: true,
          }).start(() => setShowStatus(false));
        }, 2000);
      }
    });

    return unsubscribe;
  }, [dispatch, slideAnim, showOfflineOnly, pendingUpdates]);

  if (!showStatus && showOfflineOnly && isOnline) {
    return null;
  }

  const getStatusColor = () => {
    if (!isOnline) return '#F44336';
    if (pendingUpdates > 0) return '#FF9800';
    return '#4CAF50';
  };

  const getStatusIcon = () => {
    if (!isOnline) return 'wifi-off';
    if (pendingUpdates > 0) return 'sync';
    return 'wifi';
  };

  const getStatusText = () => {
    if (!isOnline) return 'You\'re offline';
    if (pendingUpdates > 0) return `${pendingUpdates} updates pending`;
    return 'Connected';
  };

  const getStatusSubtext = () => {
    if (!isOnline) return 'Some features may be limited';
    if (pendingUpdates > 0) return 'Updates will sync when online';
    return '';
  };

  return (
    <Animated.View
      style={[
        styles.container,
        position === 'top' ? styles.topPosition : styles.bottomPosition,
        { backgroundColor: getStatusColor() },
        { transform: [{ translateY: slideAnim }] },
        style,
      ]}
    >
      <View style={styles.content}>
        <Icon name={getStatusIcon()} size={20} color="white" />
        <View style={styles.textContainer}>
          <Text style={styles.statusText}>{getStatusText()}</Text>
          {getStatusSubtext() && (
            <Text style={styles.statusSubtext}>{getStatusSubtext()}</Text>
          )}
        </View>
        {!isOnline && (
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => {
              // Trigger network check
              NetInfo.fetch().then(state => {
                dispatch(setOnlineStatus(state.isConnected || false));
              });
            }}
          >
            <Icon name="refresh" size={16} color="white" />
          </TouchableOpacity>
        )}
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    zIndex: 1000,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  topPosition: {
    top: 0,
  },
  bottomPosition: {
    bottom: 0,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  textContainer: {
    flex: 1,
    marginLeft: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  statusSubtext: {
    color: 'white',
    fontSize: 12,
    opacity: 0.9,
    marginTop: 2,
  },
  retryButton: {
    padding: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
});
