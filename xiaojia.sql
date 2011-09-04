-- 销假申请单
select t2.fnumber 职员编码,t2.Fname_L2 姓名, t1.FBeginTime 开始时间, t1.FEndTime 结束时间,t0.fcreatetime,t0.fapplydate,t0.Flastupdatetime
from T_HR_LeaveReportBill t0
inner join T_HR_LeaveReportBillEntry t1 on t1.fbillid=t0.fid
inner join T_BD_Person t2 on t2.fid=t1.fpersonid
where t0.FIsMultiEntry=0;
