package com.example.ollamacameraapp

import android.app.Application
import android.content.ContentUris
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.ollamacameraapp.data.DescriptionRepository
import com.example.ollamacameraapp.data.ImageWithDescription
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val _images = MutableStateFlow<List<ImageWithDescription>>(emptyList())
    val images = _images.asStateFlow()
    private val repository = DescriptionRepository(application)

    init {
        loadImages()
    }

    fun loadImages() {
        viewModelScope.launch {
            val imageList = mutableListOf<ImageWithDescription>()
            val projection = arrayOf(
                MediaStore.Images.Media._ID
            )
            val selection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                MediaStore.Images.Media.RELATIVE_PATH + " LIKE ?"
            } else {
                MediaStore.Images.Media.DATA + " LIKE ?"
            }
            val selectionArgs = arrayOf("%OllamaCameraApp%")

            val sortOrder = "${MediaStore.Images.Media.DATE_ADDED} DESC"

            getApplication<Application>().contentResolver.query(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                projection,
                selection,
                selectionArgs,
                sortOrder
            )?.use { cursor ->
                val idColumn = cursor.getColumnIndexOrThrow(MediaStore.Images.Media._ID)

                while (cursor.moveToNext()) {
                    val id = cursor.getLong(idColumn)
                    val contentUri = ContentUris.withAppendedId(
                        MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                        id
                    )
                    val description = repository.getDescription(contentUri)
                    imageList.add(ImageWithDescription(contentUri, description))
                }
            }
            _images.value = imageList
        }
    }
}
