@echo off
cd /d D:\kafka_2.13-3.7.0

set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-8.0.482.8-hotspot
set PATH=%JAVA_HOME%\bin;%PATH%

bin\windows\zookeeper-server-start.bat config\zookeeper.properties