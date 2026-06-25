$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptDir "start_evolution.bat"
$startupFolder = [Environment]::GetFolderPath("Startup")

Write-Host "========================================"
Write-Host "  完美自我进化系统 - 开机自启动配置"
Write-Host "========================================"
Write-Host ""
Write-Host "系统目录: $scriptDir"
Write-Host "启动脚本: $batPath"
Write-Host "启动文件夹: $startupFolder"
Write-Host ""

if (-not (Test-Path $batPath)) {
    Write-Host "[错误] 启动脚本不存在: $batPath" -ForegroundColor Red
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut("$startupFolder\自我进化系统.lnk")
$shortcut.TargetPath = $batPath
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "完美自我进化系统 - 自动运行"
$shortcut.Save()

Write-Host "[成功] 已添加到开机自启动" -ForegroundColor Green
Write-Host ""
Write-Host "快捷方式位置: $startupFolder\自我进化系统.lnk"
Write-Host ""
Write-Host "系统将在每次开机时自动启动自我进化..."