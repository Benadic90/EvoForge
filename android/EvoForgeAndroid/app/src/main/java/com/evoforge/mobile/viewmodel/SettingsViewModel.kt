package com.evoforge.mobile.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.evoforge.mobile.core.auth.AuthManager
import kotlinx.coroutines.launch

class SettingsViewModel(private val authManager: AuthManager) : ViewModel() {

    val baseUrl = authManager.baseUrlFlow
    val token = authManager.tokenFlow

    fun updateBaseUrl(url: String) {
        viewModelScope.launch {
            authManager.saveBaseUrl(url)
        }
    }

    fun updateToken(token: String) {
        viewModelScope.launch {
            authManager.saveToken(token)
        }
    }
}
