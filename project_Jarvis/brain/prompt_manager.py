class PromptManager:

    @staticmethod
    def document_prompt(document_text: str, question: str):

        return f"""
Você é Jarvis, um assistente especialista em análise de documentos.

Documento:
{document_text}

Pergunta:
{question}

Responda de forma clara e objetiva.
"""