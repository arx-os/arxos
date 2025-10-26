package com.arxos.mobile.ui.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arxos.mobile.data.DetectedEquipment
import com.arxos.mobile.data.Equipment
import com.arxos.mobile.data.EquipmentFilter
import com.arxos.mobile.service.ArxOSCoreService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class TerminalViewModel : ViewModel() {
    private val _terminalState = MutableStateFlow(TerminalState())
    val terminalState: StateFlow<TerminalState> = _terminalState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreService()
    
    fun updateCommandText(text: String) {
        _terminalState.value = _terminalState.value.copy(commandText = text)
    }
    
    fun executeCommand() {
        val command = _terminalState.value.commandText.trim()
        if (command.isEmpty()) return
        
        _terminalState.value = _terminalState.value.copy(
            commandText = "",
            isExecuting = true,
            outputLines = _terminalState.value.outputLines + "arx$ $command"
        )
        
        viewModelScope.launch {
            try {
                val result = arxosCoreService.executeCommand(command)
                _terminalState.value = _terminalState.value.copy(
                    outputLines = _terminalState.value.outputLines + result,
                    isExecuting = false
                )
            } catch (e: Exception) {
                _terminalState.value = _terminalState.value.copy(
                    outputLines = _terminalState.value.outputLines + "Error: ${e.message}",
                    isExecuting = false
                )
            }
        }
    }
}

class ARViewModel : ViewModel() {
    private val _arState = MutableStateFlow(ARState())
    val arState: StateFlow<ARState> = _arState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreService()
    
    fun startScanning() {
        _arState.value = _arState.value.copy(
            isScanning = true,
            detectedEquipment = emptyList()
        )
    }
    
    fun stopScanning() {
        _arState.value = _arState.value.copy(isScanning = false)
    }
    
    fun updateCurrentRoom(room: String) {
        _arState.value = _arState.value.copy(currentRoom = room)
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
            position = com.google.ar.sceneform.math.Vector3(0f, 0f, 0f),
            status = "Detected",
            icon = "wrench"
        )
        addDetectedEquipment(manualEquipment)
    }
    
    fun saveScan() {
        viewModelScope.launch {
            try {
                val result = arxosCoreService.saveARScan(
                    _arState.value.detectedEquipment,
                    _arState.value.currentRoom
                )
                _arState.value = _arState.value.copy(isScanning = false)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
}

class EquipmentViewModel : ViewModel() {
    private val _equipmentState = MutableStateFlow(EquipmentState())
    val equipmentState: StateFlow<EquipmentState> = _equipmentState.asStateFlow()
    
    private val arxosCoreService = ArxOSCoreService()
    
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
    val detectedEquipment: List<DetectedEquipment> = emptyList()
)

data class EquipmentState(
    val equipment: List<Equipment> = emptyList(),
    val filteredEquipment: List<Equipment> = emptyList(),
    val searchText: String = "",
    val selectedFilter: EquipmentFilter = EquipmentFilter.ALL,
    val isLoading: Boolean = false,
    val filters: List<EquipmentFilter> = EquipmentFilter.values().toList()
)

enum class EquipmentFilter(val name: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    ALL("All", androidx.compose.material.icons.Icons.Default.List),
    HVAC("HVAC", androidx.compose.material.icons.Icons.Default.Air),
    ELECTRICAL("Electrical", androidx.compose.material.icons.Icons.Default.Bolt),
    PLUMBING("Plumbing", androidx.compose.material.icons.Icons.Default.WaterDrop),
    SAFETY("Safety", androidx.compose.material.icons.Icons.Default.Security)
}
