del *.pyc /s

:�����������·���йصı���
@echo off
echo ��ǰ�̷���%~d0
echo ��ǰ�̷���·����%~dp0
echo ��ǰ������ȫ·����%~f0
echo ��ǰ�̷���·���Ķ��ļ�����ʽ��%~sdp0
echo ��ǰCMDĬ��Ŀ¼��%cd%
pause

:ִ��python���� %1 Ϊ��һ����
python C:\Python26\Scripts\my_py_compile.py %1