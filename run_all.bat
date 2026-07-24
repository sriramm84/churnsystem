@echo off
setlocal enabledelayedexpansion

REM =====================================================
REM PATHS
REM =====================================================
set "KAFKA_HOME=D:\kafka_2.13-3.7.0"
set "SPARK_HOME=D:\spark-4.1.1-bin-hadoop3"
set "PROJECT_HOME=D:\sem-6\ChurnSystem"
set "PYTHON_EXE=C:\Python313\python.exe"

REM =====================================================
REM Spark Python Fix
REM =====================================================
set "PYSPARK_PYTHON=%PYTHON_EXE%"
set "PYSPARK_DRIVER_PYTHON=%PYTHON_EXE%"

set "PATH=%SPARK_HOME%\bin;%KAFKA_HOME%\bin\windows;%PATH%"

REM =====================================================
REM Project scripts
REM =====================================================
set "KAFKA_PRODUCER=%PROJECT_HOME%\kafka\producer.py"
set "SPARK_CONSUMER=%PROJECT_HOME%\spark\stream_consumer.py"
set "TOPIC_NAME=churn-topic"

REM ✅ Kafka connector packages (MUST match Spark version 4.1.1)
set "KAFKA_PACKAGES=org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,org.apache.spark:spark-token-provider-kafka-0-10_2.13:4.1.1"

echo.
echo =====================================================
echo   Starting Kafka + Spark Streaming System (Windows)
echo =====================================================
echo Kafka Home  : %KAFKA_HOME%
echo Spark Home  : %SPARK_HOME%
echo Project Home: %PROJECT_HOME%
echo Python      : %PYTHON_EXE%
echo Topic       : %TOPIC_NAME%
echo =====================================================
echo.

REM =====================================================
REM 1) Kill old processes + CLEAN ALL STALE STATE FIRST
REM =====================================================
echo [1/7] Killing old processes and cleaning stale Kafka/ZK state...

REM Kill python/spark first so ports are released
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM spark-submit.cmd >nul 2>&1

REM Kill any stray java Kafka/ZK processes so locks are released
for /f "tokens=2 delims== " %%a in ('
  wmic process where "name='java.exe' and (CommandLine like '%%kafka.Kafka%%' or CommandLine like '%%QuorumPeerMain%%')" get ProcessId /value ^| find "="
') do (
  taskkill /F /PID %%a >nul 2>&1
)

REM Clean Kafka log directories (meta.properties with stale broker ID is here)
if exist "%KAFKA_HOME%\kafka-logs" (
  echo   - Deleting %KAFKA_HOME%\kafka-logs
  rmdir /s /q "%KAFKA_HOME%\kafka-logs" 2>nul
)

REM Clean Kafka data directory (if log.dir is set to data/)
if exist "%KAFKA_HOME%\data" (
  echo   - Deleting %KAFKA_HOME%\data
  rmdir /s /q "%KAFKA_HOME%\data" 2>nul
)

REM Clean Zookeeper data directories (prevents epoch conflicts)
if exist "%KAFKA_HOME%\zookeeper-data" (
  echo   - Deleting %KAFKA_HOME%\zookeeper-data
  rmdir /s /q "%KAFKA_HOME%\zookeeper-data" 2>nul
)
if exist "%KAFKA_HOME%\zookeeper-logs" (
  echo   - Deleting %KAFKA_HOME%\zookeeper-logs
  rmdir /s /q "%KAFKA_HOME%\zookeeper-logs" 2>nul
)

REM =====================================================
REM 2) Start Zookeeper
REM =====================================================
echo [2/7] Starting Zookeeper...
start "ZOOKEEPER" cmd /k ""%KAFKA_HOME%\bin\windows\zookeeper-server-start.bat" "%KAFKA_HOME%\config\zookeeper.properties""

call :waitPort 2181 60
if errorlevel 1 (
  echo ERROR: Zookeeper did not open port 2181.
  pause
  goto :EOF
)

REM Clean Zookeeper broker registration (now ZK is running, safe to connect)
(
  echo deleteall /brokers/ids/0
  echo deleteall /brokers/ids/1
  echo deleteall /brokers/ids/2
  echo deleteall /controller
  echo deleteall /admin/delete_topics
  echo quit
) | call "%KAFKA_HOME%\bin\windows\zookeeper-shell.bat" 127.0.0.1:2181 >nul 2>&1

REM =====================================================
REM 3) Start Kafka broker
REM =====================================================
echo [3/7] Starting Kafka broker...
start "KAFKA" cmd /k ""%KAFKA_HOME%\bin\windows\kafka-server-start.bat" "%KAFKA_HOME%\config\server.properties""

call :waitPort 9092 120
if errorlevel 1 (
  echo ERROR: Kafka did not open port 9092.
  pause
  goto :EOF
)

REM =====================================================
REM 4) Ensure topic exists
REM =====================================================
echo [4/7] Ensuring topic exists: %TOPIC_NAME%
call "%KAFKA_HOME%\bin\windows\kafka-topics.bat" --bootstrap-server 127.0.0.1:9092 --create --if-not-exists --topic %TOPIC_NAME% --partitions 1 --replication-factor 1

REM =====================================================
REM 5) Start Producer
REM =====================================================
echo [5/7] Starting Kafka producer...
if not exist "%KAFKA_PRODUCER%" (
  echo ERROR: Producer not found: %KAFKA_PRODUCER%
  pause
  goto :EOF
)
start "PRODUCER" cmd /k ""%PYTHON_EXE%" "%KAFKA_PRODUCER%""

REM =====================================================
REM 6) Start Spark Streaming Consumer (Kafka connector FIXED)
REM =====================================================
echo [6/7] Starting Spark streaming consumer...
if not exist "%SPARK_CONSUMER%" (
  echo ERROR: Spark consumer not found: %SPARK_CONSUMER%
  pause
  goto :EOF
)

REM Delete checkpoint to avoid version mismatch errors
if exist "%PROJECT_HOME%\spark\checkpoints\churn_stream" (
  echo Deleting old checkpoint folder...
  rmdir /s /q "%PROJECT_HOME%\spark\checkpoints\churn_stream"
)

REM One-line command avoids Windows quote/^ bugs
start "SPARK_STREAM" cmd /k ""%SPARK_HOME%\bin\spark-submit.cmd" --master local[*] --packages %KAFKA_PACKAGES% --conf "spark.pyspark.python=%PYTHON_EXE%" --conf "spark.pyspark.driver.python=%PYTHON_EXE%" "%SPARK_CONSUMER%""

echo.
echo ALL SERVICES STARTED
echo.
pause
goto :EOF


REM =====================================================
REM Function: wait for TCP port
REM =====================================================
:waitPort
set "PORT=%~1"
set "TIMEOUT=%~2"
echo Waiting for port %PORT% ... (timeout %TIMEOUT%s)

for /L %%i in (1,1,%TIMEOUT%) do (
  powershell -Command "try { $c = New-Object Net.Sockets.TcpClient('127.0.0.1', %PORT%); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
  if !errorlevel! == 0 (
    echo Port %PORT% is open.
    exit /b 0
  )
  timeout /t 1 >nul
)

echo Timeout waiting for port %PORT%.
exit /b 1
