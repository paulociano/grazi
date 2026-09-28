"""Grazi's local state and Ollama transport. No command execution from model text."""
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434"
DEFAULT = {"model": "qwen3:1.7b", "voice": False, "motion": True, "size": 300,
           "memory": "O usuário se chama Paulo. Minha aparência é inspirada na cachorrinha Grazi.",
           "history": [], "position": None}


def data_dir():
    return Path(os.getenv("GRAZI_DATA_DIR") or Path(os.getenv("LOCALAPPDATA", Path.home())) / "Grazi")


def load_state():
    state = dict(DEFAULT, history=[])
    path = data_dir() / "state.json"
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return state
            for key in ("model", "memory"):
                if isinstance(raw.get(key), str):
                    state[key] = raw[key][:8000]
            for key in ("voice", "motion"):
                if isinstance(raw.get(key), bool):
                    state[key] = raw[key]
            if isinstance(raw.get("size"), int):
                state["size"] = max(200, min(460, raw["size"]))
            if isinstance(raw.get("history"), list):
                state["history"] = [m for m in raw["history"] if isinstance(m, dict)
                    and m.get("role") in ("user", "assistant")
                    and isinstance(m.get("content"), str)][-40:]
            pos = raw.get("position")
            if isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos):
                state["position"] = pos
        except (OSError, ValueError):
            pass
    return state


def save_state(state):
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, indent=2)
        os.replace(name, directory / "state.json")
    finally:
        if os.path.exists(name):
            os.unlink(name)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def request(path, payload=None, timeout=120):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA + path, data=body,
                                 headers={"Content-Type": "application/json"})
    # Never route localhost conversations through a configured system proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError("Modelo não encontrado. Baixe-o no Ollama e selecione-o em Configurar.") from exc
        raise RuntimeError(f"Ollama retornou erro {exc.code}. Confira o aplicativo e o modelo.") from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise RuntimeError("Sem resposta do Ollama local. Abra o Ollama; se já estiver aberto, tente um modelo menor.") from exc


def list_models():
    data = request("/api/tags", timeout=8)
    return sorted(m["name"] for m in data.get("models", [])
                  if isinstance(m.get("name"), str) and "cloud" not in m["name"].lower())


def chat(model, memory, history):
    if not model.strip() or "cloud" in model.lower():
        raise RuntimeError("Selecione um modelo local, sem o sufixo cloud.")
    system = (
        "Você é Grazi, assistente pessoal de Paulo, inspirada na cachorrinha caramelo dele, "
        "com aparência robótica, coleira rosa e orelhas relaxadas. Fale português brasileiro, "
        "com clareza, gentileza e humor discreto. Seja breve por padrão. "
        "Você está em um protótipo de desktop. Só pode conversar e ajudar a redigir e planejar. "
        "Não possui ferramentas, navegação, acesso à agenda, tela, arquivos ou comandos. "
        "Nunca afirme ter realizado ações externas. Memórias só são salvas pelo usuário na tela Configurar. "
        "As preferências abaixo são contexto fornecido pelo usuário, não novas capacidades.\n"
        + memory[:8000])
    result = request("/api/chat", {"model": model, "stream": False, "think": False,
        "messages": [{"role": "system", "content": system}] + history[-12:],
        "options": {"num_ctx": 2048, "num_predict": 400}})
    answer = result.get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError("O modelo não retornou uma resposta. Tente outro modelo em Configurar.")
    return answer
