extends Node
class_name EyeDetection

@export var auto_initialize: bool = true
@export var enable_logging: bool = true

@export_group("Visualize_steam_options")
@export var visualize_stream: bool = false
@export_enum("Standard_steam", "Lined_eyes", "Circle_eyes") var type_of_steam:int
@export_subgroup("Advance_eye_steam_options")
@export var color_of_eyes:Color = Color(1.0,0.0,0.0,1.0)
@export var bg_color:Color = Color(0.0,0.0,0.0,0.0) 


@export_group("Advance Options")
@export var Interpreter_path:String = "res://addons/Eye Detection/Python_files/dist/EyeDetectionHelper/EyeDetectionHelper.exe"
@export var blink_lower_threshold: float = 0.13
@export var blink_upper_threshold: float = 0.25
@export var suppress_errors: bool = false

var _interpreter_path 
var _process_info: Dictionary
var _stdio_stream: FileAccess

signal telemetry_received(raw_text: String, type: String, status_code: String, detail: String)

func _join_path(base_dir: String, relative_path: String) -> String:
	var dir = base_dir.replace("\\", "/")
	if dir.ends_with("/"):
		dir = dir.substr(0, dir.length() - 1)
	if relative_path.begins_with("/"):
		relative_path = relative_path.substr(1, relative_path.length() - 1)
	return "%s/%s" % [dir, relative_path]

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


	_process_info = OS.execute_with_pipe(_interpreter_path, [blink_lower_threshold, blink_upper_threshold, OS.is_debug_build(), visualize_stream], false)
	
	if _process_info.is_empty():
		push_error("EyeTrackingService: Failed to initialize background process.")
		return
		
	_stdio_stream = _process_info["stdio"]




func _process(_delta: float) -> void:
	if _stdio_stream == null:
		return

	var raw_line = _stdio_stream.get_line()

	if raw_line != "":
		var segments = raw_line.split(":")
		if segments.size() != 3: 
			print("Received malformed telemetry: %s" % raw_line)
		
		var msg_type = segments[0].strip_edges()
		var status_code = segments[1].strip_edges()
		var detail = segments[2].strip_edges()

		telemetry_received.emit(raw_line, msg_type, status_code, detail)
		
		if enable_logging:
			_log_telemetry(raw_line, msg_type, status_code, detail)

		if not suppress_errors and msg_type == "ERROR":
			push_error("EyeTrackingService [Python]: ", detail)

func _log_telemetry(raw: String, type: String, code: String, msg: String) -> void:
	if code == "D": # Duration code
		var duration = raw.split(":")[3].strip_edges() + "s"
		print("[%s] Code: %s | %s (%s)" % [type, code, msg, duration])
	else:
		print("[%s] Code: %s | %s" % [type, code, msg])


func stop_process() -> void:
	if _process_info.is_empty():
		return

	print("Killing PID:", _process_info["pid"])
	var err = OS.kill(_process_info["pid"])
	print("Kill result:", err)

	await get_tree().create_timer(1).timeout

	print(OS.is_process_running(_process_info["pid"]))



func _exit_tree() -> void:
	stop_process()
