@echo off
setlocal
set "PHASE4TLSA_ROOT=%~dp0.."
where conda >nul 2>nul
if errorlevel 1 (
  echo ERROR: conda was not found on PATH.
  exit /b 2
)
call conda run -n paddy-cad python "%PHASE4TLSA_ROOT%\build_phase4tlsa.py"
if errorlevel 1 (
  echo ERROR: Phase 4T-LS-A validation failed.
  exit /b 1
)
echo Phase 4T-LS-A validation completed successfully.
exit /b 0
