@echo off
setlocal
call conda activate paddy-cad
if errorlevel 1 exit /b %errorlevel%
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%~dp0..\..
python "%~dp0..\build_phase3ic.py"
if errorlevel 1 exit /b %errorlevel%
echo Phase 3I-C corrected-full, retention Boolean, keeper V2, diagnostic STL, STEP round-trip, mesh, SHA, manifest, and test validation passed.
exit /b 0
