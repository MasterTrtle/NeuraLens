# NeuraLens

# Setup

create a .env with HF_TOKEN

```bash
conda create -n medgemma python=3.10.17
pip install -r requirements.txt
```

# TO DO
fix the batch training (currently only work with batch_size=1)
refractor the notebook fine tuning code in multiples files (eg training.py, ...)
add evaluate function
change the training to also predict the other labels ()


## Building and Debugging

This project uses Gradle for building. You can use Android Studio or the command line to build and debug the app.

### Prerequisites

- Java Development Kit (JDK) 17 or higher
- Android Studio (latest version recommended) or Android SDK command-line tools

### Building the APK

To build the debug APK from the command line, run the following command in the root directory of the project:

```bash
./gradlew assembleDebug
```

The generated APK will be located in `app/build/outputs/apk/debug/app-debug.apk`.

### Installing the APK

To install the APK on a connected Android device or emulator, use the Android Debug Bridge (adb):

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Debugging

You can view the application logs for debugging purposes using `adb logcat`:

```bash
adb logcat
```

To filter the logs for this specific application, you can use a command like this:

```bash
adb logcat com.example.ollamacameraapp:V *:S
```

## Configuration

Before running the application, you need to add your Vertex AI access token in `app/src/main/java/com/example/ollamacameraapp/MainActivity.kt`.

Replace `"YOUR_ACCESS_TOKEN"` with your actual access token.
