# Сборка MPDB.exe (PyInstaller, режим onedir)
# Запуск: powershell -ExecutionPolicy Bypass -File build_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

.\.venv\Scripts\pyinstaller.exe MPDB.spec --noconfirm

# COLLECT пересоздаёт dist\MPDB с нуля - копируем базы данных рядом с .exe
if (Test-Path "output") {
    Copy-Item -Path "output" -Destination "dist\MPDB\output" -Recurse -Force
} else {
    Write-Host "Папка output не найдена - базы данных не скопированы (будут созданы при первом запуске)."
}

Write-Host ""
Write-Host "Готово: dist\MPDB\MPDB.exe"
