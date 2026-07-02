@echo off
chcp 65001 >nul
title Cabinet Veterinaire - Dr. Boulemaiz Azzeddine
color 0A
echo ===================================================
echo    Cabinet Veterinaire Dr. Boulemaiz Azzeddine
echo ===================================================
echo.
echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo N'oubliez pas de cocher "Add Python to PATH" lors de l'installation.
    pause
    exit /b
)
echo [2/3] Installation/Verification des dependances...
pip install -r requirements.txt
echo [3/3] Demarrage de l'application de bureau...
echo.
echo ===================================================
echo  L'application demarre dans sa propre fenetre...
echo ===================================================
echo.
python app.py
pause