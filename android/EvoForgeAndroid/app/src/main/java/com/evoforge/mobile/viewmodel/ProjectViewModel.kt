package com.evoforge.mobile.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.evoforge.mobile.core.auth.AuthManager
import com.evoforge.mobile.data.api.ApiClient
import com.evoforge.mobile.data.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch

class ProjectViewModel(private val authManager: AuthManager) : ViewModel() {

    private val _project = MutableStateFlow<ProjectResponse?>(null)
    val project: StateFlow<ProjectResponse?> = _project.asStateFlow()

    private val _health = MutableStateFlow<ProjectHealthReport?>(null)
    val health: StateFlow<ProjectHealthReport?> = _health.asStateFlow()

    private val _roadmap = MutableStateFlow<ProjectRoadmap?>(null)
    val roadmap: StateFlow<ProjectRoadmap?> = _roadmap.asStateFlow()

    private val _tasks = MutableStateFlow<List<PortfolioTask>>(emptyList())
    val tasks: StateFlow<List<PortfolioTask>> = _tasks.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    fun loadProjectData(projectId: String) {
        _isLoading.value = true
        _error.value = null

        viewModelScope.launch {
            val baseUrl = authManager.baseUrlFlow.firstOrNull()
            val token = authManager.tokenFlow.firstOrNull()
            val apiService = ApiClient.getService(baseUrl, token, false)
            
            if (apiService == null) {
                _error.value = "Invalid API configuration"
                _isLoading.value = false
                return@launch
            }

            try {
                val projResp = apiService.getProject(projectId)
                if (projResp.isSuccessful) _project.value = projResp.body()

                val healthResp = apiService.getProjectHealth(projectId)
                if (healthResp.isSuccessful) _health.value = healthResp.body()

                val roadResp = apiService.getProjectRoadmap(projectId)
                if (roadResp.isSuccessful) _roadmap.value = roadResp.body()

                val tasksResp = apiService.getProjectTasks(projectId)
                if (tasksResp.isSuccessful) _tasks.value = tasksResp.body() ?: emptyList()

            } catch (e: Exception) {
                _error.value = e.localizedMessage ?: "Failed to load project details"
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    class Factory(private val authManager: AuthManager) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(ProjectViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return ProjectViewModel(authManager) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
