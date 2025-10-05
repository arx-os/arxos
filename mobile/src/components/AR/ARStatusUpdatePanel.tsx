/**
 * AR Status Update Panel Component
 * Provides interface for updating equipment status in AR
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Modal,
  Alert,
  ScrollView,
} from 'react-native';
import { EquipmentStatus, EquipmentARMetadata } from '../../domain/AREntities';
import { Logger } from "../../utils/logger";

interface ARStatusUpdatePanelProps {
  equipment: {
    id: string;
    metadata: EquipmentARMetadata;
    currentStatus: EquipmentStatus;
  };
  onStatusUpdate: (equipmentId: string, status: EquipmentStatus, notes?: string) => Promise<void>;
  onClose: () => void;
  visible: boolean;
}

export const ARStatusUpdatePanel: React.FC<ARStatusUpdatePanelProps> = ({
  equipment,
  onStatusUpdate,
  onClose,
  visible,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<EquipmentStatus>(equipment.currentStatus);
  const [notes, setNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const logger = new Logger('ARStatusUpdatePanel');

  useEffect(() => {
    if (visible) {
      setSelectedStatus(equipment.currentStatus);
      setNotes('');
      setIsUpdating(false);
      setShowConfirmation(false);
    }
  }, [visible, equipment.currentStatus]);

  const handleStatusSelect = (status: EquipmentStatus) => {
    logger.info('Status selected', { equipmentId: equipment.id, status });
    setSelectedStatus(status);
  };

  const handleNotesChange = (text: string) => {
    setNotes(text);
  };

  const handleUpdatePress = () => {
    if (selectedStatus === equipment.currentStatus && !notes.trim()) {
      Alert.alert('No Changes', 'No changes to update.');
      return;
    }
    setShowConfirmation(true);
  };

  const handleConfirmUpdate = async () => {
    try {
      setIsUpdating(true);
      setShowConfirmation(false);
      
      logger.info('Updating equipment status', { 
        equipmentId: equipment.id, 
        newStatus: selectedStatus,
        hasNotes: !!notes.trim()
      });
      
      await onStatusUpdate(equipment.id, selectedStatus, notes.trim() || undefined);
      
      logger.info('Equipment status updated successfully', { equipmentId: equipment.id });
      
      Alert.alert('Success', 'Equipment status updated successfully.', [
        { text: 'OK', onPress: onClose }
      ]);
      
    } catch (error) {
      logger.error('Failed to update equipment status', { error, equipmentId: equipment.id });
      
      Alert.alert('Error', 'Failed to update equipment status. Please try again.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancel = () => {
    setShowConfirmation(false);
  };

  const getStatusColor = (status: EquipmentStatus): string => {
    switch (status) {
      case EquipmentStatus.OPERATIONAL:
        return '#00ff00';
      case EquipmentStatus.MAINTENANCE:
        return '#ffaa00';
      case EquipmentStatus.NEEDS_REPAIR:
        return '#ff6600';
      case EquipmentStatus.FAILED:
        return '#ff0000';
      case EquipmentStatus.OFFLINE:
        return '#666666';
      case EquipmentStatus.TESTING:
        return '#00aaff';
      case EquipmentStatus.STANDBY:
        return '#aa00ff';
      default:
        return '#ffffff';
    }
  };

  const getStatusIcon = (status: EquipmentStatus): string => {
    switch (status) {
      case EquipmentStatus.OPERATIONAL:
        return '✓';
      case EquipmentStatus.MAINTENANCE:
        return '🔧';
      case EquipmentStatus.NEEDS_REPAIR:
        return '⚠️';
      case EquipmentStatus.FAILED:
        return '❌';
      case EquipmentStatus.OFFLINE:
        return '⚫';
      case EquipmentStatus.TESTING:
        return '🧪';
      case EquipmentStatus.STANDBY:
        return '⏸️';
      default:
        return '❓';
    }
  };

  const getStatusDescription = (status: EquipmentStatus): string => {
    switch (status) {
      case EquipmentStatus.OPERATIONAL:
        return 'Equipment is functioning normally';
      case EquipmentStatus.MAINTENANCE:
        return 'Equipment is under maintenance';
      case EquipmentStatus.NEEDS_REPAIR:
        return 'Equipment needs repair';
      case EquipmentStatus.FAILED:
        return 'Equipment has failed';
      case EquipmentStatus.OFFLINE:
        return 'Equipment is offline';
      case EquipmentStatus.TESTING:
        return 'Equipment is being tested';
      case EquipmentStatus.STANDBY:
        return 'Equipment is on standby';
      default:
        return 'Unknown status';
    }
  };

  const getCriticalityColor = (criticality: string): string => {
    switch (criticality) {
      case 'critical':
        return '#ff0000';
      case 'high':
        return '#ff6600';
      case 'medium':
        return '#ffaa00';
      case 'low':
        return '#00ff00';
      default:
        return '#ffffff';
    }
  };

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="slide"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.panel}>
          <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
            {/* Header */}
            <View style={styles.header}>
              <Text style={styles.title}>Update Equipment Status</Text>
              <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            </View>

            {/* Equipment Info */}
            <View style={styles.equipmentInfo}>
              <Text style={styles.equipmentName}>{equipment.metadata.name}</Text>
              <Text style={styles.equipmentType}>{equipment.metadata.type}</Text>
              <Text style={styles.equipmentModel}>{equipment.metadata.model}</Text>
              
              <View style={styles.criticalityContainer}>
                <Text style={styles.criticalityLabel}>Criticality:</Text>
                <Text style={[
                  styles.criticalityValue,
                  { color: getCriticalityColor(equipment.metadata.criticality) }
                ]}>
                  {equipment.metadata.criticality.toUpperCase()}
                </Text>
              </View>

              <View style={styles.currentStatusContainer}>
                <Text style={styles.currentStatusLabel}>Current Status:</Text>
                <View style={[
                  styles.currentStatusBadge,
                  { backgroundColor: getStatusColor(equipment.currentStatus) }
                ]}>
                  <Text style={styles.currentStatusText}>
                    {getStatusIcon(equipment.currentStatus)} {equipment.currentStatus}
                  </Text>
                </View>
              </View>
            </View>

            {/* Status Selection */}
            <View style={styles.statusSelection}>
              <Text style={styles.sectionTitle}>Select New Status</Text>
              
              {Object.values(EquipmentStatus).map((status) => (
                <TouchableOpacity
                  key={status}
                  style={[
                    styles.statusOption,
                    {
                      backgroundColor: selectedStatus === status 
                        ? getStatusColor(status) 
                        : '#333333',
                      borderColor: selectedStatus === status 
                        ? getStatusColor(status) 
                        : '#555555',
                    },
                  ]}
                  onPress={() => handleStatusSelect(status)}
                  disabled={isUpdating}
                >
                  <Text style={styles.statusIcon}>
                    {getStatusIcon(status)}
                  </Text>
                  <View style={styles.statusTextContainer}>
                    <Text style={styles.statusName}>{status}</Text>
                    <Text style={styles.statusDescription}>
                      {getStatusDescription(status)}
                    </Text>
                  </View>
                  {selectedStatus === status && (
                    <Text style={styles.selectedIndicator}>✓</Text>
                  )}
                </TouchableOpacity>
              ))}
            </View>

            {/* Notes */}
            <View style={styles.notesSection}>
              <Text style={styles.sectionTitle}>Notes (Optional)</Text>
              <TextInput
                style={styles.notesInput}
                value={notes}
                onChangeText={handleNotesChange}
                placeholder="Add notes about the status change..."
                placeholderTextColor="#888888"
                multiline={true}
                numberOfLines={4}
                editable={!isUpdating}
              />
            </View>

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={onClose}
                disabled={isUpdating}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[
                  styles.updateButton,
                  {
                    backgroundColor: isUpdating ? '#666666' : '#007AFF',
                    opacity: isUpdating ? 0.6 : 1,
                  },
                ]}
                onPress={handleUpdatePress}
                disabled={isUpdating}
              >
                <Text style={styles.updateButtonText}>
                  {isUpdating ? 'Updating...' : 'Update Status'}
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>

        {/* Confirmation Modal */}
        {showConfirmation && (
          <View style={styles.confirmationOverlay}>
            <View style={styles.confirmationModal}>
              <Text style={styles.confirmationTitle}>Confirm Status Update</Text>
              
              <Text style={styles.confirmationText}>
                Are you sure you want to update the status of{' '}
                <Text style={styles.equipmentNameHighlight}>{equipment.metadata.name}</Text>{' '}
                from{' '}
                <Text style={styles.statusHighlight}>{equipment.currentStatus}</Text>{' '}
                to{' '}
                <Text style={styles.statusHighlight}>{selectedStatus}</Text>?
              </Text>
              
              {notes.trim() && (
                <View style={styles.notesPreview}>
                  <Text style={styles.notesPreviewLabel}>Notes:</Text>
                  <Text style={styles.notesPreviewText}>{notes}</Text>
                </View>
              )}
              
              <View style={styles.confirmationButtons}>
                <TouchableOpacity
                  style={styles.confirmCancelButton}
                  onPress={handleCancel}
                >
                  <Text style={styles.confirmCancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.confirmUpdateButton}
                  onPress={handleConfirmUpdate}
                >
                  <Text style={styles.confirmUpdateButtonText}>Confirm</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  panel: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
    minHeight: '60%',
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  closeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  equipmentInfo: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  equipmentName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 5,
  },
  equipmentType: {
    fontSize: 14,
    color: '#cccccc',
    marginBottom: 3,
  },
  equipmentModel: {
    fontSize: 12,
    color: '#aaaaaa',
    marginBottom: 10,
  },
  criticalityContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  criticalityLabel: {
    fontSize: 12,
    color: '#cccccc',
    marginRight: 8,
  },
  criticalityValue: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  currentStatusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  currentStatusLabel: {
    fontSize: 12,
    color: '#cccccc',
    marginRight: 8,
  },
  currentStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 5,
  },
  currentStatusText: {
    fontSize: 12,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  statusSelection: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 15,
  },
  statusOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 2,
  },
  statusIcon: {
    fontSize: 20,
    marginRight: 15,
  },
  statusTextContainer: {
    flex: 1,
  },
  statusName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 2,
  },
  statusDescription: {
    fontSize: 12,
    color: '#cccccc',
  },
  selectedIndicator: {
    fontSize: 20,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  notesSection: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333333',
  },
  notesInput: {
    backgroundColor: '#333333',
    borderRadius: 10,
    padding: 15,
    color: '#ffffff',
    fontSize: 14,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#555555',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 20,
    gap: 15,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 15,
    borderRadius: 10,
    backgroundColor: '#333333',
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  updateButton: {
    flex: 1,
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  updateButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  confirmationOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  confirmationModal: {
    backgroundColor: '#1a1a1a',
    borderRadius: 15,
    padding: 20,
    margin: 20,
    minWidth: '80%',
  },
  confirmationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 15,
    textAlign: 'center',
  },
  confirmationText: {
    fontSize: 14,
    color: '#cccccc',
    lineHeight: 20,
    marginBottom: 15,
  },
  equipmentNameHighlight: {
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statusHighlight: {
    fontWeight: 'bold',
    color: '#007AFF',
  },
  notesPreview: {
    backgroundColor: '#333333',
    borderRadius: 8,
    padding: 10,
    marginBottom: 15,
  },
  notesPreviewLabel: {
    fontSize: 12,
    color: '#aaaaaa',
    marginBottom: 5,
  },
  notesPreviewText: {
    fontSize: 12,
    color: '#cccccc',
  },
  confirmationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 15,
  },
  confirmCancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#333333',
    alignItems: 'center',
  },
  confirmCancelButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  confirmUpdateButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  confirmUpdateButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default ARStatusUpdatePanel;
