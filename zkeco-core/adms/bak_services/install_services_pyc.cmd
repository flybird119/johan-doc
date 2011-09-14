sc create memcached binPath= "%CD%\memcached.exe -p 11211 -l 127.0.0.1 -m 192 -d runservice" DisplayName= "memcached server" start= auto depend= TCPIP
@net start memcached 

python ServiceInstantMsg.pyc --startup auto install
@net start ZKECOInstantMessage

python ServiceBackupDB.pyc --startup auto install
@net start ZKECOBackupDB

python ServiceDataCommCenter.pyc --startup auto install
@net start ZKECODataCommCenterService

python ServiceADMS.pyc --startup auto install
@net start ZKECOWEBService

python ServiceWriteData.pyc --startup auto install
@net start ZKECOWriteDataService

python ServiceZksaas_adms.pyc --startup auto install
@net start ZKECOZksaasAdmsService

python ServiceAutoCalculate.pyc --startup auto install
@net start ZKECOAutoCalculateService

