#!/usr/bin/env python3
import os
import subprocess
import tempfile
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def test_mock_dry_run_rule():
    print("Testing --mock without --dry-run...")
    # Test council_runner.py
    cmd = ["python3", "council_runner.py", "--question", "Test", "--mock"]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    assert res.returncode == 1
    assert "❌ Error" in res.stdout or "❌ Error" in res.stderr

    # Test council_cycle_runner.py
    cmd = ["python3", "council_cycle_runner.py", "--prompt1", "p1", "--prompt2", "p2", "--prompt3", "p3", "--synthesis", "p4", "--mock"]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    assert res.returncode == 1
    assert "❌ Error" in res.stdout or "❌ Error" in res.stderr

    # Test council_runner.py with both
    print("Testing --mock with --dry-run...")
    cmd = ["python3", "council_runner.py", "--question", "Test", "--mock", "--dry-run"]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    assert res.returncode == 0
    print("✓ Mock/Dry-run rules passed.")

def test_audit_loop_rule():
    print("Testing 6-loop audit rule...")
    
    # We will fake the session files to simulate 5 previous failed runs
    sessions_dir = os.path.join(BASE_DIR, "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    tag = "COUNCIL_AUDIT_ROUTER_TEST123"
    
    # Create 5 fake session JSONs
    fake_files = []
    for i in range(5):
        f_path = os.path.join(sessions_dir, f"MOCK_20261007_000{i}_{tag}_council_session.json")
        with open(f_path, "w") as f:
            f.write("{}")
        fake_files.append(f_path)
    # Run the 6th audit using mock backend which will return non_compliant
    env = os.environ.copy()
    env["MOCK_TAG"] = tag
    
    cmd = ["python3", "council_runner.py", "--question", "Mock Audit", "--tag", tag, "--mock", "--dry-run"]
    res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, env=env)
    
    # After the 6th non-compliant result, it should exit with a non-zero code
    assert res.returncode == 1, f"Expected non-zero exit code, got {res.returncode}"
    assert "The council did not agree after 5 retries" in res.stdout
    print("✓ Audit loop limit rule passed.")

if __name__ == "__main__":
    test_mock_dry_run_rule()
    test_audit_loop_rule()
