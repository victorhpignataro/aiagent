import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-flash-latest"

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

# 2) A descrição que o modelo enxerga
declaracao = types.FunctionDeclaration(
    name="list_dir",
    description="Lista arquivos e pastas de um diretório do projeto.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"path": types.Schema(type="STRING", description="Caminho relativo, ex: '.'")},
    ),
)
config = types.GenerateContentConfig(tools=[types.Tool(function_declarations=[declaracao])])

# 3) O loop
pergunta = input("pergunta> ")
contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]

for _ in range(10):
    resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
    msg = resp.candidates[0].content
    contents.append(msg)
    try:
        print(msg, type(msg), msg.role)
        chamadas = [p in (msg.parts or []) if p.function_call]
    except Exception as e:
        print("erro meu", e)

    chamadas = [p.function_call for p in (msg.parts or []) if p.function_call]
    if not chamadas:
        print(resp.text)
        break

    respostas = []
    for c in chamadas:
        print(f"[ferramenta] {c.name}({dict(c.args)})")
        resultado = FERRAMENTAS[c.name](**c.args)
        respostas.append(types.Part.from_function_response(name=c.name, response={"result": resultado}))
    contents.append(types.Content(role="user", parts=respostas))