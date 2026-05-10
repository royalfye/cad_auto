import time
import logging
import numpy as np
from PIL import ImageGrab
from PySide6.QtCore import QThread, Signal
from pynput import mouse, keyboard
import pyautogui
import os

class SentinelWorker(QThread):
    new_occurrence_detected = Signal()
    finished_by_user = Signal(str)

    def __init__(self, monitor_region=None):
        super().__init__()
        self.monitor_region = monitor_region
        self.is_running = True
        self.last_screenshot = None
        
        # Define o caminho da âncora de forma absoluta para não ter erro de pasta
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.anchor_path = os.path.join(base_path, "assets", "images", "cad_targets", "11_call_number_ref.png")

        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.key_listener = keyboard.Listener(on_press=self._on_key_press)

    def _on_mouse_move(self, x, y):
        if self.is_running:
            self.stop("Movimento do mouse")

    def _on_key_press(self, key):
        if key == keyboard.Key.esc:
            self.stop("Tecla ESC")

    def stop(self, reason="Solicitado"):
        self.is_running = False
        if self.mouse_listener.running: self.mouse_listener.stop()
        if self.key_listener.running: self.key_listener.stop()
        self.finished_by_user.emit(reason)

    def run(self):
        self.mouse_listener.start()
        self.key_listener.start()
        
        logging.info(f"🛰️ Buscando âncora em: {self.anchor_path}")

        # Tenta localizar a âncora sem travar o programa
        try:
            # confidence 0.7 é mais tolerante para diferentes monitores
            anchor_loc = pyautogui.locateOnScreen(self.anchor_path, confidence=0.7)
        except Exception:
            anchor_loc = None

        if anchor_loc:
            ax, ay, aw, ah = anchor_loc
            self.monitor_region = (ax - 10, ay + ah, aw + 40, 600)
            logging.info(f"🎯 Área calibrada automaticamente: {self.monitor_region}")
        else:
            logging.error("❌ Âncora não encontrada. O CAD está na tela de chamadas?")
            self.stop("Erro de calibração: Âncora não encontrada")
            return

        while self.is_running:
            try:
                # Captura da tela
                current_img = ImageGrab.grab(bbox=(
                    self.monitor_region[0], 
                    self.monitor_region[1], 
                    self.monitor_region[0] + self.monitor_region[2], 
                    self.monitor_region[1] + self.monitor_region[3]
                )).convert('L')
                
                img_np = np.array(current_img)

                if self.last_screenshot is not None:
                    diff = np.sum(np.abs(img_np.astype(int) - self.last_screenshot.astype(int)))
                    
                    # Se houver mudança (número novo ou bolinha mudando de cor)
                    if diff > 150000: 
                        logging.info(f"🔔 Mudança detectada (Diff: {diff})")
                        self.new_occurrence_detected.emit()
                        time.sleep(15) # Pausa longa para o robô de extração agir

                self.last_screenshot = img_np
                
                # Intervalo de verificação suave
                for _ in range(20): 
                    if not self.is_running: break
                    time.sleep(0.1)

            except Exception as e:
                logging.error(f"Erro no loop: {e}")
                break