package com.evoforge.mobile.data.api

import com.evoforge.mobile.data.model.*
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    @GET("api/status")
    suspend fun getSystemStatus(): Response<SystemStatusResponse>

    @GET("api/settings/compute")
    suspend fun getComputePolicy(): Response<ComputePolicy>

    @PUT("api/settings/compute")
    suspend fun updateComputePolicy(@Body update: ComputePolicyUpdate): Response<ComputePolicy>

    @GET("api/workers")
    suspend fun getWorkers(): Response<List<WorkerResponse>>

    @POST("api/workers/{workerId}/drain")
    suspend fun drainWorker(@Path("workerId") workerId: String): Response<Unit>

    @GET("api/projects")
    suspend fun getProjects(): Response<List<ProjectResponse>>

    @GET("api/projects/{projectId}")
    suspend fun getProject(@Path("projectId") projectId: String): Response<ProjectResponse>

    @PUT("api/github/token")
    suspend fun updateGitHubToken(@Body update: GitHubTokenUpdate): Response<Unit>

    @GET("api/github/status")
    suspend fun getGitHubStatus(): Response<GitHubStatusResponse>

    @GET("api/events/recent")
    suspend fun getRecentEvents(@Query("limit") limit: Int = 20): Response<List<EventResponse>>

    @PUT("api/llm/keys")
    suspend fun updateLLMKey(@Body update: LLMKeyUpdate): Response<Unit>

    @GET("api/llm/keys/status")
    suspend fun getLLMKeyStatus(): Response<LLMKeyStatusResponse>
}
