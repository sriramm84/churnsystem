@echo off
set "KAFKA_HOME=D:\kafka_2.13-3.7.0"

echo Closing project CMD windows safely...

taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq PRODUCER*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SPARK_STREAM*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq KAFKA*" /T /F >nul 2>&1
taskkill /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq ZOOKEEPER*" /T /F >nul 2>&1

taskkill /F /IM spark-submit.cmd >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

call "%KAFKA_HOME%\bin\windows\kafka-server-stop.bat" >nul 2>&1
call "%KAFKA_HOME%\bin\windows\zookeeper-server-stop.bat" >nul 2>&1

echo Done.
pause
