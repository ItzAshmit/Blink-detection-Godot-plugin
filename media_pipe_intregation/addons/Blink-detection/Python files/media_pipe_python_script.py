import time
import sys
from pathlib import Path

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

except ImportError as e:
    print("ERROR:MIE ",": ","Import error occurred, Mediapipe library is not installed.", flush=True)
    sys.exit(1)



try:
    import cv2
except ImportError as e:
    print("ERROR:CV2IE ",": ","Import error occurred, OpenCV library is not installed.", flush=True)
    sys.exit(1)



def main():
    sys.argv
    if len(sys.argv) > 2:
        if sys.argv[2] in ["True", "true", "1"]:
            should_show_camera = True
        else:
            should_show_camera = False
    blink_detection(float(sys.argv[1]) if len(sys.argv) > 1 else 0.2, should_show_camera)


paused:bool = False

def pause(result:bool):
    global paused
    paused = result
    print("GAME:P ",": " ,"Game Paused", paused, flush=True)




def blink_detection(theshold:float = 0.2, should_show_camera:bool = False):
    print("GAME:STR ",": ","Starting blink detection with threshold (", theshold, ") and should_show_camera (", should_show_camera, ")", flush=True)

    cap = cv2.VideoCapture(0)
    print("GAME:C ",": ","Camera opened: ", cap.isOpened(), flush=True)
    if not cap.isOpened():
        print("ERROR:COC",": ","Cannot open camera", flush=True)
        return

    try:
        model_path = Path(__file__).resolve().parent / "face_landmarker.task"
        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1
        )

        landmarker = vision.FaceLandmarker.create_from_options(options)
    except Exception as e:
        print("ERROR:MLC ",": ","Model loading failed with error:", str(e), flush=True)
        return



    LEFT_EYE_FULL = [33, 160, 158, 133, 153, 144]

    RIGHT_EYE_FULL = [362, 385, 387, 263, 373, 380]

    end_time = 0.0
    start_time = 0.0
    is_blink_time:bool = False


    while True:

        if paused:
            time.sleep(0.1)
            continue

        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        h, w, _ = frame.shape

        result = landmarker.detect(mp_image)
        if result.face_landmarks:
            face = result.face_landmarks[0]

            if should_show_camera:
                for i in LEFT_EYE_FULL + RIGHT_EYE_FULL:
                    lm = face[i]
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    cv2.circle(frame, (px, py), 2, (0, 255, 0), -1)


            left_eye_width = abs(face[33].x - face[133].x)
            left_eye_y_gap = (abs(face[160].y - face[153].y) + abs(face[158].y - face[144].y)) / 2
            left_eye_ratio = left_eye_y_gap/left_eye_width

            right_eye_width = abs(face[362].x - face[263].x)
            right_eye_y_gap = (abs(face[385].y - face[373].y) + abs(face[387].y - face[380].y)) / 2
            right_eye_ratio = right_eye_y_gap/right_eye_width

            eye_ratio = (left_eye_ratio + right_eye_ratio)/2

            if not is_blink_time:
                if eye_ratio < theshold:
                    start_time = time.time()
                    print("GAME:EC ",": ","Eyes closed", flush=True)
                    is_blink_time = True


            if is_blink_time:
                if eye_ratio > theshold:
                    print("GAME:EO ",": ","Eyes opened", flush=True)
                    end_time = time.time()
                    print("GAME:D ",": ","Duration: ", str(end_time - start_time), flush=True)
                    is_blink_time = False
        
        else:
            print("ERROR:NFF",": ","No face found.", flush=True)
            continue

        if should_show_camera:
            cv2.imshow("Camera Test", frame)
            cv2.waitKey(1)



    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()