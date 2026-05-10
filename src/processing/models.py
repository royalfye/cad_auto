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
        endereco_codificado = urllib.parse.quote_plus(self.endereco)
        # Mantendo o padrão de URL que você já utiliza
        return f"https://www.google.com/maps/search/?api=1&query={endereco_codificado}"

    def formatar_para_whatsapp(self, equipe: str = "Não informada") -> str:
        """
        Gera o texto formatado para WhatsApp.
        Recebe a 'equipe' (Ala) como parâmetro para compor o rodapé.
        """
        link_maps = self.gerar_link_maps()
        
        texto = (
            f"🚨 *Nova Ocorrência* 🚨\n\n"
            f"📌 *Natureza:* {self.natureza}\n"
            f"⏰ *Horário:* {self.horario}\n"
            f"📍 *Endereço:* {self.endereco}\n"
            f"🗺️ *Google Maps:* {link_maps}\n"
            f"📖 *Histórico:* {self.historico if self.historico else 'Aguardando informações...'}\n\n"
            f"🚒 *Unidade:* {self.unidade}\n"
            f"👥 *Equipe:* {equipe}" # Adicionamos a ala aqui
        )
        return texto
    
    def gerar_link_whatsapp(self, equipe: str) -> str:
        """Gera um link wa.me com o texto da ocorrência pronto."""
        texto_formatado = self.formatar_para_whatsapp(equipe=equipe)
        texto_codificado = urllib.parse.quote(texto_formatado)
        
        # Como é para grupo, geramos o link de API que abre a conversa
        return f"https://api.whatsapp.com/send?text={texto_codificado}"