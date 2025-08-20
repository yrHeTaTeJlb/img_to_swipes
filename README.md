# Android Swipe Drawing Tool

This tool converts images into touch swipes on Android devices. Useful for drawing logos, signatures, and simple art via automated gestures.

## Performance Considerations

The script execution becomes progressively slower, particularly near completion, as pixels may be drawn multiple times. Drawing all pixels without repetition is hard. [NP-hard](https://en.wikipedia.org/wiki/Longest_path_problem), to be precise


## Prerequisites

- Python 3.7+
- For android
   - ADB (Android Debug Bridge)
   - Android device with USB debugging enabled
   - CulebraTester2 APKs installed on device
- For ios
   - Node js
   - Appium
   - Appium driver xcuitest

## Setup Instructions for android

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

1. **Enable USB debugging on your Android device**
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → System → Developer Options → Enable "USB Debugging"
   - Settings → System → Developer Options → Enable "USB debugging (Security setting)"
   - Settings → System → Developer Options → Disable "Permission Monitoring"
   - Restart

1. **Install ADB**
   - [Download](https://developer.android.com/studio/releases/platform-tools) and install Android platform tools

1. **Connect your Android device**
   - Connect via USB
   - Confirm debugging prompt on device
   - Verify connection with `adb devices`

1. **Install CulebraTester2 APKs**
   - Download APKs from [GitHub](https://github.com/dtmilano/CulebraTester2-public/wiki/Prebuilt-APKs)
   - **Fallback:** If official builds have expired, use APKs from the `culebra_tester` directory in this repository
   - Install both APKs on your device

1. **Start CulebraTester server**
   ```
   ./culebra_tester.sh
   ```

## Setup Instructions for ios
**Note: These instructions are provided for reference but haven't been verified since I don't have Apple devices. They may be incomplete or require additional steps.**

1. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

1. **Install nodejs**
   ```
   brew install node
   ```

1. **Install appium**
   ```
   npm install -g appium
   ```

1. **Install xcuitest driver**
   ```
   appium driver install xcuitest
   ```

1. **Start Appium server**
   ```
   appium
   ```

1. **Change platform [parameter](img_to_swipes.py#L22)**
   ```
   PLATFORM = "ios"
   ```

## Usage

1. **Run the image-to-swipes converter**
   ```
   python img_to_swipes.py
   ```

1. **Fine-tune script [parameters](img_to_swipes.py#L16-L21)**
   - Edit script parameters `DEBUG`, `START_X`, `START_Y`, `MAX_WIDTH`, `MAX_HEIGHT`, `IMG` in img_to_swipes.py

1. **Repeat**
   - Repeat steps 1-2 until desired result is achieved

## How It Works

1. SVG image is converted to pixel coordinates
2. Connected pixels are identified to create swipe paths
3. The script executes swipe gestures on the device via an automation framework

:shipit: