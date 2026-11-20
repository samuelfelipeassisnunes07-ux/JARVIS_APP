from typing import Any, Dict, List

import requests

from config.settings import settings


class WebSearchService:
    """Busca na web com Tavily e devolve resultados prontos para o usuário."""

    def __init__(self):
        self.api_key = settings.get("TAVILY_API_KEY", "")
        self.endpoint = "https://api.tavily.com/search"

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY não configurada")

        response = requests.post(
            self.endpoint,
            json={
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "topic": "general",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("results", [])

    def answer(self, query: str, max_results: int = 5) -> str:
        results = self.search(query, max_results)
        if not results:
            return "Não encontrei resultados para essa busca."

        lines = [f"Encontrei estas informações sobre: {query}\n"]
        for index, result in enumerate(results, start=1):
            title = result.get("title", "Resultado sem título")
            content = " ".join((result.get("content") or "").split())
            if len(content) > 350:
                content = content[:347] + "..."
            url = result.get("url", "")
            lines.append(f"{index}. {title}\n{content}\nFonte: {url}")
        return "\n\n".join(lines)
