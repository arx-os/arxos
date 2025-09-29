/**
 * Profile Screen
 * User profile and account information
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {useAppSelector, useAppDispatch} from '@/store/hooks';
import {logout} from '@/store/slices/authSlice';

export const ProfileScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const {user} = useAppSelector(state => state.auth);
  
  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Logout',
          style: 'destructive',
          onPress: () => dispatch(logout()),
        },
      ]
    );
  };
  
  const handleChangePassword = () => {
    Alert.alert(
      'Change Password',
      'Password change functionality will be available in a future update.',
      [{text: 'OK'}]
    );
  };
  
  const handleEditProfile = () => {
    Alert.alert(
      'Edit Profile',
      'Profile editing functionality will be available in a future update.',
      [{text: 'OK'}]
    );
  };
  
  const handleBiometricSettings = () => {
    Alert.alert(
      'Biometric Settings',
      'Biometric authentication settings will be available in a future update.',
      [{text: 'OK'}]
    );
  };
  
  const handleDataExport = () => {
    Alert.alert(
      'Export Data',
      'Data export functionality will be available in a future update.',
      [{text: 'OK'}]
    );
  };
  
  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This action cannot be undone. All your data will be permanently deleted.',
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            Alert.alert(
              'Confirm Deletion',
              'Are you absolutely sure you want to delete your account?',
              [
                {text: 'Cancel', style: 'cancel'},
                {
                  text: 'Delete',
                  style: 'destructive',
                  onPress: () => {
                    // TODO: Implement account deletion
                    Alert.alert('Account Deleted', 'Your account has been deleted.');
                  },
                },
              ]
            );
          },
        },
      ]
    );
  };
  
  const renderProfileItem = (
    title: string,
    subtitle: string,
    icon: string,
    onPress?: () => void,
    rightComponent?: React.ReactNode
  ) => (
    <TouchableOpacity
      style={styles.profileItem}
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.profileLeft}>
        <Icon name={icon} size={24} color="#666666" />
        <View style={styles.profileText}>
          <Text style={styles.profileTitle}>{title}</Text>
          <Text style={styles.profileSubtitle}>{subtitle}</Text>
        </View>
      </View>
      {rightComponent || (onPress && <Icon name="chevron-right" size={24} color="#cccccc" />)}
    </TouchableOpacity>
  );
  
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <Icon name="person" size={64} color="#007AFF" />
          </View>
          <Text style={styles.userName}>{user?.fullName || user?.username}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>
          <Text style={styles.userRole}>{user?.role}</Text>
        </View>
        
        {/* Account Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Settings</Text>
          
          {renderProfileItem(
            'Edit Profile',
            'Update your personal information',
            'edit',
            handleEditProfile
          )}
          
          {renderProfileItem(
            'Change Password',
            'Update your password',
            'lock',
            handleChangePassword
          )}
          
          {renderProfileItem(
            'Biometric Settings',
            'Configure fingerprint or face ID',
            'fingerprint',
            handleBiometricSettings
          )}
        </View>
        
        {/* App Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Settings</Text>
          
          {renderProfileItem(
            'Notifications',
            'Manage notification preferences',
            'notifications',
            () => {
              // TODO: Navigate to notification settings
            }
          )}
          
          {renderProfileItem(
            'Privacy',
            'Privacy and data settings',
            'privacy-tip',
            () => {
              // TODO: Navigate to privacy settings
            }
          )}
          
          {renderProfileItem(
            'Data Export',
            'Export your data',
            'download',
            handleDataExport
          )}
        </View>
        
        {/* Support */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support</Text>
          
          {renderProfileItem(
            'Help Center',
            'Get help and support',
            'help',
            () => {
              // TODO: Navigate to help center
            }
          )}
          
          {renderProfileItem(
            'Contact Support',
            'Get in touch with our team',
            'support-agent',
            () => {
              // TODO: Navigate to contact support
            }
          )}
          
          {renderProfileItem(
            'Feedback',
            'Send us your feedback',
            'feedback',
            () => {
              // TODO: Navigate to feedback form
            }
          )}
        </View>
        
        {/* App Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Information</Text>
          
          {renderProfileItem(
            'Version',
            'App version and build info',
            'info',
            () => {
              // TODO: Show version info
            },
            <Text style={styles.profileValue}>0.1.0</Text>
          )}
          
          {renderProfileItem(
            'Terms of Service',
            'View terms of service',
            'description',
            () => {
              // TODO: Show terms of service
            }
          )}
          
          {renderProfileItem(
            'Privacy Policy',
            'View privacy policy',
            'privacy-tip',
            () => {
              // TODO: Show privacy policy
            }
          )}
        </View>
        
        {/* Danger Zone */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Danger Zone</Text>
          
          {renderProfileItem(
            'Logout',
            'Sign out of your account',
            'logout',
            handleLogout,
            <Icon name="logout" size={24} color="#F44336" />
          )}
          
          {renderProfileItem(
            'Delete Account',
            'Permanently delete your account',
            'delete-forever',
            handleDeleteAccount,
            <Icon name="delete-forever" size={24} color="#F44336" />
          )}
        </View>
        
        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            ArxOS Mobile v0.1.0
          </Text>
          <Text style={styles.footerText}>
            © 2024 ArxOS. All rights reserved.
          </Text>
        </View>
      </ScrollView>
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
    alignItems: 'center',
    paddingVertical: 40,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  avatarContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 16,
    color: '#666666',
    marginBottom: 4,
  },
  userRole: {
    fontSize: 14,
    color: '#999999',
    textTransform: 'uppercase',
  },
  section: {
    backgroundColor: 'white',
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333333',
    padding: 20,
    paddingBottom: 12,
  },
  profileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  profileLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  profileText: {
    marginLeft: 16,
    flex: 1,
  },
  profileTitle: {
    fontSize: 16,
    color: '#333333',
    marginBottom: 2,
  },
  profileSubtitle: {
    fontSize: 14,
    color: '#666666',
  },
  profileValue: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  footerText: {
    fontSize: 12,
    color: '#999999',
    marginBottom: 4,
  },
});
