@echo off
setlocal enabledelayedexpansion

if not exist "locust-results" mkdir locust-results

echo ============================================
echo   Smoke test - 3 cenarios x 10s x 5 users
echo ============================================
echo.

set "FAIL=0"

for %%S in (img-150kb text-400kb img-300kb) do (
    echo --------------------------------------------
    echo  Cenario: %%S
    echo --------------------------------------------

    docker compose run --rm locust ^
        --headless ^
        -f /mnt/locust/locustfile.py ^
        -u 5 -r 1 -t 10s ^
        --tags %%S ^
        --host http://nginx ^
        --csv=/mnt/locust/results/smoke-%%S

    if errorlevel 1 (
        echo [ERRO] Locust falhou no cenario %%S
        set "FAIL=1"
    )

    set "FAILCSV=locust-results\smoke-%%S_failures.csv"
    set "LINES=0"
    if exist "!FAILCSV!" (
        for /f %%L in ('type "!FAILCSV!" ^| find /c /v ""') do set "LINES=%%L"
    )
    if !LINES! GTR 1 (
        echo [FALHAS] Verifique !FAILCSV!
        set "FAIL=1"
    ) else (
        echo [OK] sem falhas em %%S
    )
    echo.
)

echo ============================================
if "%FAIL%"=="1" (
    echo   RESULTADO: HA PROBLEMAS - revise os CSVs em locust-results\
) else (
    echo   RESULTADO: TUDO OK - pode rodar run-all.bat
)
echo ============================================

endlocal