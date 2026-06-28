import os
import platform
import sys
import time
from pathlib import Path


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


def string_to_bool(input:str) -> bool:
	input = input.lower()

	if input in ["true", "1"]:
		return True
	elif input in ["false", "0"]:
		return False

	emit("ERROR", "FE", "function_error", "string_to_bool")
	return False

SEP:str = ""
def main() -> None:

    is_debug_build = string_to_bool(sys.argv[3] if len(sys.argv) > 3 else "false")
    visualize_stream = string_to_bool(sys.argv[4] if len(sys.argv) > 4 else "false")
    type_of_stream = sys.argv[5] if len(sys.argv) > 5 else 0
    color_of_right_eye = sys.argv[6] if len(sys.argv) > 6 else "#FF000000"
    color_of_left_eye = sys.argv[7] if len(sys.argv) > 7 else "#FF000000"
    bg_color = sys.argv[8] if len(sys.argv) > 8 else "#00000000"
    color_of_right_eye2 = sys.argv[9] if len(sys.argv) > 9 else "#00B3FF00"
    color_of_left_eye2 = sys.argv[10] if len(sys.argv) > 10 else "#00B3FF00"

    global SEP
    SEP = sys.argv[11] if len(sys.argv) > 11 else "<<<SEPARATOR>>>"
    


    blink_detection(
        float(sys.argv[1]) if len(sys.argv) > 1 else 0.13,
        float(sys.argv[2]) if len(sys.argv) > 2 else 0.25,
        is_debug_build,
        visualize_stream,
        type_of_stream,
        color_of_right_eye,
        color_of_left_eye,
        color_of_right_eye2,
        color_of_left_eye2,
        bg_color
    )


def pause(result: bool) -> None:
    global paused
    paused = result
    emit("GAME", "P", f"Game Paused {paused}", "")


def blink_detection(
    closed_theshold: float = 0.1,
    opened_theshold: float = 0.3,
    is_debuged: bool = False,
    visualize_stream: bool = False,
    type_of_stream:int = 0,
    color_of_right_eye = "#FF000000",
    color_of_left_eye = "#FF000000",
    color_of_right_eye2 = "#FF000000",
    color_of_left_eye2 = "#FF000000",
    bg_color = "#00000000"
) -> None:
    
    emit(
        "GAME",
        "STR",
        f"Starting blink detection with closed threshold ({closed_theshold}), opened threshold ({opened_theshold}), is_debug_build ({is_debuged}), type_of_stream ({type_of_stream}), color_of_right_eye ({color_of_right_eye}), color_of_left_eye ({color_of_left_eye}), bg_color ({bg_color})","" 
    )

    camera_found:bool = False
    if platform.system() == "Windows":
        for i in range(5):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if cap.isOpened():
                camera_found = True
                break
            time.sleep(1.0)
        if not camera_found:
            emit("ERROR", "CNF", "Plugin Can't Open Camera", "")
            return
    else:
        cap = cv2.VideoCapture(0)
        emit("ERROR", "NW", "The detected OS is not Windows, For now the plugin only supports Windows. The game may crash", "")

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
    last_no_face_log_time = 0.0

    try:
        while True:
            if paused:
                time.sleep(0.1)
                emit("GAME", "P", "Game is paused, skipping frame processing", "")
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

            bg_screen = np.zeros((h, w, 4), dtype=np.uint8)

            bgc = change_to_BGRA(bg_color)
            
            bg_screen[:] = (bgc[0], bgc[1], bgc[2], bgc[3])

            if result.face_landmarks:
                face = result.face_landmarks[0]


                if type_of_stream == "0":
                    Show_eyes_0(visualize_stream ,frame, bg_screen)

                elif type_of_stream == "1":
                    Show_eyes_1(left_eye_full, right_eye_full, h, w, bg_screen, face, color_of_right_eye, color_of_left_eye, color_of_right_eye2, color_of_left_eye2, visualize_stream)

                elif type_of_stream == "2":
                    Show_eyes_2(left_eye_full, right_eye_full, h, w, bg_screen, face,color_of_right_eye, color_of_left_eye, color_of_right_eye2, color_of_left_eye2, visualize_stream)

                elif type_of_stream == "3":
                    Show_eyes_3(left_eye_full, right_eye_full, h, w, bg_screen, face,color_of_right_eye, color_of_left_eye, visualize_stream)
                
                left_eye_width = abs(face[33].x - face[133].x)
                left_eye_y_gap = (abs(face[160].y - face[153].y) + abs(face[158].y - face[144].y)) / 2
                left_eye_ratio = left_eye_y_gap / left_eye_width

                right_eye_width = abs(face[362].x - face[263].x)
                right_eye_y_gap = (abs(face[385].y - face[373].y) + abs(face[387].y - face[380].y)) / 2
                right_eye_ratio = right_eye_y_gap / right_eye_width

                eye_ratio = (left_eye_ratio + right_eye_ratio) / 2
                face_width = abs(face[362].x - face[33].x)

                if face_width > 0.1:
                    closed_theshold = 0.25
                    opened_theshold = 0.3
                else:
                    closed_theshold = 0.17
                    opened_theshold = 0.25

                # list_of_frames.append(eye_ratio)
                # if len(list_of_frames) < 1:
                #     continue

                # total = 0.0
                # for item in list_of_frames:
                #     total += item
                # eye_ratio = total / len(list_of_frames)
                # list_of_frames.clear()

                if not is_blink_time and eye_ratio < closed_theshold:
                    start_time = time.time()
                    emit("GAME", "EC", "Eyes closed", "")
                    is_blink_time = True

                if is_blink_time and eye_ratio > opened_theshold and time.time() - start_time > 0.05:
                    emit("GAME", "EO", "Eyes opened", "")
                    emit("GAME", "D", "Duration", str(time.time() - start_time))
                    is_blink_time = False

            else:
                now = time.monotonic()
                Transparent_screen = np.zeros((h, w, 4), dtype=np.uint8)
                frame_path = output_dir() / "Frame.png"
                if not cap.isOpened():
                    emit("ERROR", "CC", "Camera is closed, cannot write frame, Trying to reopen", "")
                    cap.release()
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    time.sleep(1.5)
                    cap.read()
                try:
                    success = cv2.imwrite(str(frame_path), Transparent_screen)
                except Exception as e:
                    emit("ERROR", "FW", f"Failed writing frame", "{str(e)}")
                if now - last_no_face_log_time >= 1.0:
                    emit("ERROR", "NFF", "No face found", "")
                    last_no_face_log_time = now
                continue

            Update_Frame(bg_screen, visualize_stream)

        cap.release()
        cv2.destroyAllWindows()
        sys.exit()

    finally:
        cap.release()
        cv2.destroyAllWindows()
        sys.exit()



def change_to_BGRA(hex_color):
    r = int(hex_color[1:3], 16)  
    g = int(hex_color[3:5], 16)  
    b = int(hex_color[5:7], 16)  
    a = int(hex_color[7:9], 16)  

    return [b, g, r, a]






def Update_Frame(bg_screen, visualize_stream: bool = False) -> None:
    if not visualize_stream:
        return

    try:
        frame_path = output_dir() / "Frame.png"
        cv2.imwrite(frame_path, bg_screen)
    except Exception as e:
        emit("ERROR", "FNF", "Error in frame overwriting",str(e))



def Show_eyes_0(visualize_stream, frame, bg_screen):
    if not visualize_stream:
        return
    bg_screen[:] = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
    








def Show_eyes_1(left_eye_full, right_eye_full, h, w, bg_screen, face, color_of_r_eye, color_of_l_eye, color_of_r_eye2, color_of_l_eye2, visualize_stream: bool = False):
    if not visualize_stream:
        return

    cl = change_to_BGRA(color_of_l_eye)
    cr = change_to_BGRA(color_of_r_eye)

    for i in left_eye_full:
            lm = face[i]
            px = int(lm.x * w)
            py = int(lm.y * h)
            cv2.circle(bg_screen, (px, py), 2, (cl[0], cl[1], cl[2], cl[3]), -1)

    for i in right_eye_full:
            lm = face[i]
            px = int(lm.x * w)
            py = int(lm.y * h)
            cv2.circle(bg_screen, (px, py), 2, (cr[0], cr[1], cr[2], cr[3]), -1)


    cl2 = change_to_BGRA(color_of_l_eye2)
    cr2 = change_to_BGRA(color_of_r_eye2)

    for i in left_eye_full:
            for ii in left_eye_full:
                lm = face[i]
                px = int(lm.x * w)
                py = int(lm.y * h)

                lm2 = face[ii]
                px2 = int(lm2.x * w)
                py2 = int(lm2.y * h)

                cv2.line(bg_screen, (px, py), (px2, py2), (cl2[0], cl2[1], cl2[2], cl2[3]), 1)

    for i in right_eye_full:
            for ii in right_eye_full:
                lm = face[i]
                px = int(lm.x * w)
                py = int(lm.y * h)

                lm2 = face[ii]
                px2 = int(lm2.x * w)
                py2 = int(lm2.y * h)

                cv2.line(bg_screen, (px, py), (px2, py2), (cr2[0], cr2[1], cr2[2], cr2[3]), 1)


def Show_eyes_2(left_eye_full, right_eye_full, h, w, bg_screen, face, color_of_r_eye, color_of_l_eye, color_of_r_eye2, color_of_l_eye2, visualize_stream: bool = False):
    if not visualize_stream:
        return

    cl = change_to_BGRA(color_of_l_eye)
    cr = change_to_BGRA(color_of_r_eye)
    cl2 = change_to_BGRA(color_of_l_eye2)
    cr2 = change_to_BGRA(color_of_r_eye2)

    for i in left_eye_full:
        lm = face[i]
        px = int(lm.x * w)
        py = int(lm.y * h)
        cv2.circle(bg_screen, (px, py), 10, (cl[0], cl[1], cl[2], cl[3]), -1)
        cv2.circle(bg_screen, (px, py), 5, (cl2[0], cl2[1], cl2[2], cl2[3]), -1)

    for i in right_eye_full:
        lm = face[i]
        px = int(lm.x * w)
        py = int(lm.y * h)
        cv2.circle(bg_screen, (px, py), 10, (cr[0], cr[1], cr[2], cr[3]), -1)
        cv2.circle(bg_screen, (px, py), 5, (cr2[0], cr2[1], cr2[2], cr2[3]), -1)

def Show_eyes_3(left_eye_full, right_eye_full, h, w, bg_screen, face,color_of_r_eye, color_of_l_eye, visualize_stream):
    if not visualize_stream:
        return

    cl = change_to_BGRA(color_of_l_eye)
    cr = change_to_BGRA(color_of_r_eye)

    for i in left_eye_full:
        lm = face[i]
        px = int(lm.x * w)
        py = int(lm.y * h)
        cv2.circle(bg_screen, (px, py), 1, (cl[0], cl[1], cl[2], cl[3]), -1)

    for i in right_eye_full:
        lm = face[i]
        px = int(lm.x * w)
        py = int(lm.y * h)
        cv2.circle(bg_screen, (px, py), 1, (cr[0], cr[1], cr[2], cr[3]), -1)







def runtime_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                return Path(sys._MEIPASS)
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except Exception as error:
        emit("ERROR", "RDIR", "Cannot retrieve any type of runtime path", str(error))

def output_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except Exception as error:
        emit("ERROR", "ODIR", "Cannot retrieve any type of runtime path even outside the python file", str(error))



# def fix_broken_camera():
#     global cap
#     if not cap.isOpened():
#         cap.release()
#         cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#         time.sleep(1.5)
#         cap.read()





if __name__ == "__main__":
    main()
