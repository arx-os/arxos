# CLI System Design: Python & PowerShell Approaches

## 🎯 **Mission: Cross-Platform CLI for Building Management**

Create comprehensive command-line interfaces for building management, ASCII-BIM integration, and work order creation, providing both Python and PowerShell implementations for cross-platform compatibility.

---

## 🏗️ **System Architecture Overview**

### **Cross-Platform Approach**
The CLI system provides two complementary implementations:
- **Python CLI**: Cross-platform implementation using Click framework
- **PowerShell CLI**: Windows-native implementation using PowerShell modules

### **Shared Core Concepts**
Both implementations share the same core functionality:
- ASCII-BIM rendering and manipulation
- Asset discovery and management
- Work order creation and management
- Location services and context awareness
- Real-time monitoring and control

---

## 🐍 **Python CLI Architecture**

### **Core Framework Structure**
```
arxos/cli/
├── __init__.py                     # Package initialization
├── core/                           # Core framework
│   ├── command_parser.py           # Command parsing and routing
│   ├── context_manager.py          # Context management
│   ├── command_registry.py         # Command registration
│   └── help_system.py              # Help and documentation
├── ascii_bim/                      # ASCII-BIM engine
│   ├── renderer.py                 # ASCII rendering
│   ├── symbol_mapper.py            # Symbol mapping
│   └── layout_optimizer.py         # Layout optimization
├── work_orders/                    # Work order system
│   ├── engine.py                   # Work order engine
│   ├── templates.py                # Template system
│   └── notifications.py            # Notification system
├── assets/                         # Asset management
│   ├── discovery.py                # Asset discovery
│   ├── management.py               # Asset management
│   └── connections.py              # Connection tracing
└── integration/                    # System integration
    ├── platform_bridge.py          # Cross-platform bridge
    ├── api_client.py               # API integration
    └── database.py                 # Database access
```

### **Python Dependencies**
```python
# Core dependencies
click>=8.0.0                        # CLI framework
asyncio                             # Async operations
dataclasses                         # Data structures
typing                              # Type hints

# Database and API
sqlalchemy>=1.4.0                   # Database ORM
requests>=2.25.0                    # HTTP client
aiohttp>=3.8.0                      # Async HTTP

# Testing and development
pytest>=6.0.0                       # Testing framework
black>=21.0.0                       # Code formatting
mypy>=0.910                         # Type checking
```

---

## 🏗️ **PowerShell Module Architecture**

### **Core Module Structure**
```
Arxos-PowerShell/
├── ArxosCLI.psm1                    # Main module file
├── Public/                          # Public cmdlets
│   ├── Get-ArxLocation.ps1         # Location services
│   ├── Find-ArxAsset.ps1           # Asset discovery
│   ├── New-ArxWorkOrder.ps1        # Work order creation
│   ├── Show-ArxAscii.ps1           # ASCII-BIM rendering
│   ├── Get-ArxSystemStatus.ps1     # System status
│   └── Trace-ArxAsset.ps1          # Asset tracing
├── Private/                         # Internal functions
│   ├── Connect-ArxDatabase.ps1     # Database connection
│   ├── Invoke-ArxAPI.ps1           # API calls
│   ├── ConvertTo-ArxAscii.ps1      # ASCII conversion
│   └── Format-ArxOutput.ps1        # Output formatting
├── Classes/                         # PowerShell classes
│   ├── ArxAsset.ps1                # Asset class
│   ├── ArxWorkOrder.ps1            # Work order class
│   └── ArxLocation.ps1             # Location class
└── Config/                         # Configuration
    ├── ArxosConfig.psd1            # Module configuration
    └── SymbolMappings.psd1         # ASCII symbol mappings
```

### **Module Dependencies**
```powershell
# Required PowerShell modules
Import-Module SqlServer          # SQL Server connectivity
Import-Module PSSqlite           # SQLite support
Import-Module PSReadLine         # Enhanced command line
Import-Module Pester             # Testing framework
```

---

## 🖥️ **Core PowerShell Classes**

### **1. ArxAsset Class**
```powershell
# Classes/ArxAsset.ps1
class ArxAsset {
    [string]$Id
    [string]$Name
    [string]$Type
    [string]$Status
    [string]$Location
    [hashtable]$Properties
    [string]$Circuit
    [string]$Panel
    [datetime]$LastMaintenance
    [string[]]$ConnectedDevices

    ArxAsset([string]$id, [string]$name, [string]$type, [string]$status, [string]$location) {
        $this.Id = $id
        $this.Name = $name
        $this.Type = $type
        $this.Status = $status
        $this.Location = $location
        $this.Properties = @{}
        $this.ConnectedDevices = @()
    }

    [string]ToString() {
        return "$($this.Name) ($($this.Type)) - $($this.Status)"
    }

    [bool]IsActive() {
        return $this.Status -eq "active"
    }

    [bool]NeedsMaintenance() {
        return $this.Status -in @("warning", "error", "maintenance")
    }
}
```

### **2. ArxWorkOrder Class**
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

    ArxWorkOrder([string]$id, [string]$assetId, [string]$description, [string]$priority, [string]$category, [string]$urgency) {
        $this.Id = $id
        $this.AssetId = $assetId
        $this.Description = $description
        $this.Priority = $priority
        $this.Category = $category
        $this.Urgency = $urgency
        $this.Status = "open"
        $this.CreatedAt = Get-Date
        $this.UpdatedAt = Get-Date
    }

    [string]ToString() {
        return "WO-$($this.Id): $($this.Description) [$($this.Priority)]"
    }

    [bool]IsHighPriority() {
        return $this.Priority -eq "high"
    }

    [bool]IsImmediate() {
        return $this.Urgency -eq "immediate"
    }
}
```

### **3. ArxLocation Class**
```powershell
# Classes/ArxLocation.ps1
class ArxLocation {
    [string]$Building
    [string]$Floor
    [string]$Room
    [string]$Coordinates
    [string]$FullPath

    ArxLocation([string]$building, [string]$floor, [string]$room) {
        $this.Building = $building
        $this.Floor = $floor
        $this.Room = $room
        $this.FullPath = "$building\Floor $floor\$room"
    }

    [string]ToString() {
        return $this.FullPath
    }

    [string]GetShortPath() {
        return "$($this.Building) $($this.Floor)-$($this.Room)"
    }
}
```

---

## 🎯 **PowerShell Cmdlets Implementation**

### **1. Location Services Cmdlets**
```powershell
# Public/Get-ArxLocation.ps1
function Get-ArxLocation {
    <#
    .SYNOPSIS
        Get current location or location information.
    
    .DESCRIPTION
        Retrieves current user location or information about a specific location.
    
    .PARAMETER Location
        Specific location to get information about.
    
    .PARAMETER Detailed
        Show detailed location information.
    
    .EXAMPLE
        Get-ArxLocation
        # Returns current location
    
    .EXAMPLE
        Get-ArxLocation -Location "Room 205" -Detailed
        # Returns detailed information about Room 205
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [string]$Location,
        
        [switch]$Detailed
    )
    
    try {
        if (-not $Location) {
            # Get current location
            $currentLocation = Get-CurrentArxLocation
            if ($Detailed) {
                return Get-DetailedLocationInfo -Location $currentLocation
            }
            return $currentLocation
        }
        else {
            # Get specific location
            $locationInfo = Get-LocationInfo -Location $Location
            if ($Detailed) {
                return Get-DetailedLocationInfo -Location $locationInfo
            }
            return $locationInfo
        }
    }
    catch {
        Write-Error "Failed to get location: $($_.Exception.Message)"
    }
}

function Get-ArxAssetsAtLocation {
    <#
    .SYNOPSIS
        Get all assets at a specific location.
    
    .DESCRIPTION
        Retrieves all assets found at the specified location.
    
    .PARAMETER Location
        Location to search for assets.
    
    .PARAMETER AssetType
        Filter by asset type.
    
    .PARAMETER Status
        Filter by asset status.
    
    .EXAMPLE
        Get-ArxAssetsAtLocation -Location "Room 205"
        # Returns all assets in Room 205
    
    .EXAMPLE
        Get-ArxAssetsAtLocation -Location "Room 205" -AssetType "electrical_outlet" -Status "inactive"
        # Returns inactive electrical outlets in Room 205
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Location,
        
        [string]$AssetType,
        
        [string]$Status
    )
    
    try {
        $assets = Find-ArxAssets -Location $Location -AssetType $AssetType -Status $Status
        return $assets
    }
    catch {
        Write-Error "Failed to get assets at location: $($_.Exception.Message)"
    }
}
```

### **2. Asset Discovery Cmdlets**
```powershell
# Public/Find-ArxAsset.ps1
function Find-ArxAsset {
    <#
    .SYNOPSIS
        Find assets by type and criteria.
    
    .DESCRIPTION
        Searches for assets based on type, location, and status criteria.
    
    .PARAMETER AssetType
        Type of asset to search for.
    
    .PARAMETER Location
        Location to search in.
    
    .PARAMETER Status
        Asset status filter.
    
    .PARAMETER Detailed
        Show detailed asset information.
    
    .EXAMPLE
        Find-ArxAsset -AssetType "electrical_outlet" -Location "Room 205" -Status "inactive"
        # Finds inactive electrical outlets in Room 205
    
    .EXAMPLE
        Find-ArxAsset -AssetType "hvac_unit" -Location "Floor 2" -Status "warning"
        # Finds HVAC units with warning status on Floor 2
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$AssetType,
        
        [string]$Location,
        
        [string]$Status,
        
        [switch]$Detailed
    )
    
    try {
        $assets = Invoke-ArxAssetSearch -AssetType $AssetType -Location $Location -Status $Status
        
        if ($Detailed) {
            return $assets | ForEach-Object { Get-ArxAssetDetails -AssetId $_.Id }
        }
        
        return $assets
    }
    catch {
        Write-Error "Failed to find assets: $($_.Exception.Message)"
    }
}

function Get-ArxAsset {
    <#
    .SYNOPSIS
        Get detailed information about a specific asset.
    
    .DESCRIPTION
        Retrieves comprehensive information about an asset including connections and history.
    
    .PARAMETER AssetId
        ID of the asset to get information about.
    
    .PARAMETER Detailed
        Show all available asset details.
    
    .EXAMPLE
        Get-ArxAsset -AssetId "E_Outlet_205_02"
        # Returns basic asset information
    
    .EXAMPLE
        Get-ArxAsset -AssetId "E_Outlet_205_02" -Detailed
        # Returns comprehensive asset details
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$AssetId,
        
        [switch]$Detailed
    )
    
    try {
        $asset = Get-ArxAssetDetails -AssetId $AssetId
        
        if ($Detailed) {
            $asset | Add-Member -NotePropertyName "Connections" -NotePropertyValue (Get-ArxAssetConnections -AssetId $AssetId)
            $asset | Add-Member -NotePropertyName "History" -NotePropertyValue (Get-ArxAssetHistory -AssetId $AssetId)
        }
        
        return $asset
    }
    catch {
        Write-Error "Failed to get asset: $($_.Exception.Message)"
    }
}

function Trace-ArxAsset {
    <#
    .SYNOPSIS
        Trace asset connections upstream or downstream.
    
    .DESCRIPTION
        Traces connections from an asset in the specified direction.
    
    .PARAMETER AssetId
        ID of the asset to trace from.
    
    .PARAMETER Direction
        Direction to trace (upstream/downstream).
    
    .PARAMETER MaxDepth
        Maximum depth for tracing.
    
    .EXAMPLE
        Trace-ArxAsset -AssetId "E_Outlet_205_02" -Direction "upstream"
        # Traces upstream connections from electrical outlet
    
    .EXAMPLE
        Trace-ArxAsset -AssetId "H_HVAC_2A" -Direction "downstream" -MaxDepth 3
        # Traces downstream connections from HVAC unit up to 3 levels
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$AssetId,
        
        [ValidateSet("upstream", "downstream")]
        [string]$Direction = "downstream",
        
        [int]$MaxDepth = 3
    )
    
    try {
        $connections = Invoke-ArxAssetTrace -AssetId $AssetId -Direction $Direction -MaxDepth $MaxDepth
        
        # Format output as tree structure
        $formattedConnections = Format-ArxConnectionTree -Connections $connections -Direction $Direction
        
        return $formattedConnections
    }
    catch {
        Write-Error "Failed to trace asset: $($_.Exception.Message)"
    }
}
```

### **3. Work Order Cmdlets**
```powershell
# Public/New-ArxWorkOrder.ps1
function New-ArxWorkOrder {
    <#
    .SYNOPSIS
        Create a new work order.
    
    .DESCRIPTION
        Creates a new work order for a specific asset with priority and category.
    
    .PARAMETER AssetId
        ID of the asset for the work order.
    
    .PARAMETER Description
        Description of the work order.
    
    .PARAMETER Priority
        Priority level (low/medium/high/critical).
    
    .PARAMETER Category
        Work order category (electrical/hvac/security/network).
    
    .PARAMETER Urgency
        Urgency level (normal/urgent/immediate).
    
    .EXAMPLE
        New-ArxWorkOrder -AssetId "E_Outlet_205_02" -Description "Electrical outlet has no power" -Priority "high" -Category "electrical" -Urgency "immediate"
        # Creates high priority electrical work order
    
    .EXAMPLE
        New-ArxWorkOrder -AssetId "H_HVAC_2A" -Description "HVAC unit temperature above normal" -Priority "medium" -Category "hvac"
        # Creates medium priority HVAC work order
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$AssetId,
        
        [Parameter(Mandatory = $true, Position = 1)]
        [string]$Description,
        
        [ValidateSet("low", "medium", "high", "critical")]
        [string]$Priority = "medium",
        
        [ValidateSet("electrical", "hvac", "security", "network", "plumbing", "general")]
        [string]$Category,
        
        [ValidateSet("normal", "urgent", "immediate")]
        [string]$Urgency = "normal"
    )
    
    try {
        # Validate asset exists
        $asset = Get-ArxAsset -AssetId $AssetId
        if (-not $asset) {
            throw "Asset $AssetId not found"
        }
        
        # Create work order
        $workOrder = [ArxWorkOrder]::new(
            (New-ArxWorkOrderId -AssetId $AssetId),
            $AssetId,
            $Description,
            $Priority,
            $Category,
            $Urgency
        )
        
        # Save to database
        Save-ArxWorkOrder -WorkOrder $workOrder
        
        # Send notifications
        Send-ArxWorkOrderNotification -WorkOrder $workOrder
        
        # Format output
        $output = [PSCustomObject]@{
            Id = $workOrder.Id
            AssetId = $workOrder.AssetId
            Description = $workOrder.Description
            Priority = $workOrder.Priority
            Category = $workOrder.Category
            Urgency = $workOrder.Urgency
            Status = $workOrder.Status
            AssignedTo = $workOrder.AssignedTo
            CreatedAt = $workOrder.CreatedAt
        }
        
        Write-Host "✅ Work Order Created: $($workOrder.Id)" -ForegroundColor Green
        return $output
    }
    catch {
        Write-Error "Failed to create work order: $($_.Exception.Message)"
    }
}

function New-ArxQuickWorkOrder {
    <#
    .SYNOPSIS
        Create a work order with automatic asset detection.
    
    .DESCRIPTION
        Creates a work order by automatically detecting the most likely asset based on description and location.
    
    .PARAMETER Description
        Description of the issue.
    
    .PARAMETER Location
        Location where the issue occurred.
    
    .PARAMETER Priority
        Priority level (low/medium/high/critical).
    
    .EXAMPLE
        New-ArxQuickWorkOrder -Description "electrical outlet no power" -Location "Room 205" -Priority "high"
        # Creates work order with automatic asset detection
    
    .EXAMPLE
        New-ArxQuickWorkOrder -Description "HVAC not cooling properly" -Location "Floor 2" -Priority "medium"
        # Creates HVAC work order with automatic asset detection
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Description,
        
        [Parameter(Mandatory = $true, Position = 1)]
        [string]$Location,
        
        [ValidateSet("low", "medium", "high", "critical")]
        [string]$Priority = "medium"
    )
    
    try {
        # Find assets at location
        $assets = Get-ArxAssetsAtLocation -Location $Location
        
        # Determine most likely asset based on description
        $targetAsset = Find-MostLikelyAsset -Description $Description -Assets $assets
        
        if (-not $targetAsset) {
            throw "Could not identify target asset from description"
        }
        
        # Determine category and urgency
        $category = Determine-ArxCategory -Description $Description
        $urgency = Determine-ArxUrgency -Priority $Priority
        
        # Create work order
        return New-ArxWorkOrder -AssetId $targetAsset.Id -Description $Description -Priority $Priority -Category $category -Urgency $urgency
    }
    catch {
        Write-Error "Failed to create quick work order: $($_.Exception.Message)"
    }
}

function Get-ArxWorkOrder {
    <#
    .SYNOPSIS
        Get work order details.
    
    .DESCRIPTION
        Retrieves detailed information about a work order.
    
    .PARAMETER WorkOrderId
        ID of the work order to retrieve.
    
    .EXAMPLE
        Get-ArxWorkOrder -WorkOrderId "WO_2024_001_205_02"
        # Returns work order details
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$WorkOrderId
    )
    
    try {
        $workOrder = Get-ArxWorkOrderDetails -WorkOrderId $WorkOrderId
        
        if ($workOrder) {
            # Format output
            $output = [PSCustomObject]@{
                Id = $workOrder.Id
                AssetId = $workOrder.AssetId
                Description = $workOrder.Description
                Priority = $workOrder.Priority
                Category = $workOrder.Category
                Urgency = $workOrder.Urgency
                Status = $workOrder.Status
                AssignedTo = $workOrder.AssignedTo
                CreatedAt = $workOrder.CreatedAt
                UpdatedAt = $workOrder.UpdatedAt
            }
            
            return $output
        }
        else {
            Write-Warning "Work order $WorkOrderId not found"
        }
    }
    catch {
        Write-Error "Failed to get work order: $($_.Exception.Message)"
    }
}
```

### **4. ASCII-BIM Rendering Cmdlets**
```powershell
# Public/Show-ArxAscii.ps1
function Show-ArxAscii {
    <#
    .SYNOPSIS
        Render location as ASCII art.
    
    .DESCRIPTION
        Renders a location as ASCII art with context-specific symbols.
    
    .PARAMETER Location
        Location to render.
    
    .PARAMETER Context
        Rendering context (it/building/unified).
    
    .PARAMETER Resolution
        Resolution level (low/medium/high).
    
    .PARAMETER FocusAsset
        Asset to focus on in the rendering.
    
    .EXAMPLE
        Show-ArxAscii -Location "Room 205" -Context "electrical"
        # Renders Room 205 with electrical context
    
    .EXAMPLE
        Show-ArxAscii -Location "Floor 2" -Context "hvac" -FocusAsset "H_HVAC_2A"
        # Renders Floor 2 with HVAC context, focusing on specific HVAC unit
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$Location,
        
        [ValidateSet("it", "building", "unified", "electrical", "hvac", "security")]
        [string]$Context = "unified",
        
        [ValidateSet("low", "medium", "high")]
        [string]$Resolution = "medium",
        
        [string]$FocusAsset
    )
    
    try {
        # Get location data
        $locationData = Get-ArxLocationData -Location $Location
        
        # Get assets at location
        $assets = Get-ArxAssetsAtLocation -Location $Location
        
        # Create rendering context
        $renderingContext = [PSCustomObject]@{
            ContextType = $Context
            Resolution = $Resolution
            FocusAsset = $FocusAsset
        }
        
        # Generate ASCII art
        $asciiArt = ConvertTo-ArxAscii -LocationData $locationData -Assets $assets -Context $renderingContext
        
        # Display ASCII art
        Write-Host $asciiArt -ForegroundColor White
        
        # Show legend if needed
        if ($Context -ne "unified") {
            Show-ArxAsciiLegend -Context $Context
        }
    }
    catch {
        Write-Error "Failed to render ASCII: $($_.Exception.Message)"
    }
}

function Show-ArxAsciiFocus {
    <#
    .SYNOPSIS
        Render focused view around specific asset.
    
    .DESCRIPTION
        Renders a focused ASCII view around a specific asset with configurable radius.
    
    .PARAMETER AssetId
        ID of the asset to focus on.
    
    .PARAMETER Radius
        Focus radius around the asset.
    
    .PARAMETER Context
        Rendering context.
    
    .EXAMPLE
        Show-ArxAsciiFocus -AssetId "E_Outlet_205_02" -Radius 5 -Context "electrical"
        # Renders focused view around electrical outlet
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$AssetId,
        
        [int]$Radius = 5,
        
        [ValidateSet("it", "building", "unified", "electrical", "hvac", "security")]
        [string]$Context = "unified"
    )
    
    try {
        # Get asset details
        $asset = Get-ArxAsset -AssetId $AssetId
        
        # Get surrounding assets
        $surroundingAssets = Get-ArxSurroundingAssets -AssetId $AssetId -Radius $Radius
        
        # Create focused rendering context
        $renderingContext = [PSCustomObject]@{
            ContextType = $Context
            FocusAsset = $AssetId
            FocusRadius = $Radius
        }
        
        # Generate focused ASCII art
        $asciiArt = ConvertTo-ArxAsciiFocus -Asset $asset -SurroundingAssets $surroundingAssets -Context $renderingContext
        
        # Display ASCII art
        Write-Host $asciiArt -ForegroundColor White
        
        # Show focus indicator
        Write-Host "Focus: $($asset.Name) ($AssetId)" -ForegroundColor Yellow
    }
    catch {
        Write-Error "Failed to render focused ASCII: $($_.Exception.Message)"
    }
}

function Show-ArxAsciiBuilding {
    <#
    .SYNOPSIS
        Render building as ASCII art.
    
    .DESCRIPTION
        Renders an entire building or floor as ASCII art.
    
    .PARAMETER BuildingId
        ID of the building to render.
    
    .PARAMETER Floor
        Specific floor to render.
    
    .PARAMETER Context
        Rendering context.
    
    .EXAMPLE
        Show-ArxAsciiBuilding -BuildingId "Building A" -Floor 2 -Context "unified"
        # Renders Floor 2 of Building A
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, Position = 0)]
        [string]$BuildingId,
        
        [string]$Floor,
        
        [ValidateSet("it", "building", "unified", "electrical", "hvac", "security")]
        [string]$Context = "unified"
    )
    
    try {
        if ($Floor) {
            $location = "$BuildingId\Floor $Floor"
        }
        else {
            $location = $BuildingId
        }
        
        # Get building data
        $buildingData = Get-ArxBuildingData -BuildingId $BuildingId -Floor $Floor
        
        # Generate building ASCII art
        $asciiArt = ConvertTo-ArxAsciiBuilding -BuildingData $buildingData -Context $Context
        
        # Display ASCII art
        Write-Host $asciiArt -ForegroundColor White
        
        # Show building info
        Write-Host "Building: $BuildingId" -ForegroundColor Cyan
        if ($Floor) {
            Write-Host "Floor: $Floor" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Error "Failed to render building ASCII: $($_.Exception.Message)"
    }
}
```

### **5. System Status Cmdlets**
```powershell
# Public/Get-ArxSystemStatus.ps1
function Get-ArxSystemStatus {
    <#
    .SYNOPSIS
        Get system status for various building systems.
    
    .DESCRIPTION
        Retrieves status information for electrical, HVAC, security, and network systems.
    
    .PARAMETER System
        System type to check (electrical/hvac/security/network/all).
    
    .PARAMETER Zone
        Zone to check (building/floor/room).
    
    .PARAMETER Detailed
        Show detailed status information.
    
    .EXAMPLE
        Get-ArxSystemStatus -System "electrical" -Zone "Floor 2"
        # Gets electrical system status for Floor 2
    
    .EXAMPLE
        Get-ArxSystemStatus -System "all" -Zone "Building A" -Detailed
        # Gets detailed status for all systems in Building A
    #>
    
    [CmdletBinding()]
    param(
        [ValidateSet("electrical", "hvac", "security", "network", "all")]
        [string]$System = "all",
        
        [string]$Zone,
        
        [switch]$Detailed
    )
    
    try {
        $systems = @()
        
        if ($System -eq "all") {
            $systems = @("electrical", "hvac", "security", "network")
        }
        else {
            $systems = @($System)
        }
        
        $results = @()
        
        foreach ($sys in $systems) {
            $status = Get-ArxSystemStatusData -System $sys -Zone $Zone
            
            if ($Detailed) {
                $status | Add-Member -NotePropertyName "Details" -NotePropertyValue (Get-ArxSystemDetails -System $sys -Zone $Zone)
            }
            
            $results += $status
        }
        
        return $results
    }
    catch {
        Write-Error "Failed to get system status: $($_.Exception.Message)"
    }
}
```

---

## 🔧 **Private Functions Implementation**

### **1. Database Connection**
```powershell
# Private/Connect-ArxDatabase.ps1
function Connect-ArxDatabase {
    <#
    .SYNOPSIS
        Connect to Arxos database.
    #>
    
    param()
    
    try {
        $config = Get-ArxConfig
        $connectionString = "Server=$($config.Database.Host);Database=$($config.Database.Name);User Id=$($config.Database.User);Password=$($config.Database.Password)"
        
        $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
        $connection.Open()
        
        return $connection
    }
    catch {
        throw "Failed to connect to database: $($_.Exception.Message)"
    }
}

function Invoke-ArxQuery {
    <#
    .SYNOPSIS
        Execute database query.
    #>
    
    param(
        [string]$Query,
        [hashtable]$Parameters = @{}
    )
    
    try {
        $connection = Connect-ArxDatabase
        
        $command = New-Object System.Data.SqlClient.SqlCommand($Query, $connection)
        
        foreach ($param in $Parameters.GetEnumerator()) {
            $command.Parameters.AddWithValue($param.Key, $param.Value) | Out-Null
        }
        
        $reader = $command.ExecuteReader()
        $results = @()
        
        while ($reader.Read()) {
            $row = @{}
            for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                $row[$reader.GetName($i)] = $reader.GetValue($i)
            }
            $results += [PSCustomObject]$row
        }
        
        $reader.Close()
        $connection.Close()
        
        return $results
    }
    catch {
        throw "Failed to execute query: $($_.Exception.Message)"
    }
}
```

### **2. API Integration**
```powershell
# Private/Invoke-ArxAPI.ps1
function Invoke-ArxAPI {
    <#
    .SYNOPSIS
        Make API call to Arxos backend.
    #>
    
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Body = @{}
    )
    
    try {
        $config = Get-ArxConfig
        $baseUrl = $config.API.BaseUrl
        $timeout = $config.API.Timeout
        
        $uri = "$baseUrl/$Endpoint"
        
        $headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $($config.API.Token)"
        }
        
        $params = @{
            Uri = $uri
            Method = $Method
            Headers = $headers
            TimeoutSec = $timeout
        }
        
        if ($Body.Count -gt 0) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-RestMethod @params
        
        return $response
    }
    catch {
        throw "Failed to call API: $($_.Exception.Message)"
    }
}
```

### **3. ASCII Conversion**
```powershell
# Private/ConvertTo-ArxAscii.ps1
function ConvertTo-ArxAscii {
    <#
    .SYNOPSIS
        Convert location data to ASCII art.
    #>
    
    param(
        [PSCustomObject]$LocationData,
        [ArxAsset[]]$Assets,
        [PSCustomObject]$Context
    )
    
    try {
        # Load symbol mappings
        $symbolMappings = Get-ArxSymbolMappings
        
        # Create grid
        $grid = Initialize-ArxGrid -LocationData $LocationData -Resolution $Context.Resolution
        
        # Place assets on grid
        foreach ($asset in $Assets) {
            $symbol = Get-ArxSymbol -Asset $asset -Context $Context.ContextType -Mappings $symbolMappings
            $position = Get-ArxAssetPosition -Asset $asset -LocationData $LocationData
            
            Set-ArxGridSymbol -Grid $grid -Position $position -Symbol $symbol
        }
        
        # Apply focus if specified
        if ($Context.FocusAsset) {
            Apply-ArxFocus -Grid $grid -FocusAsset $Context.FocusAsset -Assets $Assets
        }
        
        # Convert grid to ASCII string
        $asciiArt = Convert-ArxGridToString -Grid $grid
        
        return $asciiArt
    }
    catch {
        throw "Failed to convert to ASCII: $($_.Exception.Message)"
    }
}

function Get-ArxSymbol {
    <#
    .SYNOPSIS
        Get ASCII symbol for asset.
    #>
    
    param(
        [ArxAsset]$Asset,
        [string]$Context,
        [hashtable]$Mappings
    )
    
    $baseSymbol = $Mappings[$Asset.Type]
    if (-not $baseSymbol) {
        $baseSymbol = "?"
    }
    
    # Apply context-specific modifications
    if ($Context -eq "it" -and $Asset.Type -in @("electrical_outlet", "network_switch")) {
        $baseSymbol = "I$baseSymbol"
    }
    elseif ($Context -eq "building") {
        $baseSymbol = "B$baseSymbol"
    }
    
    # Add status indicator
    $statusSymbol = Get-ArxStatusSymbol -Status $Asset.Status
    $baseSymbol += $statusSymbol
    
    return $baseSymbol
}

function Get-ArxStatusSymbol {
    <#
    .SYNOPSIS
        Get status indicator symbol.
    #>
    
    param([string]$Status)
    
    $statusSymbols = @{
        "active" = ""
        "inactive" = "!"
        "warning" = "~"
        "error" = "X"
        "maintenance" = "M"
    }
    
    return $statusSymbols[$Status] ?? ""
}
```

---

## 📊 **Configuration Management**

### **Module Configuration**
```powershell
# Config/ArxosConfig.psd1
@{
    Database = @{
        Host = "localhost"
        Port = 5432
        Name = "arxos_db"
        User = "arxos_user"
        Password = ""
    }
    
    API = @{
        BaseUrl = "http://localhost:8080"
        Timeout = 30
        Token = ""
    }
    
    CLI = @{
        DefaultContext = "unified"
        DefaultResolution = "medium"
        AutoComplete = $true
        ColorOutput = $true
    }
    
    Notifications = @{
        Email = $true
        Slack = $false
        Webhook = ""
    }
}
```

### **Symbol Mappings**
```powershell
# Config/SymbolMappings.psd1
@{
    # IT Assets
    "network_switch" = "S"
    "access_point" = "A"
    "server" = "V"
    "router" = "R"
    "firewall" = "F"
    "ups" = "U"
    "patch_panel" = "P"
    "cable" = "-"
    "fiber" = "="
    
    # Building Assets
    "electrical_panel" = "E"
    "electrical_outlet" = "O"
    "hvac_unit" = "H"
    "lighting_fixture" = "L"
    "security_camera" = "C"
    "door" = "D"
    "window" = "W"
    "wall" = "#"
    "room" = " "
    
    # Shared Assets
    "sensor" = "O"
    "controller" = "T"
    "actuator" = "X"
    "valve" = "V"
    "pump" = "P"
}
```

---

## 🚀 **Installation and Usage**

### **Module Installation**
```powershell
# Install Arxos PowerShell module
Install-Module -Name ArxosCLI -Repository PSGallery -Force

# Import module
Import-Module ArxosCLI

# Configure module
Set-ArxConfig -DatabaseHost "localhost" -DatabaseName "arxos_db"
Set-ArxConfig -APIBaseUrl "http://localhost:8080"
```

### **Usage Examples**
```powershell
# Get current location
Get-ArxLocation

# Find electrical outlets
Find-ArxAsset -AssetType "electrical_outlet" -Location "Room 205" -Status "inactive"

# Create work order
New-ArxWorkOrder -AssetId "E_Outlet_205_02" -Description "Electrical outlet has no power" -Priority "high" -Category "electrical" -Urgency "immediate"

# Show ASCII rendering
Show-ArxAscii -Location "Room 205" -Context "electrical" -FocusAsset "E_Outlet_205_02"

# Get system status
Get-ArxSystemStatus -System "electrical" -Zone "Floor 2" -Detailed
```

### **PowerShell Profile Integration**
```powershell
# Add to PowerShell profile
Add-Content -Path $PROFILE -Value @"
# Arxos CLI Module
Import-Module ArxosCLI
Set-ArxConfig -DatabaseHost "localhost" -DatabaseName "arxos_db"
"@
```

---

## 📈 **Testing and Validation**

### **Pester Test Suite**
```powershell
# Tests/ArxosCLI.Tests.ps1
Describe "Arxos CLI Module" {
    BeforeAll {
        Import-Module ArxosCLI -Force
    }
    
    Describe "Location Services" {
        It "Should get current location" {
            $location = Get-ArxLocation
            $location | Should Not BeNullOrEmpty
        }
        
        It "Should get assets at location" {
            $assets = Get-ArxAssetsAtLocation -Location "Room 205"
            $assets | Should Not BeNullOrEmpty
        }
    }
    
    Describe "Asset Discovery" {
        It "Should find assets by type" {
            $assets = Find-ArxAsset -AssetType "electrical_outlet" -Location "Room 205"
            $assets | Should Not BeNullOrEmpty
        }
        
        It "Should get asset details" {
            $asset = Get-ArxAsset -AssetId "E_Outlet_205_02"
            $asset | Should Not BeNullOrEmpty
            $asset.Id | Should Be "E_Outlet_205_02"
        }
    }
    
    Describe "Work Order Creation" {
        It "Should create work order" {
            $workOrder = New-ArxWorkOrder -AssetId "E_Outlet_205_02" -Description "Test work order" -Priority "medium"
            $workOrder | Should Not BeNullOrEmpty
            $workOrder.Id | Should Not BeNullOrEmpty
        }
        
        It "Should create quick work order" {
            $workOrder = New-ArxQuickWorkOrder -Description "electrical outlet no power" -Location "Room 205" -Priority "high"
            $workOrder | Should Not BeNullOrEmpty
        }
    }
    
    Describe "ASCII Rendering" {
        It "Should render ASCII art" {
            $ascii = Show-ArxAscii -Location "Room 205" -Context "electrical"
            $ascii | Should Not BeNullOrEmpty
        }
    }
}
```

---

## 🎯 **Key Features Summary**

### **1. Native PowerShell Experience**
- PowerShell classes for type safety
- Pipeline support for data processing
- Error handling with try-catch blocks
- Parameter validation and help system

### **2. Comprehensive Cmdlets**
- Location services (`Get-ArxLocation`, `Get-ArxAssetsAtLocation`)
- Asset discovery (`Find-ArxAsset`, `Get-ArxAsset`, `Trace-ArxAsset`)
- Work order management (`New-ArxWorkOrder`, `New-ArxQuickWorkOrder`, `Get-ArxWorkOrder`)
- ASCII-BIM rendering (`Show-ArxAscii`, `Show-ArxAsciiFocus`, `Show-ArxAsciiBuilding`)
- System status (`Get-ArxSystemStatus`)

### **3. Windows Integration**
- SQL Server connectivity
- Windows authentication support
- PowerShell profile integration
- Windows event logging

### **4. Advanced Features**
- Async/await support for long-running operations
- Comprehensive error handling and logging
- Configuration management
- Testing framework integration

This PowerShell module provides Windows users with a native, powerful interface for building management that complements the Python CLI system while leveraging Windows-specific features and PowerShell's strengths.