package com.example.ollamacameraapp.model

import kotlinx.serialization.Serializable

@Serializable
data class TtsRequest(
    val instances: List<TtsInstance>
)

