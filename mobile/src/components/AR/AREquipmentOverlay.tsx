/**
 * AR Equipment Overlay Component
 * Renders equipment overlays in AR scene with interactive capabilities
 */

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Animated } from 'react-native';
import { EquipmentAROverlay, EquipmentStatus } from '../../domain/AREntities';
import { Vector3 } from '../../types/SpatialTypes';
import { Logger } from '../../utils/Logger';

interface AREquipmentOverlayProps {
  equipment: EquipmentAROverlay;
  position: Vector3;
  onStatusUpdate: (equipmentId: string, status: EquipmentStatus) => void;
  onPositionUpdate: (equipmentId: string, position: Vector3) => void;
  onEquipmentSelect: (equipmentId: string) => void;
  isSelected: boolean;
  scale: number;
  opacity: number;
}

export const AREquipmentOverlay: React.FC<AREquipmentOverlayProps> = ({
  equipment,
  position,
  onStatusUpdate,
  onPositionUpdate,
  onEquipmentSelect,
  isSelected,
  scale = 1.0,
  opacity = 1.0
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const logger = useRef(new Logger('AREquipmentOverlay')).current;

  useEffect(() => {
    // Start pulse animation for selected equipment
    if (isSelected) {
      startPulseAnimation();
    } else {
      stopPulseAnimation();
    }
  }, [isSelected]);

  useEffect(() => {
    // Update position when equipment position changes
    if (equipment.position.x !== position.x || 
        equipment.position.y !== position.y || 
        equipment.position.z !== position.z) {
      onPositionUpdate(equipment.equipmentId, position);
    }
  }, [position, equipment.position]);

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.2,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1.0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopPulseAnimation = () => {
    pulseAnim.stopAnimation();
    pulseAnim.setValue(1.0);
  };

  const handleEquipmentPress = () => {
    logger.info('Equipment pressed in AR', { equipmentId: equipment.equipmentId });
    onEquipmentSelect(equipment.equipmentId);
    setIsExpanded(!isExpanded);
  };

  const handleStatusUpdate = async (newStatus: EquipmentStatus) => {
    try {
      setIsUpdating(true);
      logger.info('Updating equipment status via AR', { 
        equipmentId: equipment.equipmentId, 
        newStatus 
      });
      
      await onStatusUpdate(equipment.equipmentId, newStatus);
      
      logger.info('Equipment status updated successfully', { 
        equipmentId: equipment.equipmentId, 
        newStatus 
      });
    } catch (error) {
      logger.error('Failed to update equipment status', { 
        error, 
        equipmentId: equipment.equipmentId 
      });
    } finally {
      setIsUpdating(false);
    }
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

  const getModelTypeIcon = (modelType: string): string => {
    switch (modelType) {
      case '3D':
        return '📦';
      case '2D':
        return '📄';
      case 'icon':
        return '🏷️';
      default:
        return '❓';
    }
  };

  return (
    <View style={styles.container}>
      {/* Equipment 3D Model/Icon */}
      <Animated.View
        style={[
          styles.equipmentModel,
          {
            transform: [{ scale: isSelected ? pulseAnim : scale }],
            opacity: opacity,
            backgroundColor: getStatusColor(equipment.status),
          },
        ]}
      >
        <TouchableOpacity
          style={styles.equipmentButton}
          onPress={handleEquipmentPress}
          disabled={isUpdating}
        >
          <Text style={styles.modelTypeIcon}>
            {getModelTypeIcon(equipment.modelType)}
          </Text>
          <Text style={styles.statusIcon}>
            {getStatusIcon(equipment.status)}
          </Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Equipment Info Panel */}
      {isExpanded && (
        <View style={styles.infoPanel}>
          <View style={styles.equipmentInfo}>
            <Text style={styles.equipmentName}>{equipment.metadata.name}</Text>
            <Text style={styles.equipmentType}>{equipment.metadata.type}</Text>
            <Text style={styles.equipmentModel}>{equipment.metadata.model}</Text>
            
            {equipment.metadata.manufacturer && (
              <Text style={styles.equipmentManufacturer}>
                {equipment.metadata.manufacturer}
              </Text>
            )}
            
            <Text style={styles.criticality}>
              Criticality: {equipment.metadata.criticality.toUpperCase()}
            </Text>
          </View>

          {/* Status Update Controls */}
          <View style={styles.statusControls}>
            <Text style={styles.statusLabel}>Update Status:</Text>
            
            <View style={styles.statusButtons}>
              {Object.values(EquipmentStatus).map((status) => (
                <TouchableOpacity
                  key={status}
                  style={[
                    styles.statusButton,
                    {
                      backgroundColor: equipment.status === status 
                        ? getStatusColor(status) 
                        : '#333333',
                    },
                  ]}
                  onPress={() => handleStatusUpdate(status)}
                  disabled={isUpdating || equipment.status === status}
                >
                  <Text style={styles.statusButtonText}>
                    {getStatusIcon(status)} {status}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* AR Visibility Info */}
          <View style={styles.visibilityInfo}>
            <Text style={styles.visibilityLabel}>AR Visibility:</Text>
            <Text style={styles.visibilityText}>
              Distance: {equipment.arVisibility.distance.toFixed(1)}m
            </Text>
            <Text style={styles.visibilityText}>
              Lighting: {equipment.arVisibility.lightingCondition}
            </Text>
            <Text style={styles.visibilityText}>
              Contrast: {(equipment.arVisibility.contrast * 100).toFixed(0)}%
            </Text>
          </View>

          {/* Last Updated */}
          <Text style={styles.lastUpdated}>
            Last Updated: {equipment.lastUpdated.toLocaleString()}
          </Text>
        </View>
      )}

      {/* Loading Indicator */}
      {isUpdating && (
        <View style={styles.loadingOverlay}>
          <Text style={styles.loadingText}>Updating...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  equipmentModel: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  equipmentButton: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modelTypeIcon: {
    fontSize: 20,
    color: '#ffffff',
  },
  statusIcon: {
    fontSize: 12,
    color: '#ffffff',
    marginTop: 2,
  },
  infoPanel: {
    position: 'absolute',
    top: 70,
    width: 250,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  equipmentInfo: {
    marginBottom: 15,
  },
  equipmentName: {
    fontSize: 16,
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
    marginBottom: 3,
  },
  equipmentManufacturer: {
    fontSize: 12,
    color: '#aaaaaa',
    marginBottom: 5,
  },
  criticality: {
    fontSize: 12,
    color: '#ffaa00',
    fontWeight: 'bold',
  },
  statusControls: {
    marginBottom: 15,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  statusButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  statusButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 5,
    marginRight: 5,
    marginBottom: 5,
  },
  statusButtonText: {
    fontSize: 10,
    color: '#ffffff',
    fontWeight: 'bold',
  },
  visibilityInfo: {
    marginBottom: 10,
  },
  visibilityLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 5,
  },
  visibilityText: {
    fontSize: 10,
    color: '#cccccc',
    marginBottom: 2,
  },
  lastUpdated: {
    fontSize: 10,
    color: '#aaaaaa',
    fontStyle: 'italic',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 30,
  },
  loadingText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default AREquipmentOverlay;
