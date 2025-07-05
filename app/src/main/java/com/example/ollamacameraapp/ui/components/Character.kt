package com.example.ollamacameraapp.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.ImageLoader
import coil.compose.rememberAsyncImagePainter
import coil.decode.SvgDecoder

@Composable
fun SpeechBubble(
    text: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val imageLoader = ImageLoader.Builder(context)
        .components {
            add(SvgDecoder.Factory())
        }
        .build()

    Row(
        modifier = modifier.padding(16.dp),
        verticalAlignment = Alignment.Bottom
    ) {
        Spacer(modifier = Modifier.width(80.dp))

        // Speech bubble
        Card(
            modifier = Modifier
                .background(Color.Transparent),
            colors = CardDefaults.cardColors(
                containerColor = Color.White.copy(alpha = 0.95f)
            ),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp)
            ) {
                // Speech bubble tail (pointing to character)
                Box(
                    modifier = Modifier
                        .size(0.dp) // Triangle pointer - we'll use a simple approach
                )

                Text(
                    text = text,
                    color = Color.Black,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(8.dp)
                )
            }
        }
    }
}

@Composable
fun CharacterIcon(
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val imageLoader = ImageLoader.Builder(context)
        .components {
            add(SvgDecoder.Factory())
        }
        .build()

    Box(
        modifier = modifier
            .padding(start = 4.dp, bottom = 16.dp)
    ) {
        Image(
            painter = rememberAsyncImagePainter("file:///android_asset/mikey.svg", imageLoader),
            contentDescription = "Character",
            modifier = modifier
                .size(80.dp)
        )
    }

}

