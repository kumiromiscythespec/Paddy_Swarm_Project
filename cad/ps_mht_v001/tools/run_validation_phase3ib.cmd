@echo off
setlocal
call conda activate paddy-cad
if errorlevel 1 exit /b %errorlevel%
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%~dp0..\..
python "%~dp0..\build_phase3ib.py"
if errorlevel 1 exit /b %errorlevel%
echo Phase 3I-B CAD generation, STEP round-trip, STL mesh, water-boundary, retention, SHA, manifest, and test validation passed.
exit /b 0
