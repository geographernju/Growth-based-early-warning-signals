from pathlib import Path
import subprocess
import sys
ROOT=Path("D:/code")
CURRENT=Path(__file__).resolve()
scripts=sorted((path for path in ROOT.rglob("*.py") if path.resolve()!=CURRENT and "__pycache__" not in path.parts),key=lambda path:str(path.relative_to(ROOT)).lower())
if not scripts:
    raise FileNotFoundError(f"No Python scripts found in {ROOT}")
failed=[]
for index,path in enumerate(scripts,1):
    print(f"\n[{index}/{len(scripts)}] Running: {path}",flush=True)
    result=subprocess.run([sys.executable,"-u",str(path)],cwd=path.parent)
    if result.returncode==0:
        print(f"[OK] {path.name}",flush=True)
    else:
        failed.append((path,result.returncode))
        print(f"[FAILED] {path.name} | exit code: {result.returncode}",flush=True)
print(f"\nFinished: {len(scripts)-len(failed)} succeeded, {len(failed)} failed")
for path,code in failed:
    print(f"[FAILED] {path} | exit code: {code}")
if failed:
    sys.exit(1)
