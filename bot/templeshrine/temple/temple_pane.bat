@echo off
title Temple Shrine Dungeon

set PROJECT_PATH="D:\aqw-python"
set BOT_PATH=bot.templeshrine.temple.bot_temple

echo Starting Temple Shrine Dungeon bots in a 2x2 grid...

REM Membuka semua pane dalam satu pemanggilan Windows Terminal
wt --title "P1" cmd /k "cd /d %PROJECT_PATH% && echo 1 | py -m %BOT_PATH%" ; ^
split-pane -V -s 0.5 --title "2 solstice_p2" cmd /k "cd /d %PROJECT_PATH% && echo 2 | py -m %BOT_PATH%" ; ^
move-focus left ; ^
split-pane -H -s 0.5 --title "3 midnight_p1" cmd /k "cd /d %PROJECT_PATH% && echo 3 | py -m %BOT_PATH%" ; ^
move-focus right ; ^
split-pane -H -s 0.5 --title "4 midnight_p2" cmd /k "cd /d %PROJECT_PATH% && echo 4 | py -m %BOT_PATH%"

echo Temple Shrine Dungeon is running...