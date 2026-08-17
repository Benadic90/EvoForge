package com.evoforge.mobile.data.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class SystemStatusResponse(
    val status: String = "success",
    val timestamp: String = "",
    val system_state: String,
    val active_workflows: Int = 0,
    val failed_workflows: Int = 0,
    val paused_workflows: Int = 0,
    val complete_workflows: Int = 0,
    val workflows: WorkflowSummary = WorkflowSummary(),
    val queued_tasks: Int = 0,
    val workers: WorkerSummary = WorkerSummary(),
    val agents: AgentSummary = AgentSummary(),
    val scheduler: SchedulerSummary = SchedulerSummary(),
    val healthy_executors: Int = 0,
    val unhealthy_executors: Int = 0,
    val version: String = "",
    val compute_mode: String = "HYBRID"
)

@Serializable
data class WorkflowSummary(
    val active: Int = 0,
    val failed: Int = 0,
    val paused: Int = 0,
    val complete: Int = 0
)

@Serializable
data class WorkerSummary(
    val online: Int = 0,
    val total: Int = 0
)

@Serializable
data class AgentSummary(
    val total: Int = 0
)

@Serializable
data class SchedulerSummary(
    val scheduler_id: String? = null,
    val last_tick: String? = null,
    val last_success: String? = null,
    val last_failure: String? = null,
    val next_run: String? = null,
    val status: String = "UNKNOWN",
    val version: String? = null
)

@Serializable
data class ComputePolicy(
    val mode: String,
    val allow_local: Boolean,
    val allow_cloud: Boolean,
    val prefer_local: Boolean,
    val ollama_enabled: Boolean,
    val ollama_status: String? = null
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
    val last_heartbeat_at: String? = null,
    val last_seen_at: String? = null,
    val capabilities: List<String> = emptyList(),
    val health: String = "UNKNOWN",
    val current_workflow_id: String? = null,
    val current_task_id: String? = null
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
data class ProjectAddRequest(
    val repository_full_name: String
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
    val id: Int = 0,
    val event_id: String = "",
    val timestamp: String = "",
    val created_at: String = "",
    val event_type: String,
    val severity: String = "INFO",
    val details: String = "",
    val payload: Map<String, JsonElement> = emptyMap()
)
