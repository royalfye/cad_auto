import os
import psutil
import pygetwindow as gw
import time
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CADAutomationBot:
    def __init__(self):
        self.cad_title = "CAD - Solução de Controle do Atendimento e Despacho de Emergência Policial e de Bombeiros"
        self.excel_process = "EXCEL.EXE"

    def close_excel_processes(self) -> int:
        closed_count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].upper() == self.excel_process:
                    proc.terminate()
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if closed_count > 0:
            logging.info(f"Cleaned up {closed_count} Excel process(es).")
        return closed_count

    def focus_cad_window(self) -> bool:

        try:
            windows = gw.getWindowsWithTitle(self.cad_title)
            
            if not windows:
                logging.warning(f"Window not found: {self.cad_title}")
                return False
            
            cad_window = windows[0]

            if cad_window.isMinimized:
                cad_window.restore()
            
            cad_window.activate()
            logging.info("CAD window is now focused and active.")
            return True

        except Exception as e:
            logging.error(f"Failed to focus CAD window: {e}")
            return False

    def prepare_environment(self):

        self.close_excel_processes()
        time.sleep(1) 
        
        if self.focus_cad_window():
            logging.info("Environment ready for data extraction.")
            return True
        else:
            logging.error("Environment preparation failed: CAD not found.")
            return False

if __name__ == "__main__":
    bot = CADAutomationBot()
    bot.prepare_environment()