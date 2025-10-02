import pytest
import json
import io
from unittest.mock import patch, MagicMock
from main import app

@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_ifc_data():
    """Sample IFC data for testing"""
    return b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('0',$,$,$,(#2),#3);
#2=IFCOWNERHISTORY($,$,$,$,$,$,$,$,$);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,$,$);
#4=IFCBUILDING('Building-1',$,$,$,$,$,$,$,$);
#5=IFCBUILDINGSTOREY('Storey-1',$,$,$,$,$,$,$,$);
#6=IFCSPACE('Space-1',$,$,$,$,$,$,$,$);
#7=IFCWALL('Wall-1',$,$,$,$,$,$,$,$);
#8=IFCDOOR('Door-1',$,$,$,$,$,$,$,$);
#9=IFCWINDOW('Window-1',$,$,$,$,$,$,$,$);
#10=IFCFLOWTERMINAL('Terminal-1',$,$,$,$,$,$,$,$);
ENDSEC;

END-ISO-10303-21;"""

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'ifcopenshell'
    assert 'version' in data
    assert 'timestamp' in data

def test_parse_ifc_success(client, sample_ifc_data):
    """Test successful IFC parsing"""
    response = client.post('/api/parse', data=sample_ifc_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['buildings'] >= 0
    assert data['spaces'] >= 0
    assert data['equipment'] >= 0
    assert 'metadata' in data
    assert 'processing_time' in data['metadata']

def test_parse_ifc_no_data(client):
    """Test IFC parsing with no data"""
    response = client.post('/api/parse')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data
    assert data['error']['code'] == 'NO_DATA'

def test_parse_ifc_file_too_large(client):
    """Test IFC parsing with file too large"""
    large_data = b'x' * (101 * 1024 * 1024)  # 101MB
    
    response = client.post('/api/parse', data=large_data)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data
    assert data['error']['code'] == 'FILE_TOO_LARGE'

def test_parse_ifc_invalid_format(client):
    """Test IFC parsing with invalid format"""
    invalid_data = b"Not an IFC file"
    
    response = client.post('/api/parse', data=invalid_data)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data

def test_validate_ifc_success(client, sample_ifc_data):
    """Test successful IFC validation"""
    response = client.post('/api/validate', data=sample_ifc_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'valid' in data
    assert 'warnings' in data
    assert 'errors' in data
    assert 'compliance' in data
    assert 'metadata' in data

def test_validate_ifc_no_data(client):
    """Test IFC validation with no data"""
    response = client.post('/api/validate')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data
    assert data['error']['code'] == 'NO_DATA'

def test_validate_ifc_invalid_format(client):
    """Test IFC validation with invalid format"""
    invalid_data = b"Not an IFC file"
    
    response = client.post('/api/validate', data=invalid_data)
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data

def test_metrics_endpoint(client):
    """Test the metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'ifc_requests_total' in data
    assert 'cache_size' in data
    assert 'max_file_size' in data
    assert 'cache_enabled' in data

@patch('main.ifcopenshell')
def test_parse_ifc_with_mock(mock_ifcopenshell, client, sample_ifc_data):
    """Test IFC parsing with mocked ifcopenshell"""
    # Mock the ifcopenshell.open method
    mock_model = MagicMock()
    mock_model.by_type.side_effect = lambda entity_type: {
        'IfcBuilding': [MagicMock() for _ in range(1)],
        'IfcSpace': [MagicMock() for _ in range(2)],
        'IfcFlowTerminal': [MagicMock() for _ in range(3)],
        'IfcWall': [MagicMock() for _ in range(4)],
        'IfcDoor': [MagicMock() for _ in range(5)],
        'IfcWindow': [MagicMock() for _ in range(6)],
    }.get(entity_type, [])
    
    mock_model.schema = 'IFC4'
    mock_ifcopenshell.open.return_value = mock_model
    
    response = client.post('/api/parse', data=sample_ifc_data)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['buildings'] == 1
    assert data['spaces'] == 2
    assert data['equipment'] == 3
    assert data['walls'] == 4
    assert data['doors'] == 5
    assert data['windows'] == 6
    assert data['metadata']['ifc_version'] == 'IFC4'

@patch('main.ifcopenshell')
def test_parse_ifc_error_handling(mock_ifcopenshell, client, sample_ifc_data):
    """Test IFC parsing error handling"""
    # Mock ifcopenshell to raise an exception
    mock_ifcopenshell.open.side_effect = Exception("Test error")
    
    response = client.post('/api/parse', data=sample_ifc_data)
    assert response.status_code == 500
    
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'error' in data
    assert data['error']['code'] == 'INTERNAL_ERROR'

def test_cache_functionality(client, sample_ifc_data):
    """Test cache functionality"""
    # First request
    response1 = client.post('/api/parse', data=sample_ifc_data)
    assert response1.status_code == 200
    
    # Second request (should use cache)
    response2 = client.post('/api/parse', data=sample_ifc_data)
    assert response2.status_code == 200
    
    # Both responses should be identical
    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    assert data1 == data2

def test_health_check_with_ifcopenshell_error(client):
    """Test health check when ifcopenshell fails"""
    with patch('main.ifcopenshell.file') as mock_file:
        mock_file.side_effect = Exception("IfcOpenShell error")
        
        response = client.get('/health')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'
        assert 'error' in data
