#!/usr/bin/env python3
"""
test_council_orchestrator.py — Suite de pruebas determinista de Council Orchestrator
"""

import os
import sys
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from council_runner import run_advisor, ROLES
from engine_backends import get_engine_backend

def main():
    print("========================================================")
    print("🧪 EJECUTANDO TEST SUITE: COUNCIL ORCHESTRATOR")
    print("========================================================\n")
    
    # Test 1: Verificar carga de backends
    print("👉 [1/3] Probando carga de EngineBackend...")
    mock_eng = get_engine_backend("mock")
    out = mock_eng.execute("Pregunta de prueba")
    assert "MOCK BACKEND" in out
    print("   ✓ EngineBackend mock verificado.")
    
    # Test 2: Verificar carga de skills de los 5 asesores
    print("\n👉 [2/3] Probando carga de los 5 asesores canónicos...")
    for role in ROLES:
        res = run_advisor(role, "¿Debemos proceder?", backend="mock", mock=True)
        assert res["name"] == role["name"]
        print(f"   ✓ Asesor verificado: {res['name']}")
        
    # Test 3: Simulación completa de runner con --mock
    print("\n👉 [3/3] Probando ejecución completa del runner en modo mock...")
    cmd = [sys.executable, os.path.join(BASE_DIR, "council_runner.py"), "--question", "Test question", "--mock"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
    assert res.returncode == 0, f"Error en runner: {res.stderr}"
    assert "CONSEJO AGÉNTICO COMPLETADO CON ÉXITO" in res.stdout
    print("   ✓ Deliberación determinista completada exit 0.")
    
    print("\n========================================================")
    print("🎉 SUITE DE COUNCIL ORCHESTRATOR: 100% PASS (EXIT 0)")
    print("========================================================\n")

if __name__ == "__main__":
    main()
