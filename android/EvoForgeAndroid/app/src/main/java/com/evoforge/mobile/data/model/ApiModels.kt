package com.evoforge.mobile.data.model

import kotlinx.serialization.Serializable

@Serializable
data class SystemStatusResponse(
    val status: String,
    val timestamp: String,
    val compute_mode: String
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
    val status: String,
    val priority: String,
    val confidence_score: Double
)

@Serializable
data class EventResponse(
    val event_id: String,
    val timestamp: String,
    val event_type: String,
    val severity: String,
    val details: String
)
