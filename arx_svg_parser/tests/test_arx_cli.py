"""
Tests for Arxos CLI functionality.

This module tests the command-line interface for building repository management,
ensuring all commands work correctly and handle edge cases properly.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from cmd.arx_cli import ArxCLI
from models.arxfile import ArxfileSchema, PermissionLevel, ShareType, ContractType


class TestArxCLI:
    """Test cases for Arxos CLI functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return ArxCLI()
    
    @pytest.fixture
    def mock_services(self):
        """Mock service dependencies."""
        with patch('cmd.arx_cli.VersionControlService') as mock_vc, \
             patch('cmd.arx_cli.AccessControlService') as mock_ac, \
             patch('cmd.arx_cli.EnhancedBIMAssemblyService') as mock_bim, \
             patch('cmd.arx_cli.ValidationFramework') as mock_val:
            
            # Configure mocks
            mock_vc.return_value = Mock()
            mock_ac.return_value = Mock()
            mock_bim.return_value = Mock()
            mock_val.return_value = Mock()
            
            yield {
                'version_control': mock_vc.return_value,
                'access_control': mock_ac.return_value,
                'bim_assembly': mock_bim.return_value,
                'validation': mock_val.return_value
            }
    
    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert cli.parser is not None
        assert cli.arxfile_manager is not None
        assert cli.version_control is None
        assert cli.access_control is None
        assert cli.bim_assembly is None
        assert cli.validation is None
    
    def test_parser_creation(self, cli):
        """Test argument parser creation."""
        parser = cli.parser
        
        # Test that all expected commands exist
        commands = ['init', 'pull', 'commit', 'merge', 'rollback', 
                   'share', 'status', 'log', 'validate', 'export', 'import']
        
        for command in commands:
            # Check if command exists in subparsers
            found = False
            for action in parser._subparsers._group_actions:
                if hasattr(action, 'choices'):
                    if command in action.choices:
                        found = True
                        break
            assert found, f"Command '{command}' not found in parser"
    
    def test_init_command_success(self, cli, temp_dir, mock_services):
        """Test successful repository initialization."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Mock arxfile manager
            with patch.object(cli.arxfile_manager, 'create_new') as mock_create, \
                 patch.object(cli.arxfile_manager, 'save') as mock_save:
                
                mock_schema = Mock(spec=ArxfileSchema)
                mock_create.return_value = mock_schema
                
                # Mock version control initialization
                mock_services['version_control'].initialize_repository.return_value = {'success': True}
                
                # Test init command
                args = cli.parser.parse_args([
                    'init', 'test-building', 'Test Building', 'commercial',
                    '--owner', 'owner123', '--floors', '3', '--area', '5000'
                ])
                
                result = cli.cmd_init(args)
                
                assert result == 0
                mock_create.assert_called_once()
                mock_save.assert_called_once()
                mock_services['version_control'].initialize_repository.assert_called_once_with('test-building')
                
        finally:
            os.chdir(original_cwd)
    
    def test_init_command_missing_owner(self, cli):
        """Test init command with missing required owner."""
        args = cli.parser.parse_args([
            'init', 'test-building', 'Test Building', 'commercial'
        ])
        
        # Should fail due to missing --owner
        with pytest.raises(SystemExit):
            cli.cmd_init(args)
    
    def test_pull_command_success(self, cli, mock_services):
        """Test successful pull command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock successful pull
        mock_services['version_control'].pull_changes.return_value = {
            'success': True,
            'changes': ['change1', 'change2']
        }
        
        args = cli.parser.parse_args(['pull', 'test-building'])
        result = cli.cmd_pull(args)
        
        assert result == 0
        mock_services['version_control'].pull_changes.assert_called_once_with(
            building_id='test-building',
            branch='main',
            force=False
        )
    
    def test_pull_command_no_arxfile(self, cli):
        """Test pull command without arxfile."""
        cli.arxfile_manager.schema = None
        
        args = cli.parser.parse_args(['pull', 'test-building'])
        result = cli.cmd_pull(args)
        
        assert result == 1
    
    def test_commit_command_success(self, cli, mock_services):
        """Test successful commit command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock pending changes
        mock_services['version_control'].get_pending_changes.return_value = {
            'objects': ['obj1', 'obj2']
        }
        
        # Mock successful commit
        mock_services['version_control'].create_version.return_value = {
            'success': True,
            'version_id': 'v1.0.1'
        }
        
        args = cli.parser.parse_args(['commit', '-m', 'Test commit'])
        result = cli.cmd_commit(args)
        
        assert result == 0
        mock_services['version_control'].create_version.assert_called_once()
    
    def test_commit_command_no_changes(self, cli, mock_services):
        """Test commit command with no pending changes."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock no pending changes
        mock_services['version_control'].get_pending_changes.return_value = {}
        
        args = cli.parser.parse_args(['commit', '-m', 'Test commit'])
        result = cli.cmd_commit(args)
        
        assert result == 0
    
    def test_merge_command_success(self, cli, mock_services):
        """Test successful merge command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock successful merge request creation
        mock_services['version_control'].create_merge_request.return_value = {
            'success': True,
            'merge_request_id': 'mr-001',
            'conflicts': []
        }
        
        # Mock successful merge
        mock_services['version_control'].merge_request.return_value = {
            'success': True
        }
        
        args = cli.parser.parse_args(['merge', 'feature-branch', 'main'])
        result = cli.cmd_merge(args)
        
        assert result == 0
        mock_services['version_control'].create_merge_request.assert_called_once()
        mock_services['version_control'].merge_request.assert_called_once()
    
    def test_merge_command_with_conflicts(self, cli, mock_services):
        """Test merge command with conflicts."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock merge request with conflicts
        mock_services['version_control'].create_merge_request.return_value = {
            'success': True,
            'merge_request_id': 'mr-001',
            'conflicts': ['conflict1', 'conflict2']
        }
        
        args = cli.parser.parse_args(['merge', 'feature-branch', 'main'])
        result = cli.cmd_merge(args)
        
        assert result == 0  # Should still succeed but warn about conflicts
    
    def test_rollback_command_success(self, cli, mock_services):
        """Test successful rollback command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock successful rollback
        mock_services['version_control'].rollback_to_version.return_value = {
            'success': True
        }
        
        args = cli.parser.parse_args(['rollback', 'v1.0.0'])
        result = cli.cmd_rollback(args)
        
        assert result == 0
        mock_services['version_control'].rollback_to_version.assert_called_once_with(
            building_id='test-building',
            version_id='v1.0.0',
            force=False
        )
    
    def test_share_command_success(self, cli):
        """Test successful share command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        mock_schema.get_available_shares.return_value = 100.0
        mock_schema.add_share = Mock()
        cli.arxfile_manager.schema = mock_schema
        
        # Mock save
        cli.arxfile_manager.save = Mock()
        
        args = cli.parser.parse_args(['share', 'user123', '25.0'])
        result = cli.cmd_share(args)
        
        assert result == 0
        mock_schema.add_share.assert_called_once()
        cli.arxfile_manager.save.assert_called_once()
    
    def test_share_command_insufficient_shares(self, cli):
        """Test share command with insufficient available shares."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        mock_schema.get_available_shares.return_value = 10.0  # Only 10% available
        cli.arxfile_manager.schema = mock_schema
        
        args = cli.parser.parse_args(['share', 'user123', '25.0'])
        result = cli.cmd_share(args)
        
        assert result == 1  # Should fail
    
    def test_share_command_invalid_percentage(self, cli):
        """Test share command with invalid percentage."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        args = cli.parser.parse_args(['share', 'user123', '150.0'])  # > 100%
        result = cli.cmd_share(args)
        
        assert result == 1  # Should fail
    
    def test_status_command_success(self, cli, mock_services):
        """Test successful status command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_name = 'Test Building'
        mock_schema.building_id = 'test-building'
        mock_schema.building_type = 'commercial'
        mock_schema.floor_count = 3
        mock_schema.owner_id = 'owner123'
        mock_schema.license_status = 'active'
        mock_schema.last_modified = datetime.now()
        mock_schema.get_total_shares.return_value = 25.0
        mock_schema.contracts = []
        mock_schema.permissions = []
        cli.arxfile_manager.schema = mock_schema
        
        # Mock version history
        mock_services['version_control'].get_version_history.return_value = {
            'success': True,
            'versions': [
                {'version_id': 'v1.0.1', 'message': 'Test commit', 'created_at': '2024-01-01'}
            ]
        }
        
        args = cli.parser.parse_args(['status'])
        result = cli.cmd_status(args)
        
        assert result == 0
    
    def test_log_command_success(self, cli, mock_services):
        """Test successful log command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock version history
        mock_services['version_control'].get_version_history.return_value = {
            'success': True,
            'versions': [
                {'version_id': 'v1.0.1', 'message': 'Test commit', 'created_at': '2024-01-01', 'created_by': 'user1'},
                {'version_id': 'v1.0.0', 'message': 'Initial commit', 'created_at': '2024-01-01', 'created_by': 'user1'}
            ]
        }
        
        args = cli.parser.parse_args(['log'])
        result = cli.cmd_log(args)
        
        assert result == 0
        mock_services['version_control'].get_version_history.assert_called_once_with(
            floor_id='all',
            building_id='test-building',
            limit=10
        )
    
    def test_validate_command_success(self, cli, mock_services):
        """Test successful validate command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock arxfile validation
        cli.arxfile_manager.validate = Mock(return_value=[])
        
        # Mock building validation
        mock_services['validation'].validate_building.return_value = {
            'success': True,
            'result': {'issues': []}
        }
        
        args = cli.parser.parse_args(['validate'])
        result = cli.cmd_validate(args)
        
        assert result == 0
    
    def test_validate_command_with_issues(self, cli, mock_services):
        """Test validate command with validation issues."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock arxfile validation with issues
        cli.arxfile_manager.validate = Mock(return_value=['Issue 1', 'Issue 2'])
        
        # Mock building validation with issues
        mock_services['validation'].validate_building.return_value = {
            'success': True,
            'result': {'issues': ['Building issue 1', 'Building issue 2']}
        }
        
        args = cli.parser.parse_args(['validate'])
        result = cli.cmd_validate(args)
        
        assert result == 0  # Should succeed but show warnings
    
    def test_export_command_success(self, cli, mock_services):
        """Test successful export command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock successful export
        mock_services['bim_assembly'].export_building.return_value = {
            'success': True,
            'data': '{"building": "data"}'
        }
        
        args = cli.parser.parse_args(['export', '--format', 'json'])
        result = cli.cmd_export(args)
        
        assert result == 0
        mock_services['bim_assembly'].export_building.assert_called_once_with(
            building_id='test-building',
            format='json',
            floors=None
        )
    
    def test_import_command_success(self, cli, mock_services):
        """Test successful import command."""
        # Mock arxfile schema
        mock_schema = Mock(spec=ArxfileSchema)
        mock_schema.building_id = 'test-building'
        cli.arxfile_manager.schema = mock_schema
        
        # Mock successful import
        mock_services['bim_assembly'].import_building.return_value = {
            'success': True,
            'object_count': 10
        }
        
        args = cli.parser.parse_args(['import', 'test_file.json'])
        result = cli.cmd_import(args)
        
        assert result == 0
        mock_services['bim_assembly'].import_building.assert_called_once_with(
            file_path='test_file.json',
            format=None,
            building_id='test-building',
            overwrite=False
        )
    
    def test_run_method_success(self, cli):
        """Test CLI run method with valid command."""
        with patch.object(cli, 'cmd_init') as mock_init:
            mock_init.return_value = 0
            
            result = cli.run(['init', 'test-building', 'Test Building', 'commercial', '--owner', 'owner123'])
            
            assert result == 0
            mock_init.assert_called_once()
    
    def test_run_method_no_command(self, cli):
        """Test CLI run method with no command."""
        result = cli.run([])
        assert result == 1  # Should show help and return 1
    
    def test_run_method_unknown_command(self, cli):
        """Test CLI run method with unknown command."""
        result = cli.run(['unknown-command'])
        assert result == 1  # Should fail
    
    def test_run_method_keyboard_interrupt(self, cli):
        """Test CLI run method with keyboard interrupt."""
        with patch.object(cli, 'cmd_init', side_effect=KeyboardInterrupt):
            result = cli.run(['init', 'test-building', 'Test Building', 'commercial', '--owner', 'owner123'])
            assert result == 130
    
    def test_run_method_exception(self, cli):
        """Test CLI run method with exception."""
        with patch.object(cli, 'cmd_init', side_effect=Exception("Test error")):
            result = cli.run(['init', 'test-building', 'Test Building', 'commercial', '--owner', 'owner123'])
            assert result == 1
    
    def test_initialize_services_success(self, cli, temp_dir):
        """Test service initialization."""
        # Create arxfile in temp directory
        arxfile_path = os.path.join(temp_dir, 'arxfile.yaml')
        with open(arxfile_path, 'w') as f:
            f.write("""
building_id: test-building
building_name: Test Building
building_type: commercial
address:
  street: 123 Test St
  city: Test City
owner_id: owner123
floor_count: 3
            """)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            cli._initialize_services('arxfile.yaml')
            
            assert cli.arxfile_manager.schema is not None
            assert cli.version_control is not None
            assert cli.access_control is not None
            assert cli.bim_assembly is not None
            assert cli.validation is not None
            
        finally:
            os.chdir(original_cwd)
    
    def test_initialize_services_no_arxfile(self, cli, temp_dir):
        """Test service initialization without arxfile."""
        # Change to temp directory (no arxfile)
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            cli._initialize_services('arxfile.yaml')
            
            # Should still initialize services even without arxfile
            assert cli.version_control is not None
            assert cli.access_control is not None
            assert cli.bim_assembly is not None
            assert cli.validation is not None
            
        finally:
            os.chdir(original_cwd)


def test_main_function():
    """Test main function entry point."""
    with patch('cmd.arx_cli.ArxCLI') as mock_cli_class:
        mock_cli = Mock()
        mock_cli.run.return_value = 0
        mock_cli_class.return_value = mock_cli
        
        from cmd.arx_cli import main
        result = main()
        
        assert result == 0
        mock_cli.run.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__]) 