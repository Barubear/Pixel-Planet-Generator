param(
    [string]$Python = "C:\Users\zxsyx\.conda\envs\torch\python.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$pythonRoot = Split-Path -Parent ([IO.Path]::GetFullPath($Python))
$packageRoot = Join-Path $projectRoot "package"
$buildRoot = Join-Path $projectRoot ".package_build"

foreach ($target in @($packageRoot, $buildRoot)) {
    if (Test-Path -LiteralPath $target) {
        $resolved = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $target).Path)
        if (-not $resolved.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe build target: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

New-Item -ItemType Directory -Path $packageRoot, $buildRoot | Out-Null

$builds = @(
    @{ Name = "PixelPlanetGenerator-Full"; Entry = "full_launcher.py"; Readme = "PACKAGE_README_FULL.txt" },
    @{ Name = "PixelPlanetGenerator-Simple"; Entry = "simple_launcher.py"; Readme = "PACKAGE_README_SIMPLE.txt" }
)

foreach ($build in $builds) {
    $workPath = Join-Path $buildRoot ("work-" + $build.Name)
    $specPath = Join-Path $buildRoot ("spec-" + $build.Name)
    & $Python -m PyInstaller --noconfirm --clean --onedir --windowed `
        --exclude-module numpy `
        --add-binary ((Join-Path $pythonRoot "Library\bin\tcl86t.dll") + ";.") `
        --add-binary ((Join-Path $pythonRoot "Library\bin\tk86t.dll") + ";.") `
        --name $build.Name `
        --distpath $packageRoot `
        --workpath $workPath `
        --specpath $specPath `
        (Join-Path $projectRoot $build.Entry)
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed for $($build.Name)"
    }

    $destination = Join-Path $packageRoot $build.Name
    Copy-Item -LiteralPath (Join-Path $projectRoot "ui_prototype.html") -Destination $destination
    Copy-Item -LiteralPath (Join-Path $projectRoot "locales") -Destination $destination -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot $build.Readme) -Destination (Join-Path $destination "使用说明.txt")
    New-Item -ItemType Directory -Path (Join-Path $destination "output") | Out-Null
}

$resolvedBuildRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $buildRoot).Path)
if (-not $resolvedBuildRoot.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe cleanup target: $resolvedBuildRoot"
}
Remove-Item -LiteralPath $resolvedBuildRoot -Recurse -Force

Write-Output "Packages created in $packageRoot"
