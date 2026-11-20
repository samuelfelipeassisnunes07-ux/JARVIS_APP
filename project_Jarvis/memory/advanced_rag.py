# memory/advanced_rag.py
"""
Sistema RAG avançado com ChromaDB para busca semântica eficiente.
Melhora o sistema de memória vetorial existente.
"""

import chromadb
from chromadb.config import Settings
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer
from database.db import Database

logger = logging.get_logger(__name__)

class AdvancedRAG:
    """
    Sistema RAG avançado usando ChromaDB + Sentence Transformers.
    Fornece busca semântica mais precisa e eficiente.
    """

    def __init__(self, collection_name: str = "jarvis_memory", persist_directory: str = "./data/chroma"):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Inicializa ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Carrega modelo de embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Conecta ao banco relacional para compatibilidade
        self.db = Database()

        # Cria ou obtém coleção
        self.collection = self._get_or_create_collection()

        # Migra dados existentes se necessário
        self._migrate_existing_data()

    def _get_or_create_collection(self):
        """Cria ou obtém a coleção ChromaDB."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Coleção '{self.collection_name}' encontrada com {collection.count()} documentos")
        except ValueError:
            collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Coleção '{self.collection_name}' criada")

        return collection

    def _migrate_existing_data(self):
        """Migra dados existentes do SQLite para ChromaDB."""
        try:
            # Verifica se já foi migrado
            if self.collection.count() > 0:
                logger.info("Dados já migrados para ChromaDB")
                return

            # Busca dados existentes
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content, embedding, metadata FROM embeddings")
                rows = cursor.fetchall()

            if not rows:
                logger.info("Nenhum dado para migrar")
                return

            logger.info(f"Migrando {len(rows)} documentos para ChromaDB...")

            documents = []
            embeddings = []
            metadatas = []
            ids = []

            for i, (content, embedding_json, metadata_json) in enumerate(rows):
                try:
                    # Converte embedding JSON para lista
                    if embedding_json:
                        embedding = json.loads(embedding_json)
                    else:
                        # Gera novo embedding se não existir
                        embedding = self.embedding_model.encode(content).tolist()

                    documents.append(content)
                    embeddings.append(embedding)
                    metadatas.append(json.loads(metadata_json) if metadata_json else {})
                    ids.append(f"doc_{i}")

                except Exception as e:
                    logger.warning(f"Erro ao migrar documento {i}: {e}")
                    continue

            # Adiciona em lotes para performance
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                self.collection.add(
                    documents=documents[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )

            logger.info(f"Migração concluída: {len(documents)} documentos migrados")

        except Exception as e:
            logger.error(f"Erro na migração: {e}")

    def add_document(self, content: str, metadata: Optional[Dict] = None, doc_id: Optional[str] = None) -> str:
        """
        Adiciona um documento ao sistema RAG.

        Args:
            content: Conteúdo do documento
            metadata: Metadados opcionais
            doc_id: ID opcional do documento

        Returns:
            ID do documento adicionado
        """
        # Gera embedding
        embedding = self.embedding_model.encode(content).tolist()

        # Gera ID se não fornecido
        if doc_id is None:
            import hashlib
            doc_id = hashlib.md5(content.encode()).hexdigest()

        # Adiciona à coleção
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

        # Também salva no banco relacional para compatibilidade
        self.db.save_embedding(content, metadata)

        logger.info(f"Documento adicionado: {doc_id}")
        return doc_id

    def search_similar(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict]:
        """
        Busca documentos similares à query.

        Args:
            query: Texto de busca
            n_results: Número máximo de resultados
            where: Filtros de metadados (opcional)

        Returns:
            Lista de documentos similares com scores
        """
        try:
            # Busca na coleção
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )

            # Formata resultados
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}

                    # Converte distância para similaridade (1 / (1 + distance))
                    similarity = 1 / (1 + distance)

                    formatted_results.append({
                        'content': doc,
                        'similarity': float(similarity),
                        'metadata': metadata,
                        'distance': float(distance)
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    def retrieve_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Recupera contexto relevante para uma query, limitado por tokens.

        Args:
            query: Query do usuário
            max_tokens: Número máximo de tokens no contexto

        Returns:
            Contexto concatenado
        """
        # Busca documentos similares
        results = self.search_similar(query, n_results=10)

        if not results:
            return ""

        # Ordena por similaridade e filtra por relevância
        relevant_docs = [doc for doc in results if doc['similarity'] > 0.3]

        # Concatena documentos até o limite de tokens
        context_parts = []
        current_tokens = 0

        for doc in relevant_docs:
            # Estimativa simples de tokens (1 token ≈ 4 caracteres)
            doc_tokens = len(doc['content']) // 4

            if current_tokens + doc_tokens > max_tokens:
                break

            context_parts.append(doc['content'])
            current_tokens += doc_tokens

        context = "\n\n".join(context_parts)
        logger.info(f"Contexto recuperado: {len(context_parts)} documentos, ~{current_tokens} tokens")

        return context

    def update_document(self, doc_id: str, new_content: str, new_metadata: Optional[Dict] = None):
        """
        Atualiza um documento existente.

        Args:
            doc_id: ID do documento
            new_content: Novo conteúdo
            new_metadata: Novos metadados (opcional)
        """
        try:
            # Remove documento antigo
            self.collection.delete(ids=[doc_id])

            # Adiciona novo
            self.add_document(new_content, new_metadata, doc_id)

            logger.info(f"Documento atualizado: {doc_id}")

        except Exception as e:
            logger.error(f"Erro ao atualizar documento {doc_id}: {e}")

    def delete_document(self, doc_id: str):
        """Remove um documento da coleção."""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Documento removido: {doc_id}")
        except Exception as e:
            logger.error(f"Erro ao remover documento {doc_id}: {e}")

    def get_stats(self) -> Dict:
        """Retorna estatísticas da coleção."""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection_name,
                'embedding_model': 'all-MiniLM-L6-v2'
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def clear_collection(self):
        """Limpa toda a coleção (use com cuidado!)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.warning("Coleção limpa completamente")
        except Exception as e:
            logger.error(f"Erro ao limpar coleção: {e}")

# Função para integrar com o sistema existente
def enhance_memory_with_rag():
    """
    Integra o RAG avançado com o sistema de memória existente.
    Substitui o VectorMemory antigo por uma versão melhorada.
    """
    rag_system = AdvancedRAG()

    # Exemplo de uso
    print("Sistema RAG avançado inicializado!")
    print(f"Documentos na base: {rag_system.get_stats()['total_documents']}")

    return rag_system

if __name__ == "__main__":
    # Teste do sistema
    rag = enhance_memory_with_rag()

    # Adiciona alguns documentos de exemplo
    rag.add_document(
        "Jarvis é um assistente pessoal inteligente com memória de longo prazo.",
        {"tipo": "conhecimento_geral", "fonte": "sistema"}
    )

    rag.add_document(
        "O usuário prefere respostas em português brasileiro e gosta de explicações detalhadas.",
        {"tipo": "preferencia_usuario", "fonte": "feedback"}
    )

    # Testa busca
    results = rag.search_similar("assistente pessoal", n_results=3)
    print("Resultados da busca:")
    for result in results:
        print(f"- Similaridade: {result['similarity']:.3f}")
        print(f"  Conteúdo: {result['content'][:100]}...")