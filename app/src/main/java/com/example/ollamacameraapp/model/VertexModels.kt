package com.example.ollamacameraapp.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import android.util.Log

@Serializable
data class ImageUrl(
    val url: String
)

@Serializable
data class Content(
    val type: String,
    val text: String? = null,
    val image_url: ImageUrl? = null
)

@Serializable
data class Message(
    val role: String,
    val content: List<Content>
)

@Serializable
data class Instance(
    @SerialName("@requestFormat")
    val requestFormat: String,
    val messages: List<Message>
)

@Serializable
data class VertexRequest(
    val instances: List<Instance>
)

@Serializable
data class VertexResponse(
    val predictions: JsonArray,
    val deployedModelId: String,
    val model: String,
    val modelDisplayName: String,
    val modelVersionId: String
) {
    fun getContent(): String? {
        return try {
            // The predictions array has the first element as an array of choices
            val firstElement = predictions.firstOrNull() as? JsonArray
            val firstChoice = firstElement?.firstOrNull() as? JsonObject
            val message = firstChoice?.get("message") as? JsonObject
            val content = message?.get("content") as? JsonPrimitive
            content?.content
        } catch (e: Exception) {
            Log.e("VertexResponse", "Error extracting content: ${e.message}")
            null
        }
    }
}

