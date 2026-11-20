# utils/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Configurações padrão
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "assistant.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Cores para logs no console
class ColoredFormatter(logging.Formatter):
    """Formatter personalizado com cores para o console."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',        # Verde
        'WARNING': '\033[33m',     # Amarelo
        'ERROR': '\033[31m',       # Vermelho
        'CRITICAL': '\033[35m',    # Magenta
        'RESET': '\033[0m'         # Reset
    }
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(name: str, log_level: Optional[int] = None) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger (geralmente __name__)
        log_level: Nível de log (DEBUG, INFO, etc)
    
    Returns:
        logging.Logger configurado
    """
    # Cria diretório de logs se não existir
    LOG_DIR.mkdir(exist_ok=True)
    
    # Cria o logger
    logger = logging.getLogger(name)
    
    # Se o logger já tiver handlers, não adiciona novamente
    if logger.handlers:
        return logger
    
    # Define o nível de log
    level = log_level or DEFAULT_LOG_LEVEL
    logger.setLevel(level)
    
    # Handler para arquivo (com rotação)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_format = logging.Formatter(
        DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Handler para console (com cores)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Usa cores apenas se for terminal interativo
    if sys.stdout.isatty():
        console_format = ColoredFormatter(
            DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    else:
        console_format = logging.Formatter(
            DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT
        )
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado.
    
    Args:
        name: Nome do logger
    
    Returns:
        logging.Logger configurado
    """
    return setup_logger(name)

class LoggerMixin:
    """Mixin para adicionar funcionalidade de logging a classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Retorna o logger da classe."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_debug(self, msg: str, *args, **kwargs):
        """Log em nível DEBUG."""
        self.logger.debug(msg, *args, **kwargs)
    
    def log_info(self, msg: str, *args, **kwargs):
        """Log em nível INFO."""
        self.logger.info(msg, *args, **kwargs)
    
    def log_warning(self, msg: str, *args, **kwargs):
        """Log em nível WARNING."""
        self.logger.warning(msg, *args, **kwargs)
    
    def log_error(self, msg: str, *args, **kwargs):
        """Log em nível ERROR."""
        self.logger.error(msg, *args, **kwargs)
    
    def log_critical(self, msg: str, *args, **kwargs):
        """Log em nível CRITICAL."""
        self.logger.critical(msg, *args, **kwargs)

# Decorator para log de funções
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator para logar chamadas de função.
    
    Args:
        logger: Logger a ser usado (opcional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            logger.debug(f"Chamando {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} concluída com sucesso")
                return result
            except Exception as e:
                logger.error(f"Erro em {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator

# Função para limpar logs antigos
def cleanup_old_logs(days: int = 7):
    """
    Remove logs com mais de 'days' dias.
    
    Args:
        days: Número de dias para manter logs
    """
    import time
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    
    for log_file in LOG_DIR.glob("*.log*"):
        if log_file.name == "assistant.log":
            continue
            
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime < cutoff:
            try:
                log_file.unlink()
                print(f"Removido log antigo: {log_file}")
            except Exception as e:
                print(f"Erro ao remover {log_file}: {e}")

# Configuração inicial
def init_logging():
    """Inicializa o sistema de logging."""
    # Cria diretório de logs
    LOG_DIR.mkdir(exist_ok=True)
    
    # Configura logger raiz
    root_logger = setup_logger("jarvis")
    
    # Limpa logs antigos (opcional)
    # cleanup_old_logs(days=7)
    
    return root_logger

# Executa configuração inicial quando o módulo é importado
root_logger = init_logging()




#apenas teste
#teste de importação# utils/logger.py
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configuração básica de logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Garante que o diretório de logs existe
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configura o logger raiz
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.FileHandler(log_dir / "assistant.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado.
    
    Args:
        name: Nome do módulo (geralmente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)

# Função para configurar nível de debug
def set_debug_mode(enabled: bool = True):
    """Ativa/desativa modo debug."""
    level = logging.DEBUG if enabled else logging.INFO
    logging.getLogger().setLevel(level)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)