@echo off

mkdir html
docker compose up -d
timeout /t 30 /nobreak >nul
for /L %%i in (1,1,9) do curl -sI http://localhost/ | findstr /i "X-Upstream"
