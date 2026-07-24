@echo off

set SPARK_HOME=D:\spark-4.1.1-bin-hadoop3
set PYSPARK_PYTHON=C:\Python313\python.exe
set PYSPARK_DRIVER_PYTHON=C:\Python313\python.exe

cd /d D:\ChurnSystem\spark

D:\spark-4.1.1-bin-hadoop3\bin\spark-submit.cmd ^
--packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,org.mongodb.spark:mongo-spark-connector_2.13:10.4.0 ^
stream_consumer.py