package com.evoforge.mobile.data.api

import com.evoforge.mobile.data.model.EventResponse
import com.evoforge.mobile.data.model.ProjectResponse
import com.evoforge.mobile.data.model.SystemStatusResponse
import com.evoforge.mobile.data.model.WorkerResponse
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    @GET("api/status")
    suspend fun getSystemStatus(): Response<SystemStatusResponse>

    @GET("api/workers")
    suspend fun getWorkers(): Response<List<WorkerResponse>>

    @POST("api/workers/{workerId}/drain")
    suspend fun drainWorker(@Path("workerId") workerId: String): Response<Unit>

    @GET("api/projects")
    suspend fun getProjects(): Response<List<ProjectResponse>>

    @GET("api/events/recent")
    suspend fun getRecentEvents(@Query("limit") limit: Int = 20): Response<List<EventResponse>>
}
