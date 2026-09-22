# 🏛️ Council Orchestrator
> **Deterministic Multi-Agent LLM Council Server**  
> Estándar: `STD-AGT-COUNCIL-001` | Versión: `1.0.0`

`council-orchestrator` es un servidor MCP maestro que implementa la metodología deliberativa de **LLM Council de Andrej Karpathy**, adaptada para ejecución determinista y soberana.

---

## 🧭 Flujo en 4 Fases
1. **Convocatoria Paralela:** Dispara a 5 asesores ortogonales (`The Contrarian`, `First Principles`, `The Expansionist`, `The Outsider`, `The Executor`).
2. **Evaluación Ciega (Peer Review):** Anonimiza las posturas para calificar debilidades y argumentos sin sesgos de modelo.
3. **Síntesis del Chairman:** Emite dictamen ejecutivo (Consensos, Choques, Puntos Ciegos, Veredicto y *The One Thing*).
4. **Persistencia Visual:** Genera sesiones JSON, Markdown y un reporte interactivo en HTML.

---

## 🛠️ Herramientas Expuestas

| Herramienta | Descripción | Parámetros |
| :--- | :--- | :--- |
| `council_deliberate` | Ejecuta la sesión completa de deliberación del Consejo. | `{"question": "¿Debemos hacer X?", "backend": "agy"}` |

---

## 📦 Configuración en Claude Desktop o Antigravity IDE:
```json
{
  "mcpServers": {
    "council_orchestrator": {
      "command": "python3",
      "args": ["/Users/accet/Documents/council-orchestrator/server.py"],
      "env": {
        "MCP_BEARER_TOKEN": "tu_token_aqui"
      }
    }
  }
}
```
