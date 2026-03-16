import urllib.parse
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Ocorrencia:
    id_chamada: str
    natureza: str
    horario: str
    endereco: str
    unidade: str
    status: str
    status_icone: str
    historico: str = ""
    selecionado: bool = False

    def gerar_link_maps(self) -> str:
        """Gera um link de busca no Google Maps baseado no endereço."""
        # O quote_plus transforma espaços em '+' e remove caracteres especiais
        # para que o navegador entenda a URL corretamente.
        endereco_codificado = urllib.parse.quote_plus(self.endereco)
        return f"https://www.google.com/maps/search/?api=1&query={endereco_codificado}"

    def formatar_para_whatsapp(self) -> str:
        """Gera o texto formatado para WhatsApp."""
        link_maps = self.gerar_link_maps()
        
        texto = (
            f"🚨 *Nova Ocorrência* 🚨\n\n"
            f"📌 *Natureza:* {self.natureza}\n"
            f"⏰ *Horário:* {self.horario}\n"
            f"📍 *Endereço:* {self.endereco}\n"
            f"🗺️ *Google Maps:* {link_maps}\n"
            f"📖 *Histórico:* {self.historico if self.historico else 'Aguardando informações...'}\n\n"
            f"🚒 *Unidade:* {self.unidade}"
        )
        return texto