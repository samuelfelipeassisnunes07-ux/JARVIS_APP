# Jarvis AI

Assistente pessoal em Python com FastAPI, Ollama, MySQL/SQLAlchemy e interface web.

## Estado atual

- Chat com modelos separados para conversa e código.
- Conversas persistentes: a interface reutiliza `conversation_id`; a CLI mantém uma conversa por execução.
- Memórias do usuário incluídas no contexto do modelo. A recuperação atual usa busca textual e memórias importantes, com até cinco itens.
- Identidade web por credencial aleatória criada pelo servidor. Apenas o hash é associado ao usuário no banco; os pedidos usam `Authorization: Bearer <token>`.
- Feedback de 1 a 5 e estatísticas filtradas pelo usuário autenticado.
- Consulta de clima e pesquisa web quando as respectivas chaves estão configuradas.

`memory/advanced_rag.py` e `tools/fine_tuning.py` são módulos experimentais separados. O chat não executa treinamento automático nem utiliza o ChromaDB. O exportador de fine-tuning gera um Modelfile; conversão, importação e qualidade do modelo ainda precisam de validação. Upload de documentos pela API e transcrição de voz pela interface web ainda não estão implementados.

## Executar no Windows

Na pasta `project_Jarvis`, com Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Configure o MySQL usando as variáveis descritas em `.env.example` (ou `DATABASE_URL`). Use uma conta com acesso ao banco configurado. A inicialização tenta criar o banco e as tabelas, portanto a conta precisa dessas permissões na primeira execução.

Inicie o Ollama e instale os modelos configurados em `config/default_config.yaml`. Modelos personalizados, como `jarvis-coder`, precisam estar criados localmente ou ser substituídos na configuração por um modelo disponível.

```powershell
ollama serve
```

Em outro terminal:

```powershell
.\.venv\Scripts\python.exe api.py
```

Abra http://127.0.0.1:8000. A própria API serve a interface; não é necessário um segundo servidor. `/docs` oferece a documentação dos endpoints, e `/health` indica se o assistente foi inicializado (não é uma verificação contínua dos serviços).

Para a CLI:

```powershell
.\.venv\Scripts\python.exe app.py
```

## Identidade e compatibilidade

A credencial fica no `localStorage` do navegador; o identificador da conversa fica no `sessionStorage` da aba e sobrevive a recarregamentos. Navegadores/perfis diferentes recebem identidades diferentes. Abas do mesmo perfil compartilham a identidade. Limpar o armazenamento remove a credencial e perde o acesso por essa interface às memórias anteriores. Não há recuperação de conta, login por senha ou revogação de credenciais nesta versão.

Dados existentes não são apagados. A CLI continua usando o usuário `default`; a nova interface web usa identidades próprias e não importa automaticamente as memórias antigas desse usuário.

Para clientes da API:

1. Envie `POST /session` e guarde o `token` retornado.
2. Use esse token como Bearer nos endpoints de dados.
3. Envie `POST /chat` com `{"text":"Olá"}`.
4. Nos pedidos seguintes, inclua o `conversation_id` retornado.

`user_id`, `username` e o antigo `session_id` não são aceitos no corpo de `/chat`. No feedback, `session_id` é o ID numérico da conversa convertido em texto. O servidor verifica a propriedade dessa conversa.

A execução padrão fica restrita a `127.0.0.1`. A emissão aberta de identidades atende ao protótipo local; uma publicação pública ainda precisa de política de cadastro, limites de uso, HTTPS e gestão de credenciais.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
node --test tests/frontend.test.cjs
```

As regressões usam SQLite temporário e LLM simulado, sem alterar o banco real. O teste de integração MySQL é ignorado por padrão. Para executá-lo, configure um banco dedicado de testes e defina `JARVIS_TEST_MYSQL=1`; ele grava usuários e mensagens nesse banco.

Os testes verificam conversas, memórias, validação, credenciais, isolamento, estatísticas e o contrato da interface. Não substituem uma validação com os modelos reais do Ollama.
