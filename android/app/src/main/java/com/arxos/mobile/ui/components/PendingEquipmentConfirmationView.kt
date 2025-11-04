package com.arxos.mobile.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.arxos.mobile.service.PendingEquipmentItem
import com.arxos.mobile.service.Position
import kotlinx.coroutines.launch

/**
 * Pending Equipment Confirmation View
 * Equivalent to iOS PendingEquipmentConfirmationView
 * 
 * Displays list of pending equipment items from AR scans and allows
 * users to confirm or reject them.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PendingEquipmentConfirmationView(
    pendingIds: List<String>,
    buildingName: String,
    onConfirm: (String) -> Unit,
    onReject: (String) -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    var pendingEquipment by remember { mutableStateOf<List<PendingEquipmentItem>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var showSuccessAlert by remember { mutableStateOf(false) }
    var successMessage by remember { mutableStateOf("") }
    
    val context = androidx.compose.ui.platform.LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    // Load pending equipment on appear
    LaunchedEffect(pendingIds, buildingName) {
        if (pendingIds.isNotEmpty() || buildingName.isNotEmpty()) {
            isLoading = true
            
            try {
                val service = com.arxos.mobile.service.ArxOSCoreServiceFactory.getInstance(context)
                val result = service.listPendingEquipment(buildingName)
                
                if (result.success) {
                    pendingEquipment = result.items
                } else {
                    errorMessage = result.error ?: "Failed to load pending equipment"
                }
            } catch (e: Exception) {
                errorMessage = e.message ?: "Unknown error loading pending equipment"
            } finally {
                isLoading = false
            }
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Pending Equipment") },
                navigationIcon = {
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Close")
                    }
                }
            )
        },
        modifier = modifier
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            when {
                isLoading -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            CircularProgressIndicator()
                            Text("Loading pending equipment...")
                        }
                    }
                }
                
                pendingEquipment.isEmpty() -> {
                    EmptyPendingEquipmentView()
                }
                
                else -> {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(pendingEquipment) { equipment ->
                            PendingEquipmentRow(
                                equipment = equipment,
                                onConfirm = {
                                    coroutineScope.launch {
                                        isLoading = true
                                        
                                        try {
                                            val service = com.arxos.mobile.service.ArxOSCoreServiceFactory.getInstance(context)
                                            val result = service.confirmPendingEquipment(
                                                buildingName = buildingName,
                                                pendingId = equipment.id,
                                                commitToGit = true
                                            )
                                            
                                            if (result.success) {
                                                val message = if (result.committed && result.commitId != null) {
                                                    "Equipment '${result.equipmentId}' confirmed and committed to Git (commit: ${result.commitId.take(8)})"
                                                } else {
                                                    "Equipment '${result.equipmentId}' confirmed and saved"
                                                }
                                                successMessage = message
                                                showSuccessAlert = true
                                                // Remove from list
                                                pendingEquipment = pendingEquipment.filter { it.id != equipment.id }
                                            } else {
                                                errorMessage = result.error ?: "Failed to confirm equipment"
                                            }
                                        } catch (e: Exception) {
                                            errorMessage = e.message ?: "Unknown error confirming equipment"
                                        } finally {
                                            isLoading = false
                                        }
                                    }
                                },
                                onReject = {
                                    coroutineScope.launch {
                                        isLoading = true
                                        
                                        try {
                                            val service = com.arxos.mobile.service.ArxOSCoreServiceFactory.getInstance(context)
                                            val result = service.rejectPendingEquipment(
                                                buildingName = buildingName,
                                                pendingId = equipment.id
                                            )
                                            
                                            if (result.success) {
                                                successMessage = "Equipment '${result.pendingId}' rejected"
                                                showSuccessAlert = true
                                                // Remove from list
                                                pendingEquipment = pendingEquipment.filter { it.id != equipment.id }
                                            } else {
                                                errorMessage = result.error ?: "Failed to reject equipment"
                                            }
                                        } catch (e: Exception) {
                                            errorMessage = e.message ?: "Unknown error rejecting equipment"
                                        } finally {
                                            isLoading = false
                                        }
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
    }
    
    // Success alert
    if (showSuccessAlert) {
        AlertDialog(
            onDismissRequest = { showSuccessAlert = false },
            title = { Text("Success") },
            text = { Text(successMessage) },
            confirmButton = {
                TextButton(onClick = {
                    showSuccessAlert = false
                    // Reload pending equipment
                coroutineScope.launch {
                    isLoading = true
                    
                    try {
                        val service = com.arxos.mobile.service.ArxOSCoreServiceFactory.getInstance(context)
                        val result = service.listPendingEquipment(buildingName)
                        
                        if (result.success) {
                            pendingEquipment = result.items
                        } else {
                            errorMessage = result.error ?: "Failed to load pending equipment"
                        }
                    } catch (e: Exception) {
                        errorMessage = e.message ?: "Unknown error loading pending equipment"
                    } finally {
                        isLoading = false
                    }
                }
                }) {
                    Text("OK")
                }
            }
        )
    }
    
    // Error alert
    errorMessage?.let { error ->
        AlertDialog(
            onDismissRequest = { errorMessage = null },
            title = { Text("Error") },
            text = { Text(error) },
            confirmButton = {
                TextButton(onClick = { errorMessage = null }) {
                    Text("OK")
                }
            }
        )
    }
}

/**
 * Individual pending equipment row
 */
@Composable
private fun PendingEquipmentRow(
    equipment: PendingEquipmentItem,
    onConfirm: () -> Unit,
    onReject: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        text = equipment.name,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    
                    Text(
                        text = equipment.equipmentType,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                // Confidence badge
                Surface(
                    color = confidenceColor(equipment.confidence).copy(alpha = 0.2f),
                    shape = MaterialTheme.shapes.small
                ) {
                    Text(
                        text = "${(equipment.confidence * 100).toInt()}%",
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = confidenceColor(equipment.confidence)
                    )
                }
            }
            
            Divider()
            
            // Metadata
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (equipment.roomName.isNotEmpty()) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Icon(
                            Icons.Default.LocationOn,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = equipment.roomName,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                if (equipment.floorLevel != 0) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        Icon(
                            Icons.Default.Layers,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = "Floor ${equipment.floorLevel}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            // Position info
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    text = "X: ${String.format("%.2f", equipment.position.x)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "Y: ${String.format("%.2f", equipment.position.y)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "Z: ${String.format("%.2f", equipment.position.z)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            Divider()
            
            // Action buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onReject,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Icon(Icons.Default.Close, contentDescription = null)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Reject")
                }
                
                Button(
                    onClick = onConfirm,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                ) {
                    Icon(Icons.Default.Check, contentDescription = null)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Confirm")
                }
            }
        }
    }
}

/**
 * Empty state view when no pending equipment
 */
@Composable
private fun EmptyPendingEquipmentView() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Icon(
                Icons.Default.CheckCircle,
                contentDescription = null,
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Text(
                text = "No Pending Equipment",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            
            Text(
                text = "All pending equipment has been reviewed",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

/**
 * Helper function to get confidence color
 */
private fun confidenceColor(confidence: Double): Color {
    return when {
        confidence >= 0.8 -> Color(0xFF4CAF50) // Green
        confidence >= 0.6 -> Color(0xFFFF9800) // Orange
        else -> Color(0xFFF44336) // Red
    }
}


