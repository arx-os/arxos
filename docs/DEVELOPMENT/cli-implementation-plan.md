# CLI Implementation Plan: Python & PowerShell Approaches

## 🎯 **Implementation Overview**

This plan provides a comprehensive roadmap for implementing the CLI system with both Python and PowerShell approaches, enabling cross-platform building management and ASCII-BIM integration.

---

## 🚀 **Phase 1: Core Framework Implementation (Weeks 1-2)**

### **Task 1.1: Python CLI Framework Setup**
```python
# arxos/cli/core/command_parser.py
import click
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ParsedCommand:
    command: str
    subcommand: str
    arguments: List[str]
    options: Dict[str, Any]
    context: Dict[str, Any]

class ArxCommandParser:
    """Parse and route CLI commands"""
    
    def __init__(self):
        self.command_registry = CommandRegistry()
        self.context_manager = ContextManager()
        self.help_system = HelpSystem()
    
    async def parse_command(self, args: List[str]) -> ParsedCommand:
        """Parse command line arguments"""
        # Implementation for command parsing
        pass
    
    async def route_command(self, parsed_command: ParsedCommand) -> CommandResult:
        """Route command to appropriate handler"""
        # Implementation for command routing
        pass
```

### **Task 1.2: PowerShell Module Framework Setup**
```powershell
# Create module directory structure
New-Item -ItemType Directory -Path "Arxos-PowerShell" -Force
New-Item -ItemType Directory -Path "Arxos-PowerShell\Public" -Force
New-Item -ItemType Directory -Path "Arxos-PowerShell\Private" -Force
New-Item -ItemType Directory -Path "Arxos-PowerShell\Classes" -Force
New-Item -ItemType Directory -Path "Arxos-PowerShell\Config" -Force
New-Item -ItemType Directory -Path "Arxos-PowerShell\Tests" -Force

# Create main module file
@"
# Arxos CLI PowerShell Module
# Version: 1.0.0

# Import required modules
Import-Module SqlServer -ErrorAction SilentlyContinue
Import-Module PSSqlite -ErrorAction SilentlyContinue
Import-Module PSReadLine -ErrorAction SilentlyContinue

# Import classes
. "$PSScriptRoot\Classes\ArxAsset.ps1"
. "$PSScriptRoot\Classes\ArxWorkOrder.ps1"
. "$PSScriptRoot\Classes\ArxLocation.ps1"

# Import private functions
Get-ChildItem -Path "$PSScriptRoot\Private\*.ps1" | ForEach-Object { . $_.FullName }

# Import public cmdlets
Get-ChildItem -Path "$PSScriptRoot\Public\*.ps1" | ForEach-Object { . $_.FullName }

# Export public cmdlets
Export-ModuleMember -Function (Get-ChildItem -Path "$PSScriptRoot\Public\*.ps1" | ForEach-Object { (Get-Content $_.FullName | Select-String "function" | ForEach-Object { $_.Line.Split(" ")[1].Split("(")[0] }) })
"@ | Out-File -FilePath "Arxos-PowerShell\ArxosCLI.psm1" -Encoding UTF8
```

### **Task 1.3: Context Management System**

#### **Python Context Management**
```python
# arxos/cli/core/context_manager.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Location:
    building: str
    floor: str
    room: str
    coordinates: Optional[tuple] = None

@dataclass
class Context:
    current_location: Optional[Location] = None
    current_user: Optional[str] = None
    current_building: Optional[str] = None
    session_data: Dict[str, Any] = None

class ContextManager:
    """Manage user context and session state"""
    
    def __init__(self):
        self.current_location = None
        self.current_building = None
        self.current_user = None
        self.session_data = {}
    
    async def set_location(self, location: Location):
        """Set current user location"""
        self.current_location = location
        await self.update_context({"location": location})
    
    async def get_context(self) -> Context:
        """Get current context for command execution"""
        return Context(
            current_location=self.current_location,
            current_user=self.current_user,
            current_building=self.current_building,
            session_data=self.session_data
        )
```

#### **PowerShell Context Management**
```powershell
# Private/Context-Manager.ps1
class ArxContextManager {
    [hashtable]$CurrentLocation
    [string]$CurrentUser
    [string]$CurrentBuilding
    [hashtable]$SessionData

    ArxContextManager() {
        $this.CurrentLocation = @{}
        $this.SessionData = @{}
    }

    [void]SetLocation([hashtable]$location) {
        $this.CurrentLocation = $location
        $this.UpdateContext(@{ "location" = $location })
    }

    [hashtable]GetContext() {
        return @{
            "CurrentLocation" = $this.CurrentLocation
            "CurrentUser" = $this.CurrentUser
            "CurrentBuilding" = $this.CurrentBuilding
            "SessionData" = $this.SessionData
        }
    }

    [void]UpdateContext([hashtable]$updates) {
        foreach ($key in $updates.Keys) {
            $this.SessionData[$key] = $updates[$key]
        }
    }
}
```

---

## 🎨 **Phase 2: ASCII-BIM Engine Integration (Weeks 3-4)**

### **Task 2.1: Python ASCII-BIM Renderer**
```python
# arxos/cli/ascii_bim/renderer.py
import asyncio
from typing import Dict, List, Any

class AsciiBimRenderer:
    """Render building data as ASCII art"""
    
    def __init__(self):
        self.symbol_mapper = SymbolMapper()
        self.layout_optimizer = LayoutOptimizer()
    
    async def render_building(self, building_data: Dict[str, Any]) -> str:
        """Render building as ASCII art"""
        # Implementation for ASCII rendering
        pass
    
    async def render_floor(self, floor_data: Dict[str, Any]) -> str:
        """Render floor as ASCII art"""
        # Implementation for floor rendering
        pass
    
    async def render_room(self, room_data: Dict[str, Any]) -> str:
        """Render room as ASCII art"""
        # Implementation for room rendering
        pass
```

### **Task 2.2: PowerShell ASCII-BIM Renderer**
```powershell
# Private/ConvertTo-ArxAscii.ps1
function ConvertTo-ArxAscii {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$BuildingData,
        
        [Parameter(Mandatory=$false)]
        [string]$Resolution = "standard"
    )
    
    # Initialize symbol mapper
    $symbolMapper = Get-ArxSymbolMapper
    
    # Initialize layout optimizer
    $layoutOptimizer = Get-ArxLayoutOptimizer
    
    # Render building as ASCII
    $asciiOutput = $BuildingData | ForEach-Object {
        $_.Floors | ForEach-Object {
            $_.Rooms | ForEach-Object {
                $symbol = $symbolMapper.GetSymbol($_.Type, $_.Status)
                $position = $layoutOptimizer.GetPosition($_.Coordinates)
                "$symbol"
            }
        }
    }
    
    return $asciiOutput -join "`n"
}
```

---

## 🔧 **Phase 3: Work Order System Integration (Weeks 5-6)**

### **Task 3.1: Python Work Order Engine**
```python
# arxos/cli/work_orders/engine.py
import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class WorkOrder:
    id: str
    asset_id: str
    description: str
    priority: str
    category: str
    urgency: str
    status: str
    assigned_to: str
    created_at: str

class WorkOrderEngine:
    """Create and manage work orders"""
    
    def __init__(self):
        self.template_system = TemplateSystem()
        self.notification_system = NotificationSystem()
    
    async def create_work_order(self, asset_id: str, description: str, priority: str) -> WorkOrder:
        """Create a new work order"""
        # Implementation for work order creation
        pass
    
    async def assign_work_order(self, work_order_id: str, assigned_to: str) -> bool:
        """Assign work order to technician"""
        # Implementation for work order assignment
        pass
```

### **Task 3.2: PowerShell Work Order Engine**
```powershell
# Classes/ArxWorkOrder.ps1
class ArxWorkOrder {
    [string]$Id
    [string]$AssetId
    [string]$Description
    [string]$Priority
    [string]$Category
    [string]$Urgency
    [string]$Status
    [string]$AssignedTo
    [datetime]$CreatedAt
    [datetime]$UpdatedAt
    [hashtable]$Properties

    ArxWorkOrder([string]$id, [string]$assetId, [string]$description, [string]$priority) {
        $this.Id = $id
        $this.AssetId = $assetId
        $this.Description = $description
        $this.Priority = $priority
        $this.Status = "pending"
        $this.CreatedAt = Get-Date
        $this.UpdatedAt = Get-Date
        $this.Properties = @{}
    }

    [string]ToString() {
        return "Work Order $($this.Id): $($this.Description) - $($this.Status)"
    }

    [bool]IsPending() {
        return $this.Status -eq "pending"
    }

    [bool]IsInProgress() {
        return $this.Status -eq "in_progress"
    }

    [bool]IsCompleted() {
        return $this.Status -eq "completed"
    }
}

# Public/New-ArxWorkOrder.ps1
function New-ArxWorkOrder {
    param(
        [Parameter(Mandatory=$true)]
        [string]$AssetId,
        
        [Parameter(Mandatory=$true)]
        [string]$Description,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("low", "medium", "high", "critical")]
        [string]$Priority = "medium",
        
        [Parameter(Mandatory=$false)]
        [string]$Category = "general"
    )
    
    # Generate work order ID
    $workOrderId = "WO-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    # Create work order
    $workOrder = [ArxWorkOrder]::new($workOrderId, $AssetId, $Description, $Priority)
    $workOrder.Category = $Category
    
    # Save to database
    Save-ArxWorkOrder -WorkOrder $workOrder
    
    # Send notifications
    Send-ArxWorkOrderNotification -WorkOrder $workOrder
    
    return $workOrder
}
```

---

## 📊 **Phase 4: Asset Discovery System (Weeks 7-8)**

### **Task 4.1: Python Asset Discovery**
```python
# arxos/cli/assets/discovery.py
import asyncio
from typing import Dict, List, Any

class AssetDiscovery:
    """Find and identify assets"""
    
    def __init__(self):
        self.database = DatabaseConnection()
        self.location_service = LocationService()
    
    async def find_assets_by_type(self, asset_type: str) -> List[Dict[str, Any]]:
        """Find assets by type"""
        # Implementation for type-based search
        pass
    
    async def find_assets_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Find assets by location"""
        # Implementation for location-based search
        pass
    
    async def trace_asset_connections(self, asset_id: str) -> List[Dict[str, Any]]:
        """Trace asset connections"""
        # Implementation for connection tracing
        pass
```

### **Task 4.2: PowerShell Asset Discovery**
```powershell
# Public/Find-ArxAsset.ps1
function Find-ArxAsset {
    param(
        [Parameter(Mandatory=$false)]
        [string]$Type,
        
        [Parameter(Mandatory=$false)]
        [string]$Location,
        
        [Parameter(Mandatory=$false)]
        [string]$Status,
        
        [Parameter(Mandatory=$false)]
        [switch]$IncludeConnections
    )
    
    # Build query based on parameters
    $query = "SELECT * FROM assets WHERE 1=1"
    
    if ($Type) {
        $query += " AND type = '$Type'"
    }
    
    if ($Location) {
        $query += " AND location = '$Location'"
    }
    
    if ($Status) {
        $query += " AND status = '$Status'"
    }
    
    # Execute query
    $assets = Invoke-ArxDatabaseQuery -Query $query
    
    # Convert to ArxAsset objects
    $arxAssets = $assets | ForEach-Object {
        [ArxAsset]::new($_.id, $_.name, $_.type, $_.status, $_.location)
    }
    
    # Include connections if requested
    if ($IncludeConnections) {
        $arxAssets | ForEach-Object {
            $_.ConnectedDevices = Get-ArxAssetConnections -AssetId $_.Id
        }
    }
    
    return $arxAssets
}
```

---

## 🚀 **Phase 5: Integration and Testing (Weeks 9-10)**

### **Task 5.1: Cross-Platform Integration**
```python
# arxos/cli/integration/platform_bridge.py
import asyncio
import subprocess
from typing import Dict, Any

class PlatformBridge:
    """Bridge between Python and PowerShell implementations"""
    
    def __init__(self):
        self.powershell_path = "powershell.exe"
    
    async def execute_powershell_command(self, command: str) -> Dict[str, Any]:
        """Execute PowerShell command from Python"""
        try:
            result = subprocess.run([
                self.powershell_path,
                "-Command",
                command
            ], capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### **Task 5.2: PowerShell Python Integration**
```powershell
# Private/Invoke-PythonCommand.ps1
function Invoke-PythonCommand {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Script,
        
        [Parameter(Mandatory=$false)]
        [hashtable]$Arguments = @{}
    )
    
    # Convert arguments to Python format
    $pythonArgs = $Arguments | ForEach-Object {
        $_.GetEnumerator() | ForEach-Object {
            "--$($_.Key) $($_.Value)"
        }
    }
    
    # Execute Python script
    $pythonCommand = "python -c `"$Script`" $($pythonArgs -join ' ')"
    
    try {
        $result = Invoke-Expression $pythonCommand
        return @{
            "Success" = $true
            "Output" = $result
        }
    }
    catch {
        return @{
            "Success" = $false
            "Error" = $_.Exception.Message
        }
    }
}
```

---

## 📋 **Implementation Timeline**

### **Week 1-2: Core Framework**
- [ ] Python command parser and router
- [ ] PowerShell module structure setup
- [ ] Context management systems
- [ ] Basic command registry

### **Week 3-4: ASCII-BIM Integration**
- [ ] Python ASCII-BIM renderer
- [ ] PowerShell ASCII-BIM renderer
- [ ] Symbol mapping systems
- [ ] Layout optimization

### **Week 5-6: Work Order System**
- [ ] Python work order engine
- [ ] PowerShell work order engine
- [ ] Asset validation systems
- [ ] Notification systems

### **Week 7-8: Asset Discovery**
- [ ] Python asset discovery
- [ ] PowerShell asset discovery
- [ ] Location services
- [ ] Connection tracing

### **Week 9-10: Integration and Testing**
- [ ] Cross-platform integration
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation completion

---

## 🔧 **Technology Stack**

### **Python Implementation**
- **Framework**: Click (CLI framework)
- **Async**: asyncio for concurrent operations
- **Database**: SQLAlchemy for data access
- **Testing**: pytest for unit testing

### **PowerShell Implementation**
- **Framework**: PowerShell 7+ (cross-platform)
- **Database**: SqlServer module for SQL Server
- **Testing**: Pester for unit testing
- **Modules**: PSReadLine for enhanced CLI

### **Shared Components**
- **Database**: PostgreSQL for data storage
- **API**: RESTful API for system integration
- **Authentication**: JWT for secure access
- **Logging**: Structured logging for operations

---

## 📊 **Expected Outcomes**

### **Immediate Benefits**
- **Cross-platform support**: Both Python and PowerShell implementations
- **Native experience**: Windows users get PowerShell, others get Python
- **Unified functionality**: Same capabilities across both platforms
- **Flexible deployment**: Choose the right tool for the environment

### **Long-term Benefits**
- **Easier maintenance**: Shared core concepts and APIs
- **Better user experience**: Native platform integration
- **Reduced training**: Familiar tools for each platform
- **Enterprise readiness**: Professional CLI implementations

---

**Implementation Date**: December 2024  
**Version**: 1.0.0  
**Status**: In Development 