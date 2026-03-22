import time
import logging
import numpy as np
from PIL import ImageGrab
from PySide6.QtCore import QThread, Signal
from pynput import mouse, keyboard

class SentinelWorker(QThread):
    """
    Trabalhador em segundo plano que monitora a tela do CAD.
    Emite um sinal sempre que detecta uma mudança visual (Nova Ocorrência).
    """
    new_occurrence_detected = Signal()
    finished_by_user = Signal(str) # Mensagem de por que parou

    def __init__(self, monitor_region: tuple):
        super().__init__()
        self.monitor_region = monitor_region # (x, y, width, height)
        self.is_running = True
        self.last_screenshot = None
        
        # Listeners para o Kill-Switch (Parada de Emergência)
        self.mouse_listener = mouse.Listener(on_move=self._on_mouse_move)
        self.key_listener = keyboard.Listener(on_press=self._on_key_press)

    def _on_mouse_move(self, x, y):
        # Se o usuário mexer o mouse bruscamente, paramos tudo por segurança
        # (Lógica simplificada: qualquer movimento para o monitoramento)
        if self.is_running:
            logging.info("🛑 Movimento de mouse detectado. Parando Sentinela.")
            self.stop("Movimento do mouse")

    def _on_key_press(self, key):
        if key == keyboard.Key.esc:
            logging.info("🛑 Tecla ESC pressionada. Parando Sentinela.")
            self.stop("Tecla ESC")

    def stop(self, reason="Solicitado"):
        self.is_running = False
        self.mouse_listener.stop()
        self.key_listener.stop()
        self.finished_by_user.emit(reason)

    def run(self):
        self.mouse_listener.start()
        self.key_listener.start()
        
        logging.info("🛰️ Monitoramento iniciado...")

        while self.is_running:
            # 1. Tira print da região onde as ocorrências aparecem no CAD
            current_img = ImageGrab.grab(bbox=(
                self.monitor_region[0], 
                self.monitor_region[1], 
                self.monitor_region[0] + self.monitor_region[2], 
                self.monitor_region[1] + self.monitor_region[3]
            )).convert('L') # Escala de cinza para ser mais rápido
            
            img_np = np.array(current_img)

            # 2. Compara com o último print
            if self.last_screenshot is not None:
                # Calcula a diferença entre as imagens
                diff = np.sum(np.abs(img_np.astype(int) - self.last_screenshot.astype(int)))
                
                # Sensibilidade: se mudar mais que X pixels (ajustável)
                if diff > 100000: # Valor de teste, precisaremos calibrar
                    logging.info(f"🔔 Mudança detectada no CAD! Diferença: {diff}")
                    self.new_occurrence_detected.emit()
                    # Aguarda um pouco para não disparar duplicado
                    time.sleep(5) 

            self.last_screenshot = img_np
            time.sleep(2) # Intervalo de varredura (2 segundos é ideal para não pesar)

        logging.info("🛰️ Monitoramento encerrado.")