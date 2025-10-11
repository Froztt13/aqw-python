@echo off
title Slavery

:: === Konfigurasi dasar ===
set "PROJECT_PATH=D:\Python\aqw-python"
set "BOT_PATH=bot.slavery.bot_slave"

:: === Input jumlah bot yang ingin dijalankan ===
set /p BOT_COUNT=Input your slaves count to serve: 

echo.
echo Starting %BOT_COUNT% bot...
echo.

:: === Loop untuk buka tab di Windows Terminal ===
setlocal enabledelayedexpansion
set CMD_STR=

for /L %%i in (1,1,%BOT_COUNT%) do (
    if %%i==1 (
        set CMD_STR=wt -w 0 new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i ^| py -m %BOT_PATH%"
    ) else (
        set CMD_STR=!CMD_STR! ^; new-tab --title "Slave %%i" cmd /k "cd /d %PROJECT_PATH% && echo %%i ^| py -m %BOT_PATH%"
    )
)

:: Jalankan semua tab sekaligus
call %CMD_STR%

echo.
echo Slavery is running...
