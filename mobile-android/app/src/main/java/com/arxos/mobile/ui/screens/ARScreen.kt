package com.arxos.mobile.ui.screens

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ARScreen() {
    var isScanning by remember { mutableStateOf(false) }
    var currentRoom by remember { mutableStateOf("Room 301") }
    var detectedEquipment by remember { mutableStateOf(listOf<DetectedEquipment>()) }
    
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        if (isScanning) {
            // AR Camera View (simulated)
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.Black)
            ) {
                Text(
                    text = "AR Camera View\n(ARCore integration needed)",
                    color = Color.White,
                    modifier = Modifier.align(Alignment.Center)
                )
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
                        Text(
                            text = "Scanning: $currentRoom",
                            color = Color.White,
                            modifier = Modifier.padding(12.dp)
                        )
                    }
                    
                    IconButton(
                        onClick = { isScanning = false },
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
                if (detectedEquipment.isNotEmpty()) {
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
                            items(detectedEquipment) { equipment ->
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
                            val newEquipment = DetectedEquipment(
                                id = "manual_${System.currentTimeMillis()}",
                                name = "Manual Equipment",
                                type = "Manual",
                                status = "Detected"
                            )
                            detectedEquipment = detectedEquipment + newEquipment
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
                        onClick = { isScanning = false }
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
                    value = currentRoom,
                    onValueChange = { currentRoom = it },
                    label = { Text("Room Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                Button(
                    onClick = { isScanning = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.PlayArrow, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Start AR Scan")
                }
                
                // Last Scan Results
                if (detectedEquipment.isNotEmpty()) {
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
                            
                            detectedEquipment.take(3).forEach { equipment ->
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

data class DetectedEquipment(
    val id: String,
    val name: String,
    val type: String,
    val status: String
)

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