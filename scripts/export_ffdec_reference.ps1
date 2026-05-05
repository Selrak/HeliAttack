param(
    [Parameter(Mandatory=$true)]
    [string]$Swf,

    [string]$OutRoot,

    [string]$Ffdec
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

function Resolve-FFDEC {
    param([string]$Requested)

    $names = @("ffdec-cli.exe", "ffdec-cli.bat", "ffdec.bat", "ffdec.exe")
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($Requested) {
        $candidates.Add($Requested)
    }
    if ($env:FFDEC_CLI) {
        $candidates.Add($env:FFDEC_CLI)
    }
    foreach ($root in @($env:FFDEC_HOME, $env:FFDEC_PATH)) {
        if ($root) {
            foreach ($name in $names) {
                $candidates.Add((Join-Path $root $name))
            }
        }
    }
    foreach ($name in $names) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            $candidates.Add($cmd.Source)
        }
    }

    $commonRoots = @(
        (Join-Path $RepoRoot "tools\ffdec"),
        (Join-Path $RepoRoot "tools\ffdec-cli"),
        (Join-Path $RepoRoot "ffdec"),
        (Join-Path $env:ProgramFiles "FFDec"),
        (Join-Path ${env:ProgramFiles(x86)} "FFDec"),
        (Join-Path $env:LOCALAPPDATA "JPEXS Free Flash Decompiler"),
        (Join-Path $env:LOCALAPPDATA "Programs\JPEXS Free Flash Decompiler"),
        (Join-Path $env:ProgramFiles "JPEXS Free Flash Decompiler"),
        (Join-Path ${env:ProgramFiles(x86)} "JPEXS Free Flash Decompiler")
    )
    foreach ($root in $commonRoots) {
        if ($root -and (Test-Path $root)) {
            foreach ($name in $names) {
                $candidates.Add((Join-Path $root $name))
            }
        }
    }

    foreach ($candidate in $candidates) {
        if (-not $candidate) {
            continue
        }
        $expanded = [Environment]::ExpandEnvironmentVariables($candidate)
        if (Test-Path $expanded) {
            return (Resolve-Path $expanded).Path
        }
        $cmd = Get-Command $expanded -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }

    $searched = ($candidates | Where-Object { $_ } | Select-Object -Unique) -join "`n  "
    throw @"
FFDEC command-line executable was not found.

Install JPEXS Free Flash Decompiler, then either:
  1. Add the folder containing ffdec-cli.exe to PATH.
  2. Set an environment variable:
       `$env:FFDEC_CLI = 'C:\Path\To\ffdec-cli.exe'
  3. Pass it explicitly:
       .\export_ffdec_reference.ps1 D:\cthin\Downloads\heli-attack-2.swf -Ffdec 'C:\Path\To\ffdec-cli.exe'

Also supported if present: ffdec-cli.bat, ffdec.bat, ffdec.exe.

Searched:
  $searched
"@
}

function ConvertTo-ProcessArgument {
    param([string]$Value)

    if ($Value -notmatch '[\s"]') {
        return $Value
    }
    return '"' + ($Value -replace '"', '\"') + '"'
}

function Invoke-FFDEC {
    param(
        [string[]]$FfdecArgs,
        [string]$LogName,
        [switch]$AllowFailure
    )

    $log = Join-Path $dirs.logs $LogName
    $argumentLine = ($FfdecArgs | ForEach-Object { ConvertTo-ProcessArgument $_ }) -join " "
    Write-Host "Running: $Ffdec $argumentLine"

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Ffdec
    $startInfo.Arguments = $argumentLine
    $startInfo.WorkingDirectory = $RepoRoot
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    @(
        "COMMAND: $Ffdec $argumentLine"
        "EXIT_CODE: $($process.ExitCode)"
        ""
        "STDOUT:"
        $stdout
        ""
        "STDERR:"
        $stderr
    ) -join "`r`n" | Set-Content -Path $log -Encoding UTF8

    if ($process.ExitCode -ne 0 -and -not $AllowFailure) {
        throw "FFDEC failed with exit code $($process.ExitCode). See log: $log"
    }
}

$Swf = (Resolve-Path $Swf).Path
if (-not $OutRoot) {
    $OutRoot = Join-Path $RepoRoot "reference_exports\ffdec_ha2"
}
$OutRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutRoot)
$Ffdec = Resolve-FFDEC $Ffdec

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

$dirs = @{
    swf_xml        = Join-Path $OutRoot "swf_xml"
    tag_dump       = Join-Path $OutRoot "tag_dump"
    scripts_as     = Join-Path $OutRoot "scripts_as"
    scripts_pcode  = Join-Path $OutRoot "scripts_pcode"
    scripts_hex    = Join-Path $OutRoot "scripts_hex"
    sprites_png    = Join-Path $OutRoot "sprites_png"
    sprites_svg    = Join-Path $OutRoot "sprites_svg"
    shapes_svg     = Join-Path $OutRoot "shapes_svg"
    frames_png     = Join-Path $OutRoot "frames_png"
    images         = Join-Path $OutRoot "images"
    symbol_class   = Join-Path $OutRoot "symbol_class"
    logs           = Join-Path $OutRoot "logs"
}

foreach ($d in $dirs.Values) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

function Run-FFDEC {
    param(
        [string[]]$FfdecArgs,
        [string]$LogName
    )

    Invoke-FFDEC -FfdecArgs $FfdecArgs -LogName $LogName
}

# Record tool/version/help and SWF hash.
Write-Host "Using FFDEC: $Ffdec"
Invoke-FFDEC -FfdecArgs @("-help") -LogName "ffdec_help.txt" -AllowFailure
Get-FileHash -Algorithm SHA256 $Swf | Format-List *> (Join-Path $dirs.logs "swf_sha256.txt")

# 1. Whole SWF XML: placement matrices, tags, timelines, names, depths.
Run-FFDEC @("-swf2xml", $Swf, (Join-Path $dirs.swf_xml "heli_attack_2.swf.xml")) "swf2xml.log"

# 2. Raw SWF tag dump.
Run-FFDEC @("-dumpSWF", $Swf) "dumpSWF.txt"

# 3. AS2 script list dump with export names.
Run-FFDEC @("-dumpAS2", "-exportNames", $Swf) "dumpAS2_exportNames.txt"

# 4. ActionScript source export.
Run-FFDEC @("-format", "script:as", "-export", "script", $dirs.scripts_as, $Swf) "export_scripts_as.log"

# 5. P-code with hex: useful when decompiled .as is ambiguous.
Run-FFDEC @("-format", "script:pcodehex", "-export", "script", $dirs.scripts_pcode, $Swf) "export_scripts_pcodehex.log"

# 6. Hex-only scripts: low-level fallback.
Run-FFDEC @("-format", "script:hex", "-export", "script", $dirs.scripts_hex, $Swf) "export_scripts_hex.log"

# 7. Sprites as PNG: current practical rendering reference.
Run-FFDEC @("-format", "sprite:png", "-export", "sprite", $dirs.sprites_png, $Swf) "export_sprites_png.log"

# 8. Sprites as SVG: useful for bounds/vector structure when available.
Run-FFDEC @("-format", "sprite:svg", "-export", "sprite", $dirs.sprites_svg, $Swf) "export_sprites_svg.log"

# 9. Shapes as SVG: useful for hitboxes and geometry.
Run-FFDEC @("-format", "shape:svg", "-export", "shape", $dirs.shapes_svg, $Swf) "export_shapes_svg.log"

# 10. Frames as PNG: visual reference.
Run-FFDEC @("-format", "frame:png", "-export", "frame", $dirs.frames_png, $Swf) "export_frames_png.log"

# 11. Images.
Run-FFDEC @("-format", "image:png_gif_jpeg", "-export", "image", $dirs.images, $Swf) "export_images.log"

# 12. SymbolClass mapping.
Run-FFDEC @("-export", "symbolClass", $dirs.symbol_class, $Swf) "export_symbol_class.log"

Write-Host ""
Write-Host "Done. FFDEC reference export written to:"
Write-Host $OutRoot
