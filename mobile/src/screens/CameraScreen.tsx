/**
 * Camera Screen
 * Handles photo capture for equipment documentation
 */

import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Image,
  ScrollView,
  Alert,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useRoute} from '@react-navigation/native';
import {cameraService, PhotoResult} from '@/services/cameraService';
import {equipmentService} from '@/services/equipmentService';
import {photoService, PhotoData} from '@/services/photoService';

export const CameraScreen: React.FC = () => {
  const route = useRoute();
  const {equipmentId, purpose} = route.params as {equipmentId?: string; purpose: 'photo' | 'scan' | 'ar'};
  
  const [photos, setPhotos] = useState<PhotoData[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [notes, setNotes] = useState('');
  
  const handleTakePhoto = async () => {
    if (!equipmentId) {
      Alert.alert('Error', 'Equipment ID is required to take photos');
      return;
    }

    setIsCapturing(true);
    try {
      const photoData = await photoService.capturePhoto(equipmentId, notes);
      
      // Save photo and queue for sync
      await photoService.savePhoto(photoData);
      setPhotos(prev => [...prev, photoData]);
      
      Alert.alert('Success', 'Photo captured and saved. It will sync when online.');
    } catch (error: any) {
      Alert.alert('Camera Error', `Failed to take photo: ${error.message}`);
    } finally {
      setIsCapturing(false);
    }
  };
  
  const handleSelectPhoto = async () => {
    if (!equipmentId) {
      Alert.alert('Error', 'Equipment ID is required to select photos');
      return;
    }

    try {
      const photoData = await photoService.selectPhoto(equipmentId, notes);
      
      // Save photo and queue for sync
      await photoService.savePhoto(photoData);
      setPhotos(prev => [...prev, photoData]);
      
      Alert.alert('Success', 'Photo selected and saved. It will sync when online.');
    } catch (error: any) {
      Alert.alert('Gallery Error', `Failed to select photo: ${error.message}`);
    }
  };
  
  const handleRemovePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };
  
  const handleUploadPhoto = async (photo: PhotoResult) => {
    if (!equipmentId) {
      Alert.alert('No Equipment Selected', 'Please select an equipment item first');
      return;
    }
    
    try {
      await equipmentService.uploadEquipmentPhoto(equipmentId, photo.uri);
      Alert.alert('Success', 'Photo uploaded successfully');
    } catch (error: any) {
      Alert.alert('Upload Failed', `Failed to upload photo: ${error.message}`);
    }
  };
  
  const getPurposeText = () => {
    switch (purpose) {
      case 'photo':
        return 'Documentation';
      case 'scan':
        return 'QR Code Scan';
      case 'ar':
        return 'AR Capture';
      default:
        return 'Photo Capture';
    }
  };
  
  const renderCameraView = () => (
    <View style={styles.cameraContainer}>
      {/* Camera placeholder */}
      <View style={styles.cameraPlaceholder}>
        <Icon name="camera-alt" size={128} color="#007AFF" />
        <Text style={styles.cameraPlaceholderText}>Camera View</Text>
        <Text style={styles.cameraPlaceholderSubtext}>
          This is where the camera feed would be displayed
        </Text>
      </View>
      
      {/* Notes Input */}
      <View style={styles.notesContainer}>
        <Text style={styles.notesLabel}>Photo Notes (Optional)</Text>
        <TextInput
          style={styles.notesInput}
          value={notes}
          onChangeText={setNotes}
          placeholder="Add notes about this photo..."
          placeholderTextColor="#999999"
          multiline
          numberOfLines={3}
        />
      </View>
      
      {/* Camera Controls */}
      <View style={styles.cameraControls}>
        <TouchableOpacity
          style={styles.controlButton}
          onPress={handleSelectPhoto}
          disabled={isCapturing}
        >
          <Icon name="photo-library" size={24} color="white" />
          <Text style={styles.controlButtonText}>Gallery</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.captureButton, isCapturing && styles.captureButtonDisabled]}
          onPress={handleTakePhoto}
          disabled={isCapturing}
        >
          <Icon name="camera-alt" size={32} color="white" />
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.controlButton}
          onPress={() => setShowGallery(true)}
          disabled={isCapturing}
        >
          <Icon name="collections" size={24} color="white" />
          <Text style={styles.controlButtonText}>Photos</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
  
  const renderGalleryView = () => (
    <View style={styles.galleryContainer}>
      <View style={styles.galleryHeader}>
        <TouchableOpacity onPress={() => setShowGallery(false)}>
          <Icon name="arrow-back" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.galleryTitle}>Captured Photos</Text>
        <View style={styles.placeholder} />
      </View>
      
      <ScrollView style={styles.galleryContent}>
        {photos.length === 0 ? (
          <View style={styles.emptyGallery}>
            <Icon name="photo-library" size={64} color="#cccccc" />
            <Text style={styles.emptyGalleryText}>No photos captured</Text>
            <Text style={styles.emptyGallerySubtext}>
              Take some photos to see them here
            </Text>
          </View>
        ) : (
          <View style={styles.photosGrid}>
            {photos.map((photo, index) => (
              <View key={index} style={styles.photoItem}>
                <Image source={{uri: photo.uri}} style={styles.photoImage} />
                <View style={styles.photoInfo}>
                  <Text style={styles.photoInfoText}>
                    {photo.width} × {photo.height}
                  </Text>
                  <Text style={styles.photoInfoText}>
                    {photo.fileSize ? (photo.fileSize / 1024).toFixed(1) : 'Unknown'} KB
                  </Text>
                </View>
                <View style={styles.photoActions}>
                  {equipmentId && (
                    <TouchableOpacity
                      style={styles.photoActionButton}
                      onPress={() => handleUploadPhoto(photo)}
                    >
                      <Icon name="cloud-upload" size={20} color="#007AFF" />
                    </TouchableOpacity>
                  )}
                  <TouchableOpacity
                    style={styles.photoActionButton}
                    onPress={() => handleRemovePhoto(index)}
                  >
                    <Icon name="delete" size={20} color="#F44336" />
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
  
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Camera</Text>
        <Text style={styles.subtitle}>{getPurposeText()}</Text>
      </View>
      
      {showGallery ? renderGalleryView() : renderCameraView()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    backgroundColor: 'white',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
  },
  subtitle: {
    fontSize: 14,
    color: '#666666',
    marginTop: 4,
  },
  cameraContainer: {
    flex: 1,
  },
  cameraPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  cameraPlaceholderText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'white',
    marginTop: 16,
    marginBottom: 8,
  },
  cameraPlaceholderSubtext: {
    fontSize: 14,
    color: '#cccccc',
    textAlign: 'center',
    lineHeight: 20,
  },
  notesContainer: {
    backgroundColor: 'white',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  notesLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 8,
  },
  notesInput: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#333333',
    backgroundColor: '#f9f9f9',
    textAlignVertical: 'top',
  },
  cameraControls: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  captureButton: {
    backgroundColor: 'rgba(0, 122, 255, 0.8)',
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureButtonDisabled: {
    backgroundColor: 'rgba(0, 122, 255, 0.4)',
  },
  galleryContainer: {
    flex: 1,
    backgroundColor: 'white',
  },
  galleryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  galleryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
  },
  placeholder: {
    width: 24,
  },
  galleryContent: {
    flex: 1,
  },
  emptyGallery: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyGalleryText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyGallerySubtext: {
    fontSize: 14,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 20,
  },
  photosGrid: {
    padding: 20,
  },
  photoItem: {
    backgroundColor: 'white',
    borderRadius: 8,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  photoImage: {
    width: '100%',
    height: 200,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
  },
  photoInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  photoInfoText: {
    fontSize: 12,
    color: '#666666',
  },
  photoActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 12,
  },
  photoActionButton: {
    padding: 8,
    marginLeft: 8,
  },
});
