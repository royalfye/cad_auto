from PySide6.QtCore import QThread, Signal

class AutomationWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, bot_function, *args):
        super().__init__()
        self.bot_function = bot_function
        self.args = args

    def run(self):
        try:
            # Executa a função do bot que foi passada
            success = self.bot_function(*self.args)
            self.finished.emit(success, "Processo concluído com sucesso!")
        except Exception as e:
            # Se der erro no bot, captura e envia para a interface
            self.finished.emit(False, str(e))