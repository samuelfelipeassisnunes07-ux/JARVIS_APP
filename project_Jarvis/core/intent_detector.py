# core/intent_detector.py
from typing import List, Dict, Any, Optional, Tuple
import re

class IntentDetector:
    """Detecta intenções do usuário a partir do texto."""
    
    def __init__(self):
        # Padrões para diferentes intenções
        self.patterns = {
            "code_generation": {
                "keywords": [
                    "crie", "criar", "escreva", "escrever", "gere", "gerar",
                    "implemente", "implementar", "desenvolva", "desenvolver",
                    "código para", "codigo para", "função que", "funcao que",
                    "programa que", "script que", "algoritmo para", "faça um codigo"
                ],
                "patterns": [
                    r"como (fazer|criar|implementar) .* (em|com|usando)",
                    r"preciso de (um|uma) (código|função|classe|script)",
                    r"exemplo de (código|função|classe)",
                    r"código (em|para) \w+"
                ]
            },
            "code_explanation": {
                "keywords": [
                    "explica", "explique", "o que faz", "como funciona",
                    "entender", "entenda", "detalhe", "detalhar",
                    "me explique", "pode explicar", "explicação"
                ]
            },
            "code_review": {
                "keywords": [
                    "revisa", "revise", "revisão", "review",
                    "melhorar", "otimizar", "otimize", "refatorar",
                    "code review", "revisão de código", "sugestões",
                    "como melhorar", "o que acha", "está correto"
                ]
            },
            "question": {
                "keywords": [
                    "o que é", "o que são", "como", "por que", "porque",
                    "quando", "onde", "qual", "quais", "pode explicar",
                    "diferença entre", "vs", "versus"
                ]
            },
            "greeting": {
                "keywords": [
                    "oi", "olá", "ola", "hello", "hi", "hey",
                    "bom dia", "boa tarde", "boa noite", "e aí", "e ai"
                ]
            },
            "farewell": {
                "keywords": [
                    "tchau", "até mais", "ate mais", "até logo",
                    "adeus", "bye", "encerrar", "sair", "exit"
                ]
            },
            "help": {
                "keywords": [
                    "ajuda", "help", "comandos", "o que você pode fazer",
                    "como usar", "funcionalidades", "capacidades"
                ]
            },
            "weather": {
                "keywords": [
                    "clima", "previsão do tempo", "previsao do tempo",
                    "temperatura", "como está o tempo", "como esta o tempo"
                ]
            },
            "web_search": {
                "keywords": [
                    "pesquise", "pesquisa", "pesquisar", "busque", "procure",
                    "pesquise na web", "pesquisa na web", "busque na web",
                    "procure na internet", "pesquise na internet", "busque na internet",
                    "faça uma pergunta na web", "faca uma pergunta na web",
                    "pesquisa sobre", "pesquise sobre", "busque sobre",
                    "procure informações sobre", "procure informacoes sobre",
                    "notícias sobre", "noticias sobre", "informação atual sobre",
                    "informacao atual sobre", "o que aconteceu hoje", "qual a cotação",
                    "o que pode cair", "o que pode cair no enem", "pesquisa o que pode cair"
                ]
            },
            "system": {
                "keywords": [
                    "configuração", "configurar", "settings",
                    "preferências", "preferencias", "opções", "opcoes"
                ]
            }
        }
        
        # Detecção de linguagens de programação
        self.programming_languages = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node", "nodejs"],
            "typescript": ["typescript", "ts"],
            "java": ["java"],
            "html": ["html"],
            "css": ["css"],
            "sql": ["sql", "query"],
            "bash": ["bash", "shell", "sh"],
            "c": ["c", "linguagem c"],
            "c++": ["c++", "cpp", "cplusplus"],
            "c#": ["c#", "csharp"],
            "php": ["php"],
            "ruby": ["ruby", "rb"],
            "go": ["golang", "go"],
            "rust": ["rust"],
            "swift": ["swift"],
            "kotlin": ["kotlin"],
            "r": ["r", "linguagem r"]
        }
        
        # Palavras que indicam fortemente que é código
        self.code_indicators = [
            "def ", "function", "class ", "import ", "from ",
            "if __name__", "console.log", "print(", "return ",
            "```", "const ", "let ", "var ", "public class"
        ]
        
        # Compila padrões regex para melhor performance
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compila padrões regex para melhor performance."""
        compiled = {}
        for intent, data in self.patterns.items():
            patterns = []
            if "patterns" in data:
                for pattern in data["patterns"]:
                    try:
                        compiled_pattern = re.compile(pattern, re.IGNORECASE)
                        patterns.append(compiled_pattern)
                    except re.error:
                        continue
            compiled[intent] = patterns
        return compiled
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """
        Detecta a intenção principal do texto.
        Retorna um dicionário com a intenção e informações adicionais.
        """
        text_lower = text.lower().strip()
        
        # Primeiro verifica se é uma pergunta de código
        if self.is_code_related(text):
            code_info = self._analyze_code_request(text)
            return code_info
        
        # Verifica intenções específicas por ordem de prioridade
        intent_priority = ["help", "web_search", "weather", "system", "greeting", "farewell", "question"]
        
        for intent in intent_priority:
            if self._match_intent(text_lower, intent):
                return {
                    "intent": intent,
                    "confidence": 0.8,
                    "type": "general"
                }
        
        # Se não detectou nada específico
        return {
            "intent": "general",
            "confidence": 0.5,
            "type": "general"
        }
    
    def _analyze_code_request(self, text: str) -> Dict[str, Any]:
        """Analisa detalhadamente uma requisição de código."""
        text_lower = text.lower()
        language = self.detect_programming_language(text)
        
        # Verifica se tem código no texto
        has_code = self.contains_code(text)
        
        # Determina sub-intenção
        if self.is_code_explanation(text):
            intent = "code_explanation"
            confidence = 0.9
        elif self.is_code_review(text):
            intent = "code_review"
            confidence = 0.9
        elif self.is_code_generation(text):
            intent = "code_generation"
            confidence = 0.85
        else:
            # Tenta deduzir pela presença de código
            if has_code:
                intent = "code_explanation"
                confidence = 0.7
            else:
                intent = "code_generation"
                confidence = 0.6
        
        return {
            "intent": intent,
            "confidence": confidence,
            "type": "code",
            "language": language,
            "has_code": has_code
        }
    
    def _match_intent(self, text: str, intent: str) -> bool:
        """Verifica se o texto corresponde a uma intenção específica."""
        if intent in self.patterns:
            keywords = self.patterns[intent].get("keywords", [])
            if any(keyword in text for keyword in keywords):
                return True
            
            # Verifica padrões regex compilados
            if intent in self._compiled_patterns:
                for pattern in self._compiled_patterns[intent]:
                    if pattern.search(text):
                        return True
        
        return False
    
    def is_code_related(self, text: str) -> bool:
        """Verifica se o texto está relacionado a código."""
        if self.contains_code(text) or self.detect_programming_language(text):
            return True

        # Palavras como "explique" e "crie" também aparecem em pedidos gerais.
        # Só encaminha para o modelo de código quando há vocabulário técnico.
        programming_terms = [
            "código", "codigo", "script", "programa", "função", "funcao",
            "classe", "variável", "variavel", "algoritmo", "api", "bug",
            "erro de sintaxe", "stack trace", "framework", "biblioteca",
            "método", "metodo", "endpoint", "banco de dados", "query",
            "comando", "terminal", "compilar", "implementação", "implementacao",
        ]
        return any(
            re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text.lower())
            for term in programming_terms
        )
    
    def is_code_generation(self, text: str) -> bool:
        """Verifica se é uma solicitação de geração de código."""
        text_lower = text.lower()
        return self._match_intent(text_lower, "code_generation")
    
    def is_code_explanation(self, text: str) -> bool:
        """Verifica se é uma solicitação de explicação de código."""
        text_lower = text.lower()
        return self._match_intent(text_lower, "code_explanation")
    
    def is_code_review(self, text: str) -> bool:
        """Verifica se é uma solicitação de revisão de código."""
        text_lower = text.lower()
        return self._match_intent(text_lower, "code_review")
    
    def contains_code(self, text: str) -> bool:
        """Verifica se o texto contém trechos de código."""
        # Verifica blocos de código markdown
        if "```" in text:
            return True
        
        # Verifica indicadores comuns de código
        for indicator in self.code_indicators:
            if indicator in text:
                return True
        
        return False
    
    def detect_programming_language(self, text: str) -> Optional[str]:
        """Detecta a linguagem de programação mencionada."""
        text_lower = text.lower()
        
        # Primeiro verifica se há blocos de código com especificação de linguagem
        lang_pattern = r"```(\w+)"
        match = re.search(lang_pattern, text)
        if match:
            lang = match.group(1).lower()
            for language, variations in self.programming_languages.items():
                if lang in variations or lang == language:
                    return language
        
        # Depois verifica menções no texto
        for language, variations in self.programming_languages.items():
            for variation in variations:
                if variation in text_lower:
                    # Verifica se não é parte de outra palavra
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    if re.search(pattern, text_lower):
                        return language
        
        return None
    
    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extrai blocos de código com suas linguagens."""
        code_blocks = []
        
        # Padrão para blocos de código com markdown
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        
        for lang, code in matches:
            code_blocks.append({
                "language": lang.strip() or "unknown",
                "code": code.strip(),
                "type": "block"
            })
        
        # Padrão para código inline
        inline_pattern = r"`(.*?)`"
        inline_matches = re.findall(inline_pattern, text)
        
        for code in inline_matches:
            code_blocks.append({
                "language": "unknown",
                "code": code.strip(),
                "type": "inline"
            })
        
        return code_blocks
    
    def get_primary_language(self, text: str) -> str:
        """Retorna a linguagem principal detectada ou 'unknown'."""
        lang = self.detect_programming_language(text)
        return lang or "unknown"
    
    def should_use_code_model(self, text: str) -> bool:
        """Determina se devemos usar o modelo especializado em código."""
        intent_info = self.detect_intent(text)
        return intent_info.get("type") == "code"
    
    def get_command_type(self, text: str) -> Optional[str]:
        """Detecta se é um comando especial (/code, /explain, etc)."""
        if text.startswith('/'):
            parts = text[1:].split()
            if parts:
                cmd = parts[0].lower()
                if cmd in ['code', 'c']:
                    return 'code_generation'
                elif cmd in ['explain', 'exp', 'e']:
                    return 'code_explanation'
                elif cmd in ['review', 'rev', 'r']:
                    return 'code_review'
                elif cmd in ['help', 'h']:
                    return 'help'
                elif cmd in ['exit', 'quit', 'q']:
                    return 'farewell'
        return None