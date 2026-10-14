@echo off
title Ultra Speaker

set PROJECT_PATH="%~dp0..\.."
set BOT_PATH=bot.ultra.ultra_speaker

REM Structured per-account logs for all four panes, written to
REM capture_logs/ultra/<AQW_RUN_ID>/slotN_<account>.jsonl
set AQW_TELEMETRY=1
set "AQW_RUN_ID=%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "AQW_RUN_ID=%AQW_RUN_ID: =0%"

echo Starting Ultra Speaker bots in a 2x2 grid (run %AQW_RUN_ID%)...

REM Pane n logs in as ACCOUNTS[n-1] and wears SOLO_ROLES[n-1]:
REM   1 Legion Revenant   2 ArchPaladin   3 Lord Of Order   4 Verus DoomKnight
REM so the four panes cover the four roles malgor_handler rotates through.

REM 1. Buka window dengan panel pertama (akan menjadi kiri atas)
wt --title "ultra speaker" --suppressApplicationTitle cmd /k "cd /d %PROJECT_PATH% && echo 1 | py -m %BOT_PATH%"

echo Waiting (3 secs) for lead account to be ready...
timeout /t 3 /nobreak >nul

REM 2. Buat sisa 3 panel dengan logika grid 2x2
wt -w 0 split-pane -V -s 0.5 --title "ultra speaker" cmd /k "cd /d %PROJECT_PATH% && echo 2 | py -m %BOT_PATH%" ; ^
         move-focus left ; ^
         split-pane -H -s 0.5 --title "ultra speaker" cmd /k "cd /d %PROJECT_PATH% && echo 3 | py -m %BOT_PATH%" ; ^
         move-focus up ; move-focus right ; ^
         split-pane -H -s 0.5 --title "ultra speaker" cmd /k "cd /d %PROJECT_PATH% && echo 4 | py -m %BOT_PATH%"

echo Ultra Speaker is running -- logs in capture_logs\ultra\%AQW_RUN_ID%
