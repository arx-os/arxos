package com.arxos.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch
import com.arxos.mobile.data.DetectedEquipment
import com.arxos.mobile.data.Vector3
import com.arxos.mobile.ui.components.ARViewContainer
import com.arxos.mobile.ui.components.EquipmentPlacementDialog
import com.arxos.mobile.ui.components.PendingEquipmentConfirmationView
import com.arxos.mobile.ui.viewmodel.ARViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ARScreen(viewModel: ARViewModel = androidx.lifecycle.viewmodel.compose.viewModel()) {
    val arState by viewModel.arState.collectAsState()
    val coroutineScope = rememberCoroutineScope()
    
    // State for equipment placement dialog
    var showEquipmentDialog by remember { mutableStateOf(false) }
    var pendingEquipment by remember { mutableStateOf<DetectedEquipment?>(null) }
    var equipmentName by remember { mutableStateOf("") }
    var equipmentType by remember { mutableStateOf("Unknown") }
    
    // State for pending equipment confirmation
    var showPendingConfirmation by remember { mutableStateOf(false) }
    
    // Show pending confirmation when pending IDs are available after save
    LaunchedEffect(arState.pendingEquipmentIds) {
        if (arState.pendingEquipmentIds.isNotEmpty() && !showPendingConfirmation) {
            showPendingConfirmation = true
        }
    }
    
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        if (arState.isScanning) {
            // AR Camera View with ARCore
            ARViewContainer(
                onEquipmentDetected = { equipment ->
                    viewModel.addDetectedEquipment(equipment)
                },
                isScanning = arState.isScanning,
                loadedModel = arState.loadedModel,
                modelFilePath = arState.modelFilePath,
                onEquipmentPlaced = { equipment ->
                    // Show equipment placement dialog
                    pendingEquipment = equipment
                    equipmentName = equipment.name
                    equipmentType = equipment.type
                    showEquipmentDialog = true
                }
            )
            
            // Show loading indicator if model is loading
            if (arState.isLoadingModel) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f)),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(color = Color.White)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "Loading AR model...",
                            color = Color.White
                        )
                    }
                }
            }
            
            // Show saving indicator if scan is being saved
            if (arState.isSavingScan) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f)),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(color = Color.White)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "Saving scan...",
                            color = Color.White
                        )
                    }
                }
            }
            
            // Show save error if scan save failed
            if (arState.saveScanError != null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f)),
                    contentAlignment = Alignment.Center
                ) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = Color.Red.copy(alpha = 0.9f)
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "Save Error",
                                color = Color.White,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = arState.saveScanError ?: "Unknown error",
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Button(
                                onClick = {
                                    viewModel.updateARState { it.copy(saveScanError = null) }
                                }
                            ) {
                                Text("Dismiss")
                            }
                        }
                    }
                }
            }
            
            // Show error if model loading failed
            if (arState.modelLoadError != null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f)),
                    contentAlignment = Alignment.Center
                ) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = Color.Red.copy(alpha = 0.9f)
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "Model Load Error",
                                color = Color.White,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = arState.modelLoadError ?: "Unknown error",
                                color = Color.White
                            )
                        }
                    }
                }
            }
            
            // Pending equipment confirmation view
            if (showPendingConfirmation) {
                PendingEquipmentConfirmationView(
                    pendingIds = arState.pendingEquipmentIds,
                    buildingName = if (arState.buildingName.isNotEmpty()) {
                        arState.buildingName
                    } else {
                        arState.currentRoom
                    },
                    onConfirm = { pendingId ->
                        coroutineScope.launch {
                            val result = viewModel.confirmPendingEquipment(
                                buildingName = if (arState.buildingName.isNotEmpty()) {
                                    arState.buildingName
                                } else {
                                    arState.currentRoom
                                },
                                pendingId = pendingId,
                                commitToGit = true
                            )
                            if (result.success) {
                                // Refresh pending list will happen automatically in view
                            }
                        }
                    },
                    onReject = { pendingId ->
                        coroutineScope.launch {
                            val result = viewModel.rejectPendingEquipment(
                                buildingName = if (arState.buildingName.isNotEmpty()) {
                                    arState.buildingName
                                } else {
                                    arState.currentRoom
                                },
                                pendingId = pendingId
                            )
                            if (result.success) {
                                // Refresh pending list will happen automatically in view
                            }
                        }
                    },
                    onDismiss = {
                        showPendingConfirmation = false
                    }
                )
            }
            
            // Equipment placement dialog
            if (showEquipmentDialog && pendingEquipment != null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f)),
                    contentAlignment = Alignment.Center
                ) {
                    EquipmentPlacementDialog(
                        equipmentName = equipmentName,
                        onEquipmentNameChange = { equipmentName = it },
                        equipmentType = equipmentType,
                        onEquipmentTypeChange = { equipmentType = it },
                        onSave = {
                            val equipment = pendingEquipment ?: return@EquipmentPlacementDialog
                            
                            // Create new equipment with user-provided details
                            val newEquipment = DetectedEquipment(
                                id = equipment.id,
                                name = if (equipmentName.isEmpty()) {
                                    "Equipment ${arState.detectedEquipment.size + 1}"
                                } else {
                                    equipmentName
                                },
                                type = equipmentType,
                                position = equipment.position,
                                status = "Placed",
                                icon = iconForEquipmentType(equipmentType)
                            )
                            
                            // Add to detected equipment list
                            viewModel.addDetectedEquipment(newEquipment)
                            
                            // Reset dialog state
                            showEquipmentDialog = false
                            pendingEquipment = null
                            equipmentName = ""
                            equipmentType = "Unknown"
                        },
                        onCancel = {
                            showEquipmentDialog = false
                            pendingEquipment = null
                            equipmentName = ""
                            equipmentType = "Unknown"
                        }
                    )
                }
            }
            
            // AR Overlay UI
            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                // Top Status Bar
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = Color.Black.copy(alpha = 0.7f)
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(12.dp)
                        ) {
                            Text(
                                text = "Scanning: ${arState.currentRoom}",
                                color = Color.White
                            )
                            if (arState.scanStartTime != null) {
                                val durationSeconds = (System.currentTimeMillis() - arState.scanStartTime) / 1000
                                Text(
                                    text = "Duration: ${durationSeconds}s",
                                    color = Color.White.copy(alpha = 0.7f),
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                            if (arState.floorLevel != 0) {
                                Text(
                                    text = "Floor: ${arState.floorLevel}",
                                    color = Color.White.copy(alpha = 0.7f),
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        }
                    }
                    
                    IconButton(
                        onClick = { viewModel.stopScanning() },
                        modifier = Modifier
                            .background(
                                Color.Red.copy(alpha = 0.8f),
                                RoundedCornerShape(24.dp)
                            )
                    ) {
                        Icon(
                            Icons.Default.Stop,
                            contentDescription = "Stop Scanning",
                            tint = Color.White
                        )
                    }
                }
                
                Spacer(modifier = Modifier.weight(1f))
                
                // Equipment Detection Indicators
                if (arState.detectedEquipment.isNotEmpty()) {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = Color.Black.copy(alpha = 0.7f)
                        )
                    ) {
                        LazyRow(
                            modifier = Modifier.padding(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(arState.detectedEquipment) { equipment ->
                                EquipmentTag(equipment = equipment)
                            }
                        }
                    }
                }
                
                // Control Panel
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    ControlButton(
                        icon = Icons.Default.Add,
                        label = "Add",
                        onClick = {
                            viewModel.addEquipmentManually()
                        }
                    )
                    
                    ControlButton(
                        icon = Icons.Default.List,
                        label = "List",
                        onClick = { /* Navigate to equipment list */ }
                    )
                    
                    ControlButton(
                        icon = Icons.Default.Save,
                        label = "Save",
                        onClick = { viewModel.saveScan() }
                    )
                }
            }
        } else {
            // Start Screen
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Icon(
                    Icons.Default.CameraAlt,
                    contentDescription = "AR Scanner",
                    modifier = Modifier.size(80.dp),
                    tint = MaterialTheme.colorScheme.primary
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                Text(
                    text = "AR Equipment Scanner",
                    style = MaterialTheme.typography.headlineLarge,
                    fontWeight = FontWeight.Bold
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = "Scan rooms and tag equipment using AR",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Spacer(modifier = Modifier.height(32.dp))
                
                OutlinedTextField(
                    value = arState.currentRoom,
                    onValueChange = { viewModel.updateCurrentRoom(it) },
                    label = { Text("Room Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                OutlinedTextField(
                    value = arState.buildingName,
                    onValueChange = { viewModel.updateBuildingName(it) },
                    label = { Text("Building Name (optional)") },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("Enter building name to load AR model") },
                    trailingIcon = {
                        if (arState.loadedModel != null) {
                            IconButton(onClick = { viewModel.clearLoadedModel() }) {
                                Icon(Icons.Default.Close, contentDescription = "Clear model")
                            }
                        }
                    }
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Floor Level Input
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Floor Level:",
                        modifier = Modifier.weight(1f)
                    )
                    IconButton(
                        onClick = { viewModel.updateFloorLevel(arState.floorLevel - 1) }
                    ) {
                        Icon(Icons.Default.Remove, contentDescription = "Decrease floor level")
                    }
                    Text(
                        text = "${arState.floorLevel}",
                        modifier = Modifier.padding(horizontal = 16.dp),
                        style = MaterialTheme.typography.titleMedium
                    )
                    IconButton(
                        onClick = { viewModel.updateFloorLevel(arState.floorLevel + 1) }
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Increase floor level")
                    }
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Button(
                        onClick = { viewModel.startScanning() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Icon(Icons.Default.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Start AR Scan")
                    }
                    
                    if (arState.buildingName.isNotEmpty()) {
                        Button(
                            onClick = { viewModel.loadARModel(arState.buildingName, "gltf") },
                            modifier = Modifier.weight(1f),
                            enabled = !arState.isLoadingModel
                        ) {
                            Icon(Icons.Default.ThreeDRotation, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Load Model")
                        }
                    }
                }
                
                // Last Scan Results
                if (arState.detectedEquipment.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(32.dp))
                    
                    Card(
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Text(
                                text = "Last Scan Results",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            
                            Spacer(modifier = Modifier.height(8.dp))
                            
                            arState.detectedEquipment.take(3).forEach { equipment ->
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(equipment.name)
                                    Text(
                                        equipment.status,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ControlButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        FloatingActionButton(
            onClick = onClick,
            modifier = Modifier.size(56.dp)
        ) {
            Icon(icon, contentDescription = label)
        }
        
        Spacer(modifier = Modifier.height(4.dp))
        
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = Color.White
        )
    }
}

private fun iconForEquipmentType(type: String): String {
    return when (type.lowercase()) {
        "hvac", "air conditioning", "heating" -> "fan"
        "electrical", "electrical panel" -> "bolt"
        "plumbing", "water", "piping" -> "drop"
        "safety", "fire", "sprinkler" -> "shield"
        "lighting", "light" -> "lightbulb"
        else -> "gear"
    }
}

@Composable
fun EquipmentTag(
    equipment: DetectedEquipment,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.8f)
        ),
        shape = RoundedCornerShape(16.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                Icons.Default.Settings,
                contentDescription = equipment.type,
                modifier = Modifier.size(16.dp),
                tint = Color.White
            )
            
            Spacer(modifier = Modifier.width(6.dp))
            
            Text(
                text = equipment.name,
                color = Color.White,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Medium
            )
        }
    }
}