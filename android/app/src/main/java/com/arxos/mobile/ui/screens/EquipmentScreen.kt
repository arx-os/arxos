package com.arxos.mobile.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.arxos.mobile.data.Equipment
import com.arxos.mobile.data.EquipmentFilter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EquipmentScreen() {
    var searchText by remember { mutableStateOf("") }
    var selectedFilter by remember { mutableStateOf(EquipmentFilter.ALL) }
    var isLoading by remember { mutableStateOf(false) }
    
    val equipment = remember {
        listOf(
            Equipment("1", "VAV-301", "HVAC", "Active", "Room 301", "2024-01-15"),
            Equipment("2", "Panel-301", "Electrical", "Active", "Room 301", "2024-01-10"),
            Equipment("3", "Sink-301", "Plumbing", "Maintenance", "Room 301", "2024-01-20"),
            Equipment("4", "Fire Alarm-301", "Safety", "Active", "Room 301", "2024-01-05")
        )
    }
    
    val filteredEquipment = equipment.filter { equipment ->
        if (searchText.isNotEmpty()) {
            equipment.name.contains(searchText, ignoreCase = true)
        } else true
    }.filter { equipment ->
        if (selectedFilter != EquipmentFilter.ALL) {
            equipment.type.equals(selectedFilter.displayName, ignoreCase = true)
        } else true
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Search Bar
        OutlinedTextField(
            value = searchText,
            onValueChange = { searchText = it },
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Search equipment...") },
            leadingIcon = {
                Icon(Icons.Default.Search, contentDescription = "Search")
            },
            trailingIcon = {
                if (searchText.isNotEmpty()) {
                    IconButton(onClick = { searchText = "" }) {
                        Icon(Icons.Default.Clear, contentDescription = "Clear")
                    }
                }
            }
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Filter Chips
        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(EquipmentFilter.values()) { filter ->
                FilterChip(
                    onClick = { selectedFilter = filter },
                    label = { Text(filter.displayName) },
                    selected = selectedFilter == filter,
                    leadingIcon = {
                        Icon(
                            getEquipmentIcon(filter.displayName),
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Equipment List
        if (isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Loading equipment...")
                }
            }
        } else if (filteredEquipment.isEmpty()) {
            EmptyStateView()
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filteredEquipment) { equipment ->
                    EquipmentCard(equipment = equipment)
                }
            }
        }
    }
}

@Composable
fun EquipmentCard(
    equipment: Equipment,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Equipment Icon
            Icon(
                imageVector = getEquipmentIcon(equipment.type),
                contentDescription = equipment.type,
                modifier = Modifier.size(32.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Equipment Info
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = equipment.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                
                Text(
                    text = equipment.location,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            // Status Badge
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = getStatusColor(equipment.status).copy(alpha = 0.2f)
                )
            ) {
                Text(
                    text = equipment.status,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = getStatusColor(equipment.status)
                )
            }
        }
    }
}

@Composable
fun EmptyStateView() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                Icons.Default.List,
                contentDescription = "No Equipment",
                modifier = Modifier.size(64.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = "No Equipment Found",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = "Start scanning rooms to detect equipment",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

fun getEquipmentIcon(type: String): ImageVector {
    return when (type.lowercase()) {
        "hvac" -> Icons.Default.Air
        "electrical" -> Icons.Default.Bolt
        "plumbing" -> Icons.Default.WaterDrop
        "safety" -> Icons.Default.Security
        else -> Icons.Default.Settings
    }
}

fun getStatusColor(status: String): Color {
    return when (status.lowercase()) {
        "active" -> Color.Green
        "maintenance" -> android.graphics.Color.rgb(255, 165, 0).let { Color(it) } // Orange
        "inactive" -> Color.Red
        else -> Color.Gray
    }
}
