@echo off
REM Windows batch wrapper for Codex CLI
REM This wrapper ensures proper execution on Windows systems

setlocal enabledelayedexpansion

REM Try to find codex executable in various locations
set CODEX_EXE=
set SEARCH_PATHS=%CODEX_CLI_PATH%;%PATH%;%APPDATA%\npm;%LOCALAPPDATA%\Programs\claif\bin;%USERPROFILE%\.local\bin

REM Check CODEX_CLI_PATH first
if defined CODEX_CLI_PATH (
    if exist "%CODEX_CLI_PATH%\codex.cmd" (
        set CODEX_EXE=%CODEX_CLI_PATH%\codex.cmd
    ) else if exist "%CODEX_CLI_PATH%\codex.exe" (
        set CODEX_EXE=%CODEX_CLI_PATH%\codex.exe
    ) else if exist "%CODEX_CLI_PATH%" (
        set CODEX_EXE=%CODEX_CLI_PATH%
    )
)

REM Search in PATH if not found
if not defined CODEX_EXE (
    for %%i in (codex.cmd codex.exe codex.bat codex) do (
        set RESULT=
        for %%j in ("%%~$PATH:i") do set RESULT=%%~j
        if defined RESULT (
            set CODEX_EXE=!RESULT!
            goto :found
        )
    )
)

REM Check npm global installation
if not defined CODEX_EXE (
    if exist "%APPDATA%\npm\codex.cmd" (
        set CODEX_EXE=%APPDATA%\npm\codex.cmd
    ) else if exist "%APPDATA%\npm\codex.exe" (
        set CODEX_EXE=%APPDATA%\npm\codex.exe
    )
)

REM Check Claif installation directory
if not defined CODEX_EXE (
    if exist "%LOCALAPPDATA%\Programs\claif\bin\codex.cmd" (
        set CODEX_EXE=%LOCALAPPDATA%\Programs\claif\bin\codex.cmd
    ) else if exist "%LOCALAPPDATA%\Programs\claif\bin\codex.exe" (
        set CODEX_EXE=%LOCALAPPDATA%\Programs\claif\bin\codex.exe
    )
)

:found
if not defined CODEX_EXE (
    echo Error: Codex CLI not found.
    echo.
    echo Please install Codex CLI using one of these methods:
    echo   npm install -g @openai/codex-cli
    echo   bun add -g @openai/codex-cli
    echo   claif install codex
    echo.
    echo Or set CODEX_CLI_PATH environment variable to the installation directory.
    exit /b 1
)

REM Execute Codex with all arguments
"%CODEX_EXE%" %*
exit /b %ERRORLEVEL%