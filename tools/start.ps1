# Windows PowerShell 5.1 / PowerShell 7. No execution-policy change is needed.
# Dot-source this file to test its functions without starting the assistant.

function Get-SliderPythonCandidates {
    foreach ($name in @('py', 'python3', 'python')) {
        foreach ($command in @(Get-Command $name -CommandType Application -All -ErrorAction SilentlyContinue)) {
            if (-not $command) { continue }
            # Do not launch an unconfigured Microsoft Store execution alias.
            if ($name -ne 'py' -and $command.Source -match '[\\/]WindowsApps[\\/]python(?:3)?\.exe$') { continue }
            $flags = @()
            if ($name -eq 'py') { $flags = @('-3') }
            [pscustomobject]@{ Path = $command.Source; Flags = $flags }
        }
    }
    # Python can be installed without adding it to PATH. These are Python's
    # registered install paths, followed by the normal per-user/system folders.
    foreach ($key in @('HKCU:\Software\Python\PythonCore\*\InstallPath',
                       'HKLM:\Software\Python\PythonCore\*\InstallPath',
                       'HKLM:\Software\WOW6432Node\Python\PythonCore\*\InstallPath')) {
        foreach ($item in @(Get-Item -Path $key -ErrorAction SilentlyContinue)) {
            if (-not $item) { continue }
            $executable = $item.GetValue('ExecutablePath')
            if (-not $executable -and $item.GetValue('')) {
                $executable = Join-Path ($item.GetValue('')) 'python.exe'
            }
            if ($executable) { [pscustomobject]@{ Path = $executable; Flags = @() } }
        }
    }
    foreach ($root in @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if (-not $root) { continue }
        $pattern = Join-Path $root 'Python*\python.exe'
        if ($root -eq $env:LOCALAPPDATA) { $pattern = Join-Path $root 'Programs\Python\Python*\python.exe' }
        foreach ($file in @(Get-Item -Path $pattern -ErrorAction SilentlyContinue)) {
            if ($file) { [pscustomobject]@{ Path = $file.FullName; Flags = @() } }
        }
    }
}

function Test-SliderPython {
    param($Candidate)
    $flags = @($Candidate.Flags)
    try {
        & $Candidate.Path @flags -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Find-SliderPython {
    foreach ($candidate in @(Get-SliderPythonCandidates)) {
        if (Test-SliderPython $candidate) { return $candidate }
    }
    return $null
}

function Get-SliderAdbCandidates {
    foreach ($command in @(Get-Command adb -CommandType Application -All -ErrorAction SilentlyContinue)) {
        if ($command) { $command.Source }
    }
    foreach ($root in @($env:ANDROID_HOME, $env:ANDROID_SDK_ROOT)) {
        if ($root) { Join-Path $root 'platform-tools\adb.exe' }
    }
    if ($env:LOCALAPPDATA) {
        Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
        Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\adb.exe'
    }
}

function Test-SliderAdb {
    param([string]$Path)
    try {
        & $Path version *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Find-SliderAdb {
    foreach ($candidate in @(Get-SliderAdbCandidates)) {
        if (Test-SliderAdb $candidate) { return $candidate }
    }
    return $null
}

function Update-SliderProcessPath {
    # Installers own persistent PATH changes. Refresh only this PowerShell process,
    # retaining paths provided by its caller (virtual environments, SDKs, etc.).
    $paths = @($env:PATH, [Environment]::GetEnvironmentVariable('Path', 'User'),
                        [Environment]::GetEnvironmentVariable('Path', 'Machine'))
    $env:PATH = ($paths | Where-Object { $_ }) -join [IO.Path]::PathSeparator
}

function Invoke-SliderInstaller {
    param([string]$Path, [string[]]$InstallerArguments)
    & $Path @InstallerArguments | Out-Host
    return $LASTEXITCODE
}

function Install-SliderPackage {
    param([string]$PackageId, [string]$Label)
    $winget = Get-Command winget -CommandType Application -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "$Label manque et WinGet est introuvable. Installez 'App Installer' de Microsoft, puis relancez la commande : https://apps.microsoft.com/detail/9nblggh4nns1"
    }
    Write-Host "$Label absent : installation via WinGet ($PackageId)..."
    $installerArguments = @('install', '--id', $PackageId, '--exact', '--source', 'winget',
                            '--scope', 'user', '--accept-source-agreements',
                            '--accept-package-agreements', '--disable-interactivity')
    $result = Invoke-SliderInstaller $winget.Source $installerArguments
    if ($result -ne 0) {
        throw "Installation de $Label interrompue (WinGet : $result). Corrigez l'erreur indiquee ci-dessus, puis relancez la commande."
    }
    Update-SliderProcessPath
}

function Test-SliderNeedsAdb {
    param([string[]]$AssistantArguments)
    foreach ($argument in $AssistantArguments) {
        if ($argument -in @('-h', '--help', '--backup') -or $argument -like '--backup=*') { return $false }
    }
    return $true
}

function Initialize-SliderPrerequisites {
    param([string[]]$AssistantArguments)
    $python = Find-SliderPython
    if (-not $python) {
        Install-SliderPackage 'Python.Python.3.13' 'Python 3.10+'
        $python = Find-SliderPython
        if (-not $python) {
            throw 'Python a ete installe mais reste introuvable ou incompatible. Fermez puis rouvrez PowerShell et relancez la commande.'
        }
    }
    if (Test-SliderNeedsAdb $AssistantArguments) {
        $adb = Find-SliderAdb
        if (-not $adb) {
            Install-SliderPackage 'Google.PlatformTools' 'ADB'
            $adb = Find-SliderAdb
            if (-not $adb) {
                throw 'ADB a ete installe mais reste introuvable. Fermez puis rouvrez PowerShell et relancez la commande.'
            }
        }
        # configure_shorts.py resolves adb with shutil.which. Make this exact
        # checked executable visible, including an SDK not previously in PATH.
        $env:PATH = (Split-Path -Parent $adb) + [IO.Path]::PathSeparator + $env:PATH
    }
    return $python
}

function Start-SliderAssistant {
    param([string[]]$AssistantArguments)
    $ErrorActionPreference = 'Stop'
    $python = Initialize-SliderPrerequisites $AssistantArguments
    $pythonFlags = @($python.Flags)
    $assistantFolder = Join-Path ([IO.Path]::GetTempPath()) ('smarttube-assistant.' + [guid]::NewGuid().ToString('N'))
    $assistantFile = Join-Path $assistantFolder 'configure_shorts.py'
    $previousTls = [Net.ServicePointManager]::SecurityProtocol
    try {
        New-Item -ItemType Directory -Path $assistantFolder | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = $previousTls -bor [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -TimeoutSec 120 `
            -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/configure_shorts.py' `
            -OutFile $assistantFile
        & $python.Path @pythonFlags $assistantFile @AssistantArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Assistant interrompu (code $LASTEXITCODE). Consultez le message ci-dessus."
        }
    } finally {
        [Net.ServicePointManager]::SecurityProtocol = $previousTls
        if (Test-Path -LiteralPath $assistantFolder) {
            Remove-Item -LiteralPath $assistantFolder -Recurse -Force
        }
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    Start-SliderAssistant -AssistantArguments @($args)
}
