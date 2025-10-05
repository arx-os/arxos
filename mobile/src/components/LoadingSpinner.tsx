/**
 * Loading Spinner Component
 * Reusable loading indicator with multiple variants
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';

export interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  color?: string;
  text?: string;
  overlay?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  testID?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  color = '#007AFF',
  text,
  overlay = false,
  style,
  textStyle,
  testID,
}) => {
  const containerStyle = overlay ? styles.overlay : styles.container;

  return (
    <View style={[containerStyle, style]} testID={testID}>
      <ActivityIndicator size={size} color={color} />
      {text && (
        <Text style={[styles.text, textStyle]}>{text}</Text>
      )}
    </View>
  );
};

export interface LoadingOverlayProps {
  visible: boolean;
  text?: string;
  color?: string;
  testID?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  text,
  color = '#007AFF',
  testID,
}) => {
  if (!visible) return null;

  return (
    <View style={styles.overlay} testID={testID}>
      <View style={styles.overlayContent}>
        <ActivityIndicator size="large" color={color} />
        {text && <Text style={styles.overlayText}>{text}</Text>}
      </View>
    </View>
  );
};

export interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
  testID?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
  testID,
}) => (
  <View
    style={[
      styles.skeleton,
      {
        width: width as any,
        height,
        borderRadius,
      },
      style,
    ]}
    testID={testID}
  />
);

export interface SkeletonTextProps {
  lines?: number;
  lineHeight?: number;
  spacing?: number;
  width?: number | string;
  style?: ViewStyle;
  testID?: string;
}

export const SkeletonText: React.FC<SkeletonTextProps> = ({
  lines = 3,
  lineHeight = 16,
  spacing = 8,
  width = '100%',
  style,
  testID,
}) => (
  <View style={[styles.skeletonTextContainer, style]} testID={testID}>
    {Array.from({length: lines}, (_, index) => (
      <Skeleton
        key={index}
        width={index === lines - 1 ? '75%' : width}
        height={lineHeight}
        style={{
          marginBottom: index < lines - 1 ? spacing : 0,
        }}
      />
    ))}
  </View>
);

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  overlayContent: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 12,
    padding: 24,
  },
  text: {
    fontSize: 16,
    color: '#666666',
    marginTop: 12,
    textAlign: 'center',
  },
  overlayText: {
    fontSize: 16,
    color: '#333333',
    marginTop: 12,
    textAlign: 'center',
    fontWeight: '500',
  },
  skeleton: {
    backgroundColor: '#e0e0e0',
  },
  skeletonTextContainer: {
    width: '100%',
  },
});
