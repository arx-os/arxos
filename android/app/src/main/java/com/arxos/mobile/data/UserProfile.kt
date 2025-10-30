package com.arxos.mobile.data

import android.content.Context
import android.content.SharedPreferences
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

@Serializable
data class UserProfile(
    val name: String,
    val email: String,
    val company: String? = null
) {
    companion object {
        private const val PREFS_NAME = "arxos_prefs"
        private const val KEY_PROFILE = "user_profile"
        
        /**
         * Load user profile from SharedPreferences
         */
        fun load(context: Context): UserProfile? {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val json = prefs.getString(KEY_PROFILE, null)
            return if (json != null) {
                try {
                    Json.decodeFromString<UserProfile>(json)
                } catch (e: Exception) {
                    null
                }
            } else {
                null
            }
        }
        
        /**
         * Save user profile to SharedPreferences
         */
        fun save(context: Context, profile: UserProfile) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val json = Json.encodeToString(profile)
            prefs.edit().putString(KEY_PROFILE, json).apply()
        }
        
        /**
         * Check if onboarding is needed
         */
        fun needsOnboarding(context: Context): Boolean {
            return load(context) == null
        }
        
        /**
         * Clear user profile (for logout/reset)
         */
        fun clear(context: Context) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            prefs.edit().remove(KEY_PROFILE).apply()
        }
    }
}

