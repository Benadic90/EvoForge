package com.evoforge.mobile.data.repository

import com.evoforge.mobile.data.api.ApiService
import com.evoforge.mobile.data.model.SystemStatusResponse
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

class EvoForgeRepository(private val apiService: ApiService) {

    fun getSystemStatus(): Flow<Result<SystemStatusResponse>> = flow {
        try {
            val response = apiService.getSystemStatus()
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getWorkers() = flow {
        try {
            val response = apiService.getWorkers()
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getProjects() = flow {
        try {
            val response = apiService.getProjects()
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getProject(projectId: String) = flow {
        try {
            val response = apiService.getProject(projectId)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getProjectHealth(projectId: String) = flow {
        try {
            val response = apiService.getProjectHealth(projectId)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getProjectRoadmap(projectId: String) = flow {
        try {
            val response = apiService.getProjectRoadmap(projectId)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }

    fun getProjectTasks(projectId: String) = flow {
        try {
            val response = apiService.getProjectTasks(projectId)
            if (response.isSuccessful && response.body() != null) {
                emit(Result.success(response.body()!!))
            } else {
                emit(Result.failure(Exception("HTTP ${response.code()}")))
            }
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }
}
