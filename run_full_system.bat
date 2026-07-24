@echo off
setlocal

echo ===============================
echo STARTING FULL SYSTEM
echo ===============================

REM =========================
REM CLEAN OLD PROCESSES
REM =========================
echo Cleaning old processes...
taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

timeout /t 3 >nul

REM =========================
REM START MONGODB
REM =========================
echo Starting MongoDB...
start "MongoDB" cmd /k "mongod --dbpath D:\ChurnSystem\data\db"
timeout /t 6 >nul

REM =========================
REM START ZOOKEEPER
REM =========================
echo Starting Zookeeper...
start "Zookeeper" cmd /k "cd /d D:\kafka_2.13-3.7.0 && bin\windows\zookeeper-server-start.bat config\zookeeper.properties"
timeout /t 12 >nul

REM =========================
REM START KAFKA
REM =========================
echo Starting Kafka...
start "Kafka" cmd /k "cd /d D:\kafka_2.13-3.7.0 && bin\windows\kafka-server-start.bat config\server.properties"
timeout /t 25 >nul

REM =========================
REM START PRODUCER
REM =========================
echo Starting Producer...
start "Producer" cmd /k "cd /d D:\ChurnSystem\kafka && python producer.py"
timeout /t 10 >nul

REM =========================
REM 🔥 START SPARK (FINAL FIX)
REM =========================
echo Starting Spark...

start "Spark" cmd /k "cd /d D:\ChurnSystem\spark && set PYSPARK_PYTHON=C:\Python312\python.exe && set PYSPARK_DRIVER_PYTHON=C:\Python312\python.exe && D:\spark-4.1.1-bin-hadoop3\bin\spark-submit.cmd --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1 stream_consumer.py"

timeout /t 8 >nul


REM =========================
REM START ML SERVICE
REM =========================
echo Starting ML Service...
start "ML Service" cmd /k "cd /d D:\ChurnSystem && python predict_service.py"
timeout /t 5 >nul

REM =========================
REM START BACKEND
REM =========================
echo Starting Backend...
start "Backend" cmd /k "cd /d D:\ChurnSystem\backend && npm start"
timeout /t 5 >nul

REM =========================
REM START FRONTEND
REM =========================
echo Starting Frontend...
start "Frontend" cmd /k "cd /d D:\ChurnSystem\frontend && npm start"

echo ===============================
echo SYSTEM STARTED SUCCESSFULLY
echo ===============================

echo.
echo 🔥 WAIT 10-15 SECONDS FOR DATA TO FLOW...
echo.

pause