@echo off
setlocal
call conda activate paddy-cad
if errorlevel 1 exit /b %errorlevel%
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%~dp0..\..
python "%~dp0..\build_phase3if.py"
exit /b %errorlevel%
