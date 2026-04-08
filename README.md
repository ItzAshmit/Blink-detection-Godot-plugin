# Blink Detection for Godot

**Status: Work in progress**

This addon connects Godot to a Python + MediaPipe blink detection backend. It starts a Python process, reads blink-related messages from standard output, and exposes them to Godot through a simple `BlinkDetection` node.

The addon is functional as an experiment/prototype, but it is still under active development and the editor plugin side is not fully implemented yet.

## What it does right now

- Uses a bundled Python environment inside the addon
- Runs a MediaPipe face landmark detector through Python
- Opens the default webcam and tracks both eyes
- Detects when eyes close and reopen
- Emits raw output messages back to Godot
- Optionally shows a debug camera window with eye landmarks

## Current structure

- `Main.gd`
  Editor plugin entry point. At the moment this is mostly a stub.
- `python_results.gd`
  Main Godot-facing runtime script. This defines `class_name BlinkDetection`.
- `Python files/media_pipe_python_script.py`
  Python script that performs webcam capture and blink detection with MediaPipe.
- `Python files/face_landmarker.task`
  MediaPipe face landmark model used by the Python script.

## Requirements

- Godot 4
- Windows
- A working webcam

This addon is currently Windows-oriented because it directly launches:

`addons/Blink-detection/Python files/AgniVENV/Scripts/python.exe`

If you want Linux or macOS support, the Python launcher path will need to be adapted.

## Installation

1. Copy the `Blink-detection` folder into your project's `addons/` directory.
2. Open Godot and go to `Project > Project Settings > Plugins`.
3. Enable `Blink-detection by AgniGames`.

## Basic usage

Attach or create a node that uses the `BlinkDetection` script:

```gdscript
extends Node

@onready var blink_detector: BlinkDetection = $BlinkDetection

func _ready() -> void:
	blink_detector.Output.connect(_on_blink_output)

func _on_blink_output(text: String) -> void:
	print(text)
```

You can also create a node and attach:

`res://addons/Blink-detection/python_results.gd`

## Exposed properties

`BlinkDetection` currently exposes these exported properties:

- `Enable_Console_Prints`
  Prints parsed Python messages to the Godot output.
- `should_show_camera`
  Opens a debug camera window and draws eye landmark points.
- `ignore_errors`
  When disabled, Python error messages are forwarded with `push_error`.
- `theshold`
  Blink sensitivity threshold used by the eye aspect calculation.

Note: the property is currently named `theshold` in code. That spelling is part of the current implementation.

## Output format

The Python backend prints colon-separated messages such as:

```text
GAME:EC : Eyes closed
GAME:EO : Eyes opened
GAME:D : Duration: 0.143
ERROR:NFF: No face found.
```

The Godot script reads these lines and emits them through:

`signal Output(text: String)`

You can listen to that signal and handle blink events in your own game logic.

## Limitations

- The editor plugin (`Main.gd`) does not yet provide a full editor workflow
- The runtime depends on the bundled Python environment being present
- The implementation is currently Windows-specific
- Error handling and process management are still basic
- The pause flow is not finalized yet
- The README reflects the current prototype, not a final released addon

## Planned improvements

- Better editor integration
- Cleaner event API for blink start/end/duration
- Cross-platform Python launcher support
- Improved setup and dependency management
- More robust pause/resume and shutdown behavior
- Better documentation and examples

## Notes

This addon is best treated as an in-progress prototype for webcam-based blink detection inside Godot. If you use it in a project, expect changes while the API and plugin workflow are being refined.
