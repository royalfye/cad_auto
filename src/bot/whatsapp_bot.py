import pyautogui
import pyperclip
import time
import logging
import win32gui
import win32con
import win32com.client

class WhatsAppBot:
    def __init__(self):
        pyautogui.PAUSE = 0.5
        pyautogui.FAILSAFE = True
        self.whatsapp_title = "WhatsApp"
        self.fireapp_title = "Bombeiros - 2ª CIA Passos"

    def _focar_janela(self, titulo: str) -> bool:
        """Traz uma janela específica para o primeiro plano."""
        try:
            hwnd = win32gui.FindWindow(None, titulo)
            if hwnd:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                shell = win32com.client.Dispatch("WScript.Shell")
                shell.SendKeys('%') 
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.8)
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao focar {titulo}: {e}")
            return False

    def enviar_para_grupo(self, nome_grupo: str, mensagem: str):
        """Fluxo cadenciado para garantir o envio no grupo correto."""
        
        # 1. Trazer o WhatsApp para frente
        if not self._focar_janela(self.whatsapp_title):
            logging.error("WhatsApp não encontrado.")
            return False

        try:
            # ETAPA 1: Resetar o estado do WhatsApp
            # Pressionar ESC múltiplas vezes garante que saímos de menus, 
            # caixas de busca abertas ou visualização de mídias.
            for _ in range(3):
                pyautogui.press('esc')
                time.sleep(0.2)

            # Atalho para ir para a aba de "Conversas" (Alt + 1 no novo WhatsApp Desktop)
            # Isso garante que estamos na lista de chats e não em 'Chamadas' ou 'Status'
            pyautogui.hotkey('alt', '1')
            time.sleep(0.5)

            # ETAPA 2: Digitar o nome do grupo na busca
            # Ctrl + F foca na busca de conversas
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            pyperclip.copy(nome_grupo)
            pyautogui.hotkey('ctrl', 'v')
            
            # ETAPA 3: Clicar/Entrar no grupo correspondente
            # O WhatsApp filtra. O primeiro resultado da lista é focado automaticamente.
            # Esperamos o filtro processar (crucial!)
            time.sleep(1.8) 
            
            # Pressionar baixo e Enter garante a seleção do primeiro item da lista filtrada
            pyautogui.press('down')
            pyautogui.press('enter')
            time.sleep(0.8)

            # ETAPA 4: Colar a mensagem e enviar
            pyperclip.copy(mensagem)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(0.5)

            # ETAPA 5: Retornar para o seu App
            self._focar_janela(self.fireapp_title)
            
            return True

        except Exception as e:
            logging.error(f"Falha na automação: {e}")
            # Tenta voltar o foco mesmo em caso de erro parcial
            self._focar_janela(self.fireapp_title)
            return False