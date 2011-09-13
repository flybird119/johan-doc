del *.pyc /s

:几个特殊的与路径有关的变量
@echo off
echo 当前盘符：%~d0
echo 当前盘符和路径：%~dp0
echo 当前批处理全路径：%~f0
echo 当前盘符和路径的短文件名格式：%~sdp0
echo 当前CMD默认目录：%cd%
pause

:执行python程序 %1 为第一参数
python C:\Python26\Scripts\my_py_compile.py %1