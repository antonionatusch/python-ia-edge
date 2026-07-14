import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands  # pyright: ignore[reportAttributeAccessIssue]
mp_draw = mp.solutions.drawing_utils  # pyright: ignore[reportAttributeAccessIssue]


def contar_dedos(hand_landmarks, handedness):
    lm = hand_landmarks.landmark
    dedos = 0
    if handedness == "Right":
        if lm[4].x < lm[3].x:
            dedos += 1
    else:
        if lm[4].x > lm[3].x:
            dedos += 1
    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if lm[tip].y < lm[pip].y:
            dedos += 1
    return dedos


def detectar_gesto_mp(hand_landmarks, handedness):
    lm = hand_landmarks.landmark
    cx = lm[9].x
    dedos = contar_dedos(hand_landmarks, handedness)
    if cx < 0.35:
        return "IZQUIERDA"
    elif cx > 0.65:
        return "DERECHA"
    elif dedos == 0:
        return "PUÑO"
    elif dedos == 5:
        return "ABRIR"
    else:
        return "NINGUNO"


def run_vision():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    with mp_hands.Hands(
        max_num_hands=1, min_detection_confidence=0.75, min_tracking_confidence=0.5
    ) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame_rgb)

            gesto = "NINGUNO"
            dedos = 0

            if results.multi_hand_landmarks:
                hlm = results.multi_hand_landmarks[0]
                hinfo = results.multi_handedness[0]
                side = hinfo.classification[0].label

                mp_draw.draw_landmarks(frame, hlm, mp_hands.HAND_CONNECTIONS)

                dedos = contar_dedos(hlm, side)
                gesto = detectar_gesto_mp(hlm, side)

            cv2.putText(
                frame,
                f"Gesto: {gesto}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Dedos: {dedos}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )

            cv2.imshow("Deteccion de Dedos - MP", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_vision()
