# Сборка MPDB5.exe (PyInstaller, режим onedir)
# Запуск: powershell -ExecutionPolicy Bypass -File build_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

.\.venv\Scripts\pyinstaller.exe MPDB5.spec --noconfirm

# COLLECT пересоздаёт dist\MPDB5 с нуля - копируем базы данных рядом с .exe
Copy-Item -Path "output" -Destination "dist\MPDB5\output" -Recurse -Force

Write-Host ""
Write-Host "Готово: dist\MPDB5\MPDB5.exe"
