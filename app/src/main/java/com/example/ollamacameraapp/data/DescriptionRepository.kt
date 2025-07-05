package com.example.ollamacameraapp.data

import android.content.Context
import android.net.Uri

class DescriptionRepository(context: Context) {
    private val sharedPreferences = context.getSharedPreferences("image_descriptions", Context.MODE_PRIVATE)

    fun saveDescription(uri: Uri, description: String) {
        sharedPreferences.edit().putString(uri.toString(), description).apply()
    }

    fun getDescription(uri: Uri): String? {
        return sharedPreferences.getString(uri.toString(), null)
    }
}

