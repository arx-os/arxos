/**
 * Location Service
 * Handles GPS location and geolocation operations
 */

import Geolocation from 'react-native-geolocation-service';
import {PermissionsAndroid, Platform} from 'react-native';
import {GPSLocation} from '@/types/equipment';

class LocationService {
  private watchId: number | null = null;
  private isWatching = false;
  
  /**
   * Request location permissions
   */
  async requestLocationPermission(): Promise<boolean> {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        {
          title: 'Location Permission',
          message: 'ArxOS needs access to your location to track equipment positions',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        }
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }
    
    // iOS permissions are handled automatically by the geolocation service
    return true;
  }
  
  /**
   * Get current location
   */
  async getCurrentLocation(): Promise<GPSLocation> {
    const hasPermission = await this.requestLocationPermission();
    if (!hasPermission) {
      throw new Error('Location permission denied');
    }
    
    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude || undefined,
            heading: position.coords.heading || undefined,
            speed: position.coords.speed || undefined,
          });
        },
        (error) => {
          reject(new Error(`Location error: ${error.message}`));
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 10000,
        }
      );
    });
  }
  
  /**
   * Watch location changes
   */
  async watchLocation(
    onLocationUpdate: (location: GPSLocation) => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    const hasPermission = await this.requestLocationPermission();
    if (!hasPermission) {
      throw new Error('Location permission denied');
    }
    
    if (this.isWatching) {
      return;
    }
    
    this.watchId = Geolocation.watchPosition(
      (position) => {
        const location: GPSLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude || undefined,
          heading: position.coords.heading || undefined,
          speed: position.coords.speed || undefined,
        };
        onLocationUpdate(location);
      },
      (error) => {
        if (onError) {
          onError(new Error(`Location watch error: ${error.message}`));
        }
      },
      {
        enableHighAccuracy: true,
        distanceFilter: 10, // Update every 10 meters
        interval: 1000, // Update every second
        fastestInterval: 500, // Fastest update every 500ms
      }
    );
    
    this.isWatching = true;
  }
  
  /**
   * Stop watching location
   */
  stopWatchingLocation(): void {
    if (this.watchId !== null) {
      Geolocation.clearWatch(this.watchId);
      this.watchId = null;
      this.isWatching = false;
    }
  }
  
  /**
   * Calculate distance between two points
   */
  calculateDistance(
    location1: GPSLocation,
    location2: GPSLocation
  ): number {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = (location1.latitude * Math.PI) / 180;
    const φ2 = (location2.latitude * Math.PI) / 180;
    const Δφ = ((location2.latitude - location1.latitude) * Math.PI) / 180;
    const Δλ = ((location2.longitude - location1.longitude) * Math.PI) / 180;
    
    const a =
      Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    
    return R * c; // Distance in meters
  }
  
  /**
   * Check if location is within radius
   */
  isLocationWithinRadius(
    center: GPSLocation,
    location: GPSLocation,
    radiusMeters: number
  ): boolean {
    const distance = this.calculateDistance(center, location);
    return distance <= radiusMeters;
  }
  
  /**
   * Get location accuracy level
   */
  getLocationAccuracyLevel(accuracy: number): 'high' | 'medium' | 'low' {
    if (accuracy <= 5) {
      return 'high';
    } else if (accuracy <= 20) {
      return 'medium';
    } else {
      return 'low';
    }
  }
  
  /**
   * Format location for display
   */
  formatLocation(location: GPSLocation): string {
    const lat = location.latitude.toFixed(6);
    const lng = location.longitude.toFixed(6);
    const accuracy = location.accuracy.toFixed(1);
    
    return `${lat}, ${lng} (±${accuracy}m)`;
  }
  
  /**
   * Get location from address (reverse geocoding)
   */
  async getLocationFromAddress(address: string): Promise<GPSLocation | null> {
    // TODO: Implement reverse geocoding
    // This would typically use a service like Google Geocoding API
    // or react-native-geocoding
    console.log('Reverse geocoding not implemented yet');
    return null;
  }
  
  /**
   * Get address from location (geocoding)
   */
  async getAddressFromLocation(location: GPSLocation): Promise<string | null> {
    // TODO: Implement geocoding
    // This would typically use a service like Google Geocoding API
    // or react-native-geocoding
    console.log('Geocoding not implemented yet');
    return null;
  }
}

export const locationService = new LocationService();
