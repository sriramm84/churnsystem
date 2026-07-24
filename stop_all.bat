@echo off
setlocal enabledelayedexpansion

REM =====================================================
REM PATHS
REM =====================================================
set "KAFKA_HOME=D:\kafka_2.13-3.7.0"

echo.
echo =====================================================
echo   STOPPING Kafka + Spark Streaming System (Windows)
echo =====================================================
echo.

REM =====================================================
REM 1) Close only CMD windows started by run_all
REM (SAFE: does NOT affect Chrome)
REM =====================================================
echo [1/8] Closing project CMD windows (PRODUCER, SPARK_STREAM, KAFKA, ZOOKEEPER, PREDICT_SERVICE)...

REM added IMAGENAME eq cmd.exe (prevents killing Chrome)
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq PRODUCER*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SPARK_STREAM*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq KAFKA*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq ZOOKEEPER*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq PREDICT_SERVICE*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq PIPELINE_CONTROLLER*" /T /F >nul 2>&1

REM =====================================================
REM 2) Kill producer python
REM =====================================================
echo [2/8] Killing python producer if running...
taskkill /F /IM python.exe >nul 2>&1

REM =====================================================
REM 3) Kill spark-submit
REM =====================================================
echo [3/8] Killing spark-submit if running...
taskkill /F /IM spark-submit.cmd >nul 2>&1

REM =====================================================
REM 4) Try graceful stop Kafka + ZK
REM =====================================================
echo [4/8] Attempting graceful Kafka stop...
call "%KAFKA_HOME%\bin\windows\kafka-server-stop.bat" >nul 2>&1
timeout /t 2 >nul

echo [5/8] Attempting graceful Zookeeper stop...
call "%KAFKA_HOME%\bin\windows\zookeeper-server-stop.bat" >nul 2>&1
timeout /t 2 >nul

REM =====================================================
REM 5) Kill ONLY Kafka/Zookeeper java processes
REM =====================================================
echo [6/8] Cleaning Kafka/Zookeeper Java processes safely...

for /f "tokens=2 delims== " %%a in ('
  wmic process where "name='java.exe' and (CommandLine like '%%kafka.Kafka%%' or CommandLine like '%%QuorumPeerMain%%')" get ProcessId /value ^| find "="
') do (
  echo Killing PID: %%a
  taskkill /F /PID %%a >nul 2>&1
)

REM =====================================================
REM 7) Kill prediction service python
REM =====================================================
echo [7/8] Killing prediction service if running...
for /f "tokens=2 delims== " %%a in ('
  wmic process where "name='python.exe' and CommandLine like '%%predict_service.py%%'" get ProcessId /value ^| find "="
') do (
  echo Killing prediction service PID: %%a
  taskkill /F /PID %%a >nul 2>&1
)

REM =====================================================
REM 8) Done
REM =====================================================
echo.
echo STOP COMPLETE: Kafka + Spark + Producer + Zookeeper + Prediction Service closed.
echo.
pause
