package com.example.ollamacameraapp.model

import android.util.Base64
import kotlinx.serialization.Serializable

@Serializable
data class TtsResponse(
    val predictions: List<Prediction>
) {
    @Serializable
    data class Prediction(
        val audioContent: String
    )

    fun getAudioContentAsBytes(): ByteArray? {
        return predictions.firstOrNull()?.audioContent?.let {
            Base64.decode(it, Base64.DEFAULT)
        }
    }
}

