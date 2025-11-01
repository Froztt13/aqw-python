@echo off
title Slavery

:: === Basic configuration ===
set "PROJECT_PATH=D:\Python\aqw-python"
set "BOT_PATH=bot.slavery.bot_slave"

echo ==============================
echo   Slavery Launcher
echo ==============================
echo.

echo Bot Configuration:
call :ShowConfig
echo.

set /p FOLLOW_PLAYER=Enter player name to follow:
if "%FOLLOW_PLAYER%"=="" (
    echo Error: No player name specified!
    pause
    exit /b 1
)
echo.

echo Available slaves:
call :ExtractSlaveList
echo.
echo Input example: 1,3,4
echo (Separate with commas without spaces)
echo.
set /p SLAVES=Enter slave numbers to run:

echo.
echo Following player: %FOLLOW_PLAYER%
echo Running slaves: %SLAVES%
echo.

setlocal enabledelayedexpansion
set CMD_STR=

:: === Convert comma input to spaces and loop ===
for %%i in (%SLAVES%) do (
    if not defined CMD_STR (
        set CMD_STR=wt -w 0 new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i %FOLLOW_PLAYER% ^| py -m %BOT_PATH% %FOLLOW_PLAYER%"
    ) else (
        set CMD_STR=!CMD_STR! ^; new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i %FOLLOW_PLAYER% ^| py -m %BOT_PATH% %FOLLOW_PLAYER%"
    )
)

:: Run all selected tabs
if defined CMD_STR (
    call %CMD_STR%
    echo.
    echo Slavery is running...
) else (
    echo No slaves selected.
)

pause

goto :eof

:ShowConfig
setlocal

:: Use Python to extract configuration values
py -c "import sys; sys.path.append(r'%PROJECT_PATH%'); from bot.slavery.bot_slave import server, default_room_number, targets_priority, slaves, whitelist; print(f'   Server: {server}'); print(f'   Default Room: {default_room_number}'); print(f'   Targets Priority: {targets_priority}'); print(f'   Total Slaves: {len(slaves)}'); print(f'   Whitelist Items: {len(whitelist)}')" 2>nul

:: If Python method fails, show error message
if %errorlevel% neq 0 (
    echo   Unable to load configuration from bot_slave.py
    echo   Please check if Python environment is properly configured
)

endlocal
goto :eof

:ExtractSlaveList
setlocal

:: Use Python to extract slave list dynamically
py -c "import sys; sys.path.append(r'%PROJECT_PATH%'); from bot.slavery.bot_slave import slaves; [print(f'   {i+1}. {slave.username} ({slave.char_class})') for i, slave in enumerate(slaves)]" 2>nul

:: If Python method fails, show a simple message
if %errorlevel% neq 0 (
    echo   Unable to load slave list from bot_slave.py
    echo   Please check if Python environment is properly configured
)

endlocal
goto :eof