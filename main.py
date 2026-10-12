import os
import json
import ollama

MODEL = "gemma4:e2b"

# 1) A ferramenta: uma função Python comum
def list_dir(path: str = ".") -> dict:
    base = os.path.abspath(".")
    alvo = os.path.abspath(path)
    if not alvo.startswith(base):
        return {"erro": "caminho fora do diretório permitido"}
    try:
        return {"itens": os.listdir(alvo)}
    except Exception as e:
        return {"erro": str(e)}

FERRAMENTAS = {"list_dir": list_dir}

# 2) A descrição que o modelo enxerga (formato OpenAI/Ollama tools)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Lista arquivos e pastas de um diretório do projeto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho relativo, ex: '.'",
                    }
                },
            },
        },
    }
]

# 3) O loop
pergunta = input("pergunta> ")
messages = [{"role": "user", "content": pergunta}]

for _ in range(10):
    resp = ollama.chat(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )

    msg = resp["message"]
    messages.append(msg)

    chamadas = msg.get("tool_calls") or []

    if not chamadas:
        print(msg.get("content", ""))
        break

    for c in chamadas:
        fn = c["function"]
        nome = fn["name"]
        # args pode vir como dict ou string JSON dependendo da versão
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args) if args else {}

        print(f"[ferramenta] {nome}({args})")
        resultado = FERRAMENTAS[nome](**args)

        messages.append({
            "role": "tool",
            "name": nome,
            "content": json.dumps(resultado, ensure_ascii=False),
        })