#!/usr/bin/env python3
"""
server.py — Servidor MCP: Council Orchestrator (El Orquestador Maestro del Consejo)
Protocolo: Model Context Protocol (MCP / JSON-RPC 2.0)
Expone la capacidad de convocar la deliberación completa de los 5 asesores de Karpathy,
la revisión cruzada anónima y el dictamen del Chairman desde cualquier conversación de chat.
"""

import sys
import os
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROUTER_DEV_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if ROUTER_DEV_DIR not in sys.path:
    sys.path.insert(0, ROUTER_DEV_DIR)

from mcp_bundler import verify_token

TOOL_DEFINITIONS = [
    {
        "name": "council_deliberate",
        "description": "Convoca la sesión completa del Consejo Agéntico Determinista (5 Asesores + Revisión Ciega + Dictamen de Presidencia). Retorna el veredicto y genera reporte HTML.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "La pregunta, propuesta o decisión que el Consejo debe evaluar"
                },
                "backend": {
                    "type": "string",
                    "enum": ["agy", "mock"],
                    "default": "agy",
                    "description": "Motor de inferencia a utilizar (por defecto agy)"
                }
            },
            "required": ["question"]
        }
    }
]

def handle_request(line: str) -> dict:
    try:
        req = json.loads(line)
    except Exception:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})
    
    token = os.environ.get("MCP_BEARER_TOKEN", "")
    auth = verify_token(token)
    
    if not auth.get("valid") and os.environ.get("MCP_BYPASS_AUTH") != "1":
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32001, "message": f"Unauthorized: {auth.get('error')}"}}
        
    scopes = auth.get("scopes", ["read", "execute"])
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "accet-council-orchestrator", "version": "1.0.0"}
            }
        }
        
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOL_DEFINITIONS
            }
        }
        
    elif method == "tools/call":
        if "execute" not in scopes and "admin" not in scopes:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32002, "message": "Scope denied: requires 'execute'"}}
            
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "council_deliberate":
            question = args.get("question", "")
            backend = args.get("backend", "agy")
            
            # Invocar council_runner.py en subproceso determinista
            cmd = [sys.executable, os.path.join(ROUTER_DEV_DIR, "council_runner.py"), "--question", question, "--backend", backend]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                output = proc.stdout if proc.returncode == 0 else f"Error: {proc.stderr}\nOutput: {proc.stdout}"
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": output}]
                    }
                }
            except subprocess.TimeoutExpired:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": "El Consejo excedió el tiempo límite de 300 segundos"}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": f"Fallo al ejecutar el Consejo: {str(e)}"}}
                
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Herramienta no encontrada: {tool_name}"}}
        
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Método no soportado: {method}"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        resp = handle_request(line)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
