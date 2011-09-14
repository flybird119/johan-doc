
$(function(){
	var td=new Date()

	render_widgets($("#id_calculateform"));
	
	$("#id_cometime").val(td.getFullYear()+"-"+N2((td.getMonth()+1))+"-01")
	$("#id_endtime").val(td.getFullYear()+"-"+N2((td.getMonth()+1))+"-"+N2(td.getDate()))
	$.ajax({
	    url:"../../../att/choice_widget_for_select_emp/?multiple=T",
	    type:"POST",
	    dataType:"html",
	    success:function(sdata){
	        $("#show_emp_tree").html(sdata);
        }
    });
	
	$('#calculatetabs').tabs("#calculatetabs > div");
	
	$("#id_checkforget").click(function(event){

		showDialog("../../data/att/CheckExact/_op_/OpAddManyCheckExact/",gettext('补签卡'),380,160,event);
	});
	$("#id_leave").click(function(event){
		showDialog("../../data/att/EmpSpecDay/_op_/OpAddManyUserID/",gettext('补请假'),410,200,event);
	});
	
	$("#id_li_shifts").click(function(event){
		showDialog("../../data/att/USER_OF_RUN/_op_/OpAddUserOfRun/",gettext('新增排班'),870,340,event);
	});
	
	$("#id_tmpshifts").click(function(event){
		showDialog("../../data/att/USER_OF_RUN/_op_/OpAddTempShifts/",gettext('临时排班'),610,355,event);
	});

	//统计
	$("#id_calculate").click(function(){
		var st=new Date($("#id_cometime").val().replace(/-/g,"/"));
		var et=new Date($("#id_endtime").val().replace(/-/g,"/"));
		if(st>et)
		{
			alert(gettext("开始日期不能大于结束日期"));
			return;
		}
		if(et>new Date())
		{
			alert(gettext("结束日期不能大于今天"));
			return;
		}
		if(((et-st)>31*24*60*60*1000)|| (et.getMonth()>st.getMonth() && et.getDate()>=st.getDate()))
		{
			alert(gettext("统计只能当月日期，或者天数不能超过开始日期的月份天数！ "));
			return;			
		}
		
		if(!setPostData())
			return ;
		if( confirm(gettext("统计的时间可能会较长，请耐心等待"))==false)
		{
			return ;
		}
		
		var option={
			url:"../../att/AttReCalc/",			
			type:"POST",
			success:function(data){
				//var tmp=data.split(";")				
				//if( tmp.length>1)
				//	$("#id_ReturnMsg").html("<p>"+tmp[1].substr(8)+"</p>");	
				//alert("OK");
				var typevalue=	parseInt($("#id_current_report").val());
						//$("#caltabs-"+typevalue).click();
						//return;\
						where=""
						//alert(typevalue);
						switch(typevalue)
						{
							case 1:
								where+=""
								AttRecAbnormite(where)
								break;
							case 2:
								DailyReport(where)
							
								break;
							case 3:
								AttShifts(where)
								break;
							case 4:
								AttException(where)
								break;
							case 5:
								CalculateReport(where)
								break;
				            case 6:
				            	OrignalRecord(where)
				            	break;
				            case 7:
				            	CheckForget(where)
				            	break;
							case 8:
								LeaveReport(where)
								break;
							case 9:
								LEReport(where)
								break;
							case 10:
								PunchCardReport(where)
								break;
							default:
								break;
						};
//						$("#id_slide").click();
				
			}
		}
		$("#id_calculateform").ajaxSubmit(option);
	});
	//查询
	$("#id_query").click(function(){
		//alert("ok");
		var where=""
		var typevalue=	parseInt($("#id_current_report").val());
		//$("#caltabs-"+typevalue).click();
		//return;
		switch(typevalue)
		{
			case 1:
				where+=""
				AttRecAbnormite(where)
				break;
			case 2:
				DailyReport(where)
			
				break;
			case 3:
				AttShifts(where)
				break;
			case 4:
				AttException(where)
				break;
			case 5:
				CalculateReport(where)
				break;
            case 6:
            	OrignalRecord(where)
            	break;
            case 7:
            	CheckForget(where)
            	break;
			case 8:
				LeaveReport(where)
				break;
			case 9:
				LEReport(where)
				break
			case 10:
				PunchCardReport(where)
				break
			default:
				break;
		};
	});
	//默认显示第一个报表
	//AttRecAbnormite("");
});
function getquerystring()
{
	var where=[]
		ds=[]
	$("#show_emp_tree").find("input[name='deptIDs']").each(function(){
		ds.push($(this).val());
	})
	var depts=ds.toString();
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	$("input[name='UserIDs']").val(users.toString());
	if(users.length==0)
	{
		$("input[name='DeptIDs']").val(depts);
		$("input[name='UserIDs']").val("");
		if(depts.length>0)
		{
			where.push('UserID__DeptID__in='+depts)
		}		
	}
	else
	{
		$("input[name='DeptIDs']").val("");
		$("input[name='UserIDs']").val(users.toString());
		if(users.length>0)
		{
			where.push('UserID__in='+users)
		}
	}
	st=$("#id_cometime").val();
	et=$("#id_endtime").val();
	det=new Date(et.replace(/-/g,"/"))
	det.setDate(det.getDate()+1)
	ett=det.getFullYear()+"-"+N2(det.getMonth()+1)+"-"+N2(det.getDate())
	switch(parseInt($("#id_current_report").val()))
	{
		case 1:
			where.push('checktime__range=("'+ st +'","'+ ett +'")')
			break;
		case 3:
			where.push('AttDate__range=("'+ st +'","'+ et +'")')
			break;
		case 4:
			where.push('StartTime__gte='+ st )
			where.push('EndTime__lte='+ ett)
			break;
		case 6:
			where.push('TTime__range=("'+ st +'","'+ ett +'")')
			break;
		case 7:
			where.push('CHECKTIME__range=("'+ st +'","'+ ett +'")')
			break;
		default:
			break;
	}
	return where
	//var rid=$("#id_current_report").val()
//	alert(rid);
//	d=$("#subtabs-"+rid).get(0).g.init_query;
//	$("#subtabs-"+rid).get(0).g.init_query=$.zk.concat_query(d,where);
}
function setPostData()	//必须选择人员或部门的验证
{
	ds=[]
	$("#show_emp_tree").find("input[name='deptIDs']").each(function(){
		ds.push($(this).val());
	})
	var depts=ds.toString();		
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	if(depts=="" && users=="")
	{	
		alert(gettext("请选择人员或部门"));
		return false
	}
	$("input[name='UserIDs']").val(users.toString());
	if(users.length==0)
	{
		$("input[name='DeptIDs']").val(depts);
		$("input[name='UserIDs']").val("");
	}
	else
	{
		$("input[name='DeptIDs']").val("");
		$("input[name='UserIDs']").val(users.toString());
	}
	return true
}
//设置报表，操作相关的共用属性
function SetProperty(reportid,app,model,reportname)
{
		//每次点击不同报表时，将清除已经选择的人员列表
		if($("#id_current_report").val()!=reportid);
		{
			
			$("#id_current_report").val(reportid);
			$("#subtabs-"+reportid).empty();
		}
		if(reportid==2 || reportid==5 || reportid==8 || reportid==9)//数据计算模型		
		{
			$("#id_sys_isModelExport").val("false")
		}
		else//数据表模型
		{
			$("#id_sys_isModelExport").val("true")

		}
		if(reportid==2 || reportid==3 || reportid==5 || reportid==8)
		{
			$("#id_attexcept_desc").show();
		}
		else
		{
			$("#id_attexcept_desc").hide();
		}
		$("#id_sys_cur_app").val(app);
   		$("#id_sys_cur_model").val(model);
   		$("#id_sys_cur_grid").val("#subtabs-"+reportid);
   		$("#id_sys_cur_exporttitle").val(reportname);
		
}



function AttRecAbnormite(where)//统计结果详情
{
	
	SetProperty("1",'att','AttRecAbnormite',gettext('统计结果详情'));
	$("#subtabs-1").model_grid(getPubOpt('att','AttRecAbnormite',getquerystring()));
}
function DailyReport(where)//每日考勤统计表
{
	
	if(!setPostData())
		return ;
	$("#id_calculateform").find("input[name='pa']").remove();	
	var url="../../att/DailyCalcReport/"
	var option={
				url:url,	
				dataType:"json",	
				data:"pa=T",	
				type:"POST",
				success:function(data){
				
					SetProperty("2",'list',data.tmp_name,gettext('每日考勤统计表'));
					$("#subtabs-2").grid(getDataOpt(data,url));
					
				}
			}

	load_description();
	$("#id_calculateform").ajaxSubmit(option);
	
}
function load_description()
{
	$.ajax({
					url:"../../att/getallexcept/",
					dataType:"json",
					type:"POST",
					success:function(ret){
						var html=""
						data=ret.data
						for(var i=0;i<data.length;i++)
						{
							var tmp=data[i]
							html+="<span>"+tmp[0]+":<span class='color_orange'>"+ tmp[2] +"( "+tmp[1]+" )</span></span>&nbsp;&nbsp;";
						}
//						alert('load_description:'+html);
						$("#id_attexcept_desc").html(html);
					}
				});
	
}
function AttShifts(where)//考勤明细表
{
	SetProperty("3",'att','AttShifts',gettext('考勤明细表'));
	
	$("#subtabs-3").model_grid(getPubOpt('att','AttShifts',getquerystring()));
	load_description();
}
function AttException(where)//请假明细表
{
	SetProperty("4",'att','AttException',gettext('请假明细表'));

	$("#subtabs-4").model_grid(getPubOpt('att','AttException',getquerystring()));
}
function CalculateReport(where)//考勤统计汇总表
{
	
	if(!setPostData())
		return ;
	$("#id_calculateform").find("input[name='pa']").remove();	
	var url="../../att/CalcReport/"
	var option={
				url:url,	
				dataType:"json",	
				data:"pa=T",	
				type:"POST",
				success:function(data){
					SetProperty("5",'list',data.tmp_name,gettext('考勤统计汇总表'));
					$("#subtabs-5").grid(getDataOpt(data,url));
					
				}
			}
	$("#id_calculateform").ajaxSubmit(option);
	load_description();
}	

function att_abnormal_report(where)//考勤异常表
{
	
	if(!setPostData())
		return ;
	$("#id_calculateform").find("input[name='pa']").remove();	
	var url="../../att/att_abnormal_report/"
	var option={
				url:url,	
				dataType:"json",	
				data:"pa=T",	
				type:"POST",
				success:function(data){
//					alert("return data:"+data);
					SetProperty("10",'list',data.tmp_name,gettext('考勤异常表'));
//					SetProperty("10",'att','AttShifts',gettext('考勤异常表'));
					$("#subtabs-10").grid(getDataOpt(data,url));
					
				}
			}
	$("#id_calculateform").ajaxSubmit(option);
//	load_description();
}

function LEReport(where)//统计每天最早与最晚记录
{
	if(!setPostData())
		return ;
	$("#id_calculateform").find("input[name='pa']").remove();	
	var url="../../att/lereport/"
	var option={
				url:url,	
				dataType:"json",	
				data:"pa=T",	
				type:"POST",
				success:function(data){
					SetProperty("9",'list',data.tmp_name,gettext('统计最早于最晚'));
					$("#subtabs-9").grid(getDataOpt2(data,url));
					
				}
			}
	$("#id_calculateform").ajaxSubmit(option);
	
}	



function OrignalRecord(where)//原始记录表
{
	SetProperty("6",'iclock','Transaction',gettext('原始记录表'));
	
	$("#subtabs-6").model_grid(getPubOpt('iclock','Transaction',getquerystring()));
}	

function CheckForget(where)//补签卡表
{
	SetProperty("7",'att','checkexact',gettext('补签卡表'));
	
	$("#subtabs-7").model_grid(getPubOpt('att','checkexact',getquerystring()));
}	

function LeaveReport(where)//请假汇总表
{


	if(!setPostData())
		return ;
	$("#id_calculateform").find("input[name='pa']").remove();
	var url="../../att/CalcLeaveReport/"
	var option={
				url:url,	
				dataType:"json",		
				data:"pa=T",
				type:"POST",
				success:function(data){
					SetProperty("8",'list',data.tmp_name,gettext('请假汇总表'));
					$("#subtabs-8").grid(getDataOpt(data,url));
						
				}
			}
	$("#id_calculateform").ajaxSubmit(option);
	load_description();
}


getdata=function(opt){
	$.ajax({ 
	   type: "POST",
	   url:opt.url+"?r="+Math.random(),
	   data:opt.data,
	   dataType:"json",
	   success:function(json){
			var gridd=$(opt.ddiv);
			json.multiple_select=null;
			json.on_pager=function(grid,p){
				$.ajax({
					type:"POST",
					url:opt.url+"?p="+p,
					data:opt.data,
					dataType:"json",
					success:function(msg){
						$.extend(grid.g,msg);
						grid.g.reload_data(msg);
					}
				});
			 return false;
			 }; 
			SetProperty("9","list" ,json.tmp_name)
			gridd.grid(json);
			
			
	   }
  })
}

function PunchCardReport(where)
{
	var dt1=$("#id_cometime").val()
	var dt2=$("#id_endtime").val()
	if (dt1=="" || dt2==""){
		alert(gettext("请选择开始日期或结束日期!"));
		return
	}
	if (dt1>dt2){
		alert(gettext("开始日期不能大于结束日期!"));
		return
	}
	var ddt1 = new Date(dt1)
	var ddt2 = new Date(dt2)
    iDays = parseInt(Math.abs(ddt2 - ddt1) / 1000 / 60 / 60 /24) +1
    if (iDays>31){
		alert(gettext("最多只能查询31天的数据!"));
		return
	}
	var depts=$("#show_emp_tree").find("input[name='id_input_department']").val();		
	var users=$("#show_emp_tree").find("div[id^='emp_select_']").get(0).g.get_store_emp();
	
	postdata={"starttime":dt1,"endtime":dt2,"deptids":depts,"empids":users}
	getdata({"url":"../../att/GenerateEmpPunchCard/","ddiv":"#subtabs-9","data":postdata})
	
	
}
	
function getUserId(g)
{
	
	var rid=$("#id_current_report").val();
	var userids=[]
	if(g==undefined)
		return userids
	if(rid==2 || rid==5 ||rid==8 )
	{
		var selected=g.get_selected().indexes
		for(var s=0	;s< selected.length;s++)
		{
			var tmp=g.data[selected[s]][0]			
			userids.push(tmp)
		}		
	}
	else
	{
		var selected=g.get_selected().indexes
		for(var s=0	;s< selected.length;s++)
		{
			var tmp=g.data[selected[s]][1]
//			tmp=tmp.substr(0,tmp.indexOf(" "));
			userids.push(tmp)
		}
	}
	return userids
	
}
function showDialog(url,title,width,height,event)
{
	var advhtml=""
    var userlist=[]
    var sdata={}
	var userid=getUserId($("#calculatetabs").find("#subtabs-"+$("#id_current_report").val()).get(0).g);  //查询结果中选择的人员
	
	if( userid.length<=0)
	{
		alert(gettext('请在查询结果中选择人员！'));
		return;
	}
	//alert(selected.toString());
	//var userid=selected.query_string;
	//userid=userid.replace(/K/g,'UserID');
	var tmp=[]
	for(var i=0;i<userid.length;i++)
	{
		var append=true;
		for(var j=0;j<tmp.length;j++)
		{
			if(tmp[j]==userid[i])
			{
				append=false;
				break;
			}
		}
		if(append)
		{
			tmp.push(userid[i]);
		}
	}
	userid=tmp

	$.ajax({
		type:"GET",
		url:url+"?_lock=1&UserID="+userid.join("&UserID="),
		//async:false,
		success:function(data){
		
			$(data).find("#id_span_title").hide();	
			advhtml=$("<div id='id_list'>"+data+"<div id='id_result_error'></div></div>")

			
			var cancel=function(div){					
				$("#id_list").find("#id_close").click();
			};
			var save_ok=function(){	
				if(!advhtml.find("#id_edit_form").valid())
				{
					return;
				}
				
				var opt={
					type:"POST",
					url:url,
					success:function(data){
						
						//alert(data);					
						if(data=='{ Info:"OK" }')
						{
							$("#id_list").find("#id_close").click();
						}else{
							$("#id_result_error").html("").append($(data).find(".errorlist").eq(0));
						}
					}					
				}		
				advhtml.find("#id_edit_form").ajaxSubmit(opt);		
			};
			//alert($(advhtml).find(".form_help").length);
			advhtml.find(".form_help").remove();
			advhtml.find(".zd_Emp").addClass("displayN");
			advhtml.find("#id_span_title").remove();
			advhtml.find("#objs_for_op").addClass("displayN");
			var d={}
			d["buttons"]={}
			d["buttons"][gettext('确认')]=save_ok;
			d["buttons"][gettext('取消')]=cancel;
			d["title"]=title;
			advhtml.dialog(d);
			
			/*
			//把选择的人员加入到表单中
			
			
			var ud=""
			for(var i=0;i<selected.keys.length;i++)			
			{	
				ud+="<input type='hidden' name='UserID' value='"+ selected.keys[i] +"'>"
			}
			
			var_divreport.find("#id_edit_form").append(ud)
			*/

			
		}
	});    	
	
	return;
}
function N2(nc)
{
	var tt= "00"  +nc.toString()
   
    tt=tt.toString();
    return tt.substr(tt.length-2);
}   
