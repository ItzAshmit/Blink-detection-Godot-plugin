import json
import platform
import sys
import time
import threading
from pathlib import Path

is_running: bool = True
SEP:str = ""

def emit(message_type: str, code: str, detail: str, extra: str | None = None) -> None:
    global SEP
    if SEP == "":
        SEP = "<<<SEPARATOR>>>"
    line = f"{message_type}{SEP}{code}{SEP}{detail}{SEP}{extra}"

    print(line, flush=True)


try:
    import numpy as np
except ImportError:
    emit("ERROR", "IE", "Import error occurred", "Numpy not Installed")
    sys.exit(1)


try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    emit("ERROR", "IE", "Import error occurred", "Mediapipe not Installed")
    sys.exit(1)


try:
    import cv2
except ImportError:
    emit("ERROR", "IE", "Import error occurred", "CV2 not Installed")
    sys.exit(1)

paused: bool = False
camera_index: int = 0
Heartbeat_timer:float = time.time()

def string_to_bool(input:str) -> bool:
	input = input.lower()

	if input in ["true", "1"]:
		return True
	elif input in ["false", "0"]:
		return False

	emit("ERROR", "FE", "function_error", "string_to_bool")
	return False







def main() -> None:
    closed_theshold_far = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
    opened_theshold_far = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    is_debug_build = string_to_bool(sys.argv[3] if len(sys.argv) > 3 else "false")
    closed_theshold_near = float(sys.argv[4]) if len(sys.argv) > 4 else 0.17
    opened_theshold_near = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
    theshold_far = float(sys.argv[6]) if len(sys.argv) > 6 else 0.1
    skip_frames = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    global SEP
    SEP = sys.argv[8] if len(sys.argv) > 8 else "<<<SEPARATOR>>>"

    threading.Thread(target=stdin_listener, daemon=True).start()
    
    blink_detection(
        closed_theshold_far,
        opened_theshold_far,
        is_debug_build,
        closed_theshold_near,
        opened_theshold_near,
        theshold_far,
        skip_frames
    )


def pause(result: bool) -> None:
    global paused
    paused = result
    emit("GAME", "P", f"Game Paused", str(paused))

def open_camera() -> None:
    global camera_index
    global cap
    cameras_found:list = []
    if platform.system() == "Windows":
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cameras_found.append(i)
                cap.release()
            time.sleep(0.2)
        if not len(cameras_found):
            emit("ERROR", "CNF", "Plugin Can't Open Camera", "")
            return
        emit("GAME", "CF", "Cameras found", json.dumps(cameras_found))
        camera_index = cameras_found[0]
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(0)
        emit("ERROR", "NW", "The detected OS is not Windows, For now the plugin only supports Windows. The game may crash", "")

def blink_detection(
    closed_theshold_far: float = 0.1,
    opened_theshold_far: float = 0.3,
    is_debuged: bool = False,
    closed_theshold_near: float = 0.17,
    opened_theshold_near: float = 0.25,
    theshold_far: float = 0.1,
    skip_frames: int = 0,
) -> None:
    
    emit(
        "GAME",
        "STR",
        f"Starting blink detection with closed threshold ({closed_theshold_far}), opened threshold ({opened_theshold_far}), is_debug_build ({is_debuged}), closed_theshold_near ({closed_theshold_near}), opened_theshold_near ({opened_theshold_near}), theshold_far ({theshold_far})","" 
    )

    open_camera()

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    emit("GAME", "C", f"Camera opened", str(cap.isOpened()))

    if not cap.isOpened():
        emit("ERROR", "COC", "Cannot open camera", "")
        return

    try:
        model_path = runtime_dir() / "face_landmarker.task"
        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
        )

        landmarker = vision.FaceLandmarker.create_from_options(options)
    except Exception as e:
        emit("ERROR", "MLC", f"Model loading failed with error", str(e))
        return


    left_eye_full = [33, 160, 158, 133, 153, 144]
    right_eye_full = [362, 385, 387, 263, 373, 380]

    start_time = 0.0
    is_blink_time = False
    list_of_frames: list[float] = []

    try:
        while is_running:

            heartbeat_reciever()
            
            if paused:
                time.sleep(0.1)
                continue
            
            ret, frame = cap.read()
            if not ret:
                emit("ERROR", "CRF", "Camera frame read failed", "")
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            h, w, _ = frame.shape
            frame_timestamp_ms = int(time.monotonic() * 1000)
            result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            if result.face_landmarks:
                face = result.face_landmarks[0]

                send_eye_coordinates(face, w, h, left_eye_full, right_eye_full)

                left_eye_width = abs(face[33].x - face[133].x)
                left_eye_y_gap = (abs(face[160].y - face[153].y) + abs(face[158].y - face[144].y)) / 2
                left_eye_ratio = left_eye_y_gap / left_eye_width

                right_eye_width = abs(face[362].x - face[263].x)
                right_eye_y_gap = (abs(face[385].y - face[373].y) + abs(face[387].y - face[380].y)) / 2
                right_eye_ratio = right_eye_y_gap / right_eye_width

                eye_ratio = (left_eye_ratio + right_eye_ratio) / 2
                face_width = abs(face[362].x - face[33].x)

                if face_width > theshold_far:
                    closed_theshold_far = closed_theshold_far
                    opened_theshold_far = opened_theshold_far
                else:
                    closed_theshold_far = closed_theshold_near
                    opened_theshold_far = opened_theshold_near


                list_of_frames.append(eye_ratio)
                if len(list_of_frames) < (skip_frames + 1):
                    continue

                total = 0.0
                for item in list_of_frames:
                    total += item
                eye_ratio = total / len(list_of_frames)
                list_of_frames.clear()


                if not is_blink_time and eye_ratio < closed_theshold_far:
                    start_time = time.time()
                    emit("GAME", "EC", "Eyes closed", "")
                    is_blink_time = True

                if is_blink_time and eye_ratio > opened_theshold_far and time.time() - start_time > 0.05:
                    emit("GAME", "EO", "Eyes opened", "")
                    emit("GAME", "D", "Duration", str(time.time() - start_time))
                    is_blink_time = False

        stop_process(cap)

    except Exception as e:
        emit("ERROR", "RTE", "Runtime error occurred", str(e))
        stop_process(cap)


def send_eye_coordinates(face, w, h, left_eye_full, right_eye_full):
    left_outmost_left = face[33]
    left_outmost_right = face[133]
    right_outmost_left = face[362]
    right_outmost_right = face[263]

    left_eye_left = [int(left_outmost_left.x * w), int(left_outmost_left.y * h)]
    right_eye_right = [int(right_outmost_left.x * w), int(right_outmost_left.y * h)]
    left_eye_right = [int(left_outmost_right.x * w), int(left_outmost_right.y * h)]
    right_eye_left = [int(right_outmost_right.x * w), int(right_outmost_right.y * h)]

    left_center = [int((left_eye_left[0] + left_eye_right[0]) / 2), int((left_eye_left[1] + left_eye_right[1]) / 2)]
    right_center = [int((right_eye_left[0] + right_eye_right[0]) / 2), int((right_eye_left[1] + right_eye_right[1]) / 2)]

    left_eye_x = left_center[0]
    left_eye_y = left_center[1]
    right_eye_x = right_center[0]
    right_eye_y = right_center[1]

    left_array = {}
    left_array["Center"] = [(w - left_eye_x), left_eye_y]

    lm1 = face[left_eye_full[0]]
    left_array["Corner_Left"] = [(w - int(lm1.x * w)), int(lm1.y * h)]

    lm2 = face[left_eye_full[1]]
    left_array["Top_Left"] = [(w - int(lm2.x * w)), int(lm2.y * h)]

    lm3 = face[left_eye_full[2]]
    left_array["Top_Right"] = [(w - int(lm3.x * w)), int(lm3.y * h)]

    lm4 = face[left_eye_full[3]]
    left_array["Corner_Right"] = [(w - int(lm4.x * w)), int(lm4.y * h)]

    lm5 = face[left_eye_full[4]]
    left_array["Bottom_Right"] = [(w - int(lm5.x * w)), int(lm5.y * h)]

    lm6 = face[left_eye_full[5]]
    left_array["Bottom_Left"] = [(w - int(lm6.x * w)), int(lm6.y * h)]

    right_array = {}
    right_array["Center"] = [(w - right_eye_x), right_eye_y]

    ln1 = face[right_eye_full[0]]
    right_array["Corner_Left"] = [(w - int(ln1.x * w)), int(ln1.y * h)]

    ln2 = face[right_eye_full[1]]
    right_array["Top_Left"] = [(w - int(ln2.x * w)), int(ln2.y * h)]

    ln3 = face[right_eye_full[2]]
    right_array["Top_Right"] = [(w - int(ln3.x * w)), int(ln3.y * h)]

    ln4 = face[right_eye_full[3]]
    right_array["Corner_Right"] = [(w - int(ln4.x * w)), int(ln4.y * h)]

    ln5 = face[right_eye_full[4]]
    right_array["Bottom_Right"] = [(w - int(ln5.x * w)), int(ln5.y * h)]

    ln6 = face[right_eye_full[5]]
    right_array["Bottom_Left"] = [(w - int(ln6.x * w)), int(ln6.y * h)]


    jsonfy_left = json.dumps(left_array)
    jsonfy_right = json.dumps(right_array)

    emit("GAME", "COR", "LEFT", jsonfy_left)
    emit("GAME", "COR", "RIGHT", jsonfy_right)

    
def runtime_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                return Path(sys._MEIPASS)
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except Exception as error:
        emit("ERROR", "RDIR", "Cannot retrieve any type of runtime path", str(error))


def stdin_listener():
    global is_running
    global Heartbeat_timer
    while is_running:
        line = sys.stdin.readline()
        if not line:
            break
        command = line.strip()
        if command == "PAUSE":
            pause(True)
        elif command == "RESUME":
            pause(False)
        elif command == "STOP":
            emit("GAME", "STOP", "Stopping the process", "")
            time.sleep(0.1)
            is_running = False
        elif command.startswith("CHNAGE_CAMERA:"):
            time.sleep(0.1)
            change_camera(int(command.split(":")[1]))

        elif command == "HEARTBEAT":
            Heartbeat_timer = time.time()
            emit("GAME", "HB", "Heartbeat received", "")


def heartbeat_reciever():
    global Heartbeat_timer
    global cap
    if time.time() - Heartbeat_timer > 5.0:
        emit("ERROR", "HB", "Heartbeat not received for 5 seconds, stopping the process", "")
        stop_process(cap)


def stop_process(cap = None) -> None:
    emit("GAME", "STOP", "Stopping the process", "")
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    sys.exit()

def change_camera(camera_index_: str) -> None:
    global camera_index
    global cap

    index:int = 0
    if cap:
        cap.release()
    if platform.system() == "Windows":
        cap = cv2.VideoCapture(camera_index_, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera_index_)
        emit("ERROR", "NW", "The detected OS is not Windows, For now the plugin only supports Windows. The game may crash", "")
    if cap.isOpened():
        emit("GAME", "CC", f"Camera changed to index {camera_index_}", str(cap.isOpened()))
        index = camera_index_

    else:
        emit("ERROR", "CCF", f"Failed to change camera to index {camera_index_}, changing to initial index", str(cap.isOpened()))
        if platform.system() == "Windows":
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            index = camera_index
        else:
            cap = cv2.VideoCapture(camera_index)
            index = camera_index
            emit("ERROR", "NW", "The detected OS is not Windows, For now the plugin only supports Windows. The game may crash", "")

    emit("GAME", "CS", f"Camera changed successfully", json.dumps([camera_index, index]))

    camera_index = index

if __name__ == "__main__":
    main()