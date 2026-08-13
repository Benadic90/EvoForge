package com.evoforge.mobile.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.evoforge.mobile.data.model.SystemStatusResponse
import com.evoforge.mobile.data.model.WorkerResponse
import com.evoforge.mobile.data.repository.EvoForgeRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

sealed class UiState<out T> {
    object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
    object Offline : UiState<Nothing>()
}

class SystemViewModel(private val repository: EvoForgeRepository) : ViewModel() {

    private val _systemStatus = MutableStateFlow<UiState<SystemStatusResponse>>(UiState.Loading)
    val systemStatus: StateFlow<UiState<SystemStatusResponse>> = _systemStatus.asStateFlow()

    private val _workers = MutableStateFlow<UiState<List<WorkerResponse>>>(UiState.Loading)
    val workers: StateFlow<UiState<List<WorkerResponse>>> = _workers.asStateFlow()

    init {
        startPolling()
    }

    private fun startPolling() {
        viewModelScope.launch {
            while (isActive) {
                fetchStatus()
                fetchWorkers()
                delay(5000) // Poll every 5s
            }
        }
    }

    private suspend fun fetchStatus() {
        repository.getSystemStatus().collect { result ->
            if (result.isSuccess) {
                _systemStatus.value = UiState.Success(result.getOrNull()!!)
            } else {
                val err = result.exceptionOrNull()
                _systemStatus.value = UiState.Error(err?.message ?: "Unknown Error")
            }
        }
    }

    private suspend fun fetchWorkers() {
        repository.getWorkers().collect { result ->
            if (result.isSuccess) {
                _workers.value = UiState.Success(result.getOrNull()!!)
            } else {
                _workers.value = UiState.Error("Failed to fetch workers")
            }
        }
    }
}
