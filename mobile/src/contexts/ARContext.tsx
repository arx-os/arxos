import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Platform, Alert } from 'react-native';
import apiClient from '../services/api/client';

interface ARContextType {
  isARSupported: boolean;
  isAREnabled: boolean;
  currentFloorPlan: any | null;
  arObjects: any[];
  enableAR: () => Promise<void>;
  disableAR: () => void;
  loadFloorPlan: (floorPlanId: string) => Promise<void>;
  addARObject: (object: any) => void;
  removeARObject: (objectId: string) => void;
  isLoading: boolean;
  error: string | null;
}

const ARContext = createContext<ARContextType | undefined>(undefined);

interface ARProviderProps {
  children: ReactNode;
}

export const ARProvider: React.FC<ARProviderProps> = ({ children }) => {
  const [isARSupported, setIsARSupported] = useState(false);
  const [isAREnabled, setIsAREnabled] = useState(false);
  const [currentFloorPlan, setCurrentFloorPlan] = useState(null);
  const [arObjects, setArObjects] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkARSupport();
  }, []);

  const checkARSupport = async () => {
    try {
      // Check if platform supports AR
      if (Platform.OS === 'ios') {
        // Check for ARKit support (iOS 11+)
        setIsARSupported(true);
      } else if (Platform.OS === 'android') {
        // Check for ARCore support
        setIsARSupported(true);
      } else {
        setIsARSupported(false);
      }
    } catch (err) {
      console.error('Error checking AR support:', err);
      setIsARSupported(false);
    }
  };

  const enableAR = async (): Promise<void> => {
    if (!isARSupported) {
      throw new Error('AR is not supported on this device');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Initialize AR session
      // Request camera permissions
      // Set up AR scene
      setIsAREnabled(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enable AR';
      setError(errorMessage);
      Alert.alert('AR Error', errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const disableAR = () => {
    setIsAREnabled(false);
    setCurrentFloorPlan(null);
    setArObjects([]);
    setError(null);
  };

  const loadFloorPlan = async (floorPlanId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch floor plan data from API using the configured API client
      const response = await apiClient.get(`/buildings/${floorPlanId}`);
      const floorPlan = response.data;
      setCurrentFloorPlan(floorPlan);

      // Convert floor plan data to AR objects
      const objects = convertFloorPlanToARObjects(floorPlan);
      setArObjects(objects);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load floor plan';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const addARObject = (object: any) => {
    setArObjects(prev => [...prev, object]);
  };

  const removeARObject = (objectId: string) => {
    setArObjects(prev => prev.filter(obj => obj.id !== objectId));
  };

  const convertFloorPlanToARObjects = (floorPlan: any): any[] => {
    const objects: any[] = [];

    // Convert rooms to AR objects
    if (floorPlan.rooms) {
      floorPlan.rooms.forEach((room: any) => {
        objects.push({
          id: `room_${room.id}`,
          type: 'room',
          position: [room.bounds.min_x, 0, room.bounds.min_y],
          scale: [
            room.bounds.max_x - room.bounds.min_x,
            0.1,
            room.bounds.max_y - room.bounds.min_y
          ],
          color: '#4A90E2',
          data: room
        });
      });
    }

    // Convert equipment to AR objects
    if (floorPlan.equipment) {
      floorPlan.equipment.forEach((equipment: any) => {
        const statusColor = getEquipmentStatusColor(equipment.status);
        objects.push({
          id: `equipment_${equipment.id}`,
          type: 'equipment',
          position: [equipment.location.x, 0.5, equipment.location.y],
          scale: [0.3, 0.3, 0.3],
          color: statusColor,
          data: equipment
        });
      });
    }

    return objects;
  };

  const getEquipmentStatusColor = (status: string): string => {
    switch (status) {
      case 'normal': return '#4CAF50';
      case 'warning': return '#FF9800';
      case 'failed': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const value: ARContextType = {
    isARSupported,
    isAREnabled,
    currentFloorPlan,
    arObjects,
    enableAR,
    disableAR,
    loadFloorPlan,
    addARObject,
    removeARObject,
    isLoading,
    error
  };

  return (
    <ARContext.Provider value={value}>
      {children}
    </ARContext.Provider>
  );
};

export const useAR = (): ARContextType => {
  const context = useContext(ARContext);
  if (context === undefined) {
    throw new Error('useAR must be used within an ARProvider');
  }
  return context;
};