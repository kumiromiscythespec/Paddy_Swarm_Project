@echo off
setlocal
call conda activate paddy-cad
if errorlevel 1 exit /b %errorlevel%
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%~dp0..\..
python "%~dp0..\build_phase3id.py"
if errorlevel 1 exit /b %errorlevel%
echo Phase 3I-D positive cascade, two-stage collision, air-gap, tolerance, water-volume, coupon, STEP/STL, SHA, manifest, and test validation passed.
exit /b 0
