package com.arxos.mobile.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Equipment placement dialog for tap-to-place functionality
 * Equivalent to iOS EquipmentPlacementDialog
 */
@Composable
fun EquipmentPlacementDialog(
    equipmentName: String,
    onEquipmentNameChange: (String) -> Unit,
    equipmentType: String,
    onEquipmentTypeChange: (String) -> Unit,
    onSave: () -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    val equipmentTypes = listOf(
        "Unknown",
        "HVAC",
        "Electrical",
        "Plumbing",
        "Lighting",
        "Safety",
        "Other"
    )
    
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Place Equipment",
                    style = MaterialTheme.typography.headlineSmall
                )
                IconButton(onClick = { onCancel.invoke() }) {
                    Icon(Icons.Default.Close, contentDescription = "Close")
                }
            }
            
            Divider()
            
            // Equipment name input
            OutlinedTextField(
                value = equipmentName,
                onValueChange = onEquipmentNameChange,
                label = { Text("Equipment Name") },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Enter equipment name") }
            )
            
            // Equipment type selector
            var expanded by remember { mutableStateOf(false) }
            
            ExposedDropdownMenuBox(
                expanded = expanded,
                onExpandedChange = { expanded = !expanded }
            ) {
                OutlinedTextField(
                    value = equipmentType,
                    onValueChange = { },
                    readOnly = true,
                    label = { Text("Equipment Type") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor(),
                    trailingIcon = {
                        ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                    }
                )
                
                ExposedDropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    equipmentTypes.forEach { type ->
                        DropdownMenuItem(
                            text = { Text(type) },
                            onClick = {
                                onEquipmentTypeChange(type)
                                expanded = false
                            }
                        )
                    }
                }
            }
            
            Divider()
            
            // Action buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = { onCancel.invoke() },
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Cancel")
                }
                
                Button(
                    onClick = onSave,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Place")
                }
            }
        }
    }
}

