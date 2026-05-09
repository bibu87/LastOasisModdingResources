@echo off
REM Cleans leftover mod content, then launches the modkit.
REM Sibling of RunDevKit.bat. Point your shortcut at this file.

setlocal

set "MODKIT_ROOT=%~dp0.."
set "CLEANUP_PS=%~dp0Clean-ModkitLeftovers.ps1"
set "LOG_DIR=%~dp0Saved\Logs"
set "LOG_FILE=%LOG_DIR%\ModkitCleanup.log"

tasklist /FI "IMAGENAME eq UE4Editor.exe" 2>NUL | find /I "UE4Editor.exe" >NUL
if not errorlevel 1 (
    echo UE4Editor.exe already running, skipping cleanup.
    goto launch
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >NUL 2>&1

if exist "%CLEANUP_PS%" (
    echo Cleaning leftover mod content...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%CLEANUP_PS%' -Apply *>&1 | Tee-Object -FilePath '%LOG_FILE%' -Append"
    if errorlevel 1 (
        echo.
        echo Cleanup failed. See %LOG_FILE%
        echo Press any key to launch anyway, or Ctrl+C to abort.
        pause >NUL
    )
) else (
    echo Cleanup script not found at %CLEANUP_PS% -- launching without cleanup.
)

:launch
if exist "%MODKIT_ROOT%\Engine\Binaries\Win64\UE4Editor-Win64-DebugGame-Cmd.exe" (
    set engine_dir="%MODKIT_ROOT%\Engine\Binaries\Win64\"
) else (
    set engine_dir="%MODKIT_ROOT%\Engine\Engine\Binaries\Win64\"
)

cd /d %engine_dir%
start UE4Editor.exe "%~dp0Mist.uproject" -Installed -ModDevKit

endlocal
exit /b 0
