echo %cd%
cd ../../
cd python-support/
set pythonpath=%cd%
set pythonpath
cd ../units/adms
python manage.py syncdb
pause