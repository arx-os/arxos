/**
 * Equipment Screen
 * Equipment list with search, filter, and management capabilities
 */

import React, {useState, useEffect, useCallback, useMemo} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  RefreshControl,
  Alert,
  ActivityIndicator,
  Modal,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useNavigation} from '@react-navigation/native';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {fetchEquipment, searchEquipment} from '@/store/slices/equipmentSlice';
import {logger} from '../utils/logger';
import {errorHandler} from '../utils/errorHandler';

const {width} = Dimensions.get('window');

interface Equipment {
  id: string;
  name: string;
  type: string;
  status: 'normal' | 'needs-repair' | 'failed' | 'maintenance';
  location: {
    floorId: string;
    roomId: string;
  };
  lastMaintenance?: string;
  nextMaintenance?: string;
}

interface FilterOptions {
  status: string[];
  type: string[];
  floor: string[];
}

export const EquipmentScreen: React.FC = () => {
  const navigation = useNavigation();
  const dispatch = useAppDispatch();
  const {user} = useAppSelector(state => state.auth);
  const {equipment, isLoading, searchResults} = useAppSelector(state => state.equipment);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    status: [],
    type: [],
    floor: [],
  });
  const [sortBy, setSortBy] = useState<'name' | 'status' | 'location'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const displayData = useMemo(() => {
    const data = searchResults.length > 0 ? searchResults : equipment;
    
    // Apply filters
    let filtered = data.filter(item => {
      if (filters.status.length > 0 && !filters.status.includes(item.status)) {
        return false;
      }
      if (filters.type.length > 0 && !filters.type.includes(item.type)) {
        return false;
      }
      if (filters.floor.length > 0 && !filters.floor.includes(item.location.floorId)) {
        return false;
      }
      return true;
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: string;
      let bValue: string;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'location':
          aValue = `${a.location.floorId}-${a.location.roomId}`;
          bValue = `${b.location.floorId}-${b.location.roomId}`;
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }
      
      if (sortOrder === 'asc') {
        return aValue.localeCompare(bValue);
      } else {
        return bValue.localeCompare(aValue);
      }
    });
    
    return filtered;
  }, [equipment, searchResults, filters, sortBy, sortOrder]);

  useEffect(() => {
    if (user?.organizationId) {
      logger.info('Loading equipment data', {organizationId: user.organizationId}, 'EquipmentScreen');
      dispatch(fetchEquipment(user.organizationId));
    }
  }, [dispatch, user?.organizationId]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      if (user?.organizationId) {
        await dispatch(fetchEquipment(user.organizationId));
      }
    } catch (error) {
      logger.error('Refresh failed', error, 'EquipmentScreen');
      errorHandler.handleError(error, 'EquipmentScreen');
    } finally {
      setRefreshing(false);
    }
  }, [dispatch, user?.organizationId]);

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    
    if (query.trim().length > 0) {
      try {
        logger.info('Searching equipment', {query}, 'EquipmentScreen');
        await dispatch(searchEquipment({
          query: query.trim(),
          organizationId: user?.organizationId || '',
        }));
      } catch (error) {
        logger.error('Search failed', error, 'EquipmentScreen');
        errorHandler.handleError(error, 'EquipmentScreen');
      }
    }
  }, [dispatch, user?.organizationId]);

  const handleEquipmentPress = useCallback((equipment: Equipment) => {
    logger.info('Equipment selected', {equipmentId: equipment.id}, 'EquipmentScreen');
    navigation.navigate('EquipmentDetail' as never, {equipmentId: equipment.id});
  }, [navigation]);

  const handleFilterChange = useCallback((filterType: keyof FilterOptions, value: string) => {
    setFilters(prev => {
      const currentValues = prev[filterType];
      const newValues = currentValues.includes(value)
        ? currentValues.filter(v => v !== value)
        : [...currentValues, value];
      
      return {
        ...prev,
        [filterType]: newValues,
      };
    });
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      status: [],
      type: [],
      floor: [],
    });
    setSearchQuery('');
  }, []);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'normal':
        return '#4CAF50';
      case 'needs-repair':
        return '#FF9800';
      case 'failed':
        return '#F44336';
      case 'maintenance':
        return '#2196F3';
      default:
        return '#999999';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'normal':
        return 'check-circle';
      case 'needs-repair':
        return 'warning';
      case 'failed':
        return 'error';
      case 'maintenance':
        return 'build';
      default:
        return 'help';
    }
  };

  const renderEquipmentItem = ({item}: {item: Equipment}) => (
    <TouchableOpacity
      style={styles.equipmentItem}
      onPress={() => handleEquipmentPress(item)}>
      <View style={styles.equipmentHeader}>
        <View style={styles.equipmentInfo}>
          <Text style={styles.equipmentName}>{item.name}</Text>
          <Text style={styles.equipmentType}>{item.type}</Text>
        </View>
        <View style={styles.statusContainer}>
          <Icon
            name={getStatusIcon(item.status)}
            size={20}
            color={getStatusColor(item.status)}
          />
          <Text style={[styles.statusText, {color: getStatusColor(item.status)}]}>
            {item.status.replace('-', ' ').toUpperCase()}
          </Text>
        </View>
      </View>
      
      <View style={styles.equipmentDetails}>
        <View style={styles.locationContainer}>
          <Icon name="location-on" size={16} color="#666666" />
          <Text style={styles.locationText}>
            Floor {item.location.floorId}, Room {item.location.roomId}
          </Text>
        </View>
        
        {item.nextMaintenance && (
          <View style={styles.maintenanceContainer}>
            <Icon name="schedule" size={16} color="#666666" />
            <Text style={styles.maintenanceText}>
              Next: {new Date(item.nextMaintenance).toLocaleDateString()}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      presentationStyle="pageSheet">
      <SafeAreaView style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity onPress={() => setShowFilters(false)}>
            <Text style={styles.modalCancelText}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.modalTitle}>Filters</Text>
          <TouchableOpacity onPress={clearFilters}>
            <Text style={styles.modalClearText}>Clear</Text>
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          {/* Status Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Status</Text>
            {['normal', 'needs-repair', 'failed', 'maintenance'].map(status => (
              <TouchableOpacity
                key={status}
                style={styles.filterOption}
                onPress={() => handleFilterChange('status', status)}>
                <View style={styles.filterOptionContent}>
                  <Icon
                    name={getStatusIcon(status)}
                    size={20}
                    color={getStatusColor(status)}
                  />
                  <Text style={styles.filterOptionText}>
                    {status.replace('-', ' ').toUpperCase()}
                  </Text>
                </View>
                {filters.status.includes(status) && (
                  <Icon name="check" size={20} color="#007AFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
          
          {/* Type Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Type</Text>
            {Array.from(new Set(equipment.map(eq => eq.type))).map(type => (
              <TouchableOpacity
                key={type}
                style={styles.filterOption}
                onPress={() => handleFilterChange('type', type)}>
                <View style={styles.filterOptionContent}>
                  <Icon name="category" size={20} color="#666666" />
                  <Text style={styles.filterOptionText}>{type}</Text>
                </View>
                {filters.type.includes(type) && (
                  <Icon name="check" size={20} color="#007AFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
          
          {/* Floor Filter */}
          <View style={styles.filterSection}>
            <Text style={styles.filterSectionTitle}>Floor</Text>
            {Array.from(new Set(equipment.map(eq => eq.location.floorId))).map(floor => (
              <TouchableOpacity
                key={floor}
                style={styles.filterOption}
                onPress={() => handleFilterChange('floor', floor)}>
                <View style={styles.filterOptionContent}>
                  <Icon name="layers" size={20} color="#666666" />
                  <Text style={styles.filterOptionText}>Floor {floor}</Text>
                </View>
                {filters.floor.includes(floor) && (
                  <Icon name="check" size={20} color="#007AFF" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Icon name="build" size={64} color="#cccccc" />
      <Text style={styles.emptyStateTitle}>No Equipment Found</Text>
      <Text style={styles.emptyStateText}>
        {searchQuery ? 'Try adjusting your search or filters' : 'No equipment available'}
      </Text>
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#666666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search equipment..."
          value={searchQuery}
          onChangeText={handleSearch}
          placeholderTextColor="#999999"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => handleSearch('')}>
            <Icon name="clear" size={20} color="#666666" />
          </TouchableOpacity>
        )}
      </View>
      
      <View style={styles.headerActions}>
        <TouchableOpacity
          style={[styles.filterButton, Object.values(filters).some(f => f.length > 0) && styles.filterButtonActive]}
          onPress={() => setShowFilters(true)}>
          <Icon name="filter-list" size={20} color={Object.values(filters).some(f => f.length > 0) ? "#007AFF" : "#666666"} />
          {Object.values(filters).some(f => f.length > 0) && (
            <View style={styles.filterBadge}>
              <Text style={styles.filterBadgeText}>
                {Object.values(filters).reduce((sum, f) => sum + f.length, 0)}
              </Text>
            </View>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.sortButton}
          onPress={() => {
            const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
            setSortOrder(newOrder);
          }}>
          <Icon name={sortOrder === 'asc' ? 'arrow-upward' : 'arrow-downward'} size={20} color="#666666" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      
      {isLoading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading equipment...</Text>
        </View>
      ) : (
        <FlatList
          data={displayData}
          renderItem={renderEquipmentItem}
          keyExtractor={item => item.id}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={renderEmptyState}
          contentContainerStyle={styles.listContainer}
          showsVerticalScrollIndicator={false}
        />
      )}
      
      {renderFilterModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: 'white',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#333333',
  },
  headerActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  filterButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    marginRight: 8,
    borderRadius: 6,
    position: 'relative',
  },
  filterButtonActive: {
    backgroundColor: '#f0f8ff',
  },
  filterBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: '#FF3B30',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterBadgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  sortButton: {
    padding: 8,
    borderRadius: 6,
  },
  listContainer: {
    padding: 16,
  },
  equipmentItem: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  equipmentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  equipmentInfo: {
    flex: 1,
  },
  equipmentName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  equipmentType: {
    fontSize: 14,
    color: '#666666',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
    marginLeft: 4,
  },
  equipmentDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  locationText: {
    fontSize: 14,
    color: '#666666',
    marginLeft: 4,
  },
  maintenanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  maintenanceText: {
    fontSize: 12,
    color: '#666666',
    marginLeft: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666666',
    marginTop: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  modalCancelText: {
    fontSize: 16,
    color: '#666666',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
  },
  modalClearText: {
    fontSize: 16,
    color: '#007AFF',
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  filterSection: {
    marginBottom: 24,
  },
  filterSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 12,
  },
  filterOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 8,
  },
  filterOptionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  filterOptionText: {
    fontSize: 14,
    color: '#333333',
    marginLeft: 8,
  },
});