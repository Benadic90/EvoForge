package com.evoforge.mobile.data.model

import kotlinx.serialization.Serializable

@Serializable
data class SystemStatusResponse(
    val system_state: String,
    val active_workflows: Int = 0,
    val failed_workflows: Int = 0,
    val paused_workflows: Int = 0,
    val complete_workflows: Int = 0,
    val healthy_executors: Int = 0,
    val unhealthy_executors: Int = 0,
    val version: String = "",
    val compute_mode: String? = null
)

@Serializable
data class ComputePolicy(
    val mode: String,
    val allow_local: Boolean,
    val allow_cloud: Boolean,
    val prefer_local: Boolean,
    val ollama_enabled: Boolean
)

@Serializable
data class ComputePolicyUpdate(
    val mode: String
)

@Serializable
data class WorkerResponse(
    val worker_id: String,
    val worker_type: String,
    val status: String,
    val last_heartbeat: String,
    val capabilities: List<String>
)

@Serializable
data class ProjectResponse(
    val project_id: String,
    val repository_full_name: String,
    val name: String,
    val status: String,
    val health: String,
    val health_trend: String,
    val priority_score: Double = 0.0
)

@Serializable
data class GitHubTokenUpdate(
    val token: String
)

@Serializable
data class GitHubStatusResponse(
    val configured: Boolean,
    val username: String? = null
)

@Serializable
data class LLMKeyUpdate(
    val provider: String,
    val api_key: String
)

@Serializable
data class LLMKeyStatusResponse(
    val gemini_configured: Boolean,
    val nvidia_configured: Boolean
)

@Serializable
data class EventResponse(
    val event_id: String,
    val timestamp: String,
    val event_type: String,
    val severity: String,
    val details: String
)
