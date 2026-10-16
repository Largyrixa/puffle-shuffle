import math
import time

import cv2
import mss
import numpy as np
import pyautogui as pg

cv2.setUseOptimized(True)

def configure_roi():
    with mss.MSS() as sct:
        monitor_principal = sct.monitors[1]
        screenshot = sct.grab(monitor_principal)
        frame_bgra = np.array(screenshot)
        frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

    instrucao = "Desenhe um retangulo para que a linha do meio fique no meio dos chapeus e aperte ENTER."
    cv2.putText(frame, instrucao, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    roi = cv2.selectROI("Configuracao", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Configuracao")

    if roi == (0, 0, 0, 0):
        return None

    x, y, w, h = roi
    return {"top": y, "left": x, "width": w, "height": h}

RED_THRESH = 100
def get_hats_centers(red_ch):
    hats_idx = np.where(red_ch[0] > RED_THRESH)[0]
    centers_x = []
    if len(hats_idx) > 0:
        groups = np.split(hats_idx, np.where(np.diff(hats_idx) > 2)[0] + 1)
        for group in groups:
            center = (group[-1] + group[0]) // 2
            centers_x.append(center)

    return centers_x

def main():
    monitor = configure_roi()
    if not monitor:
        return

    # Configuração para capturar uma unica linha
    monitor['top'] += monitor["height"] // 2
    monitor['height'] = 1

    print("Iniciando captura... Pressione 'q' na janela do OpenCV para sair.")

    # Variáveis de rastreamento
    hats_pos = [0, 0, 0]

    running = True
    with mss.MSS() as sct:
        while running:
            red_ch = np.array(sct.grab(monitor))[:, :, 2]

            frame = cv2.cvtColor(red_ch, cv2.COLOR_GRAY2BGR)
            frame = cv2.resize(frame, (monitor['width'], 100))

            hats_idx = get_hats_centers(red_ch)

            for x in hats_idx:
                cv2.circle(frame, (x, 50), 8, (0, 255, 0), -1)

            cv2.imshow("Scanner Linear", frame)

            key = cv2.waitKey(1) & 0xFF
            # if key == ord('o'):
            #     cur = 256
            #     for x in red_ch[0]:
            #         if x != cur:
            #             cur = x
            #             print(cur, end=' ')
            #     print(end='\r')
            if key == ord('q'):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
