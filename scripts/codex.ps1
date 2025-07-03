# PowerShell wrapper for Codex CLI
# Provides robust cross-platform execution on Windows

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Function to find Codex executable
function Find-CodexExecutable {
    # Check CODEX_CLI_PATH environment variable
    if ($env:CODEX_CLI_PATH) {
        $candidates = @(
            Join-Path $env:CODEX_CLI_PATH "codex.cmd",
            Join-Path $env:CODEX_CLI_PATH "codex.exe",
            Join-Path $env:CODEX_CLI_PATH "codex.bat",
            $env:CODEX_CLI_PATH
        )
        
        foreach ($path in $candidates) {
            if (Test-Path $path) {
                return $path
            }
        }
    }
    
    # Search in PATH
    $codexInPath = Get-Command -Name codex -ErrorAction SilentlyContinue
    if ($codexInPath) {
        return $codexInPath.Source
    }
    
    # Check common installation locations
    $searchPaths = @(
        "$env:APPDATA\npm\codex.cmd",
        "$env:APPDATA\npm\codex.exe",
        "$env:LOCALAPPDATA\Programs\claif\bin\codex.cmd",
        "$env:LOCALAPPDATA\Programs\claif\bin\codex.exe",
        "$env:USERPROFILE\.local\bin\codex.cmd",
        "$env:USERPROFILE\.local\bin\codex.exe"
    )
    
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Check if npm is available and try to find via npm
    $npmCmd = Get-Command -Name npm -ErrorAction SilentlyContinue
    if ($npmCmd) {
        try {
            $npmRoot = & npm root -g 2>$null
            if ($npmRoot) {
                $npmCodex = Join-Path $npmRoot "..\@openai\codex-cli\bin\codex"
                if (Test-Path $npmCodex) {
                    return $npmCodex
                }
            }
        } catch {
            # Ignore npm errors
        }
    }
    
    # Check if bun is available
    $bunCmd = Get-Command -Name bun -ErrorAction SilentlyContinue
    if ($bunCmd) {
        try {
            $bunPath = & bun pm bin -g 2>$null
            if ($bunPath) {
                $bunCodex = Join-Path $bunPath "codex"
                if (Test-Path $bunCodex) {
                    return $bunCodex
                }
            }
        } catch {
            # Ignore bun errors
        }
    }
    
    return $null
}

# Main execution
$codexExe = Find-CodexExecutable

if (-not $codexExe) {
    Write-Error "Codex CLI not found."
    Write-Host ""
    Write-Host "Please install Codex CLI using one of these methods:"
    Write-Host "  npm install -g @openai/codex-cli"
    Write-Host "  bun add -g @openai/codex-cli"
    Write-Host "  claif install codex"
    Write-Host ""
    Write-Host "Or set CODEX_CLI_PATH environment variable to the installation directory."
    exit 1
}

# Execute Codex with all arguments
try {
    & $codexExe @Arguments
    exit $LASTEXITCODE
} catch {
    Write-Error "Failed to execute Codex CLI: $_"
    exit 1
}