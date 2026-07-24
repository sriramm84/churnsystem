@echo off
setlocal enabledelayedexpansion

set "PYTHON=C:\Python313\python.exe"
set "SPARK_HOME=D:\spark-4.1.1-bin-hadoop3"
set "SCRIPT=D:\sem-6\ChurnSystem\spark\stream_consumer.py"

echo Starting Spark Stream Consumer...
start "SPARK_STREAM" cmd /k "set PYSPARK_PYTHON=%PYTHON% && set PYSPARK_DRIVER_PYTHON=%PYTHON% && "%SPARK_HOME%\bin\spark-submit.cmd" --master local[*] --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,org.apache.spark:spark-token-provider-kafka-0-10_2.13:4.1.1,org.mongodb.spark:mongo-spark-connector_2.13:10.4.0 --conf "spark.pyspark.python=%PYTHON%" --conf "spark.pyspark.driver.python=%PYTHON%" "%SCRIPT%""
echo Spark started.
