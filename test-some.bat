@echo off
setlocal enabledelayedexpansion

set "INSTANCES=1 2 3"
set "USERS=500"
set "SCENARIOS=img-150kb text-400kb img-300kb"

if not "%~1"=="" set "INSTANCES=%~1"
if not "%~2"=="" set "USERS=%~2"

if not exist "locust-results" mkdir locust-results

echo Instancias: %INSTANCES%
echo Usuarios  : %USERS%
echo Cenarios  : %SCENARIOS%
echo.

for %%I in (%INSTANCES%) do (
    for %%S in (%SCENARIOS%) do (
        echo === %%I inst / %USERS% users / %%S ===
        call test.bat %%I %USERS% %%S
    )
)

echo.
echo Concluido.
endlocal