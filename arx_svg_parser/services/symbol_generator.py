"""
Automated Symbol Generator Service
Generates YAML symbol definitions from building system product URLs
"""

import requests
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import json
from bs4 import BeautifulSoup
import base64
from PIL import Image
import io
import os
from pathlib import Path

from structlog import get_logger

logger = get_logger()

class SymbolGenerator:
    """Automated symbol generator from product URLs"""
    
    def __init__(self):
        self.supported_domains = {
            'carrier.com': self._extract_carrier,
            'trane.com': self._extract_trane,
            'johnsoncontrols.com': self._extract_johnson_controls,
            'honeywell.com': self._extract_honeywell,
            'siemens.com': self._extract_siemens,
            'schneider-electric.com': self._extract_schneider,
            'abb.com': self._extract_abb,
            'eaton.com': self._extract_eaton,
            'schneider-electric.us': self._extract_schneider,
        }
        
        self.system_keywords = {
            'hvac': ['air', 'heating', 'cooling', 'ventilation', 'damper', 'duct', 'fan', 'coil'],
            'electrical': ['electrical', 'power', 'switch', 'outlet', 'panel', 'circuit', 'voltage'],
            'plumbing': ['water', 'pipe', 'valve', 'pump', 'fixture', 'drain'],
            'fire_safety': ['fire', 'smoke', 'alarm', 'detector', 'sprinkler'],
            'security': ['camera', 'access', 'control', 'surveillance', 'card'],
            'av': ['audio', 'video', 'speaker', 'display', 'projector', 'microphone']
        }
    
    def generate_symbol_from_url(self, url: str, user_id: int) -> Dict:
        """
        Generate a symbol JSON from a product URL
        
        Args:
            url: Product URL to scrape
            user_id: ID of user creating the symbol
            
        Returns:
            Dict containing generated symbol data and status
        """
        try:
            # Validate URL
            if not self._validate_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format'
                }
            
            # Extract domain and determine extraction method
            domain = urlparse(url).netloc.lower()
            extractor = self._get_extractor(domain)
            
            if not extractor:
                return {
                    'success': False,
                    'error': f'Unsupported domain: {domain}. Supported domains: {list(self.supported_domains.keys())}'
                }
            
            # Extract product data
            product_data = extractor(url)
            if not product_data:
                return {
                    'success': False,
                    'error': 'Failed to extract product data from URL'
                }
            
            # Generate symbol data
            symbol_data = self._generate_symbol_data(product_data, user_id)
            
            # Generate SVG
            svg_content = self._generate_svg(product_data)
            
            # Create JSON content
            json_content = self._create_json_content(symbol_data, svg_content)
            
            return {
                'success': True,
                'symbol_data': symbol_data,
                'json_content': json_content,
                'svg_preview': svg_content,
                'product_data': product_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating symbol: {str(e)}'
            }
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _get_extractor(self, domain: str):
        """Get appropriate extractor for domain"""
        for supported_domain, extractor in self.supported_domains.items():
            if supported_domain in domain:
                return extractor
        return None
    
    def _extract_carrier(self, url: str) -> Dict:
        """Extract product data from Carrier website"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product information
            product_data = {
                'name': self._extract_text(soup, ['h1', '.product-title', '.product-name']),
                'category': 'hvac',
                'manufacturer': 'Carrier',
                'description': self._extract_text(soup, ['.product-description', '.description', 'p']),
                'specifications': self._extract_specifications(soup),
                'image_url': self._extract_image(soup),
                'model_number': self._extract_model_number(soup),
                'url': url
            }
            
            return product_data
        except Exception as e:
            print(f"Error extracting from Carrier: {e}")
            return None
    
    def _extract_trane(self, url: str) -> Dict:
        """Extract product data from Trane website"""
        # Similar implementation for Trane
        return self._extract_carrier(url)  # Use same logic for now
    
    def _extract_johnson_controls(self, url: str) -> Dict:
        """Extract product data from Johnson Controls website"""
        return self._extract_carrier(url)
    
    def _extract_honeywell(self, url: str) -> Dict:
        """Extract product data from Honeywell website"""
        return self._extract_carrier(url)
    
    def _extract_siemens(self, url: str) -> Dict:
        """Extract product data from Siemens website"""
        return self._extract_carrier(url)
    
    def _extract_schneider(self, url: str) -> Dict:
        """Extract product data from Schneider Electric website"""
        return self._extract_carrier(url)
    
    def _extract_abb(self, url: str) -> Dict:
        """Extract product data from ABB website"""
        return self._extract_carrier(url)
    
    def _extract_eaton(self, url: str) -> Dict:
        """Extract product data from Eaton website"""
        return self._extract_carrier(url)
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extract text using multiple selectors"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        return ""
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict:
        """Extract product specifications"""
        specs = {}
        
        # Look for specification tables
        spec_tables = soup.find_all('table')
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value:
                        specs[key] = value
        
        return specs
    
    def _extract_image(self, soup: BeautifulSoup) -> str:
        """Extract product image URL"""
        img_selectors = [
            '.product-image img',
            '.main-image img',
            '.hero-image img',
            'img[alt*="product"]',
            'img[alt*="Product"]'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return img['src']
        
        return ""
    
    def _extract_model_number(self, soup: BeautifulSoup) -> str:
        """Extract model number from page"""
        # Look for model number patterns
        text = soup.get_text()
        model_patterns = [
            r'Model[:\s]+([A-Z0-9\-]+)',
            r'Part[:\s]+([A-Z0-9\-]+)',
            r'Catalog[:\s]+([A-Z0-9\-]+)',
            r'([A-Z]{2,4}\d{2,4}[A-Z0-9\-]*)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _generate_symbol_data(self, product_data: Dict, user_id: int) -> Dict:
        """Generate symbol data from product information"""
        
        # Determine system category
        system = self._categorize_system(product_data)
        
        # Generate symbol ID
        symbol_id = self._generate_symbol_id(product_data['name'])
        
        # Generate display name
        display_name = self._generate_display_name(product_data['name'])
        
        # Determine category and subcategory
        category, subcategory = self._determine_category(product_data, system)
        
        return {
            'symbol_id': symbol_id,
            'system': system,
            'display_name': display_name,
            'category': category,
            'subcategory': subcategory,
            'description': product_data.get('description', ''),
            'manufacturer': product_data.get('manufacturer', ''),
            'model_number': product_data.get('model_number', ''),
            'specifications': product_data.get('specifications', {}),
            'created_by': user_id,
            'source_url': product_data.get('url', ''),
            'created_at': '2024-01-XX'
        }
    
    def _categorize_system(self, product_data: Dict) -> str:
        """Categorize product into system type"""
        text = f"{product_data.get('name', '')} {product_data.get('description', '')}".lower()
        
        for system, keywords in self.system_keywords.items():
            if any(keyword in text for keyword in keywords):
                return system
        
        return 'other'
    
    def _generate_symbol_id(self, name: str) -> str:
        """Generate symbol ID from product name"""
        # Convert to lowercase, replace spaces with underscores, remove special chars
        symbol_id = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
        symbol_id = re.sub(r'\s+', '_', symbol_id.strip())
        
        # Ensure it's not too long
        if len(symbol_id) > 30:
            symbol_id = symbol_id[:30]
        
        return symbol_id
    
    def _generate_display_name(self, name: str) -> str:
        """Generate display name from product name"""
        # Clean up the name for display
        display_name = name.strip()
        
        # Remove manufacturer prefixes if present
        manufacturers = ['Carrier', 'Trane', 'Honeywell', 'Siemens', 'Johnson Controls']
        for manufacturer in manufacturers:
            if display_name.startswith(manufacturer):
                display_name = display_name[len(manufacturer):].strip()
        
        return display_name
    
    def _determine_category(self, product_data: Dict, system: str) -> Tuple[str, str]:
        """Determine category and subcategory"""
        name = product_data.get('name', '').lower()
        description = product_data.get('description', '').lower()
        text = f"{name} {description}"
        
        # HVAC categories
        if system == 'hvac':
            if any(word in text for word in ['air handler', 'ahu', 'air handling']):
                return 'hvac', 'air_handling'
            elif any(word in text for word in ['chiller', 'cooling']):
                return 'hvac', 'cooling'
            elif any(word in text for word in ['boiler', 'heating']):
                return 'hvac', 'heating'
            elif any(word in text for word in ['damper', 'ventilation']):
                return 'hvac', 'ventilation'
            else:
                return 'hvac', 'other'
        
        # Electrical categories
        elif system == 'electrical':
            if any(word in text for word in ['panel', 'switchboard']):
                return 'electrical', 'panels'
            elif any(word in text for word in ['outlet', 'receptacle']):
                return 'electrical', 'outlets'
            elif any(word in text for word in ['switch', 'dimmer']):
                return 'electrical', 'switches'
            else:
                return 'electrical', 'other'
        
        # Default
        return system, 'other'
    
    def _generate_svg(self, product_data: Dict) -> str:
        """Generate SVG content for the symbol"""
        # This is a simplified SVG generator
        # In a real implementation, you might use AI to generate more sophisticated SVGs
        
        symbol_id = self._generate_symbol_id(product_data.get('name', 'symbol'))
        system = self._categorize_system(product_data)
        
        # Generate different SVG based on system type
        if system == 'hvac':
            svg = f'''<g id="{symbol_id}">
  <rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/>
  <text x="20" y="15" font-size="10" text-anchor="middle">{symbol_id[:4].upper()}</text>
</g>'''
        elif system == 'electrical':
            svg = f'''<g id="{symbol_id}">
  <circle cx="10" cy="10" r="8" fill="#fff" stroke="#000"/>
  <text x="10" y="14" font-size="8" text-anchor="middle">{symbol_id[:3].upper()}</text>
</g>'''
        else:
            svg = f'''<g id="{symbol_id}">
  <rect x="0" y="0" width="30" height="15" fill="#eee" stroke="#000"/>
  <text x="15" y="12" font-size="8" text-anchor="middle">{symbol_id[:3].upper()}</text>
</g>'''
        
        return svg
    
    def _create_json_content(self, symbol_data: Dict, svg_content: str) -> str:
        """Create JSON content for the symbol"""
        
        json_data = {
            'symbol_id': symbol_data['symbol_id'],
            'system': symbol_data['system'],
            'display_name': symbol_data['display_name'],
            'category': symbol_data['category'],
            'subcategory': symbol_data['subcategory'],
            'description': symbol_data['description'],
            'svg_content': svg_content,
            'dimensions': {
                'width': 40,
                'height': 20
            },
            'default_scale': 1.0,
            'properties': [
                {
                    'name': 'manufacturer',
                    'type': 'string',
                    'description': 'Equipment manufacturer',
                    'required': False
                },
                {
                    'name': 'model_number',
                    'type': 'string',
                    'description': 'Equipment model number',
                    'required': False
                },
                {
                    'name': 'funding_source',
                    'type': 'string',
                    'description': 'Source of funding for this asset',
                    'required': False
                }
            ],
            'connections': [
                {
                    'type': 'electrical',
                    'description': 'Electrical power connection'
                }
            ],
            'tags': [
                symbol_data['system'],
                symbol_data['category'],
                symbol_data['subcategory']
            ],
            'metadata': {
                'created_by': symbol_data['created_by'],
                'source_url': symbol_data['source_url'],
                'created_at': symbol_data['created_at'],
                'auto_generated': True
            }
        }
        
        return json.dumps(json_data, indent=4)
    
    def save_symbol(self, json_content: str, symbol_id: str) -> bool:
        """Save the generated symbol to the symbol library"""
        try:
            # Create symbol library path
            symbol_library_path = Path("../arx-symbol-library")
            symbol_file = symbol_library_path / f"{symbol_id}.json"
            
            # Write JSON file
            with open(symbol_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            return True
        except Exception as e:
            print(f"Error saving symbol: {e}")
            return False 