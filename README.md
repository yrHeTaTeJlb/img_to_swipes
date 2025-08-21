# Swipe Drawing Tool

This tool converts images into touch swipes on Android devices. Useful for drawing logos, signatures, and simple art via automated gestures.


# Platforms
Currently, only Android is supported. In theory, it can be extended to other platforms supported by Appium:
https://appium.io/docs/en/2.19/ecosystem/drivers/

iOS is excluded: the platform does not allow performing automated gestures on apps signed with a distribution certificate, which prevents using this tool on iOS devices.

## Prerequisites

- [UV installed](https://docs.astral.sh/uv/getting-started/installation/)
- [USB debugging enabled](https://www.mobikin.com/android-backup/how-to-enable-usb-debugging.html)


## Setup Instructions

1. **Install UV**
2. **Enable USB debugging on your Android device**
3. **Connect your device to the computer**


## Usage

1. **Select the image you want to draw in config.toml**
   ```toml
   [image]
   path = "img/fry.svg"
   ```

1. Run the script
   ```bash
   ./img_to_swipes.sh
   ```
   or
   ```bat
   img_to_swipes.cmd
   ```

1. Pay attention to where debug rects are drawn on the screen. Adjust canvas coordinates if needed:
   ```toml
   [canvas]
   x = 115
   y = 790
   width = 560
   height = 520
   ```

1. **Repeat steps 2–3 until satisfied, then disable debug rects drawing**
   ```toml
   [debug]
   draw_canvas_rect = false
   draw_image_rect = false
   draw_content_rect = false
   ```

1. **Run the script one last time**


## How It Works

1. Image is scaled and converted to grayscale
1. Black pixels are identified
1. Connected pixels are identified to create swipe paths
1. The script executes swipe gestures on the device via an automation framework

:shipit: