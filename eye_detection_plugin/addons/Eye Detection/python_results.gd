extends Node
class_name EyeDetection

## Automatically starts eye detection when the game runs.
@export var auto_initialize: bool = true

## Prints eye-detection logs to the console on every update.
@export var enable_logging: bool = true

@export_subgroup("Advance Logging")

## If Enable Logging is true, excludes log message from console printing though the corresponding code
@export var Exclude_Codes:Array[String] = [
	"HB",
	"COR",
	"CS",
	"STR",
]

## Excludes signal message from telemetry_received signal though the corresponding code
@export var Exclude_Codes_Telementry_Signal:Array[String] = [
	"HB",
	"COR",
]

@export_group("Advance Options")

## Path to the EyeDetectionHelper executable. Use a project-relative path or an absolute path.
@export var Interpreter_path: String = "res://addons/Eye Detection/Python_files/dist/EyeDetectionHelper/EyeDetectionHelper.exe"

## A face-width ratio above this value selects the thresholds for a face far from the webcam.
@export var Far_Threshold: float = 0.1

## For a face far from the webcam, an eye aspect ratio below this value is treated as closed.
@export var Closed_Threshold_Far: float = 0.25

## For a face near the webcam, an eye aspect ratio below this value is treated as closed.
@export var Closed_Threshold_Near: float = 0.17

## For a face far from the webcam, an eye aspect ratio above this value is treated as open.
@export var Open_Threshold_Far: float = 0.3

## For a face near the webcam, an eye aspect ratio above this value is treated as open.
@export var Open_Threshold_Near: float = 0.25

## Use this option to Skip Frames of Detection. This is inversly proportional to the accuracy of detection
@export var Skip_Frames:int = 0

## Suppresses error messages from the eye detection process when enabled.
@export var Suppress_Errors: bool = false

## Separator used to split values in messages exchanged with the helper process. Size of String can be reduced to achieve micro-performance
@export var SEP: String = "<<<SEP>>>"

var _interpreter_path
var _process_info: Dictionary
var _stdio_stream: FileAccess
var paused: bool = false
var is_camera_open: bool = false
var right_eye_coords: Dictionary
var left_eye_coords: Dictionary

signal camera_opened

signal available_cameras(cameras:Array)

signal camera_index_changed(past_index:int, new_index:int)

signal detection_closed

signal eyes_closed

signal eye_opened(Duration: float)

signal face_detectable_state(State:bool)

signal telemetry_received(RawText: String, Type: String, Code: String, Details: String, Extra: String)


func _ready() -> void:
	if not auto_initialize:
		return

	start_process()
	

func start_process() -> void:
	stop_process()
	if OS.is_debug_build():
		_interpreter_path = ProjectSettings.globalize_path(Interpreter_path)
	else:
		_interpreter_path = OS.get_executable_path().get_base_dir() + "/EyeDetectionHelper/EyeDetectionHelper.exe"

	if not FileAccess.file_exists(_interpreter_path):
		push_error("EyeTrackingService: Python interpreter not found at %s" % _interpreter_path)
		return

	_process_info = OS.execute_with_pipe(_interpreter_path,
	[Closed_Threshold_Far,
	Open_Threshold_Far,
	OS.is_debug_build(),
	Closed_Threshold_Near,
	Open_Threshold_Near,
	Far_Threshold,
	Skip_Frames,
	SEP,
	],
	false)
	
	if _process_info.is_empty():
		push_error("EyeTrackingService: Failed to initialize background process.")
		return
	_stdio_stream = _process_info["stdio"]
	
	heartbeat(2)



func _process(_delta: float) -> void:
	if _stdio_stream == null:
		return

	var raw_line = _stdio_stream.get_line()
	if raw_line != "":
		var segments = raw_line.split(SEP)
		if segments.size() != 4:
			print("Received malformed telemetry: %s" % raw_line)
			return
		
		var msg_type = segments[0].strip_edges()
		var status_code = segments[1].strip_edges()
		var detail = segments[2].strip_edges()
		var extra = segments[3].strip_edges()
		
		if status_code == "C" and not is_camera_open:
			is_camera_open = true
			camera_opened.emit()
		
		if status_code == "CF":
			var data = parse_json(extra)
			if data:
				available_cameras.emit(data)
		
		
		if status_code == "CS":
			var data = parse_json(extra)
			if data:
				camera_index_changed.emit(data[0], data[1])
			
			
		if not status_code in Exclude_Codes_Telementry_Signal:
			telemetry_received.emit(raw_line, msg_type, status_code, detail, extra)
		else:
			if detail == "LEFT":
				var data = parse_json(extra)
				if data:
					left_eye_coords = data
				
			if detail == "RIGHT":
				var data = parse_json(extra)
				if data:
					right_eye_coords = data
					
		
		if status_code == "EC":
			eyes_closed.emit()

		if status_code == "D":
			eye_opened.emit(float(extra))

		if status_code == "NFF":
			face_detectable_state.emit(false)
		else:
			face_detectable_state.emit(true)



		if enable_logging and not status_code in Exclude_Codes:
			_log_telemetry(raw_line, msg_type, status_code, detail, extra)

		if not Suppress_Errors and msg_type == "ERROR" and not status_code in  Exclude_Codes:
			push_error("EyeTrackingService [Python]: ", detail)

func _log_telemetry(raw: String, type: String, code: String, msg: String, extra: String) -> void:
	print("[%s] Code: %s| %s | %s" % [type, code, msg, extra])


func pause_process() -> void:
	if _process_info.is_empty():
		return
	paused = true
	_stdio_stream.store_line("PAUSE")
	_stdio_stream.flush()





func resume_process() -> void:
	if _process_info.is_empty():
		return
	paused = false
	_stdio_stream.store_line("RESUME")
	_stdio_stream.flush()



var can_change_camera:bool = true
func change_camera(camera_index:int) -> void:
	if _process_info.is_empty() or not can_change_camera:
		return
	
	can_change_camera = false
	pause_process()
	var line = "CHNAGE_CAMERA:" + str(camera_index)
	_stdio_stream.store_line(line)
	_stdio_stream.flush()
	await get_tree().create_timer(1.5).timeout
	resume_process()
	await get_tree().create_timer(0.5).timeout
	can_change_camera = true
	
	
func heartbeat(sec:int):
	while true:
		if _process_info.is_empty():
			await get_tree().create_timer(0.1).timeout
			continue
		var line = "HEARTBEAT"
		_stdio_stream.store_line(line)
		_stdio_stream.flush()
		await get_tree().create_timer(sec).timeout
	

func parse_json(data):
	var json = JSON.new()
	var error = json.parse(data)
	if error == OK:
		var parsed_data = json.data
		return parsed_data
	else:
		push_error("EyeTrackingService [Python]: ", json.get_error_message())
		return null



func stop_process() -> void:
	if _process_info.is_empty():
		return
	
	_stdio_stream.store_line("STOP")
	_stdio_stream.flush()

	if OS.is_process_running(_process_info["pid"]):
		OS.kill(_process_info["pid"])

	await get_tree().create_timer(1).timeout
	
	detection_closed.emit()
	_process_info.clear()
	_stdio_stream = null




func _exit_tree() -> void:
	stop_process()
