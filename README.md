### Support us by wishlisting our game, The Unseeing

[The Unseeing Store Page](https://store.steampowered.com/app/4864210/The_Unseeing/)

### Example scene included

### Visual documentation

[![Watch the demo](https://img.youtube.com/vi/kT5oXM1XOWc/maxresdefault.jpg)](https://www.youtube.com/watch?v=kT5oXM1XOWc)

# Eye Detection for Godot 4

> **Download the ZIP from Releases, extract it into your project folder, enable the plugin, and restart the project.**
>
> ⚠️ **This plugin currently supports Windows only.**

## What is it?

This is an easy-to-use, open-source plugin for real-time eye detection using a Windows desktop camera.

## What features does it offer?

1. Find the state of the eyes and face, such as whether the eyes are open or closed and whether a face is detectable.
2. Show the eyes in real time in-game using the eye coordinates provided by the plugin.
3. Make eyes interactive using the provided coordinates. For example, add collisions, draw with eye movements, or control in-game camera movement.

### The possibilities are as far as the developer can imagine.

# How to use it

## How to implement basic eye detection

1. Download the plugin from the Godot Asset Library or the Releases page, then place it in your project’s root directory.
2. Enable the plugin.
3. Restart the project if needed.
4. Add a node named `EyeDetection` to the scene tree. Set `auto_initialize` and `enable_logging` to `true`.
5. Run the project. You should see the results in the console.

## How to use the provided signals in gameplay

The plugin provides the following signals:

- `signal camera_opened` — Emitted when the camera opens.
- `signal available_cameras(cameras: Array)` — Emitted with an array of available camera indexes.
- `signal camera_index_changed(past_index: int, new_index: int)` — Emitted when the camera index changes.
- `signal detection_closed` — Emitted when detection closes.
- `signal eyes_closed` — Emitted when the eyes close.
- `signal eye_opened(Duration: float)` — Emitted when the eyes open.
- `signal face_detectable_state(State: bool)` — Emitted on each backend update while detection is not paused, with the face-detection state.
- `signal telemetry_received(RawText: String, Type: String, Code: String, Details: String, Extra: String)` — Emitted on each backend update while detection is not paused, with the received backend data.

These signals can be used in gameplay to create interactive experiences.

## How to draw the eye coordinates in-game

The eye coordinates are relative to the webcam viewport, `Vector2(1280, 720)`. The plugin provides them through the `right_eye_coords` and `left_eye_coords` properties as dictionaries. Each point is an `[x, y]` array:

```text
{
  "Center": [x1, y1],
  "Corner_Left": [x2, y2],
  "Top_Left": [x3, y3],
  "Top_Right": [x4, y4],
  "Corner_Right": [x5, y5],
  "Bottom_Right": [x6, y6],
  "Bottom_Left": [x7, y7]
}
```

### Beginners can start with `example_visualizations.tscn` or use this example

```gdscript
extends Node2D

@export_category("Eye_Detection_Node_Reference")
@export var eye_detection: EyeDetection

@export_category("Visualization_options")
@export_enum("Lined_eyes", "Dotted_eyes", "Round_eyes") var type_of_style: int
@export var Right_eye_color_1: Color = Color.RED
@export var Right_eye_color_2: Color = Color.BLUE
@export var Left_eye_color_1: Color = Color.GREEN
@export var Left_eye_color_2: Color = Color.YELLOW
@export var Left_Length_1 = 2.0
@export var Left_Length_2 = 1.5
@export var Right_Length_1 = 2.0
@export var Right_Length_2 = 1.5
@export_range(-1280, 1280) var Horizontal_offset = 0.0
@export_range(-720, 720) var Vertical_offset: float = 0.0

const CAMERA_VIEWPORT: Vector2 = Vector2(1280, 720)

var is_detecting_eyes: bool = false

func _ready() -> void:
	if eye_detection:
		eye_detection.camera_opened.connect(_camera_opened)
		eye_detection.detection_closed.connect(_detection_closed)
	else:
		push_error("EyeVisualizationService: Eye Detection Node not assigned")
		return

func _draw() -> void:
	if not is_detecting_eyes:
		return

	if type_of_style == 0:
		draw_lined_eyes()
	if type_of_style == 1:
		draw_dotted_eyes()
	if type_of_style == 2:
		draw_round_eyes()

func _process(_delta: float) -> void:
	if not is_detecting_eyes:
		return

	var viewport_size = get_viewport_rect().size
	position = (viewport_size / 2) + Vector2(Horizontal_offset, Vertical_offset)
	queue_redraw()

func _camera_opened() -> void:
	is_detecting_eyes = true

func _detection_closed() -> void:
	is_detecting_eyes = false

func draw_lined_eyes() -> void:
	draw_eye_outline(eye_detection.left_eye_coords.values(), Left_eye_color_1, Left_eye_color_2, Left_Length_1, Left_Length_2)
	draw_eye_outline(eye_detection.right_eye_coords.values(), Right_eye_color_1, Right_eye_color_2, Right_Length_1, Right_Length_2)

func draw_eye_outline(points: Array, line_color: Color, point_color: Color, line_width: float, point_width: float) -> void:
	for i in range(points.size()):
		var pos = get_pos_from_cords(points[i])
		var next_pos = get_pos_from_cords(points[(i + 1) % points.size()])
		draw_line(pos, next_pos, line_color, line_width)
		draw_circle(next_pos, 1, point_color, false, point_width)

func draw_dotted_eyes() -> void:
	var left_eye_cords = eye_detection.left_eye_coords.values()
	for eye_cords in left_eye_cords:
		var pos = get_pos_from_cords(eye_cords)
		draw_circle(pos, Left_Length_1, Left_eye_color_1, false, Left_Length_2)

	var right_eye_cords = eye_detection.right_eye_coords.values()
	for eye_cords in right_eye_cords:
		var pos = get_pos_from_cords(eye_cords)
		draw_circle(pos, Right_Length_1, Right_eye_color_1, false, Right_Length_2)

func draw_round_eyes() -> void:
	if eye_detection.left_eye_coords.size():
		var left_eye_center = eye_detection.left_eye_coords["Center"]
		var left_eye_center_pos = get_pos_from_cords(left_eye_center)
		draw_circle(left_eye_center_pos, 10, Left_eye_color_1)
		draw_circle(left_eye_center_pos, 5, Left_eye_color_2)

	if eye_detection.right_eye_coords.size():
		var right_eye_center = eye_detection.right_eye_coords["Center"]
		var right_eye_center_pos = get_pos_from_cords(right_eye_center)
		draw_circle(right_eye_center_pos, 10, Right_eye_color_1)
		draw_circle(right_eye_center_pos, 5, Right_eye_color_2)

func get_pos_from_cords(cords: Array) -> Vector2:
	var x = cords[0]
	var y = cords[1]
	return Vector2(x, y) - CAMERA_VIEWPORT / 2.0
```

## What are the properties for?

| Property | Type | Default | Description |
|---|---|---|---|
| `auto_initialize` | `bool` | `true` | Automatically starts eye detection when the game runs. |
| `enable_logging` | `bool` | `true` | Prints eye-detection logs to the console on every update. |
| `Exclude_Codes` | `Array[String]` | `["HB", "COR", "CS", "STR"]` | **Advanced logging.** When logging is enabled, skips console messages associated with these codes. |
| `Exclude_Codes_Telementry_Signal` | `Array[String]` | `["HB", "COR"]` | **Advanced logging.** Skips telemetry messages associated with these codes when emitting the `telemetry_received` signal. |
| `Interpreter_path` | `String` | `res://addons/Eye Detection/Python_files/dist/EyeDetectionHelper/EyeDetectionHelper.exe` | **Advanced options.** Path to the `EyeDetectionHelper` executable. Use a project-relative or absolute path. |
| `Far_Threshold` | `float` | `0.1` | **Advanced options.** A face-width ratio above this value selects the thresholds for a face far from the webcam. |
| `Closed_Threshold_Far` | `float` | `0.25` | **Advanced options.** For a face far from the webcam, an eye aspect ratio below this value is treated as closed. |
| `Closed_Threshold_Near` | `float` | `0.17` | **Advanced options.** For a face near the webcam, an eye aspect ratio below this value is treated as closed. |
| `Open_Threshold_Far` | `float` | `0.3` | **Advanced options.** For a face far from the webcam, an eye aspect ratio above this value is treated as open. |
| `Open_Threshold_Near` | `float` | `0.25` | **Advanced options.** For a face near the webcam, an eye aspect ratio above this value is treated as open. |
| `Skip_Frames` | `int` | `0` | **Advanced options.** Skips frames during detection. Increasing this value reduces detection accuracy. |
| `Suppress_Errors` | `bool` | `false` | **Advanced options.** Suppresses error messages from the eye-detection process when enabled. |
| `SEP` | `String` | `<<<SEP>>>` | **Advanced options.** Separator used to split values in messages exchanged with the helper process. A shorter string may provide a small performance benefit. |

# For exported projects

1. Export as usual.
2. Copy the `EyeDetectionHelper` folder from `addons/Eye Detection/Python_files/dist/` and paste it alongside your `.exe`, `.pck`, and `.dll` files.
3. Test the exported project. If it does not work, check that the folder was copied to the correct location.

## Known issues and suggestions

When switching from camera index 0 to index 1 and then back to index 0, the camera sometimes behaves differently than it did initially.

Aside from that, there are no other known issues with the plugin.

# For advanced users: backend messages

Data is transferred in this format:

```text
<message_type><SEP><code><SEP><detail><SEP><extra>
```

| Type | Code | Detail | Extra |
|---|---|---|---|
| `ERROR` | `IE` | `Import error occurred` | Missing dependency: `Numpy not Installed`, `Mediapipe not Installed`, or `CV2 not Installed`. |
| `ERROR` | `FE` | `function_error` | Function name; currently `string_to_bool`. |
| `GAME` | `P` | `Game Paused` | Pause state as `True` or `False`. |
| `ERROR` | `CNF` | `Plugin Can't Open Camera` | Empty. Emitted when no camera is found on Windows. |
| `GAME` | `CF` | `Cameras found` | JSON array of available camera indexes, such as `[0, 1]`. |
| `ERROR` | `NW` | `The detected OS is not Windows, For now the plugin only supports Windows. The game may crash` | Empty. |
| `GAME` | `STR` | `Starting blink detection with threshold and debug settings` | Closed/open thresholds, debug state, and far-face threshold. |
| `GAME` | `C` | `Camera opened` | Camera-open state as `True` or `False`. |
| `ERROR` | `COC` | `Cannot open camera` | Empty. |
| `ERROR` | `MLC` | `Model loading failed with error` | Exception details. |
| `ERROR` | `CRF` | `Camera frame read failed` | Empty. |
| `GAME` | `EC` | `Eyes closed` | Empty. |
| `GAME` | `EO` | `Eyes opened` | Empty. |
| `GAME` | `D` | `Duration` | Blink duration in seconds. |
| `ERROR` | `RTE` | `Runtime error occurred` | Exception details. |
| `GAME` | `COR` | `LEFT` or `RIGHT` | JSON object containing eye center, corners, and top and bottom landmark coordinates. |
| `ERROR` | `RDIR` | `Cannot retrieve any type of runtime path` | Exception details. |
| `GAME` | `STOP` | `Stopping the process` | Empty. |
| `GAME` | `HB` | `Heartbeat received` | Empty. |
| `ERROR` | `HB` | `Heartbeat not received for 5 seconds, stopping the process` | Empty. |
| `GAME` | `CC` | `Camera changed to index <camera index>` | Camera-open state as `True` or `False`. |
| `ERROR` | `CCF` | `Failed to change camera to index <camera index>, changing to initial index` | Camera-open state as `True` or `False`. |
| `GAME` | `CS` | `Camera changed successfully` | JSON array containing the initial camera index and selected index, such as `[0, 1]`. |

`HB` is used for both a received heartbeat (`GAME`) and a heartbeat timeout (`ERROR`). Check the message type to distinguish them.

# Enjoy!
