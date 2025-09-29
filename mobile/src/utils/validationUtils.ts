/**
 * Validation Utility Functions
 * Common validation functions for forms and data
 */

import {VALIDATION_RULES} from '@/constants';

export const validateRequired = (value: any): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'object') return Object.keys(value).length > 0;
  return true;
};

export const validateMinLength = (value: string, minLength: number): boolean => {
  if (!value) return false;
  return value.trim().length >= minLength;
};

export const validateMaxLength = (value: string, maxLength: number): boolean => {
  if (!value) return true;
  return value.trim().length <= maxLength;
};

export const validateLength = (value: string, minLength: number, maxLength: number): boolean => {
  if (!value) return minLength === 0;
  const length = value.trim().length;
  return length >= minLength && length <= maxLength;
};

export const validateEmail = (email: string): boolean => {
  if (!email) return false;
  return VALIDATION_RULES.EMAIL_REGEX.test(email.trim());
};

export const validatePhone = (phone: string): boolean => {
  if (!phone) return false;
  return VALIDATION_RULES.PHONE_REGEX.test(phone.trim());
};

export const validateUrl = (url: string): boolean => {
  if (!url) return false;
  try {
    new URL(url.trim());
    return true;
  } catch {
    return false;
  }
};

export const validateUuid = (uuid: string): boolean => {
  if (!uuid) return false;
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid.trim());
};

export const validateJson = (json: string): boolean => {
  if (!json) return false;
  try {
    JSON.parse(json);
    return true;
  } catch {
    return false;
  }
};

export const validateNumeric = (value: string): boolean => {
  if (!value) return false;
  return !isNaN(Number(value)) && isFinite(Number(value));
};

export const validateInteger = (value: string): boolean => {
  if (!value) return false;
  return Number.isInteger(Number(value));
};

export const validatePositive = (value: number): boolean => {
  return value > 0;
};

export const validateNegative = (value: number): boolean => {
  return value < 0;
};

export const validateRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max;
};

export const validateUsername = (username: string): boolean => {
  if (!username) return false;
  const trimmed = username.trim();
  return validateLength(trimmed, VALIDATION_RULES.USERNAME_MIN_LENGTH, VALIDATION_RULES.USERNAME_MAX_LENGTH) &&
         /^[a-zA-Z0-9_-]+$/.test(trimmed);
};

export const validatePassword = (password: string): boolean => {
  if (!password) return false;
  const trimmed = password.trim();
  return validateLength(trimmed, VALIDATION_RULES.PASSWORD_MIN_LENGTH, VALIDATION_RULES.PASSWORD_MAX_LENGTH) &&
         /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/.test(trimmed);
};

export const validatePasswordStrength = (password: string): {
  score: number;
  feedback: string[];
} => {
  if (!password) return {score: 0, feedback: ['Password is required']};
  
  const feedback: string[] = [];
  let score = 0;
  
  // Length check
  if (password.length >= 8) {
    score += 1;
  } else {
    feedback.push('Password must be at least 8 characters long');
  }
  
  // Lowercase check
  if (/[a-z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Password must contain at least one lowercase letter');
  }
  
  // Uppercase check
  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Password must contain at least one uppercase letter');
  }
  
  // Number check
  if (/\d/.test(password)) {
    score += 1;
  } else {
    feedback.push('Password must contain at least one number');
  }
  
  // Special character check
  if (/[@$!%*?&]/.test(password)) {
    score += 1;
  } else {
    feedback.push('Password must contain at least one special character (@$!%*?&)');
  }
  
  return {score, feedback};
};

export const validateEquipmentName = (name: string): boolean => {
  if (!name) return false;
  const trimmed = name.trim();
  return validateLength(trimmed, VALIDATION_RULES.EQUIPMENT_NAME_MIN_LENGTH, VALIDATION_RULES.EQUIPMENT_NAME_MAX_LENGTH);
};

export const validateNote = (note: string): boolean => {
  if (!note) return true; // Notes are optional
  return note.trim().length <= VALIDATION_RULES.NOTE_MAX_LENGTH;
};

export const validateSearchQuery = (query: string): boolean => {
  if (!query) return false;
  const trimmed = query.trim();
  return validateLength(trimmed, VALIDATION_RULES.SEARCH_QUERY_MIN_LENGTH, VALIDATION_RULES.SEARCH_QUERY_MAX_LENGTH);
};

export const validateFileSize = (fileSize: number, maxSize: number): boolean => {
  return fileSize <= maxSize;
};

export const validateFileType = (fileName: string, allowedTypes: string[]): boolean => {
  if (!fileName) return false;
  const extension = fileName.split('.').pop()?.toLowerCase();
  return extension ? allowedTypes.includes(extension) : false;
};

export const validateImageFile = (fileName: string): boolean => {
  const allowedTypes = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
  return validateFileType(fileName, allowedTypes);
};

export const validatePdfFile = (fileName: string): boolean => {
  return validateFileType(fileName, ['pdf']);
};

export const validateCsvFile = (fileName: string): boolean => {
  return validateFileType(fileName, ['csv']);
};

export const validateExcelFile = (fileName: string): boolean => {
  const allowedTypes = ['xls', 'xlsx'];
  return validateFileType(fileName, allowedTypes);
};

export const validateCoordinates = (lat: number, lng: number): boolean => {
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
};

export const validateAltitude = (altitude: number): boolean => {
  return altitude >= -1000 && altitude <= 100000; // Reasonable altitude range
};

export const validateAccuracy = (accuracy: number): boolean => {
  return accuracy >= 0 && accuracy <= 1000; // Accuracy in meters
};

export const validateHeading = (heading: number): boolean => {
  return heading >= 0 && heading < 360;
};

export const validateSpeed = (speed: number): boolean => {
  return speed >= 0 && speed <= 1000; // Speed in m/s
};

export const validateTemperature = (temperature: number): boolean => {
  return temperature >= -100 && temperature <= 100; // Temperature in Celsius
};

export const validatePressure = (pressure: number): boolean => {
  return pressure >= 0 && pressure <= 200000; // Pressure in Pascals
};

export const validateHumidity = (humidity: number): boolean => {
  return humidity >= 0 && humidity <= 100; // Humidity percentage
};

export const validateVoltage = (voltage: number): boolean => {
  return voltage >= 0 && voltage <= 1000; // Voltage in Volts
};

export const validateCurrent = (current: number): boolean => {
  return current >= 0 && current <= 1000; // Current in Amperes
};

export const validatePower = (power: number): boolean => {
  return power >= 0 && power <= 1000000; // Power in Watts
};

export const validateFrequency = (frequency: number): boolean => {
  return frequency >= 0 && frequency <= 1000000; // Frequency in Hz
};

export const validatePercentage = (percentage: number): boolean => {
  return percentage >= 0 && percentage <= 100;
};

export const validateRatio = (ratio: number): boolean => {
  return ratio >= 0 && ratio <= 1;
};

export const validateVersion = (version: string): boolean => {
  if (!version) return false;
  const versionRegex = /^\d+\.\d+\.\d+$/;
  return versionRegex.test(version.trim());
};

export const validateSemanticVersion = (version: string): boolean => {
  if (!version) return false;
  const semverRegex = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;
  return semverRegex.test(version.trim());
};

export const validateIpAddress = (ip: string): boolean => {
  if (!ip) return false;
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipRegex.test(ip.trim());
};

export const validateMacAddress = (mac: string): boolean => {
  if (!mac) return false;
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
  return macRegex.test(mac.trim());
};

export const validateHexColor = (color: string): boolean => {
  if (!color) return false;
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
  return hexRegex.test(color.trim());
};

export const validateRgbColor = (color: string): boolean => {
  if (!color) return false;
  const rgbRegex = /^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/;
  const match = color.trim().match(rgbRegex);
  if (!match) return false;
  
  const r = parseInt(match[1]);
  const g = parseInt(match[2]);
  const b = parseInt(match[3]);
  
  return r >= 0 && r <= 255 && g >= 0 && g <= 255 && b >= 0 && b <= 255;
};

export const validateHslColor = (color: string): boolean => {
  if (!color) return false;
  const hslRegex = /^hsl\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)$/;
  const match = color.trim().match(hslRegex);
  if (!match) return false;
  
  const h = parseInt(match[1]);
  const s = parseInt(match[2]);
  const l = parseInt(match[3]);
  
  return h >= 0 && h <= 360 && s >= 0 && s <= 100 && l >= 0 && l <= 100;
};

export const validateCreditCard = (cardNumber: string): boolean => {
  if (!cardNumber) return false;
  
  // Remove spaces and dashes
  const cleaned = cardNumber.replace(/[\s-]/g, '');
  
  // Check if it's all digits
  if (!/^\d+$/.test(cleaned)) return false;
  
  // Check length (13-19 digits)
  if (cleaned.length < 13 || cleaned.length > 19) return false;
  
  // Luhn algorithm
  let sum = 0;
  let isEven = false;
  
  for (let i = cleaned.length - 1; i >= 0; i--) {
    let digit = parseInt(cleaned[i]);
    
    if (isEven) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    
    sum += digit;
    isEven = !isEven;
  }
  
  return sum % 10 === 0;
};

export const validateExpiryDate = (expiryDate: string): boolean => {
  if (!expiryDate) return false;
  
  const dateRegex = /^(0[1-9]|1[0-2])\/([0-9]{2})$/;
  const match = expiryDate.trim().match(dateRegex);
  
  if (!match) return false;
  
  const month = parseInt(match[1]);
  const year = parseInt('20' + match[2]);
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth() + 1;
  
  if (year < currentYear || (year === currentYear && month < currentMonth)) {
    return false;
  }
  
  return true;
};

export const validateCvv = (cvv: string): boolean => {
  if (!cvv) return false;
  const cvvRegex = /^[0-9]{3,4}$/;
  return cvvRegex.test(cvv.trim());
};

export const validatePostalCode = (postalCode: string, country: string = 'US'): boolean => {
  if (!postalCode) return false;
  
  const patterns: {[key: string]: RegExp} = {
    US: /^\d{5}(-\d{4})?$/,
    CA: /^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$/,
    UK: /^[A-Za-z]{1,2}\d[A-Za-z\d]? \d[A-Za-z]{2}$/,
    DE: /^\d{5}$/,
    FR: /^\d{5}$/,
    JP: /^\d{3}-\d{4}$/,
    AU: /^\d{4}$/,
  };
  
  const pattern = patterns[country.toUpperCase()];
  if (!pattern) return false;
  
  return pattern.test(postalCode.trim());
};

export const validateSsn = (ssn: string): boolean => {
  if (!ssn) return false;
  const ssnRegex = /^\d{3}-\d{2}-\d{4}$/;
  return ssnRegex.test(ssn.trim());
};

export const validateEin = (ein: string): boolean => {
  if (!ein) return false;
  const einRegex = /^\d{2}-\d{7}$/;
  return einRegex.test(ein.trim());
};

export const validateIsbn = (isbn: string): boolean => {
  if (!isbn) return false;
  
  // Remove hyphens and spaces
  const cleaned = isbn.replace(/[\s-]/g, '');
  
  // Check if it's 10 or 13 digits
  if (cleaned.length === 10) {
    return validateIsbn10(cleaned);
  } else if (cleaned.length === 13) {
    return validateIsbn13(cleaned);
  }
  
  return false;
};

const validateIsbn10 = (isbn: string): boolean => {
  if (!/^\d{9}[\dX]$/.test(isbn)) return false;
  
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(isbn[i]) * (10 - i);
  }
  
  const checkDigit = isbn[9] === 'X' ? 10 : parseInt(isbn[9]);
  return (sum + checkDigit) % 11 === 0;
};

const validateIsbn13 = (isbn: string): boolean => {
  if (!/^\d{13}$/.test(isbn)) return false;
  
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(isbn[i]) * (i % 2 === 0 ? 1 : 3);
  }
  
  const checkDigit = (10 - (sum % 10)) % 10;
  return checkDigit === parseInt(isbn[12]);
};

export const validateVin = (vin: string): boolean => {
  if (!vin) return false;
  const vinRegex = /^[A-HJ-NPR-Z0-9]{17}$/;
  return vinRegex.test(vin.trim());
};

export const validateLicensePlate = (plate: string, state: string = 'US'): boolean => {
  if (!plate) return false;
  
  // Basic validation - can be enhanced for specific states
  const plateRegex = /^[A-Za-z0-9\s-]{1,8}$/;
  return plateRegex.test(plate.trim());
};

export const validatePassport = (passport: string, country: string = 'US'): boolean => {
  if (!passport) return false;
  
  const patterns: {[key: string]: RegExp} = {
    US: /^\d{9}$/,
    CA: /^[A-Za-z]{2}\d{6}$/,
    UK: /^\d{9}$/,
    DE: /^[A-Za-z]{2}\d{6}$/,
    FR: /^\d{2}[A-Za-z]{2}\d{5}$/,
    JP: /^[A-Za-z]{2}\d{7}$/,
    AU: /^[A-Za-z]{2}\d{7}$/,
  };
  
  const pattern = patterns[country.toUpperCase()];
  if (!pattern) return false;
  
  return pattern.test(passport.trim());
};

export const validateDriversLicense = (license: string, state: string = 'US'): boolean => {
  if (!license) return false;
  
  // Basic validation - can be enhanced for specific states
  const licenseRegex = /^[A-Za-z0-9\s-]{1,20}$/;
  return licenseRegex.test(license.trim());
};
