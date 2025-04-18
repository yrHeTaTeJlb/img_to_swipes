# Android Swipe Drawing Tool

This tool converts SVG images into touch swipes on Android devices. Perfect for customizing

## Performance Considerations

The script execution becomes progressively slower, particularly near completion, as pixels may be drawn multiple times. Drawing all pixels without repetition is hard. [NP-hard](https://en.wikipedia.org/wiki/Longest_path_problem), to be precise


## Prerequisites

- Python 3.7+
- ADB (Android Debug Bridge)
- Android device with USB debugging enabled
- CulebraTester2 APKs installed on device

## Setup Instructions

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Enable USB debugging on your Android device**
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → System → Developer Options → Enable "USB Debugging"
   - Settings → System → Developer Options → Enable "USB debugging (Security setting)"
   - Settings → System → Developer Options → Disable "Permission Monitoring"
   - Restart

3. **Install ADB**
   - [Download](https://developer.android.com/studio/releases/platform-tools) and install Android platform tools

4. **Connect your Android device**
   - Connect via USB
   - Confirm debugging prompt on device
   - Verify connection with `adb devices`

5. **Install CulebraTester2 APKs**
   - Download APKs from [GitHub](https://github.com/dtmilano/CulebraTester2-public/wiki/Prebuilt-APKs)
   - Install both APKs on your device

## Usage

1. **Start CulebraTester server**
   ```
   ./culebra_tester.sh
   ```

2. **Run the image-to-swipes converter**
   ```
   python img_to_swipes.py
   ```

3. **Fine-tune parameters**
   - Edit script parameters like `START_X`, `START_Y`, `MAX_WIDTH`, `MAX_HEIGHT`, `IMG`, `DRAW_DEBUG_FRAME` in img_to_swipes.py

4. **Repeat**
   - Repeat steps 2-3 until desired result is achieved

## How It Works

1. SVG image is converted to pixel coordinates
2. Connected pixels are identified to create swipe paths
3. The script executes swipe gestures on the Android device via CulebraTester

## Troubleshooting

- Ensure device is properly connected with ADB
- Check that CulebraTester2 services are running
- Adjust scaling parameters if drawing is too large/small

:shipit: