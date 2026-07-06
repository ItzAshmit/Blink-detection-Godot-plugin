# For Visual Documentation

[![Watch the demo](https://img.youtube.com/vi/kT5oXM1XOWc/maxresdefault.jpg)](https://www.youtube.com/watch?v=kT5oXM1XOWc)
> **NOTE: Techinical Side Visual Documentation isn't available yet but it will be soon**


# Eye Detection for Godot 4
> **Download the Direct .zip from Releases, extract it and paste into you project folder. Turn on the plugin and restart the project**
> 
> ⚠️ **This plugin currently supports Windows only.**
>
> ⚠️ **Visualizatio causes lag, use at you own risk.**

Bring your games to life with **real-time eye blink detection** powered by **MediaPipe** and a standard webcam.

Whether you're creating horror games, accessibility features, or experimental gameplay mechanics, this plugin provides an easy-to-use, signal-based API for integrating eye interactions into your projects.

## Features

* **Real-time blink detection**
* **Blink duration measurement**
* **Simple signal-based API**
* **Face detection state tracking**
* **Multiple visualization modes**
  * Standard Stream
  * Lined Eyes
  * Circle Eyes
  * Dotted Eyes
* **Fully customizable colors**
* **Works in both the editor and exported projects**
* **Example scene included**

##  Perfect For

* Horror games that react to player blinks
* Accessibility systems
* Experimental gameplay mechanics
* Research and educational projects
* Eye-tracking inspired interactions

## Signals

* `eyes_closed`
* `eye_opened(duration)`
* `face_detectable_state(state)`
* `telemetry_received(...)`

## Requirements

* **Windows only** (currently)
* **Godot 4.x**
* **Webcam**
* **Good lighting recommended for best accuracy**

## Getting Started

1. Add the `EyeDetection` node to your scene.
2. Run the project.
3. Connect to the provided signals.
4. Start building blink-powered gameplay!

An example scene is included to help you get started immediately.


## For Exported Projects

1. Export as usual.
2. Copy the folder "addons\Eye Detection\Python_files\dist" and paste it along side of your .exe, .pck and .dlls.
3. Test, if it doesn't work then most likely the folder is not pasted right.

## Known Issues and Suggestions

1. When the plugin is downloaded the `camera.gd` will throw a parse error. To solve this just enable the plugin and restart the project, It will be solved in the next update.

2. Visualization is very limited, I am trying to find a method to customize it directly from GDscrpit but untill then, you have to build a Python Venv yourself and update the python file and replace with the EyeDetectionHelper.exe.


Enjoy!!

# Support us by wishlisting our game The Unseeing 
[The Unseeing Store Page](https://store.steampowered.com/app/4864210/The_Unseeing/)
