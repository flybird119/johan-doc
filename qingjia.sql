-- ������뵥
select t2.Fname_L2 ����, t1.FBeginTime ��ʼʱ��, t1.FEndTime ����ʱ��,t1.freason ���ԭ��,t0.fcreatetime ����ʱ��,t3.fname_l2 ������
from T_HR_LeaveBill t0
inner join T_HR_LeaveBillEntry t1 on t1.fbillid=t0.fid
inner join T_BD_Person t2 on t2.fid=t1.fpersonid

left join T_HR_TimeAttendance t3 on t3.fid=t1.ftypeid

where t0.FIsMultiEntry=0 and t0.FApproveState and t0.fcreatetime>TO_DATE('2011-8-1 00:00:00','YYYY-MM-DD HH24:MI:SS') order by t0.fcreatetime;

select * from T_HR_TimeAttendance


-- ������뵥
select t2.Fname_L2 ����, t1.FBeginTime ��ʼʱ��, t1.FEndTime ����ʱ��,t1.freason
 ���ԭ��,t0.fcreatetime ����ʱ��
from T_HR_LeaveBill t0
inner join T_HR_LeaveBillEntry t1 on t1.fbillid=t0.fid
inner join T_BD_Person t2 on t2.fid=t1.fpersonid
where t0.FIsMultiEntry=0 and t0.fcreatetime>TO_DATE('2011-8-1 00:00:00','YYYY-MM
-DD HH24:MI:SS') order by t0.fcreatetime;


select t2.Fname_L2 ����, t1.FBeginTime ��ʼʱ��, t1.FEndTime ����ʱ��,t1.freason ���ԭ��,t0.fcreatetime ����ʱ�� from T_HR_LeaveBill t0 inner join T_HR_LeaveBillEntry t1 on t1.fbillid=t0.fid inner join T_BD_Person t2 on t2.fid=t1.fpersonid where t0.FIsMultiEntry=0 and t0.fcreatetime>TO_DATE('2011-8-1 00:00:00','YYYY-MM-DD HH24:MI:SS') order by t0.fcreatetime;
