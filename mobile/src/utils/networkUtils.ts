/**
 * Network Utility Functions
 * Common network and connectivity functions
 */

import NetInfo from '@react-native-community/netinfo';

export interface NetworkState {
  isConnected: boolean;
  type: string | null;
  isInternetReachable: boolean | null;
  details: any;
}

export const getNetworkState = async (): Promise<NetworkState> => {
  try {
    const state = await NetInfo.fetch();
    return {
      isConnected: state.isConnected || false,
      type: state.type,
      isInternetReachable: state.isInternetReachable,
      details: state.details,
    };
  } catch (error) {
    console.error('Error getting network state:', error);
    return {
      isConnected: false,
      type: null,
      isInternetReachable: null,
      details: null,
    };
  }
};

export const isOnline = async (): Promise<boolean> => {
  try {
    const state = await NetInfo.fetch();
    return state.isConnected || false;
  } catch (error) {
    console.error('Error checking online status:', error);
    return false;
  }
};

export const isInternetReachable = async (): Promise<boolean> => {
  try {
    const state = await NetInfo.fetch();
    return state.isInternetReachable || false;
  } catch (error) {
    console.error('Error checking internet reachability:', error);
    return false;
  }
};

export const getConnectionType = async (): Promise<string | null> => {
  try {
    const state = await NetInfo.fetch();
    return state.type;
  } catch (error) {
    console.error('Error getting connection type:', error);
    return null;
  }
};

export const getConnectionDetails = async (): Promise<any> => {
  try {
    const state = await NetInfo.fetch();
    return state.details;
  } catch (error) {
    console.error('Error getting connection details:', error);
    return null;
  }
};

export const isWifiConnected = async (): Promise<boolean> => {
  try {
    const state = await NetInfo.fetch();
    return state.type === 'wifi' && state.isConnected;
  } catch (error) {
    console.error('Error checking WiFi connection:', error);
    return false;
  }
};

export const isCellularConnected = async (): Promise<boolean> => {
  try {
    const state = await NetInfo.fetch();
    return state.type === 'cellular' && state.isConnected;
  } catch (error) {
    console.error('Error checking cellular connection:', error);
    return false;
  }
};

export const isEthernetConnected = async (): Promise<boolean> => {
  try {
    const state = await NetInfo.fetch();
    return state.type === 'ethernet' && state.isConnected;
  } catch (error) {
    console.error('Error checking ethernet connection:', error);
    return false;
  }
};

export const getNetworkSpeed = async (): Promise<{
  download: number | null;
  upload: number | null;
  latency: number | null;
}> => {
  try {
    const state = await NetInfo.fetch();
    const details = state.details;
    
    if (state.type === 'wifi' && details) {
      return {
        download: details.linkSpeed || null,
        upload: null,
        latency: null,
      };
    } else if (state.type === 'cellular' && details) {
      return {
        download: details.downlink || null,
        upload: null,
        latency: details.rtt || null,
      };
    }
    
    return {
      download: null,
      upload: null,
      latency: null,
    };
  } catch (error) {
    console.error('Error getting network speed:', error);
    return {
      download: null,
      upload: null,
      latency: null,
    };
  }
};

export const getSignalStrength = async (): Promise<number | null> => {
  try {
    const state = await NetInfo.fetch();
    const details = state.details;
    
    if (state.type === 'wifi' && details) {
      return details.strength || null;
    } else if (state.type === 'cellular' && details) {
      return details.strength || null;
    }
    
    return null;
  } catch (error) {
    console.error('Error getting signal strength:', error);
    return null;
  }
};

export const getNetworkQuality = async (): Promise<'excellent' | 'good' | 'fair' | 'poor' | 'unknown'> => {
  try {
    const state = await NetInfo.fetch();
    const details = state.details;
    
    if (state.type === 'wifi' && details) {
      const strength = details.strength || 0;
      if (strength >= -30) return 'excellent';
      if (strength >= -50) return 'good';
      if (strength >= -70) return 'fair';
      return 'poor';
    } else if (state.type === 'cellular' && details) {
      const strength = details.strength || 0;
      if (strength >= -70) return 'excellent';
      if (strength >= -85) return 'good';
      if (strength >= -100) return 'fair';
      return 'poor';
    }
    
    return 'unknown';
  } catch (error) {
    console.error('Error getting network quality:', error);
    return 'unknown';
  }
};

export const getNetworkInfo = async (): Promise<{
  isConnected: boolean;
  type: string | null;
  isInternetReachable: boolean | null;
  quality: string;
  speed: {
    download: number | null;
    upload: number | null;
    latency: number | null;
  };
  signalStrength: number | null;
  details: any;
}> => {
  try {
    const state = await NetInfo.fetch();
    const quality = await getNetworkQuality();
    const speed = await getNetworkSpeed();
    const signalStrength = await getSignalStrength();
    
    return {
      isConnected: state.isConnected || false,
      type: state.type,
      isInternetReachable: state.isInternetReachable,
      quality,
      speed,
      signalStrength,
      details: state.details,
    };
  } catch (error) {
    console.error('Error getting network info:', error);
    return {
      isConnected: false,
      type: null,
      isInternetReachable: null,
      quality: 'unknown',
      speed: {
        download: null,
        upload: null,
        latency: null,
      },
      signalStrength: null,
      details: null,
    };
  }
};

export const waitForConnection = async (timeout: number = 30000): Promise<boolean> => {
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const checkConnection = async () => {
      const isConnected = await isOnline();
      if (isConnected) {
        resolve(true);
        return;
      }
      
      if (Date.now() - startTime >= timeout) {
        resolve(false);
        return;
      }
      
      setTimeout(checkConnection, 1000);
    };
    
    checkConnection();
  });
};

export const waitForInternet = async (timeout: number = 30000): Promise<boolean> => {
  return new Promise((resolve) => {
    const startTime = Date.now();
    
    const checkInternet = async () => {
      const isReachable = await isInternetReachable();
      if (isReachable) {
        resolve(true);
        return;
      }
      
      if (Date.now() - startTime >= timeout) {
        resolve(false);
        return;
      }
      
      setTimeout(checkInternet, 1000);
    };
    
    checkInternet();
  });
};

export const testConnection = async (url: string = 'https://www.google.com'): Promise<{
  success: boolean;
  latency: number;
  error?: string;
}> => {
  const startTime = Date.now();
  
  try {
    const response = await fetch(url, {
      method: 'HEAD',
      timeout: 10000,
    });
    
    const latency = Date.now() - startTime;
    
    if (response.ok) {
      return {
        success: true,
        latency,
      };
    } else {
      return {
        success: false,
        latency,
        error: `HTTP ${response.status}`,
      };
    }
  } catch (error: any) {
    const latency = Date.now() - startTime;
    return {
      success: false,
      latency,
      error: error.message,
    };
  }
};

export const testApiEndpoint = async (url: string): Promise<{
  success: boolean;
  latency: number;
  status?: number;
  error?: string;
}> => {
  const startTime = Date.now();
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      timeout: 10000,
    });
    
    const latency = Date.now() - startTime;
    
    return {
      success: response.ok,
      latency,
      status: response.status,
    };
  } catch (error: any) {
    const latency = Date.now() - startTime;
    return {
      success: false,
      latency,
      error: error.message,
    };
  }
};

export const checkConnectivity = async (): Promise<{
  isConnected: boolean;
  isInternetReachable: boolean;
  connectionTest: {
    success: boolean;
    latency: number;
    error?: string;
  };
  apiTest: {
    success: boolean;
    latency: number;
    status?: number;
    error?: string;
  };
}> => {
  try {
    const isConnected = await isOnline();
    const isInternetReachable = await isInternetReachable();
    
    const connectionTest = await testConnection();
    const apiTest = await testApiEndpoint('https://api.arxos.com/v1/health');
    
    return {
      isConnected,
      isInternetReachable,
      connectionTest,
      apiTest,
    };
  } catch (error: any) {
    return {
      isConnected: false,
      isInternetReachable: false,
      connectionTest: {
        success: false,
        latency: 0,
        error: error.message,
      },
      apiTest: {
        success: false,
        latency: 0,
        error: error.message,
      },
    };
  }
};

export const getNetworkStatus = async (): Promise<{
  status: 'online' | 'offline' | 'limited' | 'unknown';
  quality: string;
  speed: string;
  details: string;
}> => {
  try {
    const networkInfo = await getNetworkInfo();
    
    let status: 'online' | 'offline' | 'limited' | 'unknown' = 'unknown';
    if (networkInfo.isConnected && networkInfo.isInternetReachable) {
      status = 'online';
    } else if (networkInfo.isConnected && !networkInfo.isInternetReachable) {
      status = 'limited';
    } else if (!networkInfo.isConnected) {
      status = 'offline';
    }
    
    let speed = 'Unknown';
    if (networkInfo.speed.download) {
      speed = `${networkInfo.speed.download} Mbps`;
    }
    
    let details = 'No connection';
    if (networkInfo.type) {
      details = `${networkInfo.type.charAt(0).toUpperCase() + networkInfo.type.slice(1)}`;
      if (networkInfo.signalStrength) {
        details += ` (${networkInfo.signalStrength} dBm)`;
      }
    }
    
    return {
      status,
      quality: networkInfo.quality,
      speed,
      details,
    };
  } catch (error) {
    console.error('Error getting network status:', error);
    return {
      status: 'unknown',
      quality: 'unknown',
      speed: 'Unknown',
      details: 'Error getting network info',
    };
  }
};

export const monitorNetworkChanges = (
  callback: (networkState: NetworkState) => void
): () => void => {
  const unsubscribe = NetInfo.addEventListener((state) => {
    const networkState: NetworkState = {
      isConnected: state.isConnected || false,
      type: state.type,
      isInternetReachable: state.isInternetReachable,
      details: state.details,
    };
    
    callback(networkState);
  });
  
  return unsubscribe;
};

export const getNetworkHistory = async (): Promise<NetworkState[]> => {
  try {
    // This would typically be stored in local storage
    // For now, return empty array
    return [];
  } catch (error) {
    console.error('Error getting network history:', error);
    return [];
  }
};

export const clearNetworkHistory = async (): Promise<void> => {
  try {
    // This would typically clear network history from local storage
    // For now, do nothing
  } catch (error) {
    console.error('Error clearing network history:', error);
  }
};
