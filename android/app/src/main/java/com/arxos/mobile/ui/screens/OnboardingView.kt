package com.arxos.mobile.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.arxos.mobile.data.UserProfile
import com.arxos.mobile.service.ArxOSCoreJNI

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OnboardingScreen(
    onComplete: () -> Unit
) {
    val context = LocalContext.current
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var company by remember { mutableStateOf("") }
    var showingError by remember { mutableStateOf(false) }
    
    val isFormValid = name.trim().isNotEmpty() && 
                      email.trim().isNotEmpty() && 
                      email.contains("@")
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        Spacer(modifier = Modifier.height(40.dp))
        
        // Welcome Icon
        Icon(
            imageVector = Icons.Default.CheckCircle,
            contentDescription = "Welcome",
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        // Title
        Text(
            text = "Welcome to ArxOS",
            style = MaterialTheme.typography.headlineMedium
        )
        
        Text(
            text = "Let's get you set up",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Form
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Your Name") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Your Email") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email)
            )
            
            OutlinedTextField(
                value = company,
                onValueChange = { company = it },
                label = { Text("Company (Optional)") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
        }
        
        if (showingError) {
            Text(
                text = "Please enter a valid name and email",
                color = MaterialTheme.colorScheme.error
            )
        }
        
        Spacer(modifier = Modifier.weight(1f))
        
        // Continue Button
        Button(
            onClick = {
                if (isFormValid) {
                    // Save profile
                    val profile = UserProfile(
                        name = name.trim(),
                        email = email.trim(),
                        company = company.trim().takeIf { it.isNotEmpty() }
                    )
                    UserProfile.save(context, profile)
                    
                    // Configure Git credentials (simulation for now)
                    Toast.makeText(
                        context,
                        "Setup complete: ${profile.name}",
                        Toast.LENGTH_SHORT
                    ).show()
                    
                    onComplete()
                } else {
                    showingError = true
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = isFormValid
        ) {
            Text("Continue")
        }
    }
}

