/**
 * Card Component
 * Reusable card component with multiple variants
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ViewStyle,
  TouchableOpacity,
  TouchableOpacityProps,
} from 'react-native';

export interface CardProps extends Omit<TouchableOpacityProps, 'style'> {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'flat';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onPress?: () => void;
  style?: ViewStyle;
  testID?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'medium',
  onPress,
  style,
  testID,
  ...props
}) => {
  const getCardStyle = (): ViewStyle => {
    const baseStyle = [styles.card, styles[`${variant}Card`], styles[`${padding}Padding`]];
    
    if (style) {
      baseStyle.push(style);
    }
    
    return StyleSheet.flatten(baseStyle);
  };

  if (onPress) {
    return (
      <TouchableOpacity
        style={getCardStyle()}
        onPress={onPress}
        testID={testID}
        activeOpacity={0.7}
        {...props}>
        {children}
      </TouchableOpacity>
    );
  }

  return (
    <View style={getCardStyle()} testID={testID} {...props}>
      {children}
    </View>
  );
};

export interface CardHeaderProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  style?: ViewStyle;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  subtitle,
  action,
  style,
}) => (
  <View style={[styles.header, style]}>
    <View style={styles.headerContent}>
      {title && <Text style={styles.title}>{title}</Text>}
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
    </View>
    {action && <View style={styles.action}>{action}</View>}
  </View>
);

export interface CardContentProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const CardContent: React.FC<CardContentProps> = ({children, style}) => (
  <View style={[styles.content, style]}>{children}</View>
);

export interface CardFooterProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const CardFooter: React.FC<CardFooterProps> = ({children, style}) => (
  <View style={[styles.footer, style]}>{children}</View>
);

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    backgroundColor: '#ffffff',
  },
  
  // Variants
  defaultCard: {
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  elevatedCard: {
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  outlinedCard: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowOpacity: 0,
    elevation: 0,
  },
  flatCard: {
    shadowOpacity: 0,
    elevation: 0,
  },
  
  // Padding variants
  nonePadding: {
    padding: 0,
  },
  smallPadding: {
    padding: 8,
  },
  mediumPadding: {
    padding: 16,
  },
  largePadding: {
    padding: 24,
  },
  
  // Header styles
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerContent: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666666',
  },
  action: {
    marginLeft: 12,
  },
  
  // Content styles
  content: {
    flex: 1,
  },
  
  // Footer styles
  footer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
});
