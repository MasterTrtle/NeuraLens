package com.example.ollamacameraapp

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Base64
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.example.ollamacameraapp.ui.theme.OllamaCameraAppTheme
import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.delay
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.util.concurrent.Executor
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

private val json = Json { ignoreUnknownKeys = true }

class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            // Permission is granted. Continue the action or workflow in your
            // app.
        } else {
            // Explain to the user that the feature is unavailable because the
            // feature requires a permission that the user has denied. At the
            // same time, respect the user's decision. Don't link to system
            // settings in an effort to convince the user to change their
            // decision.
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.CAMERA
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
        setContent {
            OllamaCameraAppTheme {
                var description by remember { mutableStateOf("...") }
                val client = HttpClient(CIO) {
                    install(ContentNegotiation) {
                        json(Json {
                            prettyPrint = true
                            isLenient = true
                            ignoreUnknownKeys = true
                        })
                    }
                }
                val imageCapture = remember { ImageCapture.Builder().build() }

                Box(modifier = Modifier.fillMaxSize()) {
                    CameraPreview(modifier = Modifier.fillMaxSize(), imageCapture = imageCapture)
                    Text(
                        text = description,
                        modifier = Modifier.align(Alignment.BottomCenter),
                        color = Color.Black,
                        fontSize = 24.sp
                    )
                }

                LaunchedEffect(Unit) {
                    while (true) {
                        try {
                            val file = takePicture(imageCapture)
                            val accessToken = "YOUR_ACCESS_TOKEN" // TODO: Replace with your access token
                            val rawResponse: String = client.post("https://4742556489435054080.europe-west4-205700227746.prediction.vertexai.goog/v1/projects/gemma-hcls25par-723/locations/europe-west4/endpoints/4742556489435054080:predict") {
                                header("Authorization", "Bearer $accessToken")
                                contentType(ContentType.Application.Json)
                                setBody(VertexRequest(
                                    instances = listOf(
                                        Instance(
                                            requestFormat = "chatCompletions",
                                            messages = listOf(
                                                Message(
                                                    role = "user",
                                                    content = listOf(
                                                        Content(
                                                            type = "text",
                                                            text = "Describe the picture in one sentence. example: A person holding a smartphone."
                                                        ),
                                                        Content(
                                                            type = "image_url",
                                                            image_url = ImageUrl(url = "data:image/jpeg;base64," + Base64.encodeToString(file.readBytes(), Base64.NO_WRAP)
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )))
                            }.bodyAsText()
                            Log.d("VertexResponse", rawResponse)
                            // use json with ignoreUnknownKeys to parse the response
                            val response = json.decodeFromString<VertexResponse>(rawResponse)
                            description = response.predictions.choices.firstOrNull()?.message?.content ?: "No description found"
                            file.delete()
                        } catch (e: Exception) {
                            description = e.message ?: "Error"
                        }
                        delay(5000)
                    }
                }
            }
        }
    }

    private suspend fun takePicture(imageCapture: ImageCapture): File {
        return suspendCoroutine { continuation ->
            val file = File.createTempFile("image", ".jpg", cacheDir)
            val outputOptions = ImageCapture.OutputFileOptions.Builder(file).build()
            imageCapture.takePicture(
                outputOptions,
                ContextCompat.getMainExecutor(this),
                object : ImageCapture.OnImageSavedCallback {
                    override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                        continuation.resume(file)
                    }

                    override fun onError(exception: ImageCaptureException) {
                        continuation.resumeWith(Result.failure(exception))
                    }
                }
            )
        }
    }
}


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
data class ContentPart(
    val content: String
)

@Serializable
data class Candidate(
    val message: ContentPart
)

@Serializable
data class Prediction(
    val choices: List<Candidate>
)

@Serializable
data class VertexResponse(
    val predictions: Prediction
)

@Composable
fun CameraPreview(modifier: Modifier, imageCapture: ImageCapture) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val cameraProviderFuture = remember { ProcessCameraProvider.getInstance(context) }

    AndroidView(
        factory = {
            val previewView = PreviewView(it)
            val executor: Executor = ContextCompat.getMainExecutor(it)
            cameraProviderFuture.addListener({
                val cameraProvider = cameraProviderFuture.get()
                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }

                val cameraSelector = CameraSelector.Builder()
                    .requireLensFacing(CameraSelector.LENS_FACING_BACK)
                    .build()

                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    lifecycleOwner,
                    cameraSelector,
                    preview,
                    imageCapture
                )
            }, executor)
            previewView
        },
        modifier = modifier
    )
}
