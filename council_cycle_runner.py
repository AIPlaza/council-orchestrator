#!/usr/bin/env python3
"""
council_cycle_runner.py — Orquestador del Patrón Canónico Council-Cycle (3 + 1)
Norma: STD-AGT-COUNCIL-002
Costo Computacional: $0.00 (Antigravity CLI / OmniRoute local)

Fases:
1. Validación determinista de pre-condiciones y dossiers de entrada (<1,500 tokens).
2. Ejecución secuencial/aislada de los 3 Consejos Especializados (Shared-Nothing).
3. Ensamblaje del dossier crudo consolidado de las 3 sesiones (sin pre-síntesis).
4. Ejecución del Consejo de Meta-Síntesis y Plan de Implementación Táctico.
5. Emisión de reportes finales y actualización de punteros de estado.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COUNCIL_RUNNER = os.path.join(BASE_DIR, "council_runner.py")

def run_single_council(prompt_file: str, tag: str, backend: str = "agy") -> bool:
    print(f"\n========================================================")
    print(f"🚀 EJECUTANDO SUB-CONSEJO: {tag}")
    print(f"• Archivo: {prompt_file}")
    print(f"========================================================")
    cmd = [
        sys.executable,
        COUNCIL_RUNNER,
        "--file", prompt_file,
        "--tag", tag
    ]
    if backend == "mock":
        cmd.extend(["--mock", "--dry-run"])
    else:
        cmd.extend(["--backend", backend])
    res = subprocess.run(cmd)
    return res.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Ejecutor del Patrón Canónico Council-Cycle (3 + 1)")
    parser.add_argument("--prompt1", required=True, help="Ruta al Prompt de la Sesión Especializada 1")
    parser.add_argument("--prompt2", required=True, help="Ruta al Prompt de la Sesión Especializada 2")
    parser.add_argument("--prompt3", required=True, help="Ruta al Prompt de la Sesión Especializada 3")
    parser.add_argument("--synthesis", required=True, help="Ruta al Prompt de la Sesión 4 de Meta-Síntesis")
    parser.add_argument("--tag", default="CYCLE", help="Prefijo de etiqueta para el ciclo")
    parser.add_argument("--backend", default="agy", choices=["agy", "omniroute", "mock"])
    parser.add_argument("--mock", action="store_true", help="Usa el backend mock.")
    parser.add_argument("--dry-run", action="store_true", help="Requerido para usar --mock.")

    args = parser.parse_args()
    
    if args.mock and not args.dry_run:
        print("❌ Error: No se permite --mock a menos que se especifique --dry-run.")
        sys.exit(1)
    if args.mock:
        args.backend = "mock"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"========================================================")
    print(f"🏛️  INICIANDO COUNCIL-CYCLE CANÓNICO (3 + 1) — {timestamp}")
    print(f"• Norma: STD-AGT-COUNCIL-002")
    print(f"• Tag:   {args.tag}")
    print(f"========================================================")

    # 1. Ejecutar las 3 sesiones especializadas
    sessions = [
        (args.prompt1, f"{args.tag}_SESION_1"),
        (args.prompt2, f"{args.tag}_SESION_2"),
        (args.prompt3, f"{args.tag}_SESION_3"),
    ]

    for p_file, s_tag in sessions:
        if not os.path.exists(p_file):
            print(f"❌ Error: Archivo de prompt no encontrado: {p_file}")
            sys.exit(1)
        ok = run_single_council(p_file, s_tag, backend=args.backend)
        if not ok:
            print(f"❌ Fallo crítico en sub-consejo {s_tag}. Abortando ciclo.")
            sys.exit(1)

    # 2. Ejecutar la sesión de meta-síntesis
    if not os.path.exists(args.synthesis):
        print(f"❌ Error: Archivo de síntesis no encontrado: {args.synthesis}")
        sys.exit(1)

    print(f"\n========================================================")
    print(f"👑 EJECUTANDO CONSEJO DE META-SÍNTESIS Y PLAN FINAL")
    print(f"========================================================")
    ok_synth = run_single_council(args.synthesis, f"{args.tag}_SINTESIS_FINAL", backend=args.backend)
    if not ok_synth:
        print(f"❌ Fallo crítico en el Consejo de Síntesis. Abortando.")
        sys.exit(1)

    print(f"\n========================================================")
    print(f"🎉 COUNCIL-CYCLE COMPLETADO SATISFACTORIAMENTE (3 + 1)")
    print(f"========================================================")

if __name__ == "__main__":
    main()
