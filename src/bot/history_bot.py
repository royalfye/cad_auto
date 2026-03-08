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

    def extrair_dados_tabela_historico(self, ui_status=None) -> str:
        """
        Localiza a tabela e extrai o conteúdo usando a largura exata da âncora.
        """
        self._log_status(ui_status, "📊 Fazendo varredura na tabela...")
        
        # 1. Localiza a âncora
        anchor_path = self.assets_path / "14_tabela_header.png"
        anchor_loc = pyautogui.locateOnScreen(str(anchor_path), confidence=0.8)

        if not anchor_loc:
            return "Erro: Cabeçalho da tabela não encontrado."

        # 2. Cálculo Dinâmico da Região
        # ax, ay: posição superior esquerda / aw, ah: largura e altura da imagem
        ax, ay, aw, ah = anchor_loc
        
        # Definimos a região: 
        # x = posição inicial da imagem
        # y = logo abaixo da imagem (ay + ah)
        # largura = exatamente a largura da imagem (aw)
        # altura = um valor que cubra a área de dados (ex: 500px ou até o fim da tela)
        search_region = (ax, ay + ah, aw, 500) 

        # 3. Captura Otimizada
        screenshot = ImageGrab.grab(bbox=(
            search_region[0], 
            search_region[1], 
            search_region[0] + search_region[2], 
            search_region[1] + search_region[3]
        )).convert('L')
        
        # 4. OCR de Parágrafo
        # O EasyOCR vai ler as colunas da esquerda para a direita, linha por linha
        img_np = np.array(screenshot)
        resultados = self.reader.readtext(img_np, detail=0, paragraph=True)

        return "\n".join(resultados) if resultados else "Nenhum dado extraído."

    def capturar_historico_por_id(self, call_id: str, ui_status=None) -> str:
        """Fluxo completo com garantia de fechamento de janelas."""
        relato_completo = ""
        
        try:
            # 1. Prepara ambiente e foca CAD
            if not self.preparar_ambiente_historico(ui_status): 
                return "Erro Foco"
            
            # 2. Busca e entra na ocorrência
            if not self.localizar_e_duplo_clique(call_id, ui_status): 
                return "Erro ID"
            
            time.sleep(1.5) 
            
            # 3. Navegação interna
            if not self.abrir_aba_historico(ui_status): 
                return "Erro Aba"
            
            time.sleep(0.5) 
            
            # 4. Acesso ao histórico detalhado
            if not self.clicar_botao_lapis(ui_status): 
                return "Erro Lápis"
            
            time.sleep(1.0) 
            
            # 5. EXTRAÇÃO FINAL (OCR)
            relato_completo = self.extrair_dados_tabela_historico(ui_status)
            
            return relato_completo

        except Exception as e:
            self.logger.error(f"Falha crítica no fluxo: {e}")
            return f"Erro: {e}"
            
        finally:
            # 6. LIMPEZA GARANTIDA: Este bloco executa SEMPRE
            # Chamamos o método que você atualizou para limpar o ambiente
            self.fechar_subjanela_gestao(ui_status)
    
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
    
    def fechar_subjanela_gestao(self, ui_status=None) -> bool:
        """
        Força o fechamento das subjanelas usando Alt+F4.
        """
        self._log_status(ui_status, "🧹 Forçando fechamento das janelas (Alt+F4)...")
        
        try:
            # 1. Garante o foco no CAD clicando no centro
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            time.sleep(0.5)

            # 2. Primeiro Alt+F4: Fecha a 'Gestão de Histórico'
            pyautogui.hotkey('alt', 'f4')
            self.logger.info("Alt+F4 enviado para a Gestão de Histórico.")
            
            # Espera um pouco mais para o CAD processar
            time.sleep(1.2) 
            
            # 3. Segundo Alt+F4 ou Esc: Fecha a ficha da Ocorrência
            # Recomendo manter o ESC no segundo para ser mais seguro e não fechar o CAD principal
            pyautogui.press('esc')
            self.logger.info("Esc enviado para sair da ficha da Ocorrência.")
            
            return True

        except Exception as e:
            self.logger.error(f"Erro no fechamento forçado: {e}")
            return False


if __name__ == "__main__":
    bot = HistoryBot()
    id_teste = "2026444219810" 
    
    print(f"🚀 Iniciando extração final para o ID: {id_teste}")
    
    texto_extraido = bot.capturar_historico_por_id(id_teste)
    
    print("\n--- CONTEÚDO CAPTURADO ---")
    print(texto_extraido)
    print("--------------------------")