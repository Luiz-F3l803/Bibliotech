@echo off
chcp 65001 >nul
title Biblioteca Escolar - Servidor Local
cd /d "%~dp0"

echo ============================================================
echo   Sistema de Biblioteca Escolar
echo ============================================================
echo.

REM ---- Verifica se o Python esta instalado ----
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python nao foi encontrado neste computador.
    echo Instale o Python em https://www.python.org/downloads/
    echo IMPORTANTE: marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b
)

REM ---- Cria o ambiente virtual, se ainda nao existir ----
if not exist "venv\" (
    echo Criando ambiente virtual pela primeira vez...
    python -m venv venv
    echo.
)

REM ---- Ativa o ambiente virtual ----
call venv\Scripts\activate.bat

REM ---- Instala/atualiza as dependencias ----
echo Verificando dependencias necessarias...
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha ao instalar as dependencias. Verifique sua conexao com a internet.
    pause
    exit /b
)

echo.
echo ============================================================
echo  Iniciando o servidor local...
echo  O sistema abrira automaticamente no seu navegador.
echo  Para ENCERRAR o sistema, feche esta janela ou pressione Ctrl+C.
echo ============================================================
echo.

REM ---- Abre o navegador apos alguns segundos (em segundo plano) ----
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5000"

REM ---- Inicia o servidor Flask ----
python app.py

pause
