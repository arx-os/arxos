/**
 * String Utility Functions
 * Common string manipulation and formatting functions
 */

export const capitalize = (str: string): string => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const capitalizeWords = (str: string): string => {
  if (!str) return '';
  return str.split(' ').map(word => capitalize(word)).join(' ');
};

export const camelCase = (str: string): string => {
  if (!str) return '';
  return str
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase());
};

export const kebabCase = (str: string): string => {
  if (!str) return '';
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\s_]+/g, '-')
    .toLowerCase();
};

export const snakeCase = (str: string): string => {
  if (!str) return '';
  return str
    .replace(/([a-z])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase();
};

export const pascalCase = (str: string): string => {
  if (!str) return '';
  return str
    .toLowerCase()
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase())
    .replace(/^[a-z]/, chr => chr.toUpperCase());
};

export const truncate = (str: string, length: number, suffix: string = '...'): string => {
  if (!str || str.length <= length) return str;
  return str.substring(0, length - suffix.length) + suffix;
};

export const truncateWords = (str: string, wordCount: number, suffix: string = '...'): string => {
  if (!str) return '';
  const words = str.split(' ');
  if (words.length <= wordCount) return str;
  return words.slice(0, wordCount).join(' ') + suffix;
};

export const slugify = (str: string): string => {
  if (!str) return '';
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

export const removeAccents = (str: string): string => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
};

export const escapeHtml = (str: string): string => {
  if (!str) return '';
  const map: {[key: string]: string} = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };
  return str.replace(/[&<>"']/g, (m) => map[m]);
};

export const unescapeHtml = (str: string): string => {
  if (!str) return '';
  const map: {[key: string]: string} = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
  };
  return str.replace(/&(amp|lt|gt|quot|#39);/g, (m) => map[m]);
};

export const stripHtml = (str: string): string => {
  if (!str) return '';
  return str.replace(/<[^>]*>/g, '');
};

export const stripWhitespace = (str: string): string => {
  if (!str) return '';
  return str.replace(/\s+/g, ' ').trim();
};

export const stripNewlines = (str: string): string => {
  if (!str) return '';
  return str.replace(/[\r\n]+/g, ' ');
};

export const normalizeWhitespace = (str: string): string => {
  if (!str) return '';
  return str.replace(/\s+/g, ' ').trim();
};

export const padLeft = (str: string, length: number, pad: string = ' '): string => {
  if (!str) str = '';
  if (str.length >= length) return str;
  return pad.repeat(length - str.length) + str;
};

export const padRight = (str: string, length: number, pad: string = ' '): string => {
  if (!str) str = '';
  if (str.length >= length) return str;
  return str + pad.repeat(length - str.length);
};

export const padCenter = (str: string, length: number, pad: string = ' '): string => {
  if (!str) str = '';
  if (str.length >= length) return str;
  const totalPad = length - str.length;
  const leftPad = Math.floor(totalPad / 2);
  const rightPad = totalPad - leftPad;
  return pad.repeat(leftPad) + str + pad.repeat(rightPad);
};

export const repeat = (str: string, count: number): string => {
  if (!str || count <= 0) return '';
  return str.repeat(count);
};

export const reverse = (str: string): string => {
  if (!str) return '';
  return str.split('').reverse().join('');
};

export const shuffle = (str: string): string => {
  if (!str) return '';
  const array = str.split('');
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
  return array.join('');
};

export const randomString = (length: number, charset: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'): string => {
  let result = '';
  for (let i = 0; i < length; i++) {
    result += charset.charAt(Math.floor(Math.random() * charset.length));
  }
  return result;
};

export const uuid = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

export const isValidEmail = (email: string): boolean => {
  if (!email) return false;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidPhone = (phone: string): boolean => {
  if (!phone) return false;
  const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
  return phoneRegex.test(phone);
};

export const isValidUrl = (url: string): boolean => {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidUuid = (uuid: string): boolean => {
  if (!uuid) return false;
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};

export const isValidJson = (json: string): boolean => {
  if (!json) return false;
  try {
    JSON.parse(json);
    return true;
  } catch {
    return false;
  }
};

export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatNumber = (num: number, decimals: number = 0): string => {
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  if (isNaN(amount)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
};

export const formatPercentage = (value: number, decimals: number = 1): string => {
  if (isNaN(value)) return '0%';
  return (value * 100).toFixed(decimals) + '%';
};

export const formatDuration = (seconds: number): string => {
  if (isNaN(seconds) || seconds < 0) return '0s';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
  }
};

export const formatDistance = (meters: number): string => {
  if (isNaN(meters) || meters < 0) return '0m';
  
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  } else {
    return `${(meters / 1000).toFixed(1)}km`;
  }
};

export const formatSpeed = (metersPerSecond: number): string => {
  if (isNaN(metersPerSecond) || metersPerSecond < 0) return '0 m/s';
  
  const kmh = metersPerSecond * 3.6;
  if (kmh < 1) {
    return `${Math.round(metersPerSecond * 100)} cm/s`;
  } else {
    return `${kmh.toFixed(1)} km/h`;
  }
};

export const formatTemperature = (celsius: number, unit: 'C' | 'F' = 'C'): string => {
  if (isNaN(celsius)) return '0°C';
  
  if (unit === 'F') {
    const fahrenheit = (celsius * 9/5) + 32;
    return `${fahrenheit.toFixed(1)}°F`;
  } else {
    return `${celsius.toFixed(1)}°C`;
  }
};

export const formatPressure = (pascals: number): string => {
  if (isNaN(pascals) || pascals < 0) return '0 Pa';
  
  if (pascals < 1000) {
    return `${Math.round(pascals)} Pa`;
  } else {
    return `${(pascals / 1000).toFixed(1)} kPa`;
  }
};

export const formatFrequency = (hertz: number): string => {
  if (isNaN(hertz) || hertz < 0) return '0 Hz';
  
  if (hertz < 1000) {
    return `${Math.round(hertz)} Hz`;
  } else if (hertz < 1000000) {
    return `${(hertz / 1000).toFixed(1)} kHz`;
  } else {
    return `${(hertz / 1000000).toFixed(1)} MHz`;
  }
};
