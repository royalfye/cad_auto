from datetime import datetime
import logging
import os
import pythoncom
from pathlib import Path
import time

import psutil
import pyautogui
import pygetwindow as gw
import win32com.client
from win32com.client import Dispatch
import win32con
import win32gui

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global Logging Configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CADAutomationBot:
    """
    Bot automation to extract the Active calls from CAD Java software from CBMMG. The final point is to get and update the .csv archive file of all active calls.   
    """
    #1 Init
    def __init__(self):
        # Paths
        self.bot_dir = Path(__file__).resolve().parent
        self.project_root = self.bot_dir.parent.parent
        self.assets_path = self.project_root / "assets" / "images" / "cad_targets"
        
        # System config
        self.cad_title = "CAD - Solução de Controle do Atendimento e Despacho de Emergência Policial e de Bombeiros"
        self.excel_process = "EXCEL.EXE"
        
        # Safety config for PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.2

    #2 Main automation flux
    def _base_extraction_flow(self, bronze_root: Path, extraction_type: str, ui_status=None) -> bool:
        try:
            self._log_status(ui_status, "🧹 Preparando ambiente...")
            self.close_excel_processes()
            
            if not self.focus_cad_window(): return False
            if not self.check_passos_filter(): return False
            
            self._log_status(ui_status, "🖱️ Navegando pelos módulos...")
            if not self.click_calls_button(): return False
            time.sleep(1)
            
            if not self.click_search_button(): return False

            # Check if is active calls or historical
            if extraction_type == "historical":
                if not self.click_classified_button(): return False
                if not self.click_last_24h_button(): return False
                if not self.click_last_3_day_button(): return False
            elif extraction_type == "active":
                if not self.click_active_button(): return False


            self._log_status(ui_status, "✍️ Filtrando cidade: Passos...")
            if not self.filter_by_city_name("passos"): return False

            self._log_status(ui_status, f"📤 Exportando {extraction_type}...")
            if not self.click_export_button(): return False

            if not self.save_excel_export(bronze_root, extraction_type=extraction_type):
                return False
            
            self._log_status(ui_status, "🧹 Limpando janelas residuais...")
            self.close_search_subwindow()
            self.focus_cad_window()
            self.focus_fireapp_window()
            return True

        except Exception as e:
            logging.error(f"Erro no fluxo {extraction_type}: {e}")
            return False
        
    #2.1 Separate the historical and active flux. (HISTORCAL isn't using at the moment)
    def run_full_extraction_flow(self, bronze_root: Path, ui_status=None) -> bool:
        return self._base_extraction_flow(bronze_root, "historical", ui_status)

    def run_active_extraction_flow(self, bronze_root: Path, ui_status=None) -> bool:
        return self._base_extraction_flow(bronze_root, "active", ui_status)
        
    #3 Logging
    def _log_status(self, ui_status, message=None):

        if message is None:
            message = ui_status
            ui_status = None
    
        logging.info(message) 
        
        if ui_status is not None and hasattr(ui_status, 'write'):
            ui_status.write(message)

    #4 Close all execel processes
    def close_excel_processes(self) -> int:
        closed_count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].upper() == self.excel_process:
                    proc.terminate() 
                    try:
                        proc.wait(timeout=0.5)
                    except psutil.TimeoutExpired:
                        proc.kill()
                        
                    closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if closed_count > 0:
            logging.info(f"🧹 Limpeza: {closed_count} processo(s) do Excel encerrado(s).")
        return closed_count
    
    #5 Focus Cad Window
    def focus_cad_window(self) -> bool:
        try:
            hwnd = win32gui.FindWindow(None, self.cad_title)
            
            if not hwnd:
                logging.warning(f"⚠️ Janela não encontrada: {self.cad_title}")
                return False

            # if its minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)

            # Maximizes
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            
            # Bypass for Windows security
            pyautogui.press('alt')
            
            # Try to bring it to the front
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                logging.warning(f"Tentativa inicial de foco falhou, tentando forçar: {e}")
                shell = win32com.client.Dispatch("WScript.Shell")
                shell.SendKeys('%')
                win32gui.SetForegroundWindow(hwnd)

            # Clicks on relative position
            rect = win32gui.GetWindowRect(hwnd)
            center_x = rect[0] + (rect[2] - rect[0]) // 2
            top_y = rect[1] + 15
            pyautogui.click(center_x, top_y)
            
            logging.info("🎯 Janela do CAD focada e pronta para interação.")
            return True

        except Exception as e:
            logging.error(f"❌ Falha crítica ao focar janela: {e}")
            return False
        
    #6 Check if Passos city is selected on the filter (MUST BE CHANGED TO CONFIG THE CITY)    
    def check_passos_filter(self) -> bool:
        """Check if the filter Passos in on the screen."""

        # Image check in assets folder
        target_image = self.assets_path / "01_filter_passos_active.png"
        if not target_image.exists():
            logging.error(f"Imagem de referência não encontrada: {target_image}")
            return False

        try:
            # target the image file
            location = pyautogui.locateOnScreen(str(target_image), confidence=0.9)
            
            if location:
                logging.info("✅ Filtro 'PASSOS' detectado com sucesso.")
                return True
            
            logging.warning("⚠️ Filtro 'PASSOS' não encontrado na tela.")
            return False
        except Exception as e:
            logging.error(f"Erro no reconhecimento de imagem: {e}")
            return False
        
    #7 Click on 'Chamadas' button
    def click_calls_button(self) -> bool:
        """Busca o botão de chamadas e clica. Mantendo sua lógica original de clique direto."""
        target_image = str(self.assets_path / "02_chamadas_button.png")
        
        if not os.path.exists(target_image):
            logging.error(f"Imagem não encontrada: {target_image}")
            return False

        try:

            button_location = None
            for _ in range(5):
                button_location = pyautogui.locateCenterOnScreen(target_image, confidence=0.9)
                if button_location:
                    break
                time.sleep(1)

            if button_location:

                pyautogui.click(button_location)
                logging.info("✅ Calls button (02) clicked successfully.")
                return True
            
            logging.warning("⚠️ Calls button (02) not found on screen.")
            return False

        except Exception as e:
            logging.error(f"Error clicking calls button: {e}")
            return False
    
    #8 Click on 'Pesquisa de Chamadas' button
    def click_search_button(self) -> bool:

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
    
    #9 For historical flux click on 'Chamadas Classificadas'
    def click_classified_button(self) -> bool:

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
        
    #9.1. For historical flux click on 'Chamadas das Últimos 24h'     
    def click_last_24h_button(self) -> bool:

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

    #10 For historical flux click on 'Últimos 3 dias' 
    def click_last_3_day_button(self) -> bool:
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
        
    #11 For Active Flux, click on "Chamadas Ativas" 
    def click_active_button(self) -> bool:
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
        
    #12 Type the word 'passos' (MUST BE CHANGED FOR CITY CONFIG) 
    def filter_by_city_name(self, city_name: str = "passos") -> bool:
        # Paths for the images
        img_field = str(self.assets_path / "07_filtro_passos.button.png")
        img_confirm = str(self.assets_path / "08_passos_button.png")

        try:
  
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
        
    #13 Click on 'Exportar CSV' to open the excel software
    def click_export_button(self) -> bool:
        
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
        
    #14 Save excel file
    def save_excel_export(self, folder_path: Path, extraction_type: str = "historical") -> bool:
        pythoncom.CoInitialize()
        excel = None
        
        try:
            logging.info("💾 Aguardando o Excel carregar...")
            time.sleep(3)

            # Forces the focus to unlock windows block
            pyautogui.press('win')
            time.sleep(0.2)
            pyautogui.press('esc')

            # Try to capture the excel instance that CAD opened
            for _ in range(15): 
                try:
                    excel = win32com.client.GetActiveObject("Excel.Application")
                    if excel.Workbooks.Count > 0:
                        break
                except Exception:
                    time.sleep(1)

            if not excel or excel.Workbooks.Count == 0:
                logging.error("❌ Instância do Excel não encontrada ou sem planilhas.")
                return False

            # Control Cofig
            excel.Visible = True
            excel.DisplayAlerts = False 
            
            # Windows variable for maximize function
            xl_maximized = -4137
            excel.WindowState = xl_maximized 

            wb = excel.Workbooks(1)
            
            # Save file config
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{timestamp}_{extraction_type}.csv"
            target_dir = folder_path / extraction_type
            target_dir.mkdir(parents=True, exist_ok=True)
            full_path = str(target_dir / filename)

            logging.info(f"💾 Salvando: {filename}")
            
            # FileFormat=6 is csv format
            wb.SaveAs(full_path, FileFormat=6) 
            
            wb.Close(SaveChanges=False)
            excel.Quit()
            
            logging.info("✅ Extração concluída com sucesso!")
            return True

        except Exception as e:
            logging.error(f"❌ Erro na captura do Excel: {e}")
            return False
        finally:
            # Safety method to ends all excell processes
            wb = None
            excel = None
            pythoncom.CoUninitialize()

    #15 Close the subwindow called 'Pesquisa Chamadas'
    def close_search_subwindow(self) -> bool:
        
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

    #16 Return to FireApp   
    def focus_fireapp_window(self) -> bool:
        """Traz a interface do FireApp de volta para o primeiro plano."""
        titulo_app = "Bombeiros - 2ª CIA Passos"
        try:
            hwnd = win32gui.FindWindow(None, titulo_app)
            if hwnd:
                # Se estiver minimizada, restaura
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Traz para frente
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                logging.info("🔙 Foco retornado ao FireApp.")
                return True
            return False
        except Exception as e:
            logging.warning(f"⚠️ Não foi possível retornar o foco para o FireApp: {e}")
            return False
        