package com.arxos.mobile.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Terminal
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.arxos.mobile.ui.screens.ARScreen
import com.arxos.mobile.ui.screens.EquipmentScreen
import com.arxos.mobile.ui.screens.TerminalScreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArxOSApp() {
    val navController = rememberNavController()
    
    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentDestination = navBackStackEntry?.destination
                
                listOf(
                    NavigationItem("terminal", Icons.Default.Terminal, "Terminal"),
                    NavigationItem("ar", Icons.Default.CameraAlt, "AR Scan"),
                    NavigationItem("equipment", Icons.Default.List, "Equipment")
                ).forEach { item ->
                    NavigationBarItem(
                        icon = { Icon(item.icon, contentDescription = item.title) },
                        label = { Text(item.title) },
                        selected = currentDestination?.hierarchy?.any { it.route == item.route } == true,
                        onClick = {
                            navController.navigate(item.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = "terminal",
            modifier = Modifier.padding(innerPadding)
        ) {
            composable("terminal") {
                TerminalScreen()
            }
            composable("ar") {
                ARScreen()
            }
            composable("equipment") {
                EquipmentScreen()
            }
        }
    }
}

data class NavigationItem(
    val route: String,
    val icon: ImageVector,
    val title: String
)