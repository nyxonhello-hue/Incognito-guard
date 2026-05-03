# ============================================================
#  Incognito Guard - Windows Installer
#  Run as Administrator in PowerShell
# ============================================================

param(
    [string]$ExtensionId = "REPLACE_WITH_YOUR_EXTENSION_ID"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Incognito Guard - Windows Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath   = Join-Path $scriptDir "IncognitoGuard.exe"

# ── 1. Force-install extension in Chrome ──────────────────
$chromePath = "HKLM:\SOFTWARE\Policies\Google\Chrome\ExtensionInstallForcelist"
if (-not (Test-Path $chromePath)) { New-Item -Path $chromePath -Force | Out-Null }
Set-ItemProperty -Path $chromePath -Name "1" -Value "$ExtensionId;https://clients2.google.com/service/update2/crx"
Write-Host "[OK] Chrome policy set" -ForegroundColor Green

# ── 2. Force-install extension in Edge ────────────────────
$edgePath = "HKLM:\SOFTWARE\Policies\Microsoft\Edge\ExtensionInstallForcelist"
if (-not (Test-Path $edgePath)) { New-Item -Path $edgePath -Force | Out-Null }
Set-ItemProperty -Path $edgePath -Name "1" -Value "$ExtensionId;https://clients2.google.com/service/update2/crx"
Write-Host "[OK] Edge policy set" -ForegroundColor Green

# ── 3. Force-install extension in Brave ───────────────────
$bravePath = "HKLM:\SOFTWARE\Policies\BraveSoftware\Brave\ExtensionInstallForcelist"
if (-not (Test-Path $bravePath)) { New-Item -Path $bravePath -Force | Out-Null }
Set-ItemProperty -Path $bravePath -Name "1" -Value "$ExtensionId;https://clients2.google.com/service/update2/crx"
Write-Host "[OK] Brave policy set" -ForegroundColor Green

# ── 4. Add IncognitoGuard.exe to Windows startup ──────────
$startupKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
if (Test-Path $exePath) {
    Set-ItemProperty -Path $startupKey -Name "IncognitoGuard" -Value "`"$exePath`""
    Write-Host "[OK] IncognitoGuard.exe added to startup" -ForegroundColor Green
} else {
    # Fallback to pythonw if exe not found
    $guardPath = Join-Path $scriptDir "guard.py"
    Set-ItemProperty -Path $startupKey -Name "IncognitoGuard" -Value "pythonw `"$guardPath`""
    Write-Host "[OK] guard.py added to startup (exe not found)" -ForegroundColor Yellow
}

# ── 5. Firefox policies.json ───────────────────────────────
$ffPolicyDir = "C:\Program Files\Mozilla Firefox\distribution"
if (Test-Path "C:\Program Files\Mozilla Firefox") {
    if (-not (Test-Path $ffPolicyDir)) {
        New-Item -ItemType Directory -Path $ffPolicyDir -Force | Out-Null
    }
    $ffPolicy = @{
        policies = @{
            ExtensionSettings = @{
                "incognito-guard@yourname.com" = @{
                    installation_mode = "force_installed"
                    install_url       = "https://addons.mozilla.org/firefox/downloads/your-ext.xpi"
                }
            }
        }
    }
    $ffPolicy | ConvertTo-Json -Depth 5 | Set-Content "$ffPolicyDir\policies.json"
    Write-Host "[OK] Firefox policy set" -ForegroundColor Green
} else {
    Write-Host "[SKIP] Firefox not found" -ForegroundColor Yellow
}

# ── 6. Launch the app now ──────────────────────────────────
if (Test-Path $exePath) {
    Start-Process $exePath
    Write-Host "[OK] Incognito Guard launched" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup complete! Restart your browsers." -ForegroundColor Green
Write-Host "  Default PIN: 1234 (change in Settings)" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
