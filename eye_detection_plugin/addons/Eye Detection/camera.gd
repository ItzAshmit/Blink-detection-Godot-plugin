extends TextureRect
class_name CameraPreview

@export var eye_sensor: EyeDetection

@export_group("Advance options")
@export var FramePath:String = "res://addons/Eye Detection/Python_files/dist/EyeDetectionHelper/Frame.png"


func _process(_delta: float) -> void:
	if eye_sensor and eye_sensor.visualize_stream:
		visible = true
		var image := Image.new()
		var exe_path = OS.get_executable_path().get_base_dir()
		var global_image_path = "EyeDetectionHelper/Frame.png"
		var path:String

		if OS.is_debug_build():
			path = ProjectSettings.globalize_path(FramePath)
		else:
			path = _join_path(exe_path, global_image_path)


		if FileAccess.file_exists(path):
			var file := FileAccess.open(path, FileAccess.READ)
			if file == null:
				return

			var length := file.get_length()

			if length <= 0:
				return

			var bytes := file.get_buffer(length)
			if bytes.is_empty():
				return

			var err := image.load_png_from_buffer(bytes)
			if err == OK:
				texture = ImageTexture.create_from_image(image)
			else:
				return
	else:
		visible = false

func _join_path(base_dir: String, relative_path: String) -> String:
	var dir = base_dir.replace("\\", "/")
	if dir.ends_with("/"):
		dir = dir.substr(0, dir.length() - 1)
	if relative_path.begins_with("/"):
		relative_path = relative_path.substr(1, relative_path.length() - 1)
	return "%s/%s" % [dir, relative_path]
