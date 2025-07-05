package com.example.ollamacameraapp.utils

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.provider.MediaStore
import android.util.Log
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.core.content.ContextCompat
import com.example.ollamacameraapp.data.DescriptionRepository
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Locale
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

suspend fun takePictureForLLM(imageCapture: ImageCapture, context: Context): File {
    return suspendCoroutine { continuation ->
        val file = File.createTempFile("image", ".jpg", context.cacheDir)
        val outputOptions = ImageCapture.OutputFileOptions.Builder(file).build()
        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(context),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                    val compressedFile = compressImage(file, context)
                    file.delete()
                    continuation.resume(compressedFile)
                }

                override fun onError(exception: ImageCaptureException) {
                    continuation.resumeWith(Result.failure(exception))
                }
            }
        )
    }
}

suspend fun takePictureAndSave(imageCapture: ImageCapture, context: Context, description: String?) {
    val name = SimpleDateFormat("yyyy-MM-dd-HH-mm-ss-SSS", Locale.US)
        .format(System.currentTimeMillis())
    val contentValues = ContentValues().apply {
        put(MediaStore.MediaColumns.DISPLAY_NAME, name)
        put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.P) {
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/OllamaCameraApp")
        }
    }

    val outputOptions = ImageCapture.OutputFileOptions
        .Builder(
            context.contentResolver,
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            contentValues
        )
        .build()

    imageCapture.takePicture(
        outputOptions,
        ContextCompat.getMainExecutor(context),
        object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                Log.d("Camera", "Image saved to ${outputFileResults.savedUri}")
                outputFileResults.savedUri?.let { uri ->
                    if (description != null) {
                        val repository = DescriptionRepository(context)
                        repository.saveDescription(uri, description)
                        Log.d("Camera", "Description saved for $uri")
                    }
                }
            }

            override fun onError(exception: ImageCaptureException) {
                Log.e("Camera", "Image capture failed", exception)
            }
        }
    )
}

private fun compressImage(originalFile: File, context: Context): File {
    val originalBitmap = BitmapFactory.decodeFile(originalFile.absolutePath)

    val maxDimension = 800
    val originalWidth = originalBitmap.width
    val originalHeight = originalBitmap.height

    val aspectRatio = originalWidth.toFloat() / originalHeight.toFloat()
    val newWidth: Int
    val newHeight: Int

    if (originalWidth > originalHeight) {
        newWidth = maxDimension
        newHeight = (maxDimension / aspectRatio).toInt()
    } else {
        newHeight = maxDimension
        newWidth = (maxDimension * aspectRatio).toInt()
    }

    val resizedBitmap = Bitmap.createScaledBitmap(originalBitmap, newWidth, newHeight, true)

    val compressedFile = File.createTempFile("compressed_image", ".jpg", context.cacheDir)
    val outputStream = FileOutputStream(compressedFile)

    resizedBitmap.compress(Bitmap.CompressFormat.JPEG, 75, outputStream)
    outputStream.close()

    originalBitmap.recycle()
    resizedBitmap.recycle()

    return compressedFile
}
