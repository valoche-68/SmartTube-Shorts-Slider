"""PowerShell dependency setup with simulated installers only (5.1 and 7)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

LAUNCHER = Path(__file__).resolve().parents[1] / "start.ps1"
SHELLS = list(dict.fromkeys(filter(None, (shutil.which("powershell"), shutil.which("pwsh")))))


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(os.name == "nt" and SHELLS, "Windows PowerShell required")
class WindowsSetupTest(unittest.TestCase):
    def run_powershell(self, body):
        # Every test blocks network and native installer execution unless it
        # explicitly replaces that function with a simulated result.
        harness = "\n".join((
            "$ErrorActionPreference = 'Stop'",
            ". " + quote(LAUNCHER),
            "function Invoke-SliderInstaller { throw 'Real installer forbidden in tests' }",
            "function Invoke-WebRequest { throw 'Network forbidden in tests' }",
            "function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }",
            body,
        ))
        with tempfile.TemporaryDirectory(prefix="shorts windows setup ") as directory:
            path = Path(directory) / "test setup.ps1"
            path.write_text(harness, encoding="utf-8")
            for shell in SHELLS:
                with self.subTest(shell=Path(shell).name):
                    result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-File", str(path)],
                                            text=True, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_help_and_local_backup_skip_adb_only(self):
        self.run_powershell(r"""
Assert (Test-SliderNeedsAdb @()) 'Interactive menu requires ADB'
Assert (Test-SliderNeedsAdb @('--status')) 'Online status requires ADB'
foreach ($options in @(@('--help'), @('-h'), @('--backup', 'living room.zip'), @('--backup=living room.zip'))) {
    Assert (-not (Test-SliderNeedsAdb $options)) 'Help/local backup must not install ADB'
}
$script:pythonChecks = 0
function Find-SliderPython {
    $script:pythonChecks++
    [pscustomobject]@{ Path = 'C:\Python\python.exe'; Flags = @() }
}
function Find-SliderAdb { throw 'ADB should not be inspected' }
function Install-SliderPackage { throw 'Nothing should be installed' }
Initialize-SliderPrerequisites @('--help') | Out-Null
Initialize-SliderPrerequisites @('--backup', 'living room.zip') | Out-Null
Assert ($script:pythonChecks -eq 2) 'Python must still be detected'
""")

    def test_existing_tools_are_reused_with_space_in_sdk_path(self):
        self.run_powershell(r"""
function Find-SliderPython { [pscustomobject]@{ Path = 'C:\Existing Python\py.exe'; Flags = @('-3') } }
function Find-SliderAdb { 'C:\Android SDK\platform-tools\adb.exe' }
function Install-SliderPackage { throw 'Existing tools must not be installed again' }
$python = Initialize-SliderPrerequisites @()
Assert ($python.Path -eq 'C:\Existing Python\py.exe') 'Existing Python should be retained'
Assert ($python.Flags[0] -eq '-3') 'Launcher flags must be retained'
Assert ($env:PATH.StartsWith('C:\Android SDK\platform-tools;')) 'Selected SDK must be visible to the assistant'
""")

    def test_install_missing_tools_and_second_call_is_idempotent(self):
        self.run_powershell(r"""
$script:hasPython = $false
$script:hasAdb = $false
$script:packages = @()
function Find-SliderPython {
    if ($script:hasPython) { [pscustomobject]@{ Path = 'C:\Python\python.exe'; Flags = @() } }
}
function Find-SliderAdb { if ($script:hasAdb) { 'C:\Android SDK\adb.exe' } }
function Install-SliderPackage($PackageId, $Label) {
    $script:packages += $PackageId
    if ($PackageId -eq 'Python.Python.3.13') { $script:hasPython = $true }
    elseif ($PackageId -eq 'Google.PlatformTools') { $script:hasAdb = $true }
    else { throw 'Unknown package' }
}
Initialize-SliderPrerequisites @() | Out-Null
Initialize-SliderPrerequisites @() | Out-Null
Assert (($script:packages -join ',') -eq 'Python.Python.3.13,Google.PlatformTools') 'Install each missing tool exactly once'
""")

    def test_only_missing_adb_is_installed(self):
        self.run_powershell(r"""
$script:adbChecks = 0
$script:packages = @()
function Find-SliderPython { [pscustomobject]@{ Path = 'C:\Python\python.exe'; Flags = @() } }
function Find-SliderAdb {
    $script:adbChecks++
    if ($script:adbChecks -gt 1) { 'C:\Android SDK\adb.exe' }
}
function Install-SliderPackage($PackageId, $Label) { $script:packages += $PackageId }
Initialize-SliderPrerequisites @() | Out-Null
Assert (($script:packages -join ',') -eq 'Google.PlatformTools') 'Do not replace a working Python'
""")

    def test_failed_installer_stops_without_refresh_or_download(self):
        self.run_powershell(r"""
function Get-Command { [pscustomobject]@{ Source = 'C:\Win Get\winget.exe' } }
function Invoke-SliderInstaller { 42 }
function Update-SliderProcessPath { throw 'Must not refresh PATH after a failed install' }
$failed = $false
try { Install-SliderPackage 'Python.Python.3.13' 'Python' }
catch { $failed = $_.Exception.Message -match 'WinGet : 42' }
Assert $failed 'Installer failure must be propagated'
""")

    def test_winget_missing_gives_official_recovery_instructions(self):
        self.run_powershell(r"""
function Get-Command { $null }
$failed = $false
try { Install-SliderPackage 'Python.Python.3.13' 'Python' }
catch { $failed = $_.Exception.Message -match 'apps.microsoft.com/detail/9nblggh4nns1' }
Assert $failed 'Missing WinGet must give an actionable official link'
""")

    def test_exact_official_package_and_user_scope_are_requested(self):
        self.run_powershell(r"""
function Get-Command { [pscustomobject]@{ Source = 'C:\Win Get\winget.exe' } }
$script:refreshed = $false
function Invoke-SliderInstaller($Path, $InstallerArguments) {
    Assert ($Path -eq 'C:\Win Get\winget.exe') 'Executable paths with spaces must remain intact'
    $expected = @('install', '--id', 'Google.PlatformTools', '--exact', '--source', 'winget',
                  '--scope', 'user', '--accept-source-agreements', '--accept-package-agreements', '--disable-interactivity')
    Assert (($InstallerArguments -join '|') -eq ($expected -join '|')) 'Unexpected installation options'
    0
}
function Update-SliderProcessPath { $script:refreshed = $true }
Install-SliderPackage 'Google.PlatformTools' 'ADB'
Assert $script:refreshed 'Newly installed commands must become visible immediately'
""")

    def test_success_without_usable_tool_is_an_error(self):
        self.run_powershell(r"""
function Find-SliderPython { $null }
function Install-SliderPackage { }
$failed = $false
try { Initialize-SliderPrerequisites @('--help') | Out-Null }
catch { $failed = $_.Exception.Message -match 'introuvable ou incompatible' }
Assert $failed 'Installer exit zero is not enough to run the assistant'
""")

    def test_store_alias_is_skipped_and_old_python_is_rejected(self):
        self.run_powershell(r"""
function Get-Command($Name, $CommandType, [switch]$All, $ErrorAction) {
    if ($Name -eq 'python') {
        [pscustomobject]@{ Source = 'C:\Users\Me\AppData\Local\Microsoft\WindowsApps\python.exe' }
        [pscustomobject]@{ Source = 'C:\Old Python\python.exe' }
        [pscustomobject]@{ Source = 'C:\Current Python\python.exe' }
    }
}
function Get-Item { @() }
$script:tested = @()
function Test-SliderPython($Candidate) {
    $script:tested += $Candidate.Path
    $Candidate.Path -eq 'C:\Current Python\python.exe'
}
$python = Find-SliderPython
Assert ($python.Path -eq 'C:\Current Python\python.exe') 'Find a supported Python before installing another'
Assert ($script:tested.Count -eq 2) 'Never execute a Store alias'
""")


if __name__ == "__main__":
    unittest.main()
