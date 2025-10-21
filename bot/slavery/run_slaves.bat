@echo off
title Slavery

:: === Basic configuration ===
set "PROJECT_PATH=D:\Python\aqw-python"
set "BOT_PATH=bot.slavery.bot_slave"

echo ==============================
echo   Slavery Launcher
echo ==============================
echo.
echo Input example: 1,3,4
echo (Separate with commas without spaces)
echo.
set /p SLAVES=Enter slave numbers to run:

echo.
echo Running slaves: %SLAVES%
echo.

setlocal enabledelayedexpansion
set CMD_STR=

:: === Convert comma input to spaces and loop ===
for %%i in (%SLAVES%) do (
    if not defined CMD_STR (
        set CMD_STR=wt -w 0 new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i ^| py -m %BOT_PATH%"
    ) else (
        set CMD_STR=!CMD_STR! ^; new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i ^| py -m %BOT_PATH%"
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