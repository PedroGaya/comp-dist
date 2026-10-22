@echo off
mkdir locust-results 2>nul
for %%I in (1 2 3) do (
  for %%U in (10 100 1000) do (
    for %%S in (img-150kb text-400kb img-300kb) do (
      echo.
      echo ============================================
      echo   Teste: %%I inst / %%U users / %%S
      echo ============================================
      call test.bat %%I %%U %%S
    )
  )
)
echo.
echo Concluido. CSVs em locust-results\