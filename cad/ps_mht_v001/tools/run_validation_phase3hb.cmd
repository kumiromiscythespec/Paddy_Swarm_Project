@echo off
setlocal
call conda activate paddy-cad
if errorlevel 1 exit /b %errorlevel%
python "%~dp0..\build_phase3hb.py"
if errorlevel 1 exit /b %errorlevel%
exit /b 0
