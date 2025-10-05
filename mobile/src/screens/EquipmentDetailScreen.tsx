/**
 * Equipment Detail Screen
 * Shows detailed information about a specific equipment item
 */

import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  Modal,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useRoute, useNavigation} from '@react-navigation/native';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {updateEquipmentStatus} from '@/store/slices/equipmentSlice';
import {Equipment, EquipmentStatusUpdate, EquipmentStatus} from '@/types/equipment';
import {cameraService} from '@/services/cameraService';
import {locationService} from '@/services/locationService';

export const EquipmentDetailScreen: React.FC = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const dispatch = useAppDispatch();
  const {user} = useAppSelector(state => state.auth);
  const {equipment} = useAppSelector(state => state.equipment);
  
  const {equipmentId} = route.params as {equipmentId: string};
  const [equipmentItem, setEquipmentItem] = useState<Equipment | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<EquipmentStatus>(EquipmentStatus.OPERATIONAL);
  const [note, setNote] = useState('');
  const [photos, setPhotos] = useState<string[]>([]);
  
  useEffect(() => {
    // Find equipment item
    const item = equipment.find(eq => eq.id === equipmentId);
    if (item) {
      setEquipmentItem(item);
      setSelectedStatus(item.status);
    }
  }, [equipment, equipmentId]);
  
  const handleStatusUpdate = async () => {
    if (!equipmentItem || !user) return;
    
    try {
      // Get current location
      const location = await locationService.getCurrentLocation();
      
      const update: EquipmentStatusUpdate = {
        equipmentId: equipmentItem.id,
        status: selectedStatus,
        notes: note,
        updatedBy: 'current_user', // TODO: Get from auth context
        updatedAt: new Date(),
      };
      
      await dispatch(updateEquipmentStatus(update));
      
      setShowStatusModal(false);
      setNote('');
      setPhotos([]);
      
      Alert.alert('Success', 'Equipment status updated successfully');
    } catch (error: any) {
      Alert.alert('Error', `Failed to update status: ${error.message}`);
    }
  };
  
  const handleTakePhoto = async () => {
    try {
      const photo = await cameraService.takePhoto();
      if (photo) {
        setPhotos(prev => [...prev, photo.uri]);
      }
    } catch (error: any) {
      Alert.alert('Error', `Failed to take photo: ${error.message}`);
    }
  };
  
  const handleSelectPhoto = async () => {
    try {
      const photo = await cameraService.selectFromGallery();
      if (photo) {
        setPhotos(prev => [...prev, photo.uri]);
      }
    } catch (error: any) {
      Alert.alert('Error', `Failed to select photo: ${error.message}`);
    }
  };
  
  const removePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };
  
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'normal':
        return '#4CAF50';
      case 'needs-repair':
        return '#FF9800';
      case 'failed':
        return '#F44336';
      case 'offline':
        return '#9E9E9E';
      case 'maintenance':
        return '#2196F3';
      default:
        return '#999999';
    }
  };
  
  if (!equipmentItem) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="error" size={64} color="#cccccc" />
          <Text style={styles.errorTitle}>Equipment Not Found</Text>
          <Text style={styles.errorSubtitle}>
            The equipment item you're looking for could not be found.
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.equipmentName}>{equipmentItem.name}</Text>
          <Text style={styles.equipmentType}>{equipmentItem.type}</Text>
          
          <View style={styles.statusContainer}>
            <View style={[styles.statusIndicator, {backgroundColor: getStatusColor(equipmentItem.status)}]} />
            <Text style={[styles.statusText, {color: getStatusColor(equipmentItem.status)}]}>
              {equipmentItem.status.toUpperCase()}
            </Text>
          </View>
        </View>
        
        {/* Location Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Location</Text>
          <View style={styles.infoRow}>
            <Icon name="location-on" size={20} color="#666666" />
            <Text style={styles.infoText}>
              {equipmentItem.floorId} - {equipmentItem.roomId}
            </Text>
          </View>
          {equipmentItem.location && (
            <View style={styles.infoRow}>
              <Icon name="place" size={20} color="#666666" />
              <Text style={styles.infoText}>
                {equipmentItem.location.x.toFixed(2)}, {equipmentItem.location.y.toFixed(2)}, {equipmentItem.location.z.toFixed(2)}
              </Text>
            </View>
          )}
        </View>
        
        {/* Specifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Specifications</Text>
          <View style={styles.infoRow}>
            <Icon name="info" size={20} color="#666666" />
            <Text style={styles.infoText}>Model: {equipmentItem.model || 'N/A'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Icon name="business" size={20} color="#666666" />
            <Text style={styles.infoText}>Manufacturer: {equipmentItem.manufacturer || 'N/A'}</Text>
          </View>
          <View style={styles.infoRow}>
            <Icon name="confirmation-number" size={20} color="#666666" />
            <Text style={styles.infoText}>Serial: N/A</Text>
          </View>
        </View>
        
        {/* Last Updated */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Last Updated</Text>
          <View style={styles.infoRow}>
            <Icon name="schedule" size={20} color="#666666" />
            <Text style={styles.infoText}>
              {equipmentItem.updatedAt.toLocaleString()}
            </Text>
          </View>
          <View style={styles.infoRow}>
            <Icon name="person" size={20} color="#666666" />
            <Text style={styles.infoText}>By: System</Text>
          </View>
        </View>
        
        {/* Notes */}
        {equipmentItem.maintenanceNotes && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Notes</Text>
            <Text style={styles.notesText}>{equipmentItem.maintenanceNotes}</Text>
          </View>
        )}
        
        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => setShowStatusModal(true)}
          >
            <Icon name="update" size={24} color="white" />
            <Text style={styles.actionButtonText}>Update Status</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.secondaryButton]}
            onPress={() => setShowNoteModal(true)}
          >
            <Icon name="note-add" size={24} color="#007AFF" />
            <Text style={[styles.actionButtonText, styles.secondaryButtonText]}>Add Note</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
      
      {/* Status Update Modal */}
      <Modal
        visible={showStatusModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowStatusModal(false)}>
              <Text style={styles.cancelButton}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Update Status</Text>
            <TouchableOpacity onPress={handleStatusUpdate}>
              <Text style={styles.saveButton}>Save</Text>
            </TouchableOpacity>
          </View>
          
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalSectionTitle}>Select Status</Text>
            {(['normal', 'needs-repair', 'failed', 'offline', 'maintenance'] as EquipmentStatus[]).map((status) => (
              <TouchableOpacity
                key={status}
                style={[
                  styles.statusOption,
                  selectedStatus === status && styles.selectedStatusOption,
                ]}
                onPress={() => setSelectedStatus(status)}
              >
                <View style={[styles.statusOptionIndicator, {backgroundColor: getStatusColor(status)}]} />
                <Text style={styles.statusOptionText}>{status.toUpperCase()}</Text>
              </TouchableOpacity>
            ))}
            
            <Text style={styles.modalSectionTitle}>Notes</Text>
            <TextInput
              style={styles.noteInput}
              placeholder="Add notes about the status update..."
              value={note}
              onChangeText={setNote}
              multiline
              numberOfLines={4}
            />
            
            <Text style={styles.modalSectionTitle}>Photos</Text>
            <View style={styles.photoActions}>
              <TouchableOpacity style={styles.photoButton} onPress={handleTakePhoto}>
                <Icon name="camera-alt" size={24} color="#007AFF" />
                <Text style={styles.photoButtonText}>Take Photo</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.photoButton} onPress={handleSelectPhoto}>
                <Icon name="photo-library" size={24} color="#007AFF" />
                <Text style={styles.photoButtonText}>Select Photo</Text>
              </TouchableOpacity>
            </View>
            
            {photos.map((photo, index) => (
              <View key={index} style={styles.photoItem}>
                <Text style={styles.photoText}>Photo {index + 1}</Text>
                <TouchableOpacity onPress={() => removePhoto(index)}>
                  <Icon name="close" size={20} color="#F44336" />
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        </SafeAreaView>
      </Modal>
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
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  equipmentName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  equipmentType: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 12,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  section: {
    backgroundColor: 'white',
    marginTop: 8,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#333333',
    marginLeft: 12,
  },
  notesText: {
    fontSize: 14,
    color: '#333333',
    lineHeight: 20,
  },
  actionsContainer: {
    flexDirection: 'row',
    padding: 20,
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
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
  saveButton: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: 'bold',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 20,
    marginBottom: 12,
  },
  statusOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#f5f5f5',
  },
  selectedStatusOption: {
    backgroundColor: '#e3f2fd',
  },
  statusOptionIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  statusOptionText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333333',
  },
  noteInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333333',
    textAlignVertical: 'top',
  },
  photoActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  photoButton: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  photoButtonText: {
    fontSize: 14,
    color: '#007AFF',
    marginTop: 4,
  },
  photoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginBottom: 8,
  },
  photoText: {
    fontSize: 14,
    color: '#333333',
  },
});
