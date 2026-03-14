from PySide6.QtCore import QThread, Signal

class AutomationWorker(QThread):
    # O primeiro valor é o sucesso (bool), o segundo é a mensagem ou o texto capturado (str)
    finished = Signal(bool, str)
    # Adicionamos um sinal de status para as mensagens aparecerem na barra da interface
    status = Signal(str)

    def __init__(self, bot_function, *args, **kwargs):
        super().__init__()
        self.bot_function = bot_function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # Criamos um dicionário de argumentos finais
            final_kwargs = dict(self.kwargs)
            
            # Verificamos se a função aceita o parâmetro 'ui_status'
            import inspect
            sig = inspect.signature(self.bot_function)
            
            if 'ui_status' in sig.parameters:
                final_kwargs['ui_status'] = self.status

            # Executa a função
            # Usamos apenas *self.args e os nossos final_kwargs tratados
            result = self.bot_function(*self.args, **final_kwargs)
            
            # Lógica de retorno (mantém a sua)
            if isinstance(result, str) and result != "":
                self.finished.emit(True, result)
            elif isinstance(result, bool):
                msg = "Processo concluído!" if result else "O processo falhou."
                self.finished.emit(result, msg)
            else:
                self.finished.emit(False, "Resultado inesperado do robô.")

        except Exception as e:
            self.finished.emit(False, f"Erro na automação: {str(e)}")