@echo off
set INST=%1
set USERS=%2
set SCENARIO=%3

if "%SCENARIO%"=="" ( echo Usage: test.bat ^<instancias^> ^<usuarios^> ^<img-150kb^|text-400kb^|img-300kb^> & exit /b 1 )
if "%USERS%"=="" ( echo Faltou o numero de usuarios. & exit /b 1 )
if "%SCENARIO%"=="" ( echo Faltou o cenario. & exit /b 1 )

echo [1/3] Ajustando wordpress para %INST% instancia(s)...
docker compose up -d --scale wordpress=%INST% >nul
timeout /t 8 /nobreak >nul

set /a SPAWN=%USERS% / 20
if %SPAWN% LSS 1 set SPAWN=1

echo [2/3] Locust: %USERS% usuarios (spawn %SPAWN%/s) - cenario %SCENARIO%...
docker compose run --rm locust ^
  --headless ^
  -f /mnt/locust/locustfile.py ^
  -u %USERS% -r %SPAWN% -t 2m ^
  --tags %SCENARIO% ^
  --host http://nginx ^
  --csv=/mnt/locust/results/%INST%inst-%USERS%users-%SCENARIO%

echo [3/3] Resultado: locust-results\%INST%inst-%USERS%users-%SCENARIO%_stats.csv