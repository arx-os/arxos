# CLI System: Complete Architecture & Implementation

## 🎯 **Overview**

The CLI System provides comprehensive command-line interface capabilities for the Arxos platform, including git-style workflow commands, ASCII-BIM integration, offline sync capabilities, and workflow automation.

**Status**: 🔄 **IN DEVELOPMENT**  
**Priority**: High

---

## 📊 **Current State Analysis**

### ✅ **What's Already Built**
- Some CLI commands (arx_cli.py, various command modules)
- Export CLI functionality
- Basic command parsing

### ❌ **What's Missing**
- Complete arx command suite
- ASCII-BIM CLI integration
- Git-style workflow commands
- Offline sync capabilities
- Workflow automation
- Comprehensive error handling

---

## 🏗️ **Complete Architecture Plan**

### **2.1 Core CLI Framework**

```python
# arxos/cli/core/cli_framework.py
class ArxCLIFramework:
    """Core CLI framework for Arxos"""
    
    def __init__(self):
        self.command_registry = CommandRegistry()
        self.help_system = HelpSystem()
        self.error_handler = ErrorHandler()
        self.config_manager = ConfigManager()
    
    def register_command(self, command: Command):
        """Register a new command"""
        
        # Validate command structure
        if not command.name:
            raise ValueError("Command must have a name")
        
        if not command.handler:
            raise ValueError("Command must have a handler")
        
        # Register command
        self.command_registry.register(command)
        
        # Update help system
        self.help_system.add_command(command)
    
    def execute_command(self, args: List[str]) -> int:
        """Execute command with arguments"""
        
        try:
            # Parse arguments
            parsed_args = self.parse_arguments(args)
            
            # Find command
            command = self.command_registry.get_command(parsed_args.command)
            if not command:
                self.error_handler.handle_command_not_found(parsed_args.command)
                return 1
            
            # Validate arguments
            validation_result = command.validate_arguments(parsed_args)
            if not validation_result.is_valid:
                self.error_handler.handle_validation_errors(validation_result.errors)
                return 1
            
            # Execute command
            result = command.handler(parsed_args)
            
            # Handle result
            if result.success:
                return 0
            else:
                self.error_handler.handle_execution_error(result.error)
                return 1
                
        except Exception as e:
            self.error_handler.handle_unexpected_error(e)
            return 1
    
    def get_help(self, command_name: str) -> str:
        """Get help for specific command"""
        
        if not command_name:
            return self.help_system.get_general_help()
        
        command = self.command_registry.get_command(command_name)
        if not command:
            return f"Command '{command_name}' not found"
        
        return self.help_system.get_command_help(command)
    
    def parse_arguments(self, args: List[str]) -> ParsedArguments:
        """Parse command line arguments"""
        
        if not args:
            return ParsedArguments(command="help", options={}, arguments=[])
        
        command = args[0]
        remaining_args = args[1:]
        
        # Parse options and arguments
        options = {}
        arguments = []
        
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]
            
            if arg.startswith('--'):
                # Long option
                if '=' in arg:
                    key, value = arg[2:].split('=', 1)
                    options[key] = value
                else:
                    key = arg[2:]
                    if i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith('-'):
                        options[key] = remaining_args[i + 1]
                        i += 1
                    else:
                        options[key] = True
            elif arg.startswith('-'):
                # Short option
                key = arg[1:]
                if i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith('-'):
                    options[key] = remaining_args[i + 1]
                    i += 1
                else:
                    options[key] = True
            else:
                # Argument
                arguments.append(arg)
            
            i += 1
        
        return ParsedArguments(
            command=command,
            options=options,
            arguments=arguments
        )
```

### **2.2 Git-Style Workflow Commands**

```python
# arxos/cli/commands/repository_commands.py
import click
from arxos.cli.core.repository_manager import RepositoryManager

@click.group()
def repo():
    """Repository management commands."""
    pass

@repo.command()
@click.argument('building_id')
@click.argument('building_name')
@click.option('--description', '-d', help='Building description')
@click.option('--type', '-t', default='commercial', help='Building type')
def init(building_id, building_name, description, type):
    """Initialize new building repository."""
    
    try:
        repo_manager = RepositoryManager()
        result = repo_manager.initialize_repository(
            building_id=building_id,
            building_name=building_name,
            description=description,
            building_type=type
        )
        
        if result.success:
            click.echo(f"✅ Repository initialized: {building_name}")
            click.echo(f"   Building ID: {building_id}")
            click.echo(f"   Type: {type}")
        else:
            click.echo(f"❌ Failed to initialize repository: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@repo.command()
@click.argument('files', nargs=-1)
@click.option('--all', '-a', is_flag=True, help='Add all files')
def add(files, all):
    """Add files to staging area."""
    
    try:
        repo_manager = RepositoryManager()
        
        if all:
            result = repo_manager.add_all_files()
        else:
            result = repo_manager.add_files(files)
        
        if result.success:
            click.echo(f"✅ Added {len(result.added_files)} files to staging")
            for file in result.added_files:
                click.echo(f"   + {file}")
        else:
            click.echo(f"❌ Failed to add files: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@repo.command()
@click.option('-m', '--message', required=True, help='Commit message')
@click.option('--author', '-a', help='Commit author')
def commit(message, author):
    """Commit staged changes."""
    
    try:
        repo_manager = RepositoryManager()
        result = repo_manager.commit_changes(
            message=message,
            author=author
        )
        
        if result.success:
            click.echo(f"✅ Commit created: {result.commit_id}")
            click.echo(f"   Message: {message}")
            click.echo(f"   Files: {len(result.committed_files)}")
        else:
            click.echo(f"❌ Failed to commit: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@repo.command()
@click.argument('branch')
@click.option('--create', '-c', is_flag=True, help='Create new branch')
def checkout(branch, create):
    """Switch to different branch."""
    
    try:
        repo_manager = RepositoryManager()
        result = repo_manager.checkout_branch(
            branch=branch,
            create=create
        )
        
        if result.success:
            click.echo(f"✅ Switched to branch: {branch}")
            if create:
                click.echo(f"   Created new branch")
        else:
            click.echo(f"❌ Failed to checkout: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@repo.command()
@click.argument('branch')
@click.option('--no-ff', is_flag=True, help='No fast-forward merge')
def merge(branch, no_ff):
    """Merge branch into current branch."""
    
    try:
        repo_manager = RepositoryManager()
        result = repo_manager.merge_branch(
            branch=branch,
            no_fast_forward=no_ff
        )
        
        if result.success:
            click.echo(f"✅ Merged branch: {branch}")
            click.echo(f"   Commit: {result.merge_commit}")
        else:
            click.echo(f"❌ Failed to merge: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@repo.command()
def status():
    """Show repository status."""
    
    try:
        repo_manager = RepositoryManager()
        status = repo_manager.get_status()
        
        click.echo(f"📊 Repository Status")
        click.echo(f"   Current branch: {status.current_branch}")
        click.echo(f"   Staged files: {len(status.staged_files)}")
        click.echo(f"   Modified files: {len(status.modified_files)}")
        click.echo(f"   Untracked files: {len(status.untracked_files)}")
        
        if status.staged_files:
            click.echo(f"\n📁 Staged files:")
            for file in status.staged_files:
                click.echo(f"   + {file}")
        
        if status.modified_files:
            click.echo(f"\n📝 Modified files:")
            for file in status.modified_files:
                click.echo(f"   M {file}")
        
        if status.untracked_files:
            click.echo(f"\n❓ Untracked files:")
            for file in status.untracked_files:
                click.echo(f"   ? {file}")
                
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)
```

### **2.3 ASCII-BIM CLI Integration**

```python
# arxos/cli/commands/ascii_bim_commands.py
import click
from arxos.cli.core.ascii_bim_manager import ASCIIBIMManager

@click.group()
def ascii():
    """ASCII-BIM commands."""
    pass

@ascii.command()
@click.argument('file_path')
@click.option('--format', '-f', default='table', help='Output format (table, json, yaml)')
def view(file_path, format):
    """View ASCII-BIM file in terminal."""
    
    try:
        ascii_manager = ASCIIBIMManager()
        result = ascii_manager.view_file(
            file_path=file_path,
            output_format=format
        )
        
        if result.success:
            click.echo(result.content)
        else:
            click.echo(f"❌ Failed to view file: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@ascii.command()
@click.argument('input_file')
@click.argument('output_file')
@click.option('--from-format', '-f', help='Input format')
@click.option('--to-format', '-t', help='Output format')
def convert(input_file, output_file, from_format, to_format):
    """Convert between formats."""
    
    try:
        ascii_manager = ASCIIBIMManager()
        result = ascii_manager.convert_file(
            input_file=input_file,
            output_file=output_file,
            from_format=from_format,
            to_format=to_format
        )
        
        if result.success:
            click.echo(f"✅ Converted: {input_file} → {output_file}")
            click.echo(f"   Format: {result.from_format} → {result.to_format}")
        else:
            click.echo(f"❌ Failed to convert: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@ascii.command()
@click.argument('file_path')
@click.option('--editor', '-e', help='Text editor to use')
def edit(file_path, editor):
    """Edit ASCII-BIM file interactively."""
    
    try:
        ascii_manager = ASCIIBIMManager()
        result = ascii_manager.edit_file(
            file_path=file_path,
            editor=editor
        )
        
        if result.success:
            click.echo(f"✅ File edited: {file_path}")
        else:
            click.echo(f"❌ Failed to edit: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@ascii.command()
@click.argument('file_path')
@click.option('--strict', '-s', is_flag=True, help='Strict validation')
def validate(file_path, strict):
    """Validate ASCII-BIM file."""
    
    try:
        ascii_manager = ASCIIBIMManager()
        result = ascii_manager.validate_file(
            file_path=file_path,
            strict=strict
        )
        
        if result.success:
            click.echo(f"✅ File is valid: {file_path}")
            if result.warnings:
                click.echo(f"⚠️  Warnings:")
                for warning in result.warnings:
                    click.echo(f"   - {warning}")
        else:
            click.echo(f"❌ File is invalid: {file_path}")
            click.echo(f"   Errors:")
            for error in result.errors:
                click.echo(f"   - {error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@ascii.command()
@click.argument('file1')
@click.argument('file2')
@click.option('--output', '-o', help='Output file for diff')
def diff(file1, file2, output):
    """Show differences between ASCII-BIM files."""
    
    try:
        ascii_manager = ASCIIBIMManager()
        result = ascii_manager.diff_files(
            file1=file1,
            file2=file2,
            output_file=output
        )
        
        if result.success:
            if output:
                click.echo(f"✅ Diff saved to: {output}")
            else:
                click.echo(result.diff_content)
        else:
            click.echo(f"❌ Failed to diff: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)
```

### **2.4 Offline Sync System**

```python
# arxos/cli/commands/sync_commands.py
import click
from arxos.cli.core.sync_manager import SyncManager

@click.group()
def sync():
    """Synchronization commands."""
    pass

@sync.command()
@click.option('--force', '-f', is_flag=True, help='Force sync')
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be synced')
def pull(force, dry_run):
    """Pull changes from remote repository."""
    
    try:
        sync_manager = SyncManager()
        result = sync_manager.pull_changes(
            force=force,
            dry_run=dry_run
        )
        
        if result.success:
            if dry_run:
                click.echo(f"📋 Would pull {len(result.changes)} changes")
                for change in result.changes:
                    click.echo(f"   {change.type}: {change.file}")
            else:
                click.echo(f"✅ Pulled {len(result.changes)} changes")
        else:
            click.echo(f"❌ Failed to pull: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@sync.command()
@click.option('--force', '-f', is_flag=True, help='Force push')
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be pushed')
def push(force, dry_run):
    """Push changes to remote repository."""
    
    try:
        sync_manager = SyncManager()
        result = sync_manager.push_changes(
            force=force,
            dry_run=dry_run
        )
        
        if result.success:
            if dry_run:
                click.echo(f"📋 Would push {len(result.changes)} changes")
                for change in result.changes:
                    click.echo(f"   {change.type}: {change.file}")
            else:
                click.echo(f"✅ Pushed {len(result.changes)} changes")
        else:
            click.echo(f"❌ Failed to push: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@sync.command()
@click.argument('remote_name')
@click.argument('remote_url')
def add_remote(remote_name, remote_url):
    """Add remote repository."""
    
    try:
        sync_manager = SyncManager()
        result = sync_manager.add_remote(
            name=remote_name,
            url=remote_url
        )
        
        if result.success:
            click.echo(f"✅ Added remote: {remote_name}")
            click.echo(f"   URL: {remote_url}")
        else:
            click.echo(f"❌ Failed to add remote: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@sync.command()
def list_remotes():
    """List remote repositories."""
    
    try:
        sync_manager = SyncManager()
        remotes = sync_manager.list_remotes()
        
        if remotes:
            click.echo(f"📡 Remote repositories:")
            for remote in remotes:
                click.echo(f"   {remote.name}: {remote.url}")
        else:
            click.echo(f"📡 No remote repositories configured")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)
```

### **2.5 Workflow Automation**

```python
# arxos/cli/commands/workflow_commands.py
import click
from arxos.cli.core.workflow_manager import WorkflowManager

@click.group()
def workflow():
    """Workflow automation commands."""
    pass

@workflow.command()
@click.argument('workflow_name')
@click.argument('steps', nargs=-1)
@click.option('--description', '-d', help='Workflow description')
def create(workflow_name, steps, description):
    """Create new workflow."""
    
    try:
        workflow_manager = WorkflowManager()
        result = workflow_manager.create_workflow(
            name=workflow_name,
            steps=steps,
            description=description
        )
        
        if result.success:
            click.echo(f"✅ Created workflow: {workflow_name}")
            click.echo(f"   Steps: {len(steps)}")
        else:
            click.echo(f"❌ Failed to create workflow: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@workflow.command()
@click.argument('workflow_name')
def run(workflow_name):
    """Run workflow."""
    
    try:
        workflow_manager = WorkflowManager()
        result = workflow_manager.run_workflow(
            name=workflow_name
        )
        
        if result.success:
            click.echo(f"✅ Workflow completed: {workflow_name}")
            click.echo(f"   Duration: {result.duration}")
            click.echo(f"   Steps executed: {result.steps_executed}")
        else:
            click.echo(f"❌ Workflow failed: {result.error}")
            exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)

@workflow.command()
def list():
    """List available workflows."""
    
    try:
        workflow_manager = WorkflowManager()
        workflows = workflow_manager.list_workflows()
        
        if workflows:
            click.echo(f"📋 Available workflows:")
            for workflow in workflows:
                click.echo(f"   {workflow.name}: {workflow.description}")
        else:
            click.echo(f"📋 No workflows available")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        exit(1)
```

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Core Framework (Week 1-2)**
- [ ] Core CLI framework implementation
- [ ] Command registry system
- [ ] Help system
- [ ] Error handling

### **Phase 2: Repository Commands (Week 3-4)**
- [ ] Git-style workflow commands
- [ ] Repository management
- [ ] Branch operations
- [ ] Status reporting

### **Phase 3: ASCII-BIM Integration (Week 5-6)**
- [ ] ASCII-BIM CLI commands
- [ ] File viewing and editing
- [ ] Format conversion
- [ ] Validation

### **Phase 4: Sync & Automation (Week 7-8)**
- [ ] Offline sync capabilities
- [ ] Workflow automation
- [ ] Remote management
- [ ] Performance optimization

---

## 📊 **Success Metrics**

### **Performance Targets**
- **Command Execution**: < 200ms for typical commands
- **File Operations**: < 100ms for file operations
- **Sync Operations**: < 5 seconds for typical sync
- **Memory Usage**: < 100MB for CLI operations

### **Quality Targets**
- **Command Coverage**: 100% command coverage
- **Error Handling**: Comprehensive error handling
- **User Experience**: Intuitive command interface
- **Documentation**: Complete help system

---

## 🔧 **Integration Points**

### **Repository Manager**
```python
# arxos/cli/core/repository_manager.py
class RepositoryManager:
    """Manage building repositories"""
    
    def initialize_repository(self, building_id: str, building_name: str, **kwargs) -> RepositoryResult:
        """Initialize new building repository"""
        
    def add_files(self, files: List[str]) -> AddResult:
        """Add files to staging area"""
        
    def commit_changes(self, message: str, author: str = None) -> CommitResult:
        """Commit staged changes"""
        
    def checkout_branch(self, branch: str, create: bool = False) -> CheckoutResult:
        """Switch to different branch"""
        
    def merge_branch(self, branch: str, no_fast_forward: bool = False) -> MergeResult:
        """Merge branch into current branch"""
        
    def get_status(self) -> RepositoryStatus:
        """Get repository status"""
```

### **ASCII-BIM Manager**
```python
# arxos/cli/core/ascii_bim_manager.py
class ASCIIBIMManager:
    """Manage ASCII-BIM operations"""
    
    def view_file(self, file_path: str, output_format: str = 'table') -> ViewResult:
        """View ASCII-BIM file"""
        
    def convert_file(self, input_file: str, output_file: str, **kwargs) -> ConvertResult:
        """Convert between formats"""
        
    def edit_file(self, file_path: str, editor: str = None) -> EditResult:
        """Edit ASCII-BIM file"""
        
    def validate_file(self, file_path: str, strict: bool = False) -> ValidateResult:
        """Validate ASCII-BIM file"""
        
    def diff_files(self, file1: str, file2: str, output_file: str = None) -> DiffResult:
        """Show differences between files"""
```

The CLI System provides comprehensive command-line interface capabilities with git-style workflows, ASCII-BIM integration, and automation features for seamless building management. 