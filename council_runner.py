#!/usr/bin/env python3
"""
council_runner.py — Ejecutor Determinístico del Consejo Agéntico de ACCET
Norma: STD-AGT-COUNCIL-001 (Metodología LLM Council / Andrej Karpathy)
Zero API Cost: Ejecución mediante Antigravity CLI (`agy -p`) o endpoints locales de OmniRoute.

Fases de Ejecución:
1. Frame: Encuadre determinista del problema (vía prompt Lyra 4-D o argumento).
2. Convene: Convocatoria paralela de los 5 asesores ortogonales (The Contrarian, First Principles, The Expansionist, The Outsider, The Executor).
3. Anonymous Peer Review: Revisión crítica cruzada de los argumentos anonimizados.
4. Chairman Synthesis: Deliberación ejecutiva final, resolución de choques y definición de "The One Thing".
5. Persistence & Report: Registro en JSON, Markdown y generación de reporte HTML interactivo.
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

ROLES = [
    {"id": "the-contrarian", "name": "The Contrarian", "letter": "Asesor A"},
    {"id": "first-principles-thinker", "name": "First Principles Thinker", "letter": "Asesor B"},
    {"id": "the-expansionist", "name": "The Expansionist", "letter": "Asesor C"},
    {"id": "the-outsider", "name": "The Outsider", "letter": "Asesor D"},
    {"id": "the-executor", "name": "The Executor", "letter": "Asesor E"},
]

def load_skill_content(role_id: str) -> str:
    skill_path = os.path.join(SKILLS_DIR, role_id, "SKILL.md")
    if not os.path.exists(skill_path):
        # Fallback to .agents/skills
        fallback_path = os.path.join(BASE_DIR, "..", ".agents", "skills", role_id, "SKILL.md")
        if os.path.exists(fallback_path):
            skill_path = fallback_path
        else:
            return f"# Skill {role_id}\nActúa bajo el rol de {role_id}."
    with open(skill_path, "r", encoding="utf-8") as f:
        return f.read()

try:
    from engine_backends import get_engine_backend
except ImportError:
    get_engine_backend = None

def call_backend(prompt: str, backend: str = "agy", mock: bool = False) -> str:
    """Invoca el backend de inferencia seleccionado (agy, omniroute o mock)."""
    selected = "mock" if mock else backend
    if get_engine_backend:
        eng = get_engine_backend(selected)
        if eng:
            return eng.execute(prompt, timeout=180)

    if backend == "agy":
        try:
            result = subprocess.run(
                ["agy", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode != 0:
                err = result.stderr.strip() or f"Exit code {result.returncode}"
                return f"[ERROR AGY]: {err}"
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "[ERROR AGY]: Timeout de ejecución (180s)."
        except Exception as e:
            return f"[ERROR AGY INVOCATION]: {str(e)}"
    
    return f"[ERROR]: Backend {backend} no soportado o no configurado."

def run_advisor(role: dict, framed_problem: str, backend: str, mock: bool) -> dict:
    role_id = role["id"]
    role_name = role["name"]
    skill_doc = load_skill_content(role_id)
    
    prompt = f"""Instrucciones de Rol:
{skill_doc}

---
PROBLEMA / PROPUESTA A EVALUAR:
{framed_problem}

---
Recuerda cumplir estrictamente tu identidad, lente de pensamiento, reglas de comportamiento y el formato de salida estructurado especificado en tu Skill. Mantén tu respuesta entre 150 y 300 palabras.
"""
    start_t = time.time()
    response = call_backend(prompt, backend=backend, mock=mock)
    elapsed = round(time.time() - start_t, 2)
    
    return {
        "role_id": role_id,
        "name": role_name,
        "letter": role["letter"],
        "elapsed_seconds": elapsed,
        "response": response
    }

def run_peer_review(advisors_results: list, framed_problem: str, backend: str, mock: bool) -> str:
    """Fase de revisión por pares ciega."""
    anonymized_dossier = []
    for adv in advisors_results:
        anonymized_dossier.append(f"### {adv['letter']} (Lente Evaluador Anónimo)\n{adv['response']}\n")
    
    full_dossier = "\n---\n".join(anonymized_dossier)
    
    peer_prompt = f"""Eres el Revisor Crítico de Evaluación por Pares del Consejo Agéntico.
A continuación se presentan 5 evaluaciones anónimas (Asesor A, B, C, D, E) sobre el siguiente problema:

PROBLEMA ORIGINAL:
{framed_problem}

EVALUACIONES ANÓNIMAS:
{full_dossier}

---
TAREA DE REVISIÓN CIEGA:
Evalúa objetivamente las 5 respuestas y produce un análisis de máximo 250 palabras respondiendo:
1. ¿Cuál es el argumento individual más sólido y revelador de todo el conjunto (citando por letra)?
2. ¿Cuál es la mayor debilidad, sesgo peligroso o ingenuidad técnica encontrada (citando por letra)?
3. ¿Qué punto ciego crítico no fue abordado adecuadamente por ninguno de los asesores?
"""
    return call_backend(peer_prompt, backend=backend, mock=mock)

def run_chairman(advisors_results: list, peer_review: str, framed_problem: str, backend: str, mock: bool) -> str:
    chairman_skill = load_skill_content("council-chairman")
    
    briefing = []
    for adv in advisors_results:
        briefing.append(f"### {adv['name']} ({adv['letter']})\n{adv['response']}\n")
    
    chairman_prompt = f"""Instrucciones de Presidencia:
{chairman_skill}

---
PROBLEMA ORIGINAL:
{framed_problem}

---
INFORME DE LOS 5 ASESORES:
{chr(10).join(briefing)}

---
EVALUACIÓN CRUZADA ANÓNIMA (PEER REVIEW):
{peer_review}

---
Emite tu Dictamen Final Ejecutivo siguiendo estrictamente la estructura:
1. Puntos de Consenso Inequívocos
2. Choques Críticos y Disensos Irreconciliables (y cómo los resuelves)
3. Puntos Ciegos Descubiertos
4. Veredicto Final Ejecutivo (DECISIÓN: PROCEDER / PIVOTAR / ABORTAR)
5. La Primera Acción Innegociable (The One Thing to Do First)
"""
    return call_backend(chairman_prompt, backend=backend, mock=mock)

def generate_html_report(session_data: dict, output_path: str):
    ts = session_data["timestamp"]
    problem = session_data["framed_problem"]
    chairman = session_data["chairman_synthesis"]
    peer = session_data["peer_review"]
    advisors = session_data["advisors"]
    
    advisor_cards = ""
    for adv in advisors:
        clean_resp = adv['response'].replace('\n', '<br>')
        advisor_cards += f"""
        <div class="advisor-card">
            <div class="card-header">
                <span class="badge">{adv['letter']}</span>
                <h3>{adv['name']}</h3>
                <span class="time">{adv['elapsed_seconds']}s</span>
            </div>
            <div class="card-body">
                {clean_resp}
            </div>
        </div>
        """
        
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consejo Agéntico — Sesión {ts}</title>
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-bright: #f0f6fc;
            --accent: #58a6ff;
            --success: #238636;
            --warning: #d29922;
            --danger: #f85149;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ color: var(--text-bright); margin-bottom: 5px; }}
        .meta {{ color: #8b949e; font-size: 0.9em; }}
        .section-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 30px;
        }}
        .section-title {{
            color: var(--accent);
            margin-top: 0;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}
        .advisors-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .advisor-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }}
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            border-bottom: 1px solid #21262d;
            padding-bottom: 8px;
        }}
        .card-header h3 {{
            margin: 0;
            font-size: 1.1em;
            color: var(--text-bright);
        }}
        .badge {{
            background: #238636;
            color: #fff;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .time {{ color: #8b949e; font-size: 0.8em; }}
        .card-body {{ font-size: 0.9em; }}
        .chairman-box {{
            background: #1c2128;
            border-left: 4px solid var(--accent);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏛️ Dictamen del Consejo Agéntico Determinista</h1>
            <div class="meta">Protocolo: STD-AGT-COUNCIL-001 | Sesión: {ts} | Backend: {session_data.get('backend')}</div>
        </header>

        <div class="section-box">
            <h2 class="section-title">🎯 Problema o Decisión Evaluada</h2>
            <p>{problem.replace(chr(10), '<br>')}</p>
        </div>

        <div class="section-box chairman-box">
            <h2 class="section-title" style="color: #58a6ff;">⚖️ Dictamen de la Presidencia (Council Chairman)</h2>
            <div>{chairman.replace(chr(10), '<br>')}</div>
        </div>

        <div class="section-box">
            <h2 class="section-title">🔍 Revisión por Pares Anónima (Peer Review)</h2>
            <div>{peer.replace(chr(10), '<br>')}</div>
        </div>

        <h2 style="color: var(--text-bright);">👥 Deliberaciones Individuales de los 5 Asesores</h2>
        <div class="advisors-grid">
            {advisor_cards}
        </div>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(description="Ejecutor Determinista del Consejo Agéntico (STD-AGT-COUNCIL-001)")
    parser.add_argument("--question", "-q", type=str, help="Pregunta o propuesta a evaluar directamente.")
    parser.add_argument("--file", "-f", type=str, help="Ruta a un archivo .prompt.md o .md con el framed problem.")
    parser.add_argument("--backend", "-b", type=str, default="agy", choices=["agy", "omniroute"], help="Motor de inferencia.")
    parser.add_argument("--mock", action="store_true", help="Ejecuta en modo simulación rápida sin llamar a la CLI.")
    parser.add_argument("--parallel", action="store_true", default=True, help="Ejecuta los 5 asesores en paralelo.")
    args = parser.parse_args()

    # Resolver problema
    framed_problem = ""
    if args.file:
        file_path = args.file
        if not os.path.isabs(file_path):
            if os.path.exists(file_path):
                file_path = os.path.abspath(file_path)
            elif os.path.exists(os.path.join(BASE_DIR, file_path)):
                file_path = os.path.join(BASE_DIR, file_path)
            elif os.path.exists(os.path.join(BASE_DIR, "..", file_path)):
                file_path = os.path.join(BASE_DIR, "..", file_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                framed_problem = f.read()
        else:
            print(f"Error: Archivo {args.file} no encontrado.")
            sys.exit(1)
    elif args.question:
        framed_problem = args.question
    else:
        print("Uso: python3 council_runner.py --question '¿Debemos hacer X?' O --file 'ruta/al/prompt.md'")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    
    print(f"\n========================================================")
    print(f"🏛️  INICIANDO CONSEJO AGÉNTICO DETERMINISTA (STD-AGT-COUNCIL-001)")
    print(f"========================================================")
    print(f"• Timestamp: {timestamp}")
    print(f"• Backend:   {args.backend.upper()} (Mock: {args.mock})")
    print(f"• Problema:  {framed_problem[:120]}...\n")

    # FASE 2: CONVENE (5 Asesores)
    print("⏳ [Fase 2/4] Convocando a los 5 Asesores en deliberación ciega...")
    advisors_results = []
    
    if args.parallel:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_role = {
                executor.submit(run_advisor, role, framed_problem, args.backend, args.mock): role 
                for role in ROLES
            }
            for future in as_completed(future_to_role):
                res = future.result()
                advisors_results.append(res)
                print(f"   ✓ {res['name']} completó análisis en {res['elapsed_seconds']}s")
    else:
        for role in ROLES:
            res = run_advisor(role, framed_problem, args.backend, args.mock)
            advisors_results.append(res)
            print(f"   ✓ {res['name']} completó análisis en {res['elapsed_seconds']}s")

    # Ordenar por el orden canónico
    order_map = {r["id"]: idx for idx, r in enumerate(ROLES)}
    advisors_results.sort(key=lambda x: order_map.get(x["role_id"], 99))

    # FASE 3: ANONYMOUS PEER REVIEW
    print("\n⏳ [Fase 3/4] Ejecutando Revisión Cruzada Anónima (Peer Review)...")
    peer_review = run_peer_review(advisors_results, framed_problem, args.backend, args.mock)
    print("   ✓ Revisión por pares completada.")

    # FASE 4: CHAIRMAN SYNTHESIS
    print("\n⏳ [Fase 4/4] Deliberación de Presidencia (Council Chairman)...")
    chairman_synthesis = run_chairman(advisors_results, peer_review, framed_problem, args.backend, args.mock)
    print("   ✓ Dictamen de Presidencia emitido con éxito.\n")

    # FASE 5: PERSISTENCE
    session_data = {
        "timestamp": timestamp,
        "backend": args.backend,
        "mock": args.mock,
        "framed_problem": framed_problem,
        "advisors": advisors_results,
        "peer_review": peer_review,
        "chairman_synthesis": chairman_synthesis
    }

    json_path = os.path.join(SESSIONS_DIR, f"{timestamp}_council_session.json")
    md_path = os.path.join(SESSIONS_DIR, f"{timestamp}_council_session.md")
    html_path = os.path.join(SESSIONS_DIR, f"{timestamp}_report.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    # Markdown output
    md_content = f"""# Sesión de Consejo Agéntico: {timestamp}
**Norma:** STD-AGT-COUNCIL-001  
**Backend:** {args.backend} | **Mock:** {args.mock}

## Problema Evaluado
{framed_problem}

---

## ⚖️ Dictamen de la Presidencia (Council Chairman)
{chairman_synthesis}

---

## 🔍 Revisión Cruzada Anónima (Peer Review)
{peer_review}

---

## 👥 Deliberaciones Individuales de los Asesores

"""
    for adv in advisors_results:
        md_content += f"### {adv['name']} ({adv['letter']}) — [{adv['elapsed_seconds']}s]\n\n{adv['response']}\n\n---\n\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    generate_html_report(session_data, html_path)

    print("========================================================")
    print(f"🎉 CONSEJO AGÉNTICO COMPLETADO CON ÉXITO")
    print(f"========================================================")
    print(f"📄 Sesión JSON: {json_path}")
    print(f"📝 Sesión MD:   {md_path}")
    print(f"🌐 Reporte HTML:{html_path}")
    print("\nDictamen Ejecutivo Rápido:")
    print("--------------------------")
    for line in chairman_synthesis.split("\n")[:15]:
        print(line)
    print("...\n")

if __name__ == "__main__":
    main()
