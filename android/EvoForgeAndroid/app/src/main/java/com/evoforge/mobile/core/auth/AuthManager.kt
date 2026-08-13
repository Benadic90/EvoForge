package com.evoforge.mobile.core.auth

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "settings")

class AuthManager(private val context: Context) {
    companion object {
        val BASE_URL_KEY = stringPreferencesKey("base_url")
        val TOKEN_KEY = stringPreferencesKey("auth_token")
    }

    val baseUrlFlow: Flow<String?> = context.dataStore.data.map { it[BASE_URL_KEY] }
    val tokenFlow: Flow<String?> = context.dataStore.data.map { it[TOKEN_KEY] }

    suspend fun saveBaseUrl(url: String) {
        context.dataStore.edit { prefs ->
            prefs[BASE_URL_KEY] = url
        }
    }

    suspend fun saveToken(token: String) {
        context.dataStore.edit { prefs ->
            prefs[TOKEN_KEY] = token
        }
    }
}
