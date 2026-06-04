@echo off
cd /d C:\alerta-de-fluctuacion

echo ============================================================
echo  PRUEBA DE EMAIL — envia un mail de prueba para verificar
echo  que el SMTP de Office 365 esta bien configurado en .env
echo ============================================================
echo.
"C:\Users\aarmoa\AppData\Local\Programs\Python\Python312\python.exe" scripts\test_email.py
echo.
echo ============================================================
echo  Si dice "Email enviado OK", revisa tu bandeja de entrada.
echo  Si dio error 535, IT tiene que habilitar SMTP AUTH para tu
echo  cuenta (o necesitas una contrasena de aplicacion con MFA).
echo ============================================================
pause
