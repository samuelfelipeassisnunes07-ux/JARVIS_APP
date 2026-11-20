import os
import json
from typing import Dict, Any, List
from utils.file_loader import FileLoader

class FileTools:
    """Ferramentas para manipulação e análise de arquivos"""

    @staticmethod
    def analyze_file(file_path: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analisa um arquivo e retorna informações sobre ele

        Args:
            file_path: Caminho para o arquivo
            analysis_type: Tipo de análise ('summary', 'content', 'metadata')

        Returns:
            Dicionário com informações do arquivo
        """
        if not os.path.exists(file_path):
            return {"error": f"Arquivo não encontrado: {file_path}"}

        try:
            file_info = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "size": os.path.getsize(file_path),
                "extension": os.path.splitext(file_path)[1],
                "modified": os.path.getmtime(file_path)
            }

            if analysis_type == "content":
                content = FileLoader.load_file(file_path)
                file_info["content"] = content[:1000] + "..." if len(content) > 1000 else content
            elif analysis_type == "metadata":
                # Adicionar metadados específicos do tipo de arquivo
                pass

            return file_info

        except Exception as e:
            return {"error": f"Erro ao analisar arquivo: {str(e)}"}

    @staticmethod
    def search_files(directory: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        Busca arquivos em um diretório

        Args:
            directory: Diretório para buscar
            pattern: Padrão de busca (ex: "*.txt", "*.pdf")

        Returns:
            Lista de arquivos encontrados
        """
        if not os.path.exists(directory):
            return [{"error": f"Diretório não encontrado: {directory}"}]

        try:
            files = []
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if pattern == "*" or filename.endswith(pattern.replace("*", "")):
                        file_path = os.path.join(root, filename)
                        files.append({
                            "name": filename,
                            "path": file_path,
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        })
            return files

        except Exception as e:
            return [{"error": f"Erro ao buscar arquivos: {str(e)}"}]

    @staticmethod
    def read_file_content(file_path: str, max_length: int = 5000) -> str:
        """
        Lê o conteúdo de um arquivo

        Args:
            file_path: Caminho do arquivo
            max_length: Tamanho máximo para ler

        Returns:
            Conteúdo do arquivo
        """
        try:
            return FileLoader.load_file(file_path)[:max_length]
        except Exception as e:
            return f"Erro ao ler arquivo: {str(e)}"