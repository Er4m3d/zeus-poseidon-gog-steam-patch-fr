@echo off
title Patch FR - Zeus et Poseidon (GOG) - Installation
if not exist "%~dp0fichiers\Zeus_Text.eng" goto pasextrait
if not exist "%~dp0scripts\patch.ps1" goto pasextrait
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\patch.ps1"
exit /b %errorlevel%

:pasextrait
echo.
echo  Le patch n'est pas complet ou n'a pas ete extrait.
echo  Faites un clic droit sur le fichier ZIP puis "Extraire tout...",
echo  puis lancez INSTALLER.bat depuis le dossier extrait.
echo.
pause
exit /b 1
