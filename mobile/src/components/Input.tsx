/**
 * Input Component
 * Reusable input component with validation and error states
 */

import React, {useState, forwardRef} from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  ViewStyle,
  TextStyle,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

export interface InputProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChangeText: (text: string) => void;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  multiline?: boolean;
  numberOfLines?: number;
  maxLength?: number;
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad';
  secureTextEntry?: boolean;
  leftIcon?: string;
  rightIcon?: string;
  onRightIconPress?: () => void;
  style?: ViewStyle;
  inputStyle?: TextStyle;
  testID?: string;
}

export const Input = forwardRef<TextInput, InputProps>(({
  label,
  placeholder,
  value,
  onChangeText,
  error,
  helperText,
  disabled = false,
  required = false,
  multiline = false,
  numberOfLines = 1,
  maxLength,
  keyboardType = 'default',
  secureTextEntry = false,
  leftIcon,
  rightIcon,
  onRightIconPress,
  style,
  inputStyle,
  testID,
}, ref) => {
  const [isFocused, setIsFocused] = useState(false);

  const getContainerStyle = (): ViewStyle => {
    const baseStyle = [styles.container];
    
    if (error) {
      baseStyle.push(styles.errorContainer);
    } else if (isFocused) {
      baseStyle.push(styles.focusedContainer);
    }
    
    if (disabled) {
      baseStyle.push(styles.disabledContainer);
    }
    
    if (style) {
      baseStyle.push(style);
    }
    
    return StyleSheet.flatten(baseStyle);
  };

  const getInputStyle = (): TextStyle => {
    const baseStyle = [styles.input];
    
    if (multiline) {
      baseStyle.push(styles.multilineInput);
    }
    
    if (disabled) {
      baseStyle.push(styles.disabledInput);
    }
    
    if (inputStyle) {
      baseStyle.push(inputStyle);
    }
    
    return StyleSheet.flatten(baseStyle);
  };

  return (
    <View style={styles.wrapper}>
      {label && (
        <View style={styles.labelContainer}>
          <Text style={styles.label}>{label}</Text>
          {required && <Text style={styles.required}>*</Text>}
        </View>
      )}
      
      <View style={getContainerStyle()}>
        {leftIcon && (
          <Icon
            name={leftIcon}
            size={20}
            color={error ? '#FF3B30' : isFocused ? '#007AFF' : '#666666'}
            style={styles.leftIcon}
          />
        )}
        
        <TextInput
          ref={ref}
          style={getInputStyle()}
          placeholder={placeholder}
          placeholderTextColor="#999999"
          value={value}
          onChangeText={onChangeText}
          editable={!disabled}
          multiline={multiline}
          numberOfLines={numberOfLines}
          maxLength={maxLength}
          keyboardType={keyboardType}
          secureTextEntry={secureTextEntry}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          testID={testID}
        />
        
        {rightIcon && (
          <TouchableOpacity
            onPress={onRightIconPress}
            style={styles.rightIconContainer}
            disabled={!onRightIconPress}>
            <Icon
              name={rightIcon}
              size={20}
              color={error ? '#FF3B30' : isFocused ? '#007AFF' : '#666666'}
            />
          </TouchableOpacity>
        )}
      </View>
      
      {(error || helperText) && (
        <View style={styles.messageContainer}>
          {error ? (
            <View style={styles.errorContainer}>
              <Icon name="error" size={16} color="#FF3B30" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : (
            <Text style={styles.helperText}>{helperText}</Text>
          )}
        </View>
      )}
      
      {maxLength && (
        <View style={styles.counterContainer}>
          <Text style={styles.counterText}>
            {value.length}/{maxLength}
          </Text>
        </View>
      )}
    </View>
  );
});

Input.displayName = 'Input';

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: 16,
  },
  labelContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333333',
  },
  required: {
    fontSize: 14,
    color: '#FF3B30',
    marginLeft: 4,
  },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    paddingHorizontal: 12,
    minHeight: 44,
  },
  focusedContainer: {
    borderColor: '#007AFF',
    backgroundColor: '#ffffff',
    shadowColor: '#007AFF',
    shadowOffset: {width: 0, height: 0},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  errorContainer: {
    borderColor: '#FF3B30',
    backgroundColor: '#fff5f5',
  },
  disabledContainer: {
    backgroundColor: '#f5f5f5',
    opacity: 0.6,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#333333',
    paddingVertical: 12,
  },
  multilineInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  disabledInput: {
    color: '#999999',
  },
  leftIcon: {
    marginRight: 8,
  },
  rightIconContainer: {
    marginLeft: 8,
    padding: 4,
  },
  messageContainer: {
    marginTop: 4,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 12,
    color: '#FF3B30',
    marginLeft: 4,
  },
  helperText: {
    fontSize: 12,
    color: '#666666',
  },
  counterContainer: {
    alignItems: 'flex-end',
    marginTop: 4,
  },
  counterText: {
    fontSize: 12,
    color: '#999999',
  },
});
