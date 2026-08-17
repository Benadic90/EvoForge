package com.evoforge.mobile.data.api

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object ApiClient {
    private var retrofit: Retrofit? = null
    private var currentBaseUrl: String? = null
    
    // Shared JSON instance for all APIs
    private val json = Json { 
        ignoreUnknownKeys = true 
        isLenient = true
        coerceInputValues = true
    }

    fun getService(baseUrl: String?, token: String?, forceRebuild: Boolean = false): ApiService? {
        
        val safeBaseUrl = normalizeBaseUrl(baseUrl) ?: return null

        if (retrofit == null || currentBaseUrl != safeBaseUrl || forceRebuild) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val authInterceptor = Interceptor { chain ->
                val requestBuilder = chain.request().newBuilder()
                if (!token.isNullOrBlank()) {
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
                chain.proceed(requestBuilder.build())
            }

            val client = OkHttpClient.Builder()
                .addInterceptor(authInterceptor)
                .addInterceptor(loggingInterceptor)
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build()

            val contentType = "application/json".toMediaType()

            try {
                retrofit = Retrofit.Builder()
                    .baseUrl(safeBaseUrl)
                    .client(client)
                    .addConverterFactory(json.asConverterFactory(contentType))
                    .build()
                currentBaseUrl = safeBaseUrl
            } catch (e: Exception) {
                e.printStackTrace()
                return null
            }
        }

        return retrofit?.create(ApiService::class.java)
    }

    private fun normalizeBaseUrl(baseUrl: String?): String? {
        var normalized = baseUrl?.trim().orEmpty()
        if (normalized.isBlank()) return null

        if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
            normalized = "https://$normalized"
        }

        normalized = normalized.trimEnd('/')
        if (normalized.contains("/api/")) {
            normalized = normalized.substringBefore("/api/")
        }
        if (normalized.endsWith("/api")) {
            normalized = normalized.removeSuffix("/api")
        }

        return "$normalized/"
    }
}
