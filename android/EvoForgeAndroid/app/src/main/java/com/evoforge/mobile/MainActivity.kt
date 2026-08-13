package com.evoforge.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.evoforge.mobile.core.auth.AuthManager
import com.evoforge.mobile.ui.navigation.EvoForgeNavGraph
import com.evoforge.mobile.ui.theme.EvoForgeTheme
import com.evoforge.mobile.viewmodel.SystemViewModel

class MainActivity : ComponentActivity() {

    private lateinit var authManager: AuthManager

    private val systemViewModel: SystemViewModel by viewModels {
        SystemViewModel.Factory(authManager)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        authManager = AuthManager(applicationContext)

        setContent {
            EvoForgeTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    EvoForgeNavGraph(systemViewModel, authManager)
                }
            }
        }
    }
}
