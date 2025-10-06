@echo off
setlocal enabledelayedexpansion

REM === 1. Install dependencies ===
echo Installing dependencies...
pip install --upgrade --force-reinstall requests==2.32.4 beautifulsoup4==4.13.4 PySide6==6.9.1 pywin32==311 pytz==2025.2 python-dateutil==2.9.0.post0

REM === 2. Get Startup folder path ===
for /f "tokens=*" %%i in ('powershell -command "[Environment]::GetFolderPath('Startup')"') do set startupPath=%%i

echo Startup folder detected: %startupPath%

REM === 3. Define project folder name and install location ===
set projectName=Miti-Tithi-main
set installDir=C:\Program Files\%projectName%
set currentDir=%~dp0

REM === 4. Copy project to Program Files ===
echo Copying project to %installDir%...
if exist "%installDir%" (
    rmdir /s /q "%installDir%"
)
xcopy "%currentDir%" "%installDir%\" /E /I /Y

REM === 5. Copy VBS launcher to Startup ===
echo Copying launcher.exe.vbs to Startup...
copy "%installDir%\launcher.exe.vbs" "%startupPath%\mitiTithi.vbs" /Y

REM === 6. Wait 5 seconds ===
echo Waiting for 5 seconds...
timeout /t 5 /nobreak >nul

REM === 7. Run VBS script to start app ===
echo Running launcher.exe.vbs...
cscript //nologo "%startupPath%\mitiTithi.vbs"

echo Setup complete. Your project is installed in Program Files and will run on startup.
pause


