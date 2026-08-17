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

@Serializable
data class PortfolioEvidence(
    val evidence_id: String = "",
    val project_id: String = "",
    val task_id: String? = null,
    val source: String = "",
    val source_type: String = "",
    val source_id: String? = null,
    val source_url: String? = null,
    val observation: String = "",
    val severity: String = "UNKNOWN",
    val timestamp: String = "",
    val expires_at: String? = null,
    val confidence: Double = 1.0,
    val metadata: Map<String, JsonElement> = emptyMap()
)

@Serializable
data class ProjectHealthReport(
    val project_id: String = "",
    val overall_health: String = "UNKNOWN",
    val security_health: Double? = null,
    val test_health: Double? = null,
    val documentation_health: Double? = null,
    val maintenance_health: Double? = null,
    val activity_health: Double? = null,
    val technical_debt: Double? = null,
    val ci_health: Double? = null,
    val roadmap_health: Double? = null,
    val evidence: List<PortfolioEvidence> = emptyList(),
    val warnings: List<String> = emptyList(),
    val unknown_fields: List<String> = emptyList(),
    val timestamp: String = ""
)

@Serializable
data class Milestone(
    val milestone_id: String = "",
    val title: String = "",
    val description: String = "",
    val priority: String = "",
    val status: String = "",
    val dependencies: List<String> = emptyList(),
    val evidence: List<String> = emptyList(),
    val target_date: String? = null
)

@Serializable
data class ProjectRoadmap(
    val roadmap_id: String = "",
    val project_id: String = "",
    val version: String = "",
    val vision: String = "",
    val milestones: List<Milestone> = emptyList(),
    val objectives: List<String> = emptyList(),
    val dependencies: List<String> = emptyList(),
    val status: String = "",
    val created_at: String = "",
    val updated_at: String = ""
)

@Serializable
data class PortfolioTask(
    val task_id: String = "",
    val canonical_task_id: String? = null,
    val project_id: String = "",
    val repository_full_name: String? = null,
    val title: String = "",
    val description: String = "",
    val source: String = "",
    val source_type: String = "unknown",
    val source_id: String = "",
    val source_url: String? = null,
    val priority: Double = 0.0,
    val confidence: Double = 1.0,
    val risk: String = "LOW",
    val estimated_minutes: Int? = null,
    val dependencies: List<String> = emptyList(),
    val required_capabilities: List<String> = emptyList(),
    val status: String = "DISCOVERED",
    val created_at: String = "",
    val updated_at: String = "",
    val metadata: Map<String, JsonElement> = emptyMap()
)
