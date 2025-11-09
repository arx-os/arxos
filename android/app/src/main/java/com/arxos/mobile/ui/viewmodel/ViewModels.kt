package com.arxos.mobile.ui.viewmodel

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.arxos.mobile.data.DetectedEquipment
import com.arxos.mobile.data.Equipment
import com.arxos.mobile.data.EquipmentFilter
import com.arxos.mobile.data.Vector3
import com.arxos.mobile.service.ArxOSCoreServiceFactory
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class TerminalViewModel(application: Application) : AndroidViewModel(application) {
    private val _terminalState = MutableStateFlow(TerminalState())
    val terminalState: StateFlow<TerminalState> = _terminalState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreServiceFactory.getInstance(application)
    
    fun updateCommandText(text: String) {
        _terminalState.value = _terminalState.value.copy(commandText = text)
    }
    
    fun executeCommand() {
        val command = _terminalState.value.commandText.trim()
        if (command.isEmpty()) return
        
        _terminalState.value = _terminalState.value.copy(
            commandText = "",
            isExecuting = true,
            outputLines = _terminalState.value.outputLines + listOf("arx$ $command")
        )
        
        viewModelScope.launch {
            try {
                val result = arxosCoreService.executeCommand(command)
                _terminalState.value = _terminalState.value.copy(
                    outputLines = _terminalState.value.outputLines + listOf(result.output),
                    isExecuting = false
                )
            } catch (e: Exception) {
                _terminalState.value = _terminalState.value.copy(
                    outputLines = _terminalState.value.outputLines + listOf("Error: ${e.message}"),
                    isExecuting = false
                )
            }
        }
    }
}

class ARViewModel(application: Application) : AndroidViewModel(application) {
    private val _arState = MutableStateFlow(ARState())
    val arState: StateFlow<ARState> = _arState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreServiceFactory.getInstance(application)
    
    fun updateARState(update: (ARState) -> ARState) {
        _arState.value = update(_arState.value)
    }
    
    fun startScanning() {
        _arState.value = _arState.value.copy(
            isScanning = true,
            detectedEquipment = emptyList(),
            scanStartTime = System.currentTimeMillis()
        )
    }
    
    fun stopScanning() {
        _arState.value = _arState.value.copy(
            isScanning = false,
            scanStartTime = null
        )
    }
    
    fun updateFloorLevel(level: Int) {
        _arState.value = _arState.value.copy(floorLevel = level)
    }
    
    fun updateCurrentRoom(room: String) {
        _arState.value = _arState.value.copy(currentRoom = room)
    }
    
    fun updateBuildingName(building: String) {
        _arState.value = _arState.value.copy(buildingName = building)
        arxosCoreService.setActiveBuilding(building)
    }
    
    fun addDetectedEquipment(equipment: DetectedEquipment) {
        val currentEquipment = _arState.value.detectedEquipment.toMutableList()
        if (!currentEquipment.any { it.id == equipment.id }) {
            currentEquipment.add(equipment)
            _arState.value = _arState.value.copy(detectedEquipment = currentEquipment)
        }
    }
    
    fun addEquipmentManually() {
        val manualEquipment = DetectedEquipment(
            id = "manual_${System.currentTimeMillis()}",
            name = "Manual Equipment",
            type = "Manual",
            position = Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "wrench"
        )
        addDetectedEquipment(manualEquipment)
    }
    
    fun saveScan() {
        if (_arState.value.isSavingScan) {
            return
        }
        
        _arState.value = _arState.value.copy(
            isSavingScan = true,
            saveScanError = null,
            pendingEquipmentIds = emptyList()
        )
        
        viewModelScope.launch {
            try {
                // Calculate scan duration
                val scanDurationMs = _arState.value.scanStartTime?.let {
                    System.currentTimeMillis() - it
                }
                
                // Build ARScanData matching Rust FFI structure
                val scanData = com.arxos.mobile.data.ARScanData(
                    detectedEquipment = _arState.value.detectedEquipment,
                    roomBoundaries = com.arxos.mobile.data.RoomBoundaries(),
                    deviceType = android.os.Build.MODEL,
                    appVersion = null,
                    scanDurationMs = scanDurationMs,
                    pointCount = null,
                    accuracyEstimate = null,
                    lightingConditions = null,
                    roomName = _arState.value.currentRoom,
                    floorLevel = _arState.value.floorLevel
                )
                
                val buildingName = (
                    if (_arState.value.buildingName.isNotEmpty()) {
                        _arState.value.buildingName
                    } else {
                        _arState.value.currentRoom
                    }
                )

                arxosCoreService.setActiveBuilding(buildingName)
                val saveResult = arxosCoreService.saveARScan(
                    scanData = scanData,
                    buildingName = buildingName,
                    confidenceThreshold = 0.7
                )
                
                if (saveResult.success) {
                    _arState.value = _arState.value.copy(
                        isScanning = false,
                        isSavingScan = false,
                        pendingEquipmentIds = saveResult.pendingIds,
                        scanStartTime = null
                    )
                } else {
                    _arState.value = _arState.value.copy(
                        isSavingScan = false,
                        saveScanError = saveResult.error ?: "Failed to save scan"
                    )
                }
            } catch (e: Exception) {
                _arState.value = _arState.value.copy(
                    isSavingScan = false,
                    saveScanError = e.message ?: "Unknown error saving scan"
                )
            }
        }
    }
    
    fun loadARModel(buildingName: String, format: String = "gltf") {
        if (_arState.value.isLoadingModel) {
            return
        }
        
        _arState.value = _arState.value.copy(
            isLoadingModel = true,
            modelLoadError = null,
            loadedModel = buildingName,
            modelFilePath = null
        )
        
        viewModelScope.launch {
            try {
                arxosCoreService.setActiveBuilding(buildingName)
                val result = arxosCoreService.loadARModel(buildingName, format)
                
                if (result.success && result.filePath != null) {
                    _arState.value = _arState.value.copy(
                        isLoadingModel = false,
                        modelFilePath = result.filePath,
                        modelLoadError = null
                    )
                } else {
                    _arState.value = _arState.value.copy(
                        isLoadingModel = false,
                        modelLoadError = result.error ?: "Failed to load AR model",
                        modelFilePath = null
                    )
                }
            } catch (e: Exception) {
                _arState.value = _arState.value.copy(
                    isLoadingModel = false,
                    modelLoadError = e.message ?: "Unknown error loading model",
                    modelFilePath = null
                )
            }
        }
    }
    
    fun clearLoadedModel() {
        _arState.value = _arState.value.copy(
            loadedModel = null,
            modelFilePath = null,
            modelLoadError = null,
            isLoadingModel = false
        )
    }
    
    /**
     * List pending equipment for a building
     */
    suspend fun listPendingEquipment(buildingName: String): com.arxos.mobile.service.PendingEquipmentListResult {
        arxosCoreService.setActiveBuilding(buildingName)
        return arxosCoreService.listPendingEquipment(buildingName)
    }
    
    /**
     * Confirm pending equipment
     */
    suspend fun confirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        commitToGit: Boolean = true
    ): com.arxos.mobile.service.PendingEquipmentConfirmResult {
        arxosCoreService.setActiveBuilding(buildingName)
        return arxosCoreService.confirmPendingEquipment(buildingName, pendingId, commitToGit)
    }
    
    /**
     * Reject pending equipment
     */
    suspend fun rejectPendingEquipment(
        buildingName: String,
        pendingId: String
    ): com.arxos.mobile.service.PendingEquipmentRejectResult {
        arxosCoreService.setActiveBuilding(buildingName)
        return arxosCoreService.rejectPendingEquipment(buildingName, pendingId)
    }
}

class EquipmentViewModel(application: Application) : AndroidViewModel(application) {
    private val _equipmentState = MutableStateFlow(EquipmentState())
    val equipmentState: StateFlow<EquipmentState> = _equipmentState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreServiceFactory.getInstance(application)
    
    init {
        loadEquipment()
    }
    
    fun updateSearchText(text: String) {
        _equipmentState.value = _equipmentState.value.copy(searchText = text)
    }
    
    fun clearSearch() {
        _equipmentState.value = _equipmentState.value.copy(searchText = "")
    }
    
    fun setFilter(filter: EquipmentFilter) {
        _equipmentState.value = _equipmentState.value.copy(selectedFilter = filter)
    }
    
    private fun loadEquipment() {
        _equipmentState.value = _equipmentState.value.copy(isLoading = true)
        
        viewModelScope.launch {
            try {
                val equipment = arxosCoreService.getEquipment()
                _equipmentState.value = _equipmentState.value.copy(
                    equipment = equipment,
                    isLoading = false
                )
            } catch (e: Exception) {
                _equipmentState.value = _equipmentState.value.copy(isLoading = false)
            }
        }
    }
}

// State classes
data class TerminalState(
    val commandText: String = "",
    val outputLines: List<String> = listOf(
        "ArxOS Mobile Terminal - Git for Buildings",
        "Type 'help' for available commands"
    ),
    val isExecuting: Boolean = false
)

data class ARState(
    val isScanning: Boolean = false,
    val currentRoom: String = "Room 301",
    val buildingName: String = "",
    val detectedEquipment: List<DetectedEquipment> = emptyList(),
    val loadedModel: String? = null,
    val isLoadingModel: Boolean = false,
    val modelFilePath: String? = null,
    val modelLoadError: String? = null,
    val scanStartTime: Long? = null,
    val floorLevel: Int = 0,
    val isSavingScan: Boolean = false,
    val saveScanError: String? = null,
    val pendingEquipmentIds: List<String> = emptyList()
)

data class EquipmentState(
    val equipment: List<Equipment> = emptyList(),
    val filteredEquipment: List<Equipment> = emptyList(),
    val searchText: String = "",
    val selectedFilter: EquipmentFilter = EquipmentFilter.ALL,
    val isLoading: Boolean = false,
    val filters: List<EquipmentFilter> = EquipmentFilter.values().toList()
)
