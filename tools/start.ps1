# Run with Windows PowerShell 5.1 or PowerShell 7; no policy change is needed.
$ErrorActionPreference = 'Stop'
$assistantArgs = @($args)
$pythonPath = $null
$pythonFlags = @()

foreach ($candidate in @('py', 'python3', 'python')) {
    $command = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue
    if (-not $command) { continue }
    # Avoid opening the Microsoft Store through an unconfigured python.exe alias.
    if ($candidate -ne 'py' -and $command.Source -match '[\\/]WindowsApps[\\/]') { continue }
    $flags = @()
    if ($candidate -eq 'py') { $flags = @('-3') }
    & $command.Source @flags -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonPath = $command.Source
        $pythonFlags = $flags
        break
    }
}
if (-not $pythonPath) {
    throw 'Python 3.10+ requis / required: https://www.python.org/downloads/ . Installez Python puis relancez cette commande.'
}

$assistantFolder = Join-Path ([IO.Path]::GetTempPath()) ('smarttube-assistant.' + [guid]::NewGuid().ToString('N'))
$assistantFile = Join-Path $assistantFolder 'configure_shorts.py'
$previousTls = [Net.ServicePointManager]::SecurityProtocol
try {
    New-Item -ItemType Directory -Path $assistantFolder | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = $previousTls -bor [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -TimeoutSec 120 `
        -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/configure_shorts.py' `
        -OutFile $assistantFile
    & $pythonPath @pythonFlags $assistantFile @assistantArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Assistant interrompu (code $LASTEXITCODE). Consultez le message ci-dessus."
    }
} finally {
    [Net.ServicePointManager]::SecurityProtocol = $previousTls
    if (Test-Path -LiteralPath $assistantFolder) {
        Remove-Item -LiteralPath $assistantFolder -Recurse -Force
    }
}
