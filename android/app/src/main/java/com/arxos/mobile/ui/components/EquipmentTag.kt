package com.arxos.mobile.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.arxos.mobile.data.DetectedEquipment

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
                imageVector = getEquipmentIcon(equipment.type),
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

@Composable
fun EquipmentStatusBadge(
    status: String,
    modifier: Modifier = Modifier
) {
    val backgroundColor = when (status.lowercase()) {
        "detected" -> Color.Green.copy(alpha = 0.2f)
        "tagged" -> Color.Blue.copy(alpha = 0.2f)
        "saved" -> Color.Purple.copy(alpha = 0.2f)
        else -> Color.Gray.copy(alpha = 0.2f)
    }
    
    val textColor = when (status.lowercase()) {
        "detected" -> Color.Green
        "tagged" -> Color.Blue
        "saved" -> Color.Purple
        else -> Color.Gray
    }
    
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = backgroundColor),
        shape = RoundedCornerShape(8.dp)
    ) {
        Text(
            text = status,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            color = textColor,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Medium
        )
    }
}

private fun getEquipmentIcon(type: String): ImageVector {
    return when (type.lowercase()) {
        "hvac" -> Icons.Default.Air
        "electrical" -> Icons.Default.Bolt
        "plumbing" -> Icons.Default.WaterDrop
        "safety" -> Icons.Default.Security
        "manual" -> Icons.Default.Build
        else -> Icons.Default.Settings
    }
}
