@echo off
echo 🤖 Preparando Respaldodox Bot para GitHub y Railway...

echo.
echo 📁 Inicializando Git...
git init

echo.
echo 📝 Agregando archivos...
git add .

echo.
echo 💾 Haciendo commit...
git commit -m "Respaldodox Bot v2.0 - Listo para Railway"

echo.
echo 🔗 Configurando repositorio remoto...
git remote add origin https://github.com/NmsK12/PorBortRepo.git

echo.
echo 🚀 Subiendo a GitHub...
git branch -M main
git push -u origin main

echo.
echo ✅ ¡Proyecto subido exitosamente!
echo.
echo 📋 Próximos pasos:
echo 1. Ve a https://railway.app
echo 2. Conecta tu cuenta de GitHub
echo 3. Selecciona el repositorio PorBortRepo
echo 4. Configura las variables de entorno
echo 5. ¡Despliega!
echo.
pause
