import os
from pathlib import Path
import time
import logging
import psutil
import pygetwindow as gw
import pyautogui

# --- GLOBAL CONFIGURATION (PEP 8) ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CADAutomationBot:
    def __init__(self):
        self.cad_title = "CAD - Solução de Controle do Atendimento e Despacho de Emergência Policial e de Bombeiros"
        self.excel_process = "EXCEL.EXE"
        
        # Path configuration for assets
        self.assets_path = Path(__file__).resolve().parent.parent.parent / "assets" / "images" / "cad_targets"
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def check_passos_filter(self) -> bool:
        """
        Searches for the 'Passos Filter' reference image on the screen.
        Returns:
            bool: True if found, False otherwise.
        """
        target_image = str(self.assets_path / "01_filter_passos_active.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Reference image not found at: {target_image}")
            return False

        try:
            # confidence=0.9 requires opencv-python. 
            # It allows 10% of variation (anti-aliasing, etc)
            location = pyautogui.locateOnScreen(target_image, confidence=0.9)
            
            if location:
                logging.info("Filter 'PASSOS' is correctly selected.")
                return True
            
            logging.warning("Filter 'PASSOS' NOT detected on screen.")
            return False

        except Exception as e:
            logging.error(f"Error during image recognition: {e}")
            return False
        
    def close_excel_processes(self) -> int:
        """
        Forcefully terminates any running Excel instances to prevent file locks.
        Returns:
            int: Number of closed processes.
        """
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
        """
        Locates, restores, maximizes, and brings the CAD window to the foreground.
        Uses Alt-key precedence to bypass Windows Foreground Lock.
        """
        try:
            windows = gw.getWindowsWithTitle(self.cad_title)
            
            if not windows:
                logging.warning(f"Window not found: {self.cad_title}")
                return False
            
            cad_window = windows[0]

            # 1. Handle Minimized State
            if cad_window.isMinimized:
                logging.info("CAD window is minimized. Restoring...")
                cad_window.restore()
                time.sleep(0.5)

            # 2. Handle Maximize State (with Error 0 suppression)
            if not cad_window.isMaximized:
                try:
                    cad_window.maximize()
                    time.sleep(0.5)
                except Exception as e:
                    if "Error code 0" not in str(e):
                        logging.debug(f"Maximize adjustment info: {e}")

            # 3. Force Foreground Focus
            # We send an 'Alt' key press to signal Windows that a focus change is coming
            pyautogui.press('alt')
            
            try:
                cad_window.activate()
                logging.info("CAD window activated.")
            except Exception as e:
                # If activate still fails to bring it front, we try a fallback click
                if "Error code 0" in str(e):
                    logging.info("CAD window was already focused.")
                else:
                    logging.warning(f"Focus challenge detected, using fallback click: {e}")
                    # Clicks on the top bar (X: 100px from left, Y: 10px from top)
                    pyautogui.click(cad_window.left + 100, cad_window.top + 10)

            logging.info("CAD window is now focused and in foreground.")
            return True

        except Exception as e:
            logging.error(f"Critical failure during window focusing: {e}")
            return False
        
    def click_calls_button(self) -> bool:
        """
        Searches for the calls button (02_chamadas_button.png) and clicks it.
        Returns:
            bool: True if clicked successfully, False otherwise.
        """
        target_image = str(self.assets_path / "02_chamadas_button.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Image not found: {target_image}")
            return False

        try:
            # Localiza o centro da imagem na tela
            button_location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            
            if button_location:
                pyautogui.click(button_location)
                logging.info("Calls button (02) clicked successfully.")
                return True
            
            logging.warning("Calls button (02) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error clicking calls button: {e}")
            return False
        
    def click_search_button(self) -> bool:
        """
        Locates and clicks the search tool button (03_pesquisa_button.png).
        Returns:
            bool: True if clicked, False otherwise.
        """
        target_image = str(self.assets_path / "03_pesquisa_button.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Image not found: {target_image}")
            return False

        try:
            # Procuro o botão de pesquisa
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            
            if location:
                pyautogui.click(location)
                logging.info("Search button (03) clicked successfully.")
                return True
            
            logging.warning("Search button (03) not found.")
            return False

        except Exception as e:
            logging.error(f"Error clicking search button: {e}")
            return False
    
    def click_classified_button(self) -> bool:
        """
        Locates and clicks the 'Classificadas' button (04_classificadas_button.png).
        This usually filters for already classified/closed occurrences.
        Returns:
            bool: True if clicked, False otherwise.
        """
        target_image = str(self.assets_path / "04_classificadas_button.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Image not found: {target_image}")
            return False

        try:
            # Busca o botão de ocorrências classificadas
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            
            if location:
                pyautogui.click(location)
                logging.info("Classified button (04) clicked successfully.")
                return True
            
            logging.warning("Classified button (04) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error clicking classified button: {e}")
            return False
        
    def click_last_24h_button(self) -> bool:
        """
        Locates and clicks the 'Last 24 Hours' filter button (05).
        Returns:
            bool: True if clicked, False otherwise.
        """
        target_image = str(self.assets_path / "05_ultimas_24_button.png")
        if not os.path.exists(target_image):
            logging.error(f"Image not found: {target_image}")
            return False

        try:
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            if location:
                pyautogui.click(location)
                logging.info("Last 24h button (05) clicked.")
                return True
            return False
        except Exception as e:
            logging.error(f"Error clicking button 05: {e}")
            return False

    def click_last_3_months_button(self) -> bool:
        """
        Locates and clicks the 'Last 3 Months' filter button (06).
        Returns:
            bool: True if clicked, False otherwise.
        """
        target_image = str(self.assets_path / "06_ultimos_3_button.png")
        if not os.path.exists(target_image):
            logging.error(f"Image not found: {target_image}")
            return False

        try:
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            if location:
                pyautogui.click(location)
                logging.info("Last 3 months button (06) clicked.")
                return True
            return False
        except Exception as e:
            logging.error(f"Error clicking button 06: {e}")
            return False
        
    def filter_by_city_name(self, city_name: str = "passos") -> bool:
        """
        Clicks the city filter field (07), types the city name, 
        and clicks the confirmation button (08).
        """
        # Paths for the images
        img_field = str(self.assets_path / "07_filtro_passos.button.png")
        img_confirm = str(self.assets_path / "08_passos_button.png")

        try:
            # Step 07: Click the filter field
            field_loc = pyautogui.locateCenterOnScreen(img_field, confidence=0.9)
            if not field_loc:
                logging.warning("City filter field (07) not found.")
                return False
            
            pyautogui.click(field_loc)
            time.sleep(0.5) # Wait for focus
            
            # Type the city name
            pyautogui.write(city_name, interval=0.1)
            logging.info(f"Typed city: {city_name}")
            time.sleep(0.5)

            # Step 08: Click the confirmation button
            confirm_loc = pyautogui.locateCenterOnScreen(img_confirm, confidence=0.9)
            if not confirm_loc:
                logging.warning("City confirmation button (08) not found.")
                return False
            
            pyautogui.click(confirm_loc)
            logging.info("City filter confirmed (08).")
            return True

        except Exception as e:
            logging.error(f"Error during city filtering: {e}")
            return False
        
    def click_export_button(self) -> bool:
        """
        Locates and clicks the 'Export' button (09).
        This action typically triggers the file saving dialog.
        Returns:
            bool: True if clicked, False otherwise.
        """
        target_image = str(self.assets_path / "09_exportar_button.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Export image not found: {target_image}")
            return False

        try:
            # Locate the export button
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
            
            if location:
                pyautogui.click(location)
                logging.info("Export button (09) clicked successfully.")
                return True
            
            logging.warning("Export button (09) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error while clicking export button: {e}")
            return False
        

    def prepare_environment(self) -> bool:
        """
        Main orchestration for setting up the environment.
        1. Closes Excel.
        2. Focusses and Maximizes CAD.
        """
        self.close_excel_processes()
        time.sleep(1) # Wait for OS process release
        
        if self.focus_cad_window():
            logging.info("Environment preparation successful.")
            return True
        
        logging.error("Environment preparation failed.")
        return False

# --- ENTRY POINT ---
if __name__ == "__main__":
    bot = CADAutomationBot()
    bot.prepare_environment()