# memory/vector_memory.py
import json  
import requests
import numpy as np  
from database.db import Database

OLLAMA_URL = "http://localhost:11434/api/embeddings"

class VectorMemory:
    """
    Gerencia memória vetorial usando embeddings do nomic-embed-text.
    Permite busca semântica no banco de dados.
    """
    
    def __init__(self):
        self.db = Database()
        self.model = "nomic-embed-text"  
    
    def create_embedding(self, text: str) -> list:
        """
        Cria um embedding para o texto usando Ollama.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista com o vetor de embedding
        """
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30 
            )
            
            response.raise_for_status()  
            return response.json()["embedding"]
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar embedding: {e}")
            return []
        except (KeyError, ValueError) as e:
            print(f"Erro ao processar resposta do embedding: {e}")
            return []
    
    def save_embedding(self, text: str, metadata: dict = None):
        """
        Salva embedding no banco de dados.
        
        Args:
            text: Texto original
            metadata: Metadados adicionais (opcional)
        """
        embedding = self.create_embedding(text)
        
        if not embedding:  
            print("⚠️ Embedding vazio, não salvando")
            return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                content_hash = str(hash(text))  # Pode melhorar para sha256 depois
                
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO embeddings
                    (content_hash, content, embedding, model, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        content_hash,
                        text,
                        json.dumps(embedding),  
                        self.model,
                        json.dumps(metadata) if metadata else None  
                    )
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Erro ao salvar embedding: {e}")
            return False
    
    def search_similar(self, query: str, limit: int = 5) -> list:
        """
            Busca textos similares usando similaridade de cosseno.
        
        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de textos similares com scores
        """
        query_embedding = self.create_embedding(query)
        
        if not query_embedding:
            return []
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Busca todos os embeddings
                cursor.execute(
                    "SELECT content, embedding FROM embeddings ORDER BY created_at DESC"
                )
                
                results = []
                query_vec = np.array(query_embedding)
                
                for content, embedding_json in cursor.fetchall():
                    try:
                        # Converte JSON de volta para vetor
                        embedding = np.array(json.loads(embedding_json))
                        
                        # Calcula similaridade de cosseno
                        similarity = np.dot(query_vec, embedding) / (
                            np.linalg.norm(query_vec) * np.linalg.norm(embedding)
                        )
                        
                        results.append({
                            "content": content,
                            "similarity": float(similarity)
                        })
                        
                    except Exception as e:
                        print(f"Erro ao processar embedding: {e}")
                        continue
                
                # Ordena por similaridade e retorna os melhores
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
                
        except Exception as e:
            print(f"Erro na busca semântica: {e}")
            return []
    
    def get_stats(self) -> dict:
        """
            Retorna estatísticas da memória vetorial.
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM embeddings")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT model, COUNT(*) FROM embeddings GROUP BY model")
                models = dict(cursor.fetchall())
                
                return {
                    "total_embeddings": total,
                    "models": models,
                    "status": "active"
                }
        except Exception as e:
            return {
                "total_embeddings": 0,
                "error": str(e),
                "status": "error"
            }
    
    def clear_old_embeddings(self, days: int = 30):
        """
            Remove embeddings mais antigos que X dias.
        
        Args:
            days: Número de dias para manter
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    DELETE FROM embeddings 
                    WHERE julianday('now') - julianday(created_at) > ?
                    """,
                    (days,)
                )
                
                conn.commit()
                print(f"✅ Embeddings antigos removidos: {cursor.rowcount}")
                
        except Exception as e:
            print(f"Erro ao limpar embeddings: {e}")