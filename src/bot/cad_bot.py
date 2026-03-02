import os
import time
import logging
import psutil
import pygetwindow as gw
import pyautogui
import win32com.client
import win32gui
import win32con
import pythoncom
from pathlib import Path
from datetime import datetime

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CADAutomationBot:
    def __init__(self):
        self.bot_dir = Path(__file__).resolve().parent
        self.project_root = self.bot_dir.parent.parent
        self.assets_path = self.project_root / "assets" / "images" / "cad_targets"
        
        self.cad_title = "CAD - Solução de Controle do Atendimento e Despacho de Emergência Policial e de Bombeiros"
        self.excel_process = "EXCEL.EXE"
        
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.2

    def _log_status(self, ui_status, message=None):
    # Lógica inteligente para detectar se você esqueceu o ui_status
        if message is None:
            message = ui_status  # O texto estava no primeiro parâmetro
            ui_status = None     # Não temos objeto de UI nesse caso
    
    # 1. Sempre loga no terminal (Bom para debug)
        logging.info(message) 
        
        # 2. Se tiver UI (Streamlit), tenta escrever nela
        if ui_status is not None:
            if hasattr(ui_status, 'write'):
                ui_status.write(message)

    def run_full_extraction_flow(self, bronze_root: Path, ui_status=None) -> bool:
        try:
            self._log_status(ui_status, "🧹 Encerrando instâncias do Excel...")
            self.close_excel_processes()
            
            self._log_status(ui_status, "🔍 Localizando janela do CAD...")
            if not self.focus_cad_window(): return False
            
            self._log_status(ui_status, "✅ Verificando filtros iniciais...")
            if not self.check_passos_filter(): return False
            
            self._log_status(ui_status, "🖱️ Navegando pelos módulos...")
            if not self.click_calls_button(): return False
            time.sleep(1)
            
            if not self.click_search_button(): return False
            if not self.click_classified_button(): return False
            if not self.click_last_24h_button(): return False
            if not self.click_last_3_months_button(): return False
            
            self._log_status(ui_status, "✍️ Filtrando cidade: Passos...")
            if not self.filter_by_city_name("passos"): return False

            self._log_status(ui_status, "📤 Exportando para Excel...")
            if not self.click_export_button(): return False

            self._log_status(ui_status, "💾 Capturando dados do Excel via COM...")
            if not self.save_excel_export(bronze_root, extraction_type="historical"):
                return False
            
            self._log_status(ui_status, "🧹 Limpando janelas residuais...")
            self.close_search_subwindow()
            self.focus_cad_window()
            return True

        except Exception as e:
            logging.error(f"Critical error in historical extraction flow: {e}")
            return False
        
    def run_active_extraction_flow(self, bronze_root: Path, ui_status=None) -> bool:
        try:
            self._log_status(ui_status, "🧹 Encerrando instâncias do Excel...")
            self.close_excel_processes()

            self._log_status(ui_status, "🔍 Localizando janela do CAD...")
            if not self.focus_cad_window(): return False

            self._log_status(ui_status, "✅ Verificando filtros iniciais...")
            if not self.check_passos_filter(): return False

            self._log_status(ui_status, "🖱️ Navegando pelos módulos...")
            if not self.click_calls_button(): return False
            time.sleep(1)
            
            if not self.click_search_button(): return False
            if not self.click_active_button(): return False
            
            self._log_status(ui_status, "✍️ Filtrando cidade: Passos...")
            if not self.filter_by_city_name("passos"): return False
            
            self._log_status(ui_status, "📤 Exportando chamadas ativas...")
            if not self.click_export_button(): return False

            if not self.save_excel_export(bronze_root, extraction_type="active"):
                return False
            
            self._log_status(ui_status, "🧹 Limpando janelas residuais...")
            self.close_search_subwindow()
            self.focus_cad_window()
            return True
        except Exception as e:
            logging.error(f"Error in active flow: {e}")
            return False
        
    def run_active_extraction_flow(self, bronze_root: Path, ui_status) -> bool:
        """
        Orchestrates the RPA sequence for ACTIVE (real-time) calls.
        """
        try:
            self._log_status("🧹 Encerrando instâncias do Excel...")
            self.close_excel_processes()

            self._log_status("🔍 Localizando janela do CAD...")
            if not self.focus_cad_window():
                return False

            self._log_status("✅ Verificando filtros iniciais...")
            if not self.check_passos_filter():
                return False

            self._log_status("🖱️ Navegando pelos módulos...")
            if not self.click_calls_button(): return False
            time.sleep(1)
            
            # Sequence for historical/classified calls
            if not self.click_search_button(): return False
            if not self.click_active_button(): return False
            self._log_status("✍️ Filtrando cidade: Passos...")
            if not self.filter_by_city_name("passos"): return False
            
            self._log_status("📤 Exportando chamadas ativas...")
            if not self.click_export_button(): return False

            # Chamamos a MESMA função de salvamento, mas com a flag 'active'
            if not self.save_excel_export(bronze_root, extraction_type="active"):
                return False
            
            self._log_status("🧹 Limpando janelas residuais...")
            self.close_search_subwindow()
            
            # Final focus for user experience
            self.focus_cad_window()

            return True
        except Exception as e:
            logging.error(f"Error in active flow: {e}")
            return False

    def save_excel_export(self, folder_path: Path, extraction_type: str = "historical") -> bool:
        """
        Saves the active Excel workbook as a CSV in the Bronze layer.
        extraction_type: Can be 'active' or 'historical' to differentiate folders/files.
        """
        pythoncom.CoInitialize()
        
        try:
            logging.info(f"Connecting to Excel via COM for {extraction_type} extraction...")
            time.sleep(3) 
            
            excel = win32com.client.GetActiveObject("Excel.Application")
            excel.DisplayAlerts = False 

            workbook = excel.ActiveWorkbook
            if not workbook:
                logging.error("No active workbook found.")
                return False

            # --- STEP: GENERATE FILENAME ---
            # Format: 2026-03-01_14-30_active.csv
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{timestamp}_{extraction_type}.csv"
            
            # Define target path (01_bronze/active/ or 01_bronze/historical/)
            target_dir = folder_path / extraction_type
            target_dir.mkdir(parents=True, exist_ok=True)
            
            full_output_path = target_dir / filename

            # SaveAs (FileFormat=6 is CSV)
            workbook.SaveAs(str(full_output_path), FileFormat=6)
            logging.info(f"Bronze layer updated: {full_output_path}")

            workbook.Close(SaveChanges=False)
            excel.Quit()
            return True

        except Exception as e:
            logging.error(f"COM Automation failed: {e}")
            return False
        finally:
            pythoncom.CoUninitialize()



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

        try:
            # 1. Localiza o 'Handle' (ID único) da janela pelo título
            hwnd = win32gui.FindWindow(None, self.cad_title)
            
            if not hwnd:
                logging.warning(f"Janela não encontrada: {self.cad_title}")
                return False

            # 2. Se a janela estiver minimizada, restaura
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)

            # 3. Força a janela a ficar no topo e maximizada
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            
            # 4. TRUQUE DE MESTRE: Simula um 'Alt' antes de dar o SetForegroundWindow
            # O Windows permite trocar o foco se o usuário pressionou Alt recentemente.
            pyautogui.press('alt')
            
            win32gui.SetForegroundWindow(hwnd)
            
            # 5. Clique de segurança na barra de título (garante foco do teclado)
            # Pegamos a posição da janela para clicar em um lugar neutro
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0] + 200 # 200px da esquerda
            y = rect[1] + 10  # 10px do topo
            pyautogui.click(x, y)
            
            logging.info("Janela do CAD focada com sucesso via Win32 API.")
            return True

        except Exception as e:
            logging.error(f"Falha crítica ao focar janela: {e}")
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
            # Search for search button
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
        Locates and clicks the 'Classificadas' button (04).
        Includes a small delay for Java UI rendering.
        """
        target_image = str(self.assets_path / "04_classificadas_button.png")
        
        time.sleep(0.8) 

        try:
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.85)
            
            if location:
                pyautogui.click(location)
                logging.info("Classified button (04) clicked successfully.")
                return True
            
            logging.warning("Classified button (04) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error clicking classified button: {e}")
            return False
    
    def click_active_button(self) -> bool:
        """
        Locates and clicks the 'Ativas' button (10).
        Includes a small delay for Java UI rendering.
        """
        target_image = str(self.assets_path / "10_ativas_button.png")
        
        time.sleep(0.8) 

        try:
            location = pyautogui.locateCenterOnScreen(target_image, confidence=0.85)
            
            if location:
                pyautogui.click(location)
                logging.info("Active button (04) clicked successfully.")
                return True
            
            logging.warning("Active button (04) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error clicking active button: {e}")
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
            time.sleep(0.2) # Wait for focus
            
            # Type the city name
            pyautogui.write(city_name, interval=0.1)
            logging.info(f"Typed city: {city_name}")
            time.sleep(0.2)

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

    def close_search_subwindow(self) -> bool:
        """
        Locates the 'Pesquisa Chamadas' subwindow and closes it to 
        return the CAD to its initial state.
        """
        subwindow_title = "Pesquisa Chamadas"
        try:
            # Search for the specific subwindow
            windows = gw.getWindowsWithTitle(subwindow_title)
            
            if not windows:
                logging.info(f"Subwindow '{subwindow_title}' already closed or not found.")
                return True # Not an error, it's already in the desired state

            subwindow = windows[0]
            
            # Bringing to front and closing
            subwindow.activate()
            time.sleep(0.5)
            subwindow.close()
            
            logging.info(f"Subwindow '{subwindow_title}' closed successfully.")
            return True

        except Exception as e:
            logging.error(f"Failed to close subwindow '{subwindow_title}': {e}")
            # Fallback: Send ESC key if window.close() fails
            pyautogui.press('esc')
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