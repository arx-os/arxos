import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Alert } from 'react-native';
import {
  ViroARScene,
  ViroARSceneNavigator,
  ViroBox,
  ViroNode,
  ViroText,
  ViroMaterials,
  ViroAmbientLight,
  ViroDirectionalLight,
  ViroCamera,
  ViroAnimations
} from 'react-viro';
import { useAR } from '../../contexts/ARContext';

interface ARSceneProps {
  floorPlanId?: string;
}

const ARFloorPlanScene: React.FC = () => {
  const { arObjects, currentFloorPlan, addARObject } = useAR();
  const [selectedObject, setSelectedObject] = useState<any>(null);

  useEffect(() => {
    // Register materials
    ViroMaterials.createMaterials({
      room: {
        lightingModel: 'Lambert',
        diffuseColor: '#4A90E2',
        transparency: 0.7
      },
      equipment_normal: {
        lightingModel: 'Lambert',
        diffuseColor: '#4CAF50'
      },
      equipment_warning: {
        lightingModel: 'Lambert',
        diffuseColor: '#FF9800'
      },
      equipment_failed: {
        lightingModel: 'Lambert',
        diffuseColor: '#F44336'
      },
      selected: {
        lightingModel: 'Lambert',
        diffuseColor: '#FFEB3B',
        transparency: 0.8
      }
    });

    // Register animations
    ViroAnimations.registerAnimations({
      pulse: {
        properties: {
          scaleX: '+=0.2',
          scaleY: '+=0.2',
          scaleZ: '+=0.2'
        },
        duration: 1000,
        easing: 'EaseInEaseOut'
      }
    });
  }, []);

  const onObjectTap = (object: any) => {
    setSelectedObject(object);
    
    // Show object information
    Alert.alert(
      object.data.name || 'AR Object',
      `Type: ${object.type}\nStatus: ${object.data.status || 'Unknown'}`,
      [
        { text: 'Close', style: 'cancel' },
        { 
          text: 'Details', 
          onPress: () => {
            // Navigate to object details
            console.log('Show details for:', object);
          }
        }
      ]
    );
  };

  const renderARObjects = () => {
    return arObjects.map((object) => {
      const isSelected = selectedObject?.id === object.id;
      
      if (object.type === 'room') {
        return (
          <ViroBox
            key={object.id}
            position={object.position}
            scale={object.scale}
            materials={isSelected ? ['selected'] : ['room']}
            onTap={() => onObjectTap(object)}
            animation={isSelected ? { name: 'pulse', run: true, loop: true } : undefined}
          />
        );
      } else if (object.type === 'equipment') {
        const material = `equipment_${object.data.status || 'normal'}`;
        return (
          <ViroNode key={object.id} position={object.position}>
            <ViroBox
              scale={object.scale}
              materials={isSelected ? ['selected'] : [material]}
              onTap={() => onObjectTap(object)}
              animation={isSelected ? { name: 'pulse', run: true, loop: true } : undefined}
            />
            <ViroText
              text={object.data.name || 'Equipment'}
              scale={[0.1, 0.1, 0.1]}
              position={[0, 0.5, 0]}
              style={styles.arText}
            />
          </ViroNode>
        );
      }
      
      return null;
    });
  };

  return (
    <ViroARScene>
      <ViroAmbientLight color="#ffffff" intensity={200} />
      <ViroDirectionalLight 
        color="#ffffff" 
        direction={[0, -1, 0]} 
        intensity={250}
      />
      
      {renderARObjects()}
      
      {/* Floor plane indicator */}
      <ViroBox
        position={[0, -0.1, 0]}
        scale={[10, 0.01, 10]}
        materials={['room']}
      />
      
      {/* Title overlay */}
      {currentFloorPlan && (
        <ViroText
          text={currentFloorPlan.name || 'Floor Plan'}
          scale={[0.2, 0.2, 0.2]}
          position={[0, 2, -2]}
          style={styles.titleText}
        />
      )}
    </ViroARScene>
  );
};

export const ARScene: React.FC<ARSceneProps> = ({ floorPlanId }) => {
  const { 
    isARSupported, 
    isAREnabled, 
    enableAR, 
    disableAR, 
    loadFloorPlan, 
    isLoading,
    error 
  } = useAR();

  useEffect(() => {
    if (floorPlanId && isAREnabled) {
      loadFloorPlan(floorPlanId);
    }
  }, [floorPlanId, isAREnabled]);

  const handleEnableAR = async () => {
    try {
      await enableAR();
      if (floorPlanId) {
        await loadFloorPlan(floorPlanId);
      }
    } catch (err) {
      console.error('Failed to enable AR:', err);
    }
  };

  if (!isARSupported) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>
          AR is not supported on this device
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.button} onPress={handleEnableAR}>
          <Text style={styles.buttonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!isAREnabled) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>ArxOS AR View</Text>
        <Text style={styles.subtitle}>
          View building floor plans in augmented reality
        </Text>
        <TouchableOpacity 
          style={styles.button} 
          onPress={handleEnableAR}
          disabled={isLoading}
        >
          <Text style={styles.buttonText}>
            {isLoading ? 'Starting AR...' : 'Start AR'}
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.arContainer}>
      <ViroARSceneNavigator
        autofocus={true}
        initialScene={{
          scene: ARFloorPlanScene
        }}
        style={styles.arScene}
      />
      
      {/* AR Controls */}
      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlButton} onPress={disableAR}>
          <Text style={styles.controlButtonText}>Exit AR</Text>
        </TouchableOpacity>
      </View>
      
      {/* Loading overlay */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <Text style={styles.loadingText}>Loading floor plan...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20
  },
  arContainer: {
    flex: 1
  },
  arScene: {
    flex: 1
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    textAlign: 'center'
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
    textAlign: 'center'
  },
  button: {
    backgroundColor: '#4A90E2',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 8,
    minWidth: 150
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center'
  },
  errorText: {
    fontSize: 16,
    color: '#F44336',
    textAlign: 'center',
    marginBottom: 20
  },
  controls: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  controlButton: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 6
  },
  controlButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600'
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center'
  },
  loadingText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600'
  },
  arText: {
    fontFamily: 'Arial',
    fontSize: 12,
    color: '#ffffff',
    textAlignVertical: 'center',
    textAlign: 'center'
  },
  titleText: {
    fontFamily: 'Arial',
    fontSize: 18,
    color: '#4A90E2',
    textAlignVertical: 'center',
    textAlign: 'center'
  }
});