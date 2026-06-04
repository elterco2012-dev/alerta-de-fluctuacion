@echo off
cd /d C:\alerta-de-fluctuacion

echo ============================================================
echo  PRUEBA DE EMAIL — verifica Outlook COM y/o SMTP
echo ============================================================
echo.
echo  Requiere: Outlook abierto con tu cuenta aaron.armoa@wurth.com.ar
echo  Si falla con "pywin32 no instalado":
echo    pip install pywin32
echo ============================================================
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\test_email.py
echo.
echo ============================================================
echo  Si dice "Email enviado via Outlook COM" = todo OK.
echo  Si da error 535 SMTP = IT tiene SMTP AUTH deshabilitado,
echo    usar solo el camino Outlook COM (pip install pywin32).
echo ============================================================
pause
