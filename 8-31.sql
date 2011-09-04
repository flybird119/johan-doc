-- 请假申请单
select t2.Fname_L2 姓名, t1.FBeginTime 开始时间, t1.FEndTime 结束时间,t1.freason 请假原因,t0.fcreatetime 创建时间,t3.fname_l2 请假类别
from T_HR_LeaveBill t0
inner join T_HR_LeaveBillEntry t1 on t1.fbillid=t0.fid
inner join T_BD_Person t2 on t2.fid=t1.fpersonid

left join T_HR_TimeAttendance t3 on t3.fid=t1.ftypeid

where t0.FApproveState in (0,1)   order by t0.fcreatetime;


--------------------销假申请--------------------
select t2.Fname_L2 姓名, t1.FBeginTime 开始时间, t1.FEndTime 结束时间,t1.freason 请假原因,t0.fcreatetime 创建时间,t3.fname_l2 请假类别
from T_HR_LeaveBill t0
inner join T_HR_LeaveBillEntry t1 on t1.fbillid=t0.fid
inner join T_BD_Person t2 on t2.fid=t1.fpersonid

left join T_HR_TimeAttendance t3 on t3.fid=t1.ftypeid

where t0.FIsMultiEntry=0 and (t0.FApproveState=0 or t0.FApproveState=1 ) order by t0.fcreatetime;


