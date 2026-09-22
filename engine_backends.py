"""
engine_backends.py — Abstracción de Motores de Inferencia para Servidores MCP
Estándar: STD-AGT-COUNCIL-001 / STD-FRG-SKILL-001

Aísla el protocolo MCP de la capa física de cómputo:
- AgyCliBackend: Inferencia local en macOS vía Antigravity CLI ($0.00)
- OmniRouteBackend: Inferencia local o remota vía gateway OmniRoute / OpenAI compatible
- MockBackend: Inferencia determinista simulada para CI/CD y tests
"""

import os
import subprocess
import urllib.request
import json
import time

class BaseEngineBackend:
    def execute(self, prompt: str, timeout: int = 180) -> str:
        raise NotImplementedError

class AgyCliBackend(BaseEngineBackend):
    def execute(self, prompt: str, timeout: int = 180) -> str:
        try:
            result = subprocess.run(
                ["agy", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode != 0:
                err = result.stderr.strip() or f"Exit code {result.returncode}"
                return f"[ERROR AGY]: {err}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return f"[ERROR AGY]: Timeout de ejecución ({timeout}s)."
        except Exception as e:
            return f"[ERROR AGY INVOCATION]: {str(e)}"

class OmniRouteBackend(BaseEngineBackend):
    def __init__(self, base_url: str = None, model: str = "auto"):
        self.base_url = base_url or os.environ.get("OMNIROUTE_URL", "http://localhost:20128")
        self.model = model

    def execute(self, prompt: str, timeout: int = 180) -> str:
        endpoint = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"[ERROR OMNIROUTE]: {str(e)}"

class MockBackend(BaseEngineBackend):
    def execute(self, prompt: str, timeout: int = 180) -> str:
        time.sleep(0.1)
        return f"[MOCK BACKEND]: Respuesta determinista generada para prompt de longitud {len(prompt)}."

def get_engine_backend(name: str = None) -> BaseEngineBackend:
    backend_name = name or os.environ.get("MCP_BACKEND", "agy").lower()
    if backend_name == "omniroute":
        return OmniRouteBackend()
    elif backend_name == "mock":
        return MockBackend()
    return AgyCliBackend()
