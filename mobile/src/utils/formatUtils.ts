/**
 * Format Utility Functions
 * Common formatting functions for display
 */

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

export const formatVoltage = (volts: number): string => {
  if (isNaN(volts)) return '0 V';
  return `${volts.toFixed(1)} V`;
};

export const formatCurrent = (amperes: number): string => {
  if (isNaN(amperes)) return '0 A';
  return `${amperes.toFixed(1)} A`;
};

export const formatPower = (watts: number): string => {
  if (isNaN(watts)) return '0 W';
  return `${watts.toFixed(1)} W`;
};

export const formatEnergy = (joules: number): string => {
  if (isNaN(joules)) return '0 J';
  return `${joules.toFixed(1)} J`;
};

export const formatForce = (newtons: number): string => {
  if (isNaN(newtons)) return '0 N';
  return `${newtons.toFixed(1)} N`;
};

export const formatMass = (kilograms: number): string => {
  if (isNaN(kilograms)) return '0 kg';
  return `${kilograms.toFixed(1)} kg`;
};

export const formatLength = (meters: number): string => {
  if (isNaN(meters)) return '0 m';
  return `${meters.toFixed(1)} m`;
};

export const formatArea = (squareMeters: number): string => {
  if (isNaN(squareMeters)) return '0 m²';
  return `${squareMeters.toFixed(1)} m²`;
};

export const formatVolume = (cubicMeters: number): string => {
  if (isNaN(cubicMeters)) return '0 m³';
  return `${cubicMeters.toFixed(1)} m³`;
};

export const formatAngle = (radians: number): string => {
  if (isNaN(radians)) return '0°';
  const degrees = (radians * 180) / Math.PI;
  return `${degrees.toFixed(1)}°`;
};

export const formatCoordinate = (coordinate: number, precision: number = 6): string => {
  if (isNaN(coordinate)) return '0.000000';
  return coordinate.toFixed(precision);
};

export const formatLatitude = (latitude: number): string => {
  if (isNaN(latitude)) return '0.000000°';
  const abs = Math.abs(latitude);
  const direction = latitude >= 0 ? 'N' : 'S';
  return `${abs.toFixed(6)}°${direction}`;
};

export const formatLongitude = (longitude: number): string => {
  if (isNaN(longitude)) return '0.000000°';
  const abs = Math.abs(longitude);
  const direction = longitude >= 0 ? 'E' : 'W';
  return `${abs.toFixed(6)}°${direction}`;
};

export const formatAltitude = (altitude: number): string => {
  if (isNaN(altitude)) return '0 m';
  return `${altitude.toFixed(1)} m`;
};

export const formatAccuracy = (accuracy: number): string => {
  if (isNaN(accuracy)) return '0 m';
  return `±${accuracy.toFixed(1)} m`;
};

export const formatHeading = (heading: number): string => {
  if (isNaN(heading)) return '0°';
  return `${heading.toFixed(1)}°`;
};

export const formatTimestamp = (timestamp: number): string => {
  if (isNaN(timestamp)) return '0';
  return new Date(timestamp).toISOString();
};

export const formatDate = (date: Date | string, format: 'short' | 'long' | 'time' | 'datetime' = 'short'): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(d.getTime())) {
    return 'Invalid Date';
  }
  
  switch (format) {
    case 'short':
      return d.toLocaleDateString();
    case 'long':
      return d.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    case 'time':
      return d.toLocaleTimeString();
    case 'datetime':
      return d.toLocaleString();
    default:
      return d.toLocaleDateString();
  }
};

export const formatRelativeTime = (date: Date | string): string => {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMinutes < 1) {
    return 'Just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return formatDate(d, 'short');
  }
};

export const formatFileSize = (bytes: number): string => {
  return formatBytes(bytes);
};

export const formatFileType = (fileName: string): string => {
  if (!fileName) return 'Unknown';
  const extension = fileName.split('.').pop()?.toLowerCase();
  return extension ? extension.toUpperCase() : 'Unknown';
};

export const formatFileName = (fileName: string, maxLength: number = 20): string => {
  if (!fileName) return 'Unknown';
  if (fileName.length <= maxLength) return fileName;
  
  const extension = fileName.split('.').pop();
  const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'));
  const truncatedName = nameWithoutExt.substring(0, maxLength - extension!.length - 4);
  
  return `${truncatedName}...${extension}`;
};

export const formatUrl = (url: string, maxLength: number = 30): string => {
  if (!url) return '';
  if (url.length <= maxLength) return url;
  
  const start = url.substring(0, maxLength - 3);
  return `${start}...`;
};

export const formatEmail = (email: string, maxLength: number = 25): string => {
  if (!email) return '';
  if (email.length <= maxLength) return email;
  
  const [local, domain] = email.split('@');
  if (local.length + domain.length + 1 <= maxLength) return email;
  
  const truncatedLocal = local.substring(0, maxLength - domain.length - 4);
  return `${truncatedLocal}...@${domain}`;
};

export const formatPhoneNumber = (phone: string): string => {
  if (!phone) return '';
  
  // Remove all non-digit characters
  const digits = phone.replace(/\D/g, '');
  
  // Format as (XXX) XXX-XXXX for US numbers
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  
  // Format as +X (XXX) XXX-XXXX for international numbers
  if (digits.length === 11 && digits[0] === '1') {
    return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  }
  
  // Return original if it doesn't match expected patterns
  return phone;
};

export const formatCreditCard = (cardNumber: string): string => {
  if (!cardNumber) return '';
  
  // Remove all non-digit characters
  const digits = cardNumber.replace(/\D/g, '');
  
  // Format as XXXX XXXX XXXX XXXX
  if (digits.length === 16) {
    return `${digits.slice(0, 4)} ${digits.slice(4, 8)} ${digits.slice(8, 12)} ${digits.slice(12)}`;
  }
  
  // Return original if it doesn't match expected pattern
  return cardNumber;
};

export const formatExpiryDate = (expiryDate: string): string => {
  if (!expiryDate) return '';
  
  // Remove all non-digit characters
  const digits = expiryDate.replace(/\D/g, '');
  
  // Format as MM/YY
  if (digits.length === 4) {
    return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  }
  
  // Return original if it doesn't match expected pattern
  return expiryDate;
};

export const formatCvv = (cvv: string): string => {
  if (!cvv) return '';
  
  // Remove all non-digit characters
  const digits = cvv.replace(/\D/g, '');
  
  // Return up to 4 digits
  return digits.slice(0, 4);
};

export const formatSsn = (ssn: string): string => {
  if (!ssn) return '';
  
  // Remove all non-digit characters
  const digits = ssn.replace(/\D/g, '');
  
  // Format as XXX-XX-XXXX
  if (digits.length === 9) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
  }
  
  // Return original if it doesn't match expected pattern
  return ssn;
};

export const formatEin = (ein: string): string => {
  if (!ein) return '';
  
  // Remove all non-digit characters
  const digits = ein.replace(/\D/g, '');
  
  // Format as XX-XXXXXXX
  if (digits.length === 9) {
    return `${digits.slice(0, 2)}-${digits.slice(2)}`;
  }
  
  // Return original if it doesn't match expected pattern
  return ein;
};

export const formatVin = (vin: string): string => {
  if (!vin) return '';
  
  // VIN should be 17 characters
  if (vin.length === 17) {
    return vin.toUpperCase();
  }
  
  // Return original if it doesn't match expected pattern
  return vin;
};

export const formatLicensePlate = (plate: string): string => {
  if (!plate) return '';
  
  // Convert to uppercase and remove extra spaces
  return plate.toUpperCase().replace(/\s+/g, ' ');
};

export const formatPassport = (passport: string): string => {
  if (!passport) return '';
  
  // Convert to uppercase
  return passport.toUpperCase();
};

export const formatDriversLicense = (license: string): string => {
  if (!license) return '';
  
  // Convert to uppercase and remove extra spaces
  return license.toUpperCase().replace(/\s+/g, ' ');
};

export const formatIsbn = (isbn: string): string => {
  if (!isbn) return '';
  
  // Remove hyphens and spaces
  const cleaned = isbn.replace(/[\s-]/g, '');
  
  // Format as XXX-XXXXXXXXX for ISBN-10
  if (cleaned.length === 10) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
  }
  
  // Format as XXX-XXXXXXXXXXXX for ISBN-13
  if (cleaned.length === 13) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 12)}-${cleaned.slice(12)}`;
  }
  
  // Return original if it doesn't match expected patterns
  return isbn;
};

export const formatUuid = (uuid: string): string => {
  if (!uuid) return '';
  
  // Remove hyphens and spaces
  const cleaned = uuid.replace(/[\s-]/g, '');
  
  // Format as XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
  if (cleaned.length === 32) {
    return `${cleaned.slice(0, 8)}-${cleaned.slice(8, 12)}-${cleaned.slice(12, 16)}-${cleaned.slice(16, 20)}-${cleaned.slice(20)}`;
  }
  
  // Return original if it doesn't match expected pattern
  return uuid;
};

export const formatHexColor = (color: string): string => {
  if (!color) return '';
  
  // Remove # if present
  const cleaned = color.replace('#', '');
  
  // Convert to uppercase
  return `#${cleaned.toUpperCase()}`;
};

export const formatRgbColor = (r: number, g: number, b: number): string => {
  if (isNaN(r) || isNaN(g) || isNaN(b)) return 'rgb(0, 0, 0)';
  
  return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
};

export const formatHslColor = (h: number, s: number, l: number): string => {
  if (isNaN(h) || isNaN(s) || isNaN(l)) return 'hsl(0, 0%, 0%)';
  
  return `hsl(${Math.round(h)}, ${Math.round(s)}%, ${Math.round(l)}%)`;
};

export const formatVersion = (version: string): string => {
  if (!version) return '0.0.0';
  
  // Remove any non-digit and non-dot characters
  const cleaned = version.replace(/[^\d.]/g, '');
  
  // Split by dots and ensure we have at least 3 parts
  const parts = cleaned.split('.').filter(part => part.length > 0);
  
  // Pad with zeros if needed
  while (parts.length < 3) {
    parts.push('0');
  }
  
  // Take only the first 3 parts
  return parts.slice(0, 3).join('.');
};

export const formatSemanticVersion = (version: string): string => {
  if (!version) return '0.0.0';
  
  // Remove any non-digit, non-dot, and non-hyphen characters
  const cleaned = version.replace(/[^\d.-]/g, '');
  
  // Split by dots and hyphens
  const parts = cleaned.split(/[.-]/).filter(part => part.length > 0);
  
  // Ensure we have at least 3 parts
  while (parts.length < 3) {
    parts.push('0');
  }
  
  // Take only the first 3 parts
  return parts.slice(0, 3).join('.');
};

export const formatIpAddress = (ip: string): string => {
  if (!ip) return '0.0.0.0';
  
  // Remove any non-digit and non-dot characters
  const cleaned = ip.replace(/[^\d.]/g, '');
  
  // Split by dots
  const parts = cleaned.split('.').filter(part => part.length > 0);
  
  // Ensure we have exactly 4 parts
  while (parts.length < 4) {
    parts.push('0');
  }
  
  // Take only the first 4 parts
  return parts.slice(0, 4).join('.');
};

export const formatMacAddress = (mac: string): string => {
  if (!mac) return '00:00:00:00:00:00';
  
  // Remove any non-hex characters
  const cleaned = mac.replace(/[^0-9A-Fa-f]/g, '');
  
  // Ensure we have exactly 12 characters
  const padded = cleaned.padEnd(12, '0').slice(0, 12);
  
  // Format as XX:XX:XX:XX:XX:XX
  return `${padded.slice(0, 2)}:${padded.slice(2, 4)}:${padded.slice(4, 6)}:${padded.slice(6, 8)}:${padded.slice(8, 10)}:${padded.slice(10)}`.toUpperCase();
};

export const formatPostalCode = (postalCode: string, country: string = 'US'): string => {
  if (!postalCode) return '';
  
  // Remove any non-alphanumeric characters
  const cleaned = postalCode.replace(/[^A-Za-z0-9]/g, '');
  
  // Format based on country
  if (country.toUpperCase() === 'US') {
    // Format as XXXXX or XXXXX-XXXX
    if (cleaned.length === 5) {
      return cleaned;
    } else if (cleaned.length === 9) {
      return `${cleaned.slice(0, 5)}-${cleaned.slice(5)}`;
    }
  } else if (country.toUpperCase() === 'CA') {
    // Format as X9X 9X9
    if (cleaned.length === 6) {
      return `${cleaned.slice(0, 3)} ${cleaned.slice(3)}`;
    }
  } else if (country.toUpperCase() === 'UK') {
    // Format as XX9 9XX
    if (cleaned.length === 6) {
      return `${cleaned.slice(0, 3)} ${cleaned.slice(3)}`;
    }
  }
  
  // Return original if it doesn't match expected patterns
  return postalCode;
};
