package com.evoforge.mobile.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.evoforge.mobile.core.auth.AuthManager
import com.evoforge.mobile.data.api.ApiClient
import com.evoforge.mobile.data.api.ApiService
import com.evoforge.mobile.data.model.ComputePolicy
import com.evoforge.mobile.data.model.ComputePolicyUpdate
import com.evoforge.mobile.data.model.SystemStatusResponse
import com.evoforge.mobile.data.model.ProjectResponse
import com.evoforge.mobile.data.model.GitHubStatusResponse
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

sealed class ConnectionState {
    object NotConfigured : ConnectionState()
    object Connecting : ConnectionState()
    object Online : ConnectionState()
    data class Offline(val reason: String) : ConnectionState()
}

class SystemViewModel(private val authManager: AuthManager) : ViewModel() {

    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.NotConfigured)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _systemStatus = MutableStateFlow<SystemStatusResponse?>(null)
    val systemStatus: StateFlow<SystemStatusResponse?> = _systemStatus.asStateFlow()

    private val _computePolicy = MutableStateFlow<ComputePolicy?>(null)
    val computePolicy: StateFlow<ComputePolicy?> = _computePolicy.asStateFlow()

    private val _projects = MutableStateFlow<List<ProjectResponse>>(emptyList())
    val projects: StateFlow<List<ProjectResponse>> = _projects.asStateFlow()

    private val _githubStatus = MutableStateFlow<GitHubStatusResponse?>(null)
    val githubStatus: StateFlow<GitHubStatusResponse?> = _githubStatus.asStateFlow()

    private var apiService: ApiService? = null

    init {
        // Initially try to connect if we already have a URL
        viewModelScope.launch {
            if (!authManager.baseUrlFlow.firstOrNull().isNullOrBlank()) {
                connect(false)
            }
        }
        startPolling()
    }

    fun connect(forceRebuild: Boolean = true) {
        viewModelScope.launch {
            _connectionState.value = ConnectionState.Connecting
            
            val baseUrl = authManager.baseUrlFlow.firstOrNull()
            val token = authManager.tokenFlow.firstOrNull()
            
            apiService = ApiClient.getService(baseUrl, token, forceRebuild)

            if (apiService == null) {
                _connectionState.value = ConnectionState.Offline("Invalid Control Plane URL")
                return@launch
            }

            try {
                val response = apiService!!.getSystemStatus()
                if (response.isSuccessful) {
                    _systemStatus.value = response.body()
                    _connectionState.value = ConnectionState.Online
                    fetchComputePolicy()
                    fetchGitHubStatus()
                    fetchProjects()
                } else {
                    _connectionState.value = ConnectionState.Offline("HTTP ${response.code()}: ${response.message()}")
                }
            } catch (e: Exception) {
                _connectionState.value = ConnectionState.Offline(e.localizedMessage ?: "Connection Refused")
            }
        }
    }

    fun updateComputeMode(mode: String) {
        // Optimistic UI Update
        val currentPolicy = _computePolicy.value
        if (currentPolicy != null) {
            _computePolicy.value = currentPolicy.copy(mode = mode)
        } else {
            _computePolicy.value = ComputePolicy(mode = mode, allow_local = true, allow_cloud = true, prefer_local = false, ollama_enabled = true)
        }

        viewModelScope.launch {
            apiService?.let { api ->
                try {
                    val update = ComputePolicyUpdate(mode)
                    val response = api.updateComputePolicy(update)
                    if (response.isSuccessful) {
                        _computePolicy.value = response.body()
                        // Refresh status to ensure compute mode is up to date
                        fetchStatus()
                    } else {
                        // Revert on failure
                        _computePolicy.value = currentPolicy
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                    // Revert on failure
                    _computePolicy.value = currentPolicy
                }
            }
        }
    }

    private suspend fun fetchComputePolicy() {
        apiService?.let { api ->
            try {
                val response = api.getComputePolicy()
                if (response.isSuccessful) {
                    _computePolicy.value = response.body()
                }
            } catch (e: Exception) {
                // Ignore for polling
            }
        }
    }

    private suspend fun fetchStatus() {
        apiService?.let { api ->
            try {
                val response = api.getSystemStatus()
                if (response.isSuccessful) {
                    _systemStatus.value = response.body()
                    if (_connectionState.value !is ConnectionState.Online) {
                        _connectionState.value = ConnectionState.Online
                    }
                } else {
                    if (_connectionState.value is ConnectionState.Online) {
                        _connectionState.value = ConnectionState.Offline("HTTP ${response.code()}")
                    }
                }
            } catch (e: Exception) {
                if (_connectionState.value is ConnectionState.Online) {
                    _connectionState.value = ConnectionState.Offline("Connection Lost")
                }
            }
        }
    }

    private suspend fun fetchGitHubStatus() {
        apiService?.let { api ->
            try {
                val response = api.getGitHubStatus()
                if (response.isSuccessful) {
                    _githubStatus.value = response.body()
                }
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    private suspend fun fetchProjects() {
        apiService?.let { api ->
            try {
                val response = api.getProjects()
                if (response.isSuccessful) {
                    _projects.value = response.body() ?: emptyList()
                }
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    fun updateGitHubToken(token: String) {
        viewModelScope.launch {
            apiService?.let { api ->
                try {
                    val update = com.evoforge.mobile.data.model.GitHubTokenUpdate(token)
                    val response = api.updateGitHubToken(update)
                    if (response.isSuccessful) {
                        fetchGitHubStatus()
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }

    private fun startPolling() {
        viewModelScope.launch {
            while (isActive) {
                if (_connectionState.value is ConnectionState.Online || _connectionState.value is ConnectionState.Offline) {
                    fetchStatus()
                    fetchComputePolicy()
                    fetchGitHubStatus()
                    fetchProjects()
                }
                delay(5000) // Poll every 5s
            }
        }
    }

    class Factory(private val authManager: AuthManager) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(SystemViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return SystemViewModel(authManager) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
