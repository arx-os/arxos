/**
 * AR Screen
 * Augmented Reality interface for equipment visualization and interaction
 */

import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {initializeAR, startARSession, stopARSession, createSpatialAnchor} from '@/store/slices/arSlice';
import {SpatialAnchor} from '@/types/ar';
import {Equipment} from '@/types/equipment';
import {equipmentService} from '@/services/equipmentService';
import {AREquipmentOverlay} from '@/components/AR/AREquipmentOverlay';

export const ARScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const {isSupported, permissionGranted, sessionActive, detectedAnchors, selectedAnchor} = useAppSelector(state => state.ar);
  const [showEquipmentModal, setShowEquipmentModal] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null);
  const [isLoadingEquipment, setIsLoadingEquipment] = useState(false);
  
  useEffect(() => {
    // Initialize AR when component mounts
    initializeARService();
  }, []);

  useEffect(() => {
    // Load equipment when AR session starts
    if (sessionActive) {
      loadEquipmentData();
    }
  }, [sessionActive]);
  
  const initializeARService = async () => {
    setIsInitializing(true);
    try {
      await dispatch(initializeAR());
    } catch (error: any) {
      Alert.alert('AR Initialization Failed', error.message);
    } finally {
      setIsInitializing(false);
    }
  };

  const loadEquipmentData = async () => {
    setIsLoadingEquipment(true);
    try {
      // For demo purposes, we'll use a mock building ID
      // In a real app, this would come from navigation params or user selection
      const buildingId = 'demo-building-1';
      const equipmentData = await equipmentService.getEquipmentByBuilding(buildingId);
      setEquipment(equipmentData);
    } catch (error: any) {
      Alert.alert('Failed to Load Equipment', error.message);
    } finally {
      setIsLoadingEquipment(false);
    }
  };

  const handleEquipmentSelect = (equipmentId: string) => {
    const selected = equipment.find(eq => eq.id === equipmentId);
    setSelectedEquipment(selected || null);
    setShowEquipmentModal(true);
  };

  const handleEquipmentStatusUpdate = async (equipmentId: string, status: string) => {
    try {
      await equipmentService.updateEquipmentStatus({
        equipmentId,
        status,
        timestamp: new Date().toISOString(),
        technicianId: 'current-user', // This would come from auth
        notes: 'Status updated via AR',
      });
      
      // Update local state
      setEquipment(prev => prev.map(eq => 
        eq.id === equipmentId ? { ...eq, status } : eq
      ));
      
      Alert.alert('Success', 'Equipment status updated successfully');
    } catch (error: any) {
      Alert.alert('Update Failed', error.message);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'operational':
        return '#4CAF50';
      case 'needs_attention':
        return '#FF9800';
      case 'out_of_service':
        return '#F44336';
      default:
        return '#666666';
    }
  };
  
  const handleStartSession = async () => {
    try {
      await dispatch(startARSession({
        configuration: {
          planeDetection: true,
          lightEstimation: true,
          worldAlignment: 'gravity',
        },
        resetTracking: true,
        removeExistingAnchors: false,
      }));
    } catch (error: any) {
      Alert.alert('Failed to Start AR Session', error.message);
    }
  };
  
  const handleStopSession = async () => {
    try {
      await dispatch(stopARSession());
    } catch (error: any) {
      Alert.alert('Failed to Stop AR Session', error.message);
    }
  };
  
  const handleCreateAnchor = async () => {
    if (!selectedAnchor) {
      Alert.alert('No Equipment Selected', 'Please select an equipment item first');
      return;
    }
    
    try {
      // Create spatial anchor at current camera position
      await dispatch(createSpatialAnchor({
        equipmentId: selectedAnchor.equipmentId,
        position: {x: 0, y: 0, z: 0}, // TODO: Get actual camera position
        rotation: {x: 0, y: 0, z: 0, w: 1}, // TODO: Get actual camera rotation
      }));
      
      Alert.alert('Success', 'Spatial anchor created successfully');
    } catch (error: any) {
      Alert.alert('Failed to Create Anchor', error.message);
    }
  };
  
  const renderARView = () => {
    if (!isSupported) {
      return (
        <View style={styles.errorContainer}>
          <Icon name="error" size={64} color="#cccccc" />
          <Text style={styles.errorTitle}>AR Not Supported</Text>
          <Text style={styles.errorSubtitle}>
            Augmented Reality is not supported on this device.
          </Text>
        </View>
      );
    }
    
    if (!permissionGranted) {
      return (
        <View style={styles.errorContainer}>
          <Icon name="camera-alt" size={64} color="#cccccc" />
          <Text style={styles.errorTitle}>Camera Permission Required</Text>
          <Text style={styles.errorSubtitle}>
            Please grant camera permission to use AR features.
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={initializeARService}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }
    
    if (isInitializing) {
      return (
        <View style={styles.loadingContainer}>
          <Icon name="view-in-ar" size={64} color="#007AFF" />
          <Text style={styles.loadingTitle}>Initializing AR...</Text>
          <Text style={styles.loadingSubtitle}>Please wait while we set up the AR environment</Text>
        </View>
      );
    }
    
    if (!sessionActive) {
      return (
        <View style={styles.startContainer}>
          <Icon name="play-arrow" size={64} color="#007AFF" />
          <Text style={styles.startTitle}>Start AR Session</Text>
          <Text style={styles.startSubtitle}>
            Point your camera at equipment to visualize and interact with it
          </Text>
          <TouchableOpacity style={styles.startButton} onPress={handleStartSession}>
            <Text style={styles.startButtonText}>Start AR</Text>
          </TouchableOpacity>
        </View>
      );
    }
    
    return (
      <View style={styles.arContainer}>
        {/* AR Camera View would go here */}
        <View style={styles.arPlaceholder}>
          <Icon name="view-in-ar" size={128} color="#007AFF" />
          <Text style={styles.arPlaceholderText}>AR Camera View</Text>
          <Text style={styles.arPlaceholderSubtext}>
            This is where the AR camera feed would be displayed
          </Text>
          
          {/* Equipment Overlays */}
          {isLoadingEquipment ? (
            <View style={styles.loadingOverlay}>
              <Text style={styles.loadingText}>Loading equipment...</Text>
            </View>
          ) : (
            <View style={styles.equipmentOverlays}>
              {equipment.slice(0, 3).map((eq, index) => (
                <AREquipmentOverlay
                  key={eq.id}
                  equipment={{
                    id: eq.id,
                    name: eq.name,
                    type: eq.type,
                    status: eq.status,
                    position: { x: 0, y: 0, z: 0 }, // Mock position
                    metadata: {
                      lastMaintenance: eq.lastMaintenance,
                      nextMaintenance: eq.nextMaintenance,
                      specifications: eq.specifications,
                    }
                  }}
                  position={{ x: index * 50, y: 0, z: -100 }}
                  onStatusUpdate={handleEquipmentStatusUpdate}
                  onPositionUpdate={() => {}} // Mock function
                  onEquipmentSelect={handleEquipmentSelect}
                  isSelected={selectedEquipment?.id === eq.id}
                  scale={1.0}
                  opacity={1.0}
                />
              ))}
            </View>
          )}
        </View>
        
        {/* AR Controls */}
        <View style={styles.arControls}>
          <TouchableOpacity style={styles.controlButton} onPress={handleStopSession}>
            <Icon name="stop" size={24} color="white" />
            <Text style={styles.controlButtonText}>Stop AR</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.controlButton} onPress={handleCreateAnchor}>
            <Icon name="add" size={24} color="white" />
            <Text style={styles.controlButtonText}>Create Anchor</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.controlButton} onPress={() => setShowEquipmentModal(true)}>
            <Icon name="build" size={24} color="white" />
            <Text style={styles.controlButtonText}>Equipment</Text>
          </TouchableOpacity>
        </View>
        
        {/* Detected Anchors */}
        {detectedAnchors.length > 0 && (
          <View style={styles.anchorsContainer}>
            <Text style={styles.anchorsTitle}>Detected Anchors ({detectedAnchors.length})</Text>
            {detectedAnchors.map((anchor) => (
              <TouchableOpacity
                key={anchor.id}
                style={[
                  styles.anchorItem,
                  selectedAnchor?.id === anchor.id && styles.selectedAnchorItem,
                ]}
                onPress={() => {
                  // TODO: Set selected anchor
                }}
              >
                <Text style={styles.anchorText}>{anchor.equipmentId}</Text>
                <Text style={styles.anchorSubtext}>
                  Confidence: {(anchor.confidence * 100).toFixed(1)}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container}>
      {renderARView()}
      
      {/* Equipment Selection Modal */}
      <Modal
        visible={showEquipmentModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowEquipmentModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Equipment</Text>
            <View style={styles.placeholder} />
          </View>
          
          <View style={styles.modalContent}>
            <Text style={styles.modalSubtitle}>
              Select equipment to create spatial anchors for AR visualization
            </Text>
            
            {/* Equipment list would go here */}
            <View style={styles.equipmentList}>
              <Text style={styles.equipmentPlaceholder}>
                Equipment list would be displayed here
              </Text>
            </View>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    backgroundColor: 'white',
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  errorSubtitle: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    backgroundColor: 'white',
  },
  loadingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  loadingSubtitle: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 20,
  },
  startContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    backgroundColor: 'white',
  },
  startTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  startSubtitle: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  startButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  startButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  arContainer: {
    flex: 1,
  },
  arPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  arPlaceholderText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 16,
    marginBottom: 8,
  },
  arPlaceholderSubtext: {
    fontSize: 14,
    color: '#cccccc',
    textAlign: 'center',
    lineHeight: 20,
  },
  arControls: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  controlButton: {
    backgroundColor: 'rgba(0, 122, 255, 0.8)',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  controlButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  anchorsContainer: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    borderRadius: 8,
    padding: 12,
  },
  anchorsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
  },
  anchorItem: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 8,
    borderRadius: 4,
    marginBottom: 4,
  },
  selectedAnchorItem: {
    backgroundColor: 'rgba(0, 122, 255, 0.3)',
  },
  anchorText: {
    fontSize: 12,
    color: 'white',
    fontWeight: 'bold',
  },
  anchorSubtext: {
    fontSize: 10,
    color: '#cccccc',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  cancelButton: {
    fontSize: 16,
    color: '#007AFF',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
  },
  placeholder: {
    width: 50,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 20,
    lineHeight: 20,
  },
  equipmentList: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  equipmentPlaceholder: {
    fontSize: 14,
    color: '#999999',
    fontStyle: 'italic',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  equipmentOverlays: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  equipmentDetails: {
    padding: 20,
  },
  equipmentInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  equipmentLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
  },
  equipmentValue: {
    fontSize: 16,
    color: '#666666',
    flex: 1,
    textAlign: 'right',
  },
  statusButtons: {
    marginTop: 20,
    gap: 12,
  },
  statusButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  statusButtonGood: {
    backgroundColor: '#4CAF50',
  },
  statusButtonWarning: {
    backgroundColor: '#FF9800',
  },
  statusButtonError: {
    backgroundColor: '#F44336',
  },
  statusButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  equipmentItem: {
    padding: 16,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    marginBottom: 12,
  },
  equipmentItemName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  equipmentItemType: {
    fontSize: 14,
    color: '#666666',
    marginBottom: 4,
  },
  equipmentItemStatus: {
    fontSize: 14,
    fontWeight: 'bold',
  },
});
