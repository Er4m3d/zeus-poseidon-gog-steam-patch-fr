@echo off
title Patch FR - Zeus et Poseidon (GOG) - Desinstallation
if not exist "%~dp0scripts\patch.ps1" (
  echo.
  echo  Fichier scripts\patch.ps1 introuvable. Extrayez tout le ZIP puis relancez.
  echo.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\patch.ps1" -Desinstaller
exit /b %errorlevel%
