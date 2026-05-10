@echo off
REM Cleans leftover mod content, then launches the modkit.
REM Sibling of RunDevKit.bat. Point your shortcut at this file.

setlocal

set "MODKIT_ROOT=%~dp0.."
set "CLEANUP_PS=%~dp0Clean-ModkitLeftovers.ps1"
set "LOG_DIR=%~dp0Saved\Logs"
set "LOG_FILE=%LOG_DIR%\ModkitCleanup.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >NUL 2>&1

REM Wait up to 15s for UE4Editor.exe to fully exit before running cleanup.
REM Closing the editor and immediately re-running this bat races the OS:
REM the process lingers in tasklist while it flushes caches and releases
REM handles. Skipping cleanup in that window leaves stale Content\Mods\
REM on disk and the next session starts polluted.
tasklist /FI "IMAGENAME eq UE4Editor.exe" 2>NUL | find /I "UE4Editor.exe" >NUL
if errorlevel 1 goto run_cleanup
echo Waiting up to 15s for UE4Editor.exe to exit before cleanup...
set /a wait_remaining=15
:waitloop
tasklist /FI "IMAGENAME eq UE4Editor.exe" 2>NUL | find /I "UE4Editor.exe" >NUL
if errorlevel 1 goto run_cleanup
if %wait_remaining% LEQ 0 (
    echo [%date% %time%] ABORT: UE4Editor.exe still running after 15s wait. >> "%LOG_FILE%"
    echo.
    echo ERROR: UE4Editor.exe is still running after a 15-second wait.
    echo Close all UE4 editor instances fully, then re-run this script.
    pause
    exit /b 1
)
set /a wait_remaining-=1
timeout /t 1 /nobreak >NUL
goto waitloop

:run_cleanup
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
