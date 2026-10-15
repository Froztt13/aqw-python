@echo off
title Temple Shrine Dungeon

set PROJECT_PATH="E:\aqw\aqw_bot\aqw-python-new"
set BOT_PATH=bot.ultra.grammiel

echo Starting Temple Shrine Dungeon bots in a 2x2 grid...

REM 1. Buka window dengan panel pertama (akan menjadi kiri atas)
wt --title "ultra grammiel" --suppressApplicationTitle cmd /k "cd /d %PROJECT_PATH% && echo 1 | py -m %BOT_PATH%"

echo Waiting (3 secs) for lead account to be ready...
timeout /t 3 /nobreak >nul

REM 2. Buat sisa 3 panel dengan logika grid 2x2
wt -w 0 split-pane -V -s 0.5 --title "ultra grammiel" cmd /k "cd /d %PROJECT_PATH% && echo 2 | py -m %BOT_PATH%" ; ^
         move-focus left ; ^
         split-pane -H -s 0.5 --title "ultra grammiel" cmd /k "cd /d %PROJECT_PATH% && echo 3 | py -m %BOT_PATH%" ; ^
         move-focus up ; move-focus right ; ^
         split-pane -H -s 0.5 --title "ultra grammiel" cmd /k "cd /d %PROJECT_PATH% && echo 4 | py -m %BOT_PATH%"
         
echo Temple Shrine Dungeon is running...