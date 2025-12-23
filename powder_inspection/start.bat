@echo off
chcp 65001 >nul
title 분말 검사 시스템 서버

echo ================================================
echo 분말 검사 시스템 서버 시작
echo ================================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 설치 방법:
    echo 1. https://www.python.org/downloads/ 에서 Python 다운로드
    echo 2. 설치 시 "Add Python to PATH" 체크
    echo.
    pause
    exit /b 1
)

echo Python 버전:
python --version
echo.

REM 필요한 라이브러리 확인
echo 라이브러리 확인 중...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [경고] Flask가 설치되어 있지 않습니다. 설치를 시작합니다...
    pip install Flask Flask-CORS
    echo.
)

REM 데이터베이스 파일 확인
if not exist "database.db" (
    echo [경고] 데이터베이스가 없습니다. 초기화를 시작합니다...
    python init_db.py
    echo.
)

echo 서버를 시작합니다...
echo.
echo ================================================
echo 접속 방법:
echo - 이 PC에서: http://localhost:5000
echo - 다른 PC에서: http://[이 PC의 IP]:5000
echo.
echo 서버 종료: Ctrl+C 또는 이 창 닫기
echo ================================================
echo.

REM 서버 실행
python app.py

REM 서버 종료 시
echo.
echo 서버가 종료되었습니다.
pause
