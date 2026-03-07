import os
import sys
from pathlib import Path

# 1. Ajuste de Caminho (Bootstrap)
# Sobe 3 níveis (bot -> src -> raiz) para garantir que o Python enxergue a pasta 'src'
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 2. Bibliotecas de Terceiros
import logging
import time
import pyautogui
import easyocr
import numpy as np
import win32gui  # Necessário para as funções de foco que você já usa
import win32con
from PIL import ImageGrab

# 3. Seus Módulos
# Agora o import vai funcionar porque a raiz está no sys.path
from src.bot.cad_bot import CADAutomationBot

class HistoryBot(CADAutomationBot):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # OTIMIZAÇÃO 1: Carrega o leitor uma única vez na inicialização
        self.logger.info("⏳ Inicializando motor de visão (OCR)...")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def preparar_ambiente_historico(self, ui_status=None) -> bool:
        """
        Executa os passos iniciais que você já validou.
        """
        try:
            self._log_status(ui_status, "🧹 Limpando processos antigos...")
            self.close_excel_processes()

            self._log_status(ui_status, "🔍 Localizando janela do CAD...")
            if not self.focus_cad_window():
                return False

            self._log_status(ui_status, "✅ Verificando filtros...")
            if not self.check_passos_filter():
                return False

            return True

        except Exception as e:
            self.logger.error(f"Erro na preparação do histórico: {e}")
            return False

    def formatar_id_para_cad(self, call_id: str) -> str:
        """
        Transforma 2026444103786 em 2026-44410378-6
        """
        # Garantimos que o ID seja uma string e sem espaços
        id_limpo = str(call_id).strip()
        
        # Fatiamento:
        # id_limpo[:4] -> os primeiros 4 dígitos
        # id_limpo[4:-1] -> do 5º até o penúltimo
        # id_limpo[-1:] -> o último dígito
        id_formatado = f"{id_limpo[:4]}-{id_limpo[4:-1]}-{id_limpo[-1:]}"
        
        return id_formatado
    
    def localizar_e_duplo_clique(self, call_id: str, ui_status=None):
        id_alvo = self.formatar_id_para_cad(call_id)
        
        anchor_path = self.assets_path / "11_call_number_ref.png"
        anchor_loc = pyautogui.locateOnScreen(str(anchor_path), confidence=0.8)

        if not anchor_loc:
            return False

        ax, ay, aw, ah = anchor_loc
        search_region = (ax - 10, ay + ah, aw + 20, 800) 

        # OTIMIZAÇÃO 2: Capturar a imagem já em escala de cinza e menor
        screenshot = ImageGrab.grab(bbox=(
            search_region[0], 
            search_region[1], 
            search_region[0] + search_region[2], 
            search_region[1] + search_region[3]
        )).convert('L')
        
        img_np = np.array(screenshot)

        # OTIMIZAÇÃO 3: Parâmetros agressivos de velocidade
        # allowlist: reduz o 'dicionário' de busca
        # decoder: 'beamsearch' é mais lento, usamos o padrão ou simplificado
        # batch_size: como a imagem é pequena, aumentamos para processar tudo de uma vez
        resultados = self.reader.readtext(
            img_np, 
            allowlist='0123456789-',
            batch_size=10,
            detail=1
        )

        for (bbox, texto, prob) in resultados:
            texto_lido = texto.replace(" ", "")
            if id_alvo in texto_lido:
                # ... (lógica de clique continua igual)
                centro_x_local = int((bbox[0][0] + bbox[2][0]) / 2)
                centro_y_local = int((bbox[0][1] + bbox[2][1]) / 2)
                real_x = search_region[0] + centro_x_local
                real_y = search_region[1] + centro_y_local
                pyautogui.click(real_x, real_y, clicks=2, interval=0.1) # Duplo clique mais seco
                return True
        return False

    def clicar_botao_lapis(self, ui_status=None) -> bool:
        """
        Localiza e clica no botão do lápis (13_pencil_button.png).
        """
        self._log_status(ui_status, "✏️ Clicando no botão de edição...")
        
        path_img = self.assets_path / "13_pencil_button.png"
        location = pyautogui.locateOnScreen(str(path_img), confidence=0.8)
        
        if location:
            self.logger.info("✅ Botão do lápis encontrado e clicado.")
            pyautogui.click(location)
            return True
            
        self.logger.warning("⚠️ Botão do lápis não localizado.")
        return False

    def capturar_historico_por_id(self, call_id: str, ui_status=None) -> str:
        # 1. Prepara ambiente e foca CAD
        if not self.preparar_ambiente_historico(ui_status):
            return "Erro na preparação"

        # 2. Localiza o ID e entra na ocorrência (Duplo Clique)
        if not self.localizar_e_duplo_clique(call_id, ui_status):
            return "ID não localizado"

        # 3. Aguarda a janela de detalhes carregar
        time.sleep(1.5)

        # 4. Clica na aba de histórico
        if not self.abrir_aba_historico(ui_status):
            return "Falha ao abrir aba histórico"

        # 5. NOVO DEGRAU: Clicar no botão do lápis
        # Pequena pausa para garantir que o botão apareceu na aba
        time.sleep(0.5)
        if not self.clicar_botao_lapis(ui_status):
            return "Falha ao clicar no lápis"
        
        return "Sucesso até o botão do lápis"
    
    def abrir_aba_historico(self, ui_status=None) -> bool:
        """
        Tenta clicar no botão de histórico usando duas imagens de referência.
        """
        self._log_status(ui_status, "🖱️ Localizando aba de histórico...")
        
        # Lista com as duas opções de botões que você possui
        botoes_alvo = [
            "12_historico_button_01.png",
            "12_historico_button_02.png"
        ]

        for img_name in botoes_alvo:
            path_img = self.assets_path / img_name
            
            # Tentamos localizar na tela
            location = pyautogui.locateOnScreen(str(path_img), confidence=0.8)
            
            if location:
                self.logger.info(f"✅ Botão encontrado: {img_name}")
                pyautogui.click(location)
                return True
        
        self.logger.warning("⚠️ Não foi possível encontrar o botão de histórico.")
        return False

if __name__ == "__main__":
    bot = HistoryBot()
    id_teste = "2026444173299" 
    
    print(f"🚀 Iniciando fluxo até o lápis para o ID: {id_teste}")
    
    resultado = bot.capturar_historico_por_id(id_teste)
    
    if "Sucesso" in resultado:
        print(f"🔥 DEGRAU CONCLUÍDO: O robô chegou até o clique no lápis!")
    else:
        print(f"❌ Falha no processo: {resultado}")