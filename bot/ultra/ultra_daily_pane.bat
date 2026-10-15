@echo off
title Ultra Daily

set PROJECT_PATH="%~dp0..\.."
set BOT_PATH=bot.ultra.daily

REM Structured per-account logs for all four panes, written to
REM capture_logs/ultra/<AQW_RUN_ID>/slotN_<account>.jsonl
set AQW_TELEMETRY=1
set "AQW_RUN_ID=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "AQW_RUN_ID=%AQW_RUN_ID: =0%"

echo Starting ultra daily in a 2x2 grid (run %AQW_RUN_ID%)...

REM 1. Buka window dengan panel pertama (akan menjadi kiri atas)
wt --title "ultra daily" --suppressApplicationTitle cmd /k "cd /d %PROJECT_PATH% && echo 1 | py -m %BOT_PATH%"

echo Waiting (3 secs) for lead account to be ready...
timeout /t 3 /nobreak >nul

REM 2. Buat sisa 3 panel dengan logika grid 2x2
wt -w 0 split-pane -V -s 0.5 --title "ultra daily" cmd /k "cd /d %PROJECT_PATH% && echo 2 | py -m %BOT_PATH%" ; ^
         move-focus left ; ^
         split-pane -H -s 0.5 --title "ultra daily" cmd /k "cd /d %PROJECT_PATH% && echo 3 | py -m %BOT_PATH%" ; ^
         move-focus up ; move-focus right ; ^
         split-pane -H -s 0.5 --title "ultra daily" cmd /k "cd /d %PROJECT_PATH% && echo 4 | py -m %BOT_PATH%"

echo Ultra daily is running -- logs in capture_logs\ultra\%AQW_RUN_ID%
