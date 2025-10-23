package com.arxos.mobile.ui.components

import android.content.Context
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import com.arxos.mobile.data.DetectedEquipment
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Session
import com.google.ar.sceneform.ArSceneView
import com.google.ar.sceneform.Node
import com.google.ar.sceneform.math.Vector3
import com.google.ar.sceneform.rendering.ModelRenderable
import com.google.ar.sceneform.rendering.ShapeFactory
import com.google.ar.sceneform.rendering.MaterialFactory
import com.google.ar.sceneform.rendering.Color
import kotlinx.coroutines.delay

@Composable
fun ARViewContainer(
    modifier: Modifier = Modifier,
    onEquipmentDetected: (DetectedEquipment) -> Unit,
    isScanning: Boolean
) {
    val context = LocalContext.current
    
    AndroidView(
        factory = { context ->
            createARSceneView(context, onEquipmentDetected)
        },
        modifier = modifier.fillMaxSize(),
        update = { arSceneView ->
            if (isScanning) {
                arSceneView.resume()
            } else {
                arSceneView.pause()
            }
        }
    )
}

private fun createARSceneView(
    context: Context,
    onEquipmentDetected: (DetectedEquipment) -> Unit
): ArSceneView {
    val arSceneView = ArSceneView(context)
    
    // Check ARCore availability
    val availability = ArCoreApk.getInstance().checkAvailability(context)
    if (availability.isSupported) {
        try {
            val session = Session(context)
            arSceneView.setupSession(session)
            
            // Configure AR session
            val config = session.config
            config.planeFindingMode = com.google.ar.core.Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
            session.configure(config)
            
            // Start AR session
            arSceneView.resume()
            
            // Simulate equipment detection
            simulateEquipmentDetection(onEquipmentDetected)
            
        } catch (e: Exception) {
            // Handle ARCore setup error
            e.printStackTrace()
        }
    }
    
    return arSceneView
}

private fun simulateEquipmentDetection(
    onEquipmentDetected: (DetectedEquipment) -> Unit
) {
    // This is a simulation - in real implementation, this would use
    // ARCore's plane detection and object recognition
    val simulatedEquipment = listOf(
        DetectedEquipment(
            id = "1",
            name = "VAV-301",
            type = "HVAC",
            position = Vector3(0f, 0f, -1f),
            status = "Detected",
            icon = "fan"
        ),
        DetectedEquipment(
            id = "2",
            name = "Panel-301",
            type = "Electrical",
            position = Vector3(1f, 0f, -1f),
            status = "Detected",
            icon = "bolt"
        )
    )
    
    // Simulate detection delay
    kotlinx.coroutines.GlobalScope.launch {
        delay(2000) // 2 second delay
        simulatedEquipment.forEach { equipment ->
            onEquipmentDetected(equipment)
            delay(1000) // 1 second between detections
        }
    }
}
