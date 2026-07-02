@echo off
chcp 65001 >nul
title Build - Cabinet Veterinaire Desktop App
color 0B
echo ===================================================
echo    Construction de l'application Cabinet Veterinaire
echo ===================================================
echo.
:: 1. Force close any running instances
echo [1/7] Fermeture des processus en cours...
taskkill /f /im CabinetVeterinaire.exe >nul 2>&1
timeout /t 1 /nobreak >nul
:: 2. Check Python
echo [2/7] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERREUR: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo N'oubliez pas de cocher "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b
)
:: 3. SELF-HEALING: Clean copy-paste errors using a safe temporary script
echo [3/7] Nettoyage automatique des fichiers...
echo import os > sanitize.py
echo f_app = 'app.py' >> sanitize.py
echo if os.path.exists(f_app): >> sanitize.py
echo     with open(f_app, 'r', encoding='utf-8') as f: lines = f.readlines() >> sanitize.py
echo     cleaned = [line for line in lines if ',path:' not in line and 'replacement:' not in line] >> sanitize.py
echo     with open(f_app, 'w', encoding='utf-8') as f: f.writelines(cleaned) >> sanitize.py
echo f_set = os.path.join('templates', 'settings.html') >> sanitize.py
echo if os.path.exists(f_set): >> sanitize.py
echo     with open(f_set, 'r', encoding='utf-8') as f: lines = f.readlines() >> sanitize.py
echo     cleaned = [line for line in lines if ',path:' not in line and 'replacement:' not in line] >> sanitize.py
echo     with open(f_set, 'w', encoding='utf-8') as f: f.writelines(cleaned) >> sanitize.py
python sanitize.py >nul 2>&1
del sanitize.py >nul 2>&1
:: 4. Clean old build folders
echo [4/7] Nettoyage des anciennes versions...
if exist "CabinetVeterinaire.exe" (
    del /f /q "CabinetVeterinaire.exe" >nul 2>&1
    if exist "CabinetVeterinaire.exe" (
        echo.
        echo ❌ ERREUR : Le fichier "CabinetVeterinaire.exe" est bloque !
        echo Redemarrez votre ordinateur puis relancez ce script.
        echo.
        pause
        exit /b
    )
)
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del CabinetVeterinaire.spec 2>nul
:: 5. Install requirements (PyQt5, Flask...)
echo [5/7] Installation des dependances...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ ERREUR: L'installation des dependances a echoue.
    pause
    exit /b
)
:: 6. Make Icon
echo [6/7] Creation de l'icone...
python make_icon.py
:: 7. Build with PyInstaller
echo [7/7] Construction de l'executable independant...
echo Veuillez patienter, cette etape prend 1 a 2 minutes...
echo.
python -m PyInstaller --noconfirm --onefile --windowed --name "CabinetVeterinaire" --icon "static/img/icon.ico" --add-data "templates;templates" --add-data "static;static" --hidden-import "sqlalchemy.sql.default_comparator" app.py
echo.
echo Verification du fichier final...
if exist "dist\CabinetVeterinaire.exe" (
    echo 🚚 Deplacement de l'application vers le dossier principal...
    move /y "dist\CabinetVeterinaire.exe" "CabinetVeterinaire.exe" >nul
    
    :: Clean build files
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    del CabinetVeterinaire.spec 2>nul
    
    echo.
    echo ===================================================
    echo  ✨ SUCCES TOTAL ! ✔✔
    echo.
    echo  L'application de bureau independante a ete creee !
    echo  Le fichier "CabinetVeterinaire.exe" est disponible.
    echo ===================================================
    echo.
) else (
    echo.
    echo ❌ ERREUR: Le fichier n'a pas pu etre cree.
    echo.
)
pause