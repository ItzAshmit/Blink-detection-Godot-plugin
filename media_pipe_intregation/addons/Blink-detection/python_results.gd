extends Node
class_name BlinkDetection

@export var Enable_Console_Prints:bool = true
@export var should_show_camera:bool = false
@export var ignore_errors:bool = true
@export var theshold: float = 0.35

var interpreter_path = ProjectSettings.globalize_path("res://addons/Blink-detection/Python files/AgniVENV/Scripts/python.exe")
var script_path = ProjectSettings.globalize_path("res://addons/Blink-detection/Python files/media_pipe_python_script.py")

var py_process: Dictionary
var py_stdio: FileAccess

signal Output(text:String)


func _ready():
	py_process = OS.execute_with_pipe(interpreter_path, [script_path, theshold, should_show_camera], false)
	if py_process.is_empty():
		push_error("Failed to start Python process")
		return
	py_stdio = py_process["stdio"]

var duration = ""

func _process(_delta):
	if py_stdio == null:
		return


	var text = py_stdio.get_line()


	if text != "":
		var message_type = text.split(":")[0].strip_edges()

		var Code = text.split(":")[1].strip_edges()

		var message = text.split(":")[2].strip_edges()

		Output.emit(text)
		if Enable_Console_Prints:
			if Code == "D":
				duration = text.split(":")[3].strip_edges() + " seconds"
				print("OUTPUT: "," ~~~~~~~~~~ ","type: ", message_type," ~~~~~~~~~~ ", "Code: ", Code," ~~~~~~~~~~ ", "Message: ", message + " (" + duration + ")")
			else:
				print("OUTPUT: "," ~~~~~~~~~~ ","type: ", message_type," ~~~~~~~~~~ ", "Code: ", Code," ~~~~~~~~~~ ", "Message: ", message)

		if not ignore_errors:
			if message_type == "ERROR":
				push_error("Python Error: ", message)


func _exit_tree() -> void:
	if not py_process.is_empty():
		OS.kill(py_process["pid"])

func pause_eye_detection(result:bool):
	OS.execute_with_pipe(interpreter_path, [script_path, "pause", result], false)