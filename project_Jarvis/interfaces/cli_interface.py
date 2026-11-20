# interfaces/cli_interface.py
import sys
import os
from typing import Optional
from datetime import datetime
from core.assistant import Assistant
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class CLIInterface:
    """Interface de linha de comando para o assistente."""
    
    def __init__(self):
        self.assistant = Assistant()
        self.user_id = self.assistant.memory.db.ensure_user("default")
        self.conversation_id = self.assistant.memory.db.ensure_conversation(self.user_id)
        self.running = False
        self.commands = {
            "/exit": "Sair do assistente",
            "/quit": "Sair do assistente",
            "/clear": "Limpar a tela",
            "/help": "Mostrar esta ajuda",
            "/code": "Forçar modo código para a próxima mensagem",
            "/explain": "Forçar modo explicação de código",
            "/review": "Forçar modo revisão de código",
            "/stats": "Mostrar estatísticas da sessão",
            "/models": "Mostrar modelos em uso",
            "/save": "Salvar conversa em arquivo",
            "/debug": "Alternar modo debug"
        }
        
        self.session_stats = {
            "start_time": datetime.now(),
            "messages_count": 0,
            "code_requests": 0,
            "general_queries": 0
        }
        
        self.force_code_mode = False
    
    def start(self):
        """Inicia o loop principal da CLI."""
        self.running = True
        self._print_welcome()
        
        while self.running:
            try:
                user_input = self._get_user_input()
                
                if not user_input:
                    continue
                
                # Processa comandos especiais
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                    continue
                
                # Processa mensagem normal
                self._process_user_message(user_input)
                
            except KeyboardInterrupt:
                self._handle_interrupt()
            except Exception as e:
                self._handle_error(e)
        
        self._shutdown()
    
    def _print_welcome(self):
        """Exibe mensagem de boas-vindas."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        banner = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                     JARVIS ASSISTANT                     ║
    ║                         v2.0.0                            ║
    ╠════════════════════════════════════════════════════════════╣
    ║  🤖 Modelo Conversa: {self.assistant.llm.chat_model:<30} ║
    ║  💻 Modelo Código:   {self.assistant.llm.code_model:<30} ║
    ║  🌐 Idioma:          {settings.get('assistant.language', 'pt-BR'):<30} ║
    ║  🔧 Debug:           {str(self.assistant.debug):<30} ║
    ╠════════════════════════════════════════════════════════════╣
    ║  📋 Comandos: /help para lista completa                   ║
    ║  💡 Dica: Perguntas de código usam modelo especializado   ║
    ╚════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def _get_user_input(self) -> str:
        """Obtém input do usuário com prompt personalizado."""
        try:
            prompt = "\n💬 Você: " if not self.force_code_mode else "\n💻 [MODO CÓDIGO] Você: "
            user_input = input(prompt).strip()
            return user_input
        except EOFError:
            return "/exit"
    
    def _process_user_message(self, message: str):
        """Processa uma mensagem do usuário."""
        # Atualiza estatísticas
        self.session_stats["messages_count"] += 1
        
        # Se force_code_mode estiver ativo, adiciona flag
        if self.force_code_mode:
            message = f"[FORCE_CODE] {message}"
            self.force_code_mode = False
        
        # Processa a mensagem
        print("\n🤔 Pensando...", end="", flush=True)
        
        try:
            response = self.assistant.process_message(
                message, user_id=self.user_id, conversation_id=self.conversation_id)
            
            # Atualiza estatísticas baseado na resposta
            if "código" in response.lower() or "```" in response:
                self.session_stats["code_requests"] += 1
            else:
                self.session_stats["general_queries"] += 1
            
            # Limpa a linha "Pensando..."
            print("\r", end="", flush=True)
            
            # Exibe a resposta
            print(f"\n🤖 {self.assistant.name}:")
            
            # Formata resposta com código se houver
            if "```" in response:
                self._print_code_response(response)
            else:
                print(f"{response}")
                
        except Exception as e:
            print("\r", end="", flush=True)
            print(f"\n❌ Erro ao processar: {e}")
            logger.error(f"Erro no processamento: {e}", exc_info=True)
    
    def _print_code_response(self, response: str):
        """Exibe resposta formatada com código."""
        parts = response.split("```")
        
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Texto normal
                if part.strip():
                    print(part)
            else:  # Bloco de código
                # Tenta extrair a linguagem
                lines = part.split("\n")
                if lines and lines[0].strip() in ["python", "javascript", "java", "html", "css" "c++", "c#", "ruby", "go", "bash", "cobol", "sql", "php", "rust", "swift", "typescript", "scala", "perl",  "lua", "kotlin" "dart", "elixir", "haskell", "clojure", "fsharp" "erlang", "r", "matlab", "groovy", "visual basic" "objective-c", "assembly", "fortran", "lisp", "prolog", "scheme" "vba", "powershell", "sas", "stata", "abap", "apex", "awk", "cassandra", "coffeescript", "crystal", "d", "elm", "f#", "factor", "forth", "gcode", "hcl", "idris", "julia", "nim", "ocaml", "pascal", "pony", "rebol", "red", "ring", "squirrel", "tcl" "batch", "cmd", "diff", "dockerfile", "graphql", "ini", "json", "makefile", "md", "nginx", "protobuf", "regex", "toml", "yaml"]:  
                    lang = lines[0].strip()
                    code = "\n".join(lines[1:])
                else:
                    lang = "código"
                    code = part
                
                print(f"\n📝 [{lang.upper()}]")
                print("```")
                print(code.strip())
                print("```")
    
    def _handle_command(self, command: str):
        """Processa comandos especiais."""
        cmd = command.lower().split()[0]
        
        if cmd in ["/exit", "/quit"]:
            self.running = False
            print("\n Até mais!")
            
        elif cmd == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            self._print_welcome()
            
        elif cmd == "/help":
            self._show_help()
            
        elif cmd == "/code":
            self.force_code_mode = True
            print("\n✅ Modo código ativado para a próxima mensagem!")
            
        elif cmd == "/explain":
            print("\n Cole o código que deseja explicar (ou digite 'cancelar'):")
            code = self._get_multiline_input()
            if code and code != "cancelar":
                self._process_user_message(f"/explain {code}")
                
        elif cmd == "/review":
            print("\n Cole o código que deseja revisar (ou digite 'cancelar'):")
            code = self._get_multiline_input()
            if code and code != "cancelar":
                self._process_user_message(f"/review {code}")
                
        elif cmd == "/stats":
            self._show_stats()
            
        elif cmd == "/models":
            self._show_models()
            
        elif cmd == "/save":
            self._save_conversation()
            
        elif cmd == "/debug":
            self.assistant.debug = not self.assistant.debug
            status = "ativado" if self.assistant.debug else "desativado"
            print(f"\n Modo debug {status}!")
            
        else:
            print(f"\n Comando desconhecido: {command}")
            print("Digite /help para ver os comandos disponíveis.")
    
    def _get_multiline_input(self) -> str:
        """Obtém input multi-linha do usuário."""
        lines = []
        print("(Digite 'EOF' em uma linha vazia para finalizar)")
        
        while True:
            try:
                line = input()
                if not line and lines and lines[-1] == "EOF":
                    lines.pop()
                    break
                lines.append(line)
            except EOFError:
                break
        
        return "\n".join(lines)
    
    def _show_help(self):
        """Exibe ajuda com comandos disponíveis."""
        print("\n COMANDOS DISPONÍVEIS:")
        print("═" * 50)
        
        for cmd, desc in self.commands.items():
            print(f"  {cmd:<12} - {desc}")
        
        print("\n💡 DICAS:")
        print("═" * 50)
        print("  • O sistema detecta automaticamente quando você")
        print("    está pedindo ajuda com código e usa o modelo")
        print("    especializado jarvis-coder")
        print("  • Para forçar o modo código, use /code antes da pergunta")
        print("  • Você pode colar blocos de código diretamente")
        print("  • Use Ctrl+C para interromper a qualquer momento")
    
    def _show_stats(self):
        """Exibe estatísticas da sessão."""
        elapsed = datetime.now() - self.session_stats["start_time"]
        minutes = elapsed.total_seconds() / 60
        
        print("\n📊 ESTATÍSTICAS DA SESSÃO:")
        print("═" * 50)
        print(f"  ⏱️  Tempo ativo: {minutes:.1f} minutos")
        print(f"  💬 Total mensagens: {self.session_stats['messages_count']}")
        print(f"  💻 Requisições de código: {self.session_stats['code_requests']}")
        print(f"  🗣️  Consultas gerais: {self.session_stats['general_queries']}")
        
        if self.session_stats['messages_count'] > 0:
            code_percent = (self.session_stats['code_requests'] / 
                          self.session_stats['messages_count'] * 100)
            print(f"  📊 % código: {code_percent:.1f}%")
    
    def _show_models(self):
        """Exibe informações sobre os modelos em uso."""
        print("\n🤖 MODELOS EM USO:")
        print("═" * 50)
        print(f"  📱 Conversa:  {self.assistant.llm.chat_model}")
        print(f"     • Temperatura: {self.assistant.llm.chat_config.get('temperature', 0.8)}")
        print(f"     • Max tokens: {self.assistant.llm.chat_config.get('max_tokens', 1000)}")
        print()
        print(f"  💻 Código:    {self.assistant.llm.code_model}")
        print(f"     • Temperatura: {self.assistant.llm.code_config.get('temperature', 0.3)}")
        print(f"     • Max tokens: {self.assistant.llm.code_config.get('max_tokens', 4096)}")
        print(f"     • Top K: {self.assistant.llm.code_config.get('top_k', 40)}")
    
    def _save_conversation(self):
        """Salva a conversa em arquivo."""
        try:
            filename = f"conversa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            history = self.assistant.memory.bind(
                self.user_id, self.conversation_id).short.get_history(as_text=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Conversa com Jarvis - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(history)
            
            print(f"\n✅ Conversa salva em: {filename}")
            
        except Exception as e:
            print(f"\n❌ Erro ao salvar: {e}")
    
    def _handle_interrupt(self):
        """Lida com interrupção do usuário (Ctrl+C)."""
        print("\n\n⚠️  Interrompido pelo usuário")
        response = input("Deseja realmente sair? (s/N): ").lower()
        
        if response == 's':
            self.running = False
            print("\n👆 Até mais!")
        else:
            print("\n✅ Continuando...")
    
    def _handle_error(self, error: Exception):
        """Lida com erros inesperados."""
        print(f"\n❌ Erro inesperado: {error}")
        logger.error(f"Erro na CLI: {error}", exc_info=True)
        
        response = input("\nDeseja continuar? (s/N): ").lower()
        if response != 's':
            self.running = False
    
    def _shutdown(self):
        """Finaliza a interface."""
        logger.info("CLI finalizada")
        self.assistant.shutdown()
