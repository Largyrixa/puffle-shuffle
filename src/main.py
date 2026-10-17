import math
import time

import cv2
import mss
import numpy as np
from numpy.ma.core import true_divide
import pyautogui as pg

cv2.setUseOptimized(True)

def configure_roi():
    with mss.MSS() as sct:
        monitor_principal = sct.monitors[1]
        screenshot = sct.grab(monitor_principal)
        frame_bgra = np.array(screenshot)
        frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

    instrucao = "Desenhe um retangulo para que a linha do meio fique na parte vermelha dos chapeus e aperte ENTER."
    cv2.putText(frame, instrucao, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    roi = cv2.selectROI("Configuracao", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Configuracao")

    if roi == (0, 0, 0, 0):
        return None

    x, y, w, h = roi
    return {"top": y, "left": x, "width": w, "height": h}

RED_THRESH = 100
MOVE_THRESH = 10

def get_hats_centers(red_ch):
    hats_idx = np.where(red_ch[0] > RED_THRESH)[0]
    centers_x = []
    if len(hats_idx) > 0:
        groups = np.split(hats_idx, np.where(np.diff(hats_idx) > 2)[0] + 1)
        for group in groups:
            center = (group[-1] + group[0]) // 2
            centers_x.append(center)

    return sorted(centers_x)

def main():
    monitor = configure_roi()
    if not monitor:
        return

    # Configuração para capturar uma unica linha
    monitor['top'] += monitor["height"] // 2
    monitor['height'] = 1

    print("Iniciando captura... Pressione 'q' na janela do OpenCV para sair.")

    running = True
    with mss.MSS() as sct:
        print("Capturando as posições iniciais...")

        red_ch = np.array(sct.grab(monitor))[:, :, 2]
        last_x = get_hats_centers(red_ch)
        while len(last_x) != 3:
            time.sleep(0.1)
            red_ch = np.array(sct.grab(monitor))[:, :, 2]
            last_x = get_hats_centers(red_ch)
        initial_dist = [
            last_x[1] - last_x[0],
            last_x[2] - last_x[0],
            last_x[2] - last_x[1],
        ]
        # Lista simples mantendo a ordem física atual (esquerda, meio, direita)
        hats_ids = [0, 1, 2]
        is_overlapping = False

        while running:
            red_ch = np.array(sct.grab(monitor))[:, :, 2]

            frame = cv2.cvtColor(red_ch, cv2.COLOR_GRAY2BGR)
            frame = cv2.resize(frame, (monitor['width'], 100))
            _, frame = cv2.threshold(frame, RED_THRESH, 255, cv2.THRESH_BINARY)

            hats_idx = get_hats_centers(red_ch)

            if len(hats_idx) == 3:
                if is_overlapping:
                    dist_0_1 = last_x[1] - last_x[0]
                    dist_0_2 = last_x[2] - last_x[0]
                    dist_1_2 = last_x[2] - last_x[1]
                    if dist_0_1 < initial_dist[0]:
                        # 0 <-> 1
                        hats_ids[0], hats_ids[1] = hats_ids[1], hats_ids[0]
                    elif dist_0_2 < initial_dist[1]:
                        # 0 <-> 2
                        hats_ids[0], hats_ids[2] = hats_ids[2], hats_ids[0]
                    elif dist_1_2 < initial_dist[2]:
                        # 1 <-> 2
                        hats_ids[1], hats_ids[2] = hats_ids[2], hats_ids[1]

                    is_overlapping = False

                last_x = hats_idx

                for i, x in enumerate(hats_idx):
                    cv2.putText(frame, str(hats_ids[i]), (x - 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.circle(frame, (x, 50), 8, (0, 255, 0), -1)

                cv2.imshow("Scanner Linear", frame)
            else:
                is_overlapping = True
                cv2.putText(frame, "OVERLAPPING...", (0, 0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
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
