import os
import platform
import sys
import time
from pathlib import Path


def emit(message_type: str, code: str, detail: str, extra: str | None = None) -> None:
    line = f"{message_type}:{code}:{detail}"
    if extra is not None:
        line += f":{extra}"

    print(line, flush=True)


try:
    import numpy as np
except ImportError:
    emit("ERROR", "NIE", "Import error occurred, Numpy library is not installed.")
    sys.exit(1)


try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ImportError:
    emit("ERROR", "MIE", "Import error occurred, Mediapipe library is not installed.")
    sys.exit(1)


try:
    import cv2
except ImportError:
    emit("ERROR", "CV2IE", "Import error occurred, OpenCV library is not installed.")
    sys.exit(1)


paused: bool = False


def main() -> None:

    is_debug_build = sys.argv[3] if len(sys.argv) > 3 else "false"
    visualize_stream = sys.argv[4] if len(sys.argv) > 4 else "false"
    if is_debug_build.lower() == "true":
        is_debug_build = True
    else:
        is_debug_build = False

    if visualize_stream.lower() == "true":
        visualize_stream = True
    else:
        visualize_stream = False


    blink_detection(
        float(sys.argv[1]) if len(sys.argv) > 1 else 0.13,
        float(sys.argv[2]) if len(sys.argv) > 2 else 0.25,
        is_debug_build,
        visualize_stream
    )


def pause(result: bool) -> None:
    global paused
    paused = result
    emit("GAME", "P", f"Game Paused {paused}")


def blink_detection(
    closed_theshold: float = 0.1,
    opened_theshold: float = 0.3,
    is_debuged: bool = False,
    visualize_stream: bool = False
) -> None:
    
    emit(
        "GAME",
        "STR",
        f"Starting blink detection with closed threshold ({closed_theshold}), opened threshold ({opened_theshold}) and is_debug_build ({is_debuged})",
    )
    if platform.system() == "Windows":
        for i in range(5):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if cap.isOpened():
                break
            time.sleep(1.0)
    else:
        cap = cv2.VideoCapture(0)
        emit("ERROR", "NW", "The detected OS is not Windows, For now the plugin only supports Windows. The game may crash")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    emit("GAME", "C", f"Camera opened: {cap.isOpened()}")

    if not cap.isOpened():
        emit("ERROR", "COC", "Cannot open camera")
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
        emit("ERROR", "MLC", f"Model loading failed with error - {str(e)}")
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
                emit("GAME", "P", "Game is paused, skipping frame processing")
                continue

            ret, frame = cap.read()
            if not ret:
                emit("ERROR", "CRF", "Camera frame read failed")
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            h, w, _ = frame.shape
            frame_timestamp_ms = int(time.monotonic() * 1000)
            result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)

            black_screen = np.zeros((h, w, 4), dtype=np.uint8)
            if result.face_landmarks:
                face = result.face_landmarks[0]

                
                Show_eyes(left_eye_full, right_eye_full, h, w, black_screen, face, visualize_stream)

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

                list_of_frames.append(eye_ratio)
                if len(list_of_frames) < 1:
                    continue

                total = 0.0
                for item in list_of_frames:
                    total += item
                eye_ratio = total / len(list_of_frames)
                list_of_frames.clear()

                if not is_blink_time and eye_ratio < closed_theshold:
                    start_time = time.time()
                    emit("GAME", "EC", "Eyes closed")
                    is_blink_time = True

                if is_blink_time and eye_ratio > opened_theshold and time.time() - start_time > 0.05:
                    emit("GAME", "EO", "Eyes opened")
                    emit("GAME", "D", "Duration", str(time.time() - start_time))
                    is_blink_time = False

            else:
                now = time.monotonic()
                black_screen2 = np.zeros((h, w, 4), dtype=np.uint8)
                frame_path = output_dir() / "Frame.png"
                if not cap.isOpened():
                    emit("ERROR", "CC", "Camera is closed, cannot write frame, Trying to reopen")
                    cap.release()
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    time.sleep(1.5)
                    cap.read()
                try:
                    success = cv2.imwrite(str(frame_path), black_screen2)
                except Exception as e:
                    emit("ERROR", "FW", f"Failed writing frame: {str(e)}")
                if now - last_no_face_log_time >= 1.0:
                    emit("ERROR", "NFF", "No face found.")
                    last_no_face_log_time = now
                continue

            Update_Frame(black_screen, visualize_stream)

        cap.release()
        cv2.destroyAllWindows()
        sys.exit()

    finally:
        cap.release()
        cv2.destroyAllWindows()
        sys.exit()


def Update_Frame(black_screen, visualize_stream: bool = False) -> None:
    if not visualize_stream:
        return

    try:
        frame_path = output_dir() / "Frame.png"
        cv2.imwrite(frame_path, black_screen)
    except Exception as e:
        emit("ERROR", "FNF", f"{str(e)}")


def Show_eyes(left_eye_full, right_eye_full, h, w, black_screen, face, visualize_stream: bool = False) -> None:
    if not visualize_stream:
        return

    for i in left_eye_full + right_eye_full:
            lm = face[i]
            px = int(lm.x * w)
            py = int(lm.y * h)
            cv2.circle(black_screen, (px, py), 2, (0, 0, 255, 180), -1)

    for i in left_eye_full:
            for ii in left_eye_full:
                lm = face[i]
                px = int(lm.x * w)
                py = int(lm.y * h)

                lm2 = face[ii]
                px2 = int(lm2.x * w)
                py2 = int(lm2.y * h)

                cv2.line(black_screen, (px, py), (px2, py2), (0.0, 0.0, 150.0, 255), 1)

    for i in right_eye_full:
            for ii in right_eye_full:
                lm = face[i]
                px = int(lm.x * w)
                py = int(lm.y * h)

                lm2 = face[ii]
                px2 = int(lm2.x * w)
                py2 = int(lm2.y * h)

                cv2.line(black_screen, (px, py), (px2, py2), (0.0, 0.0, 255.0, 255), 1)




def runtime_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                return Path(sys._MEIPASS)
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except:
        emit("ERROR", "RDIR", "Cannot retrieve any type of runtime path")

def output_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    except:
        emit("ERROR", "ODIR", "Cannot retrieve any type of runtime path even outside the python file")



# def fix_broken_camera():
#     global cap
#     if not cap.isOpened():
#         cap.release()
#         cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#         time.sleep(1.5)
#         cap.read()





if __name__ == "__main__":
    main()
