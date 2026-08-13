#!/usr/bin/env python3
"""FFD 1.8 Build 2 portable-Mac bootstrap preflight.
Does not silently install system software; reports exact prerequisites and prepares local config.
"""
from pathlib import Path
import argparse, json, platform, shutil, subprocess, sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--model',default='gemma3:4b'); ap.add_argument('--write-config',action='store_true'); a=ap.parse_args()
    checks={
      'macOS': platform.system()=='Darwin',
      'Apple Silicon': platform.machine()=='arm64',
      'Python >= 3.11': sys.version_info >= (3,11),
      'git': bool(shutil.which('git')),
      'ollama': bool(shutil.which('ollama')),
    }
    model=False
    if checks['ollama']:
      try:model=a.model in subprocess.check_output(['ollama','list'],text=True,timeout=8)
      except Exception:pass
    checks[f'Ollama model {a.model}']=model
    cfg=Path.home()/'.reunion-companion'/'config.json'
    if a.write_config:
      cfg.parent.mkdir(parents=True,exist_ok=True); cfg.write_text(json.dumps({'llm_provider':'ollama','llm_model':a.model},indent=2)+'\n')
    for k,v in checks.items():print(('✓' if v else '✗'),k)
    print('Config:',cfg)
    if not checks['ollama']: print('Next: install Ollama, then run: ollama pull',a.model)
    elif not model: print('Next: ollama pull',a.model)
    return 0 if all(checks.values()) else 2
if __name__=='__main__': raise SystemExit(main())
