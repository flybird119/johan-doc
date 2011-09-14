function search_and_load(js)
{
	var scripts = document.getElementsByTagName('script');
		for (var i=0; i<scripts.length; i++) {
				var idx = scripts[i].src.indexOf('jslib/'+js);
				if(idx>0) return i;
			}
	document.write("<script src='/media/jslib/"+js+"'>");
	return -1;
}
function formatNum(num){
    if(num<10)
		return "0"+parseInt(num)
	else{
		return num
	}
}

function setDate($input,tmp_date){
		var dSplit=$.trim($input.val());
		if(dSplit.indexOf(":")==-1){
		    dSplit="";
		}else{
			dSplit=dSplit.substring(dSplit.indexOf(":")-2,dSplit.length);
		}
		var strDate=tmp_date;
		$input.val(strDate+" "+dSplit);
}

function getToday(varH){
	var d = new Date();
	var $input=$(varH).parent().parent().find("input");
	var strToday=d.getUTCFullYear()+"-"+formatNum(d.getMonth()+1)+"-"+formatNum(d.getDate());
	setDate($input,strToday);
}

function setTime($input,tmp_time){
	var dSplit=$.trim($input.val());
	if(dSplit.indexOf("-")==-1){
		dSplit="";
	}else{
		 dSplit=$.trim(dSplit.split(" ")[0]);
	}	
	var strNow=tmp_time;
	$input.val(dSplit+" "+strNow+":00");
}

function getNow(varH){
    var d = new Date();
	var $input=$(varH).parent().parent().find("input");
	var strNow=formatNum(d.getHours())+":"+formatNum(d.getMinutes())+":"+formatNum(d.getSeconds());
	setTime($input,strNow);
}

function setDataPostion(){
	$("#id_tmp_form label").each(function(){
		var var_field_id=$(this).attr("for");
		$(":[pos='"+var_field_id+"']").eq(0).html($(this).parent().next().eq(0).html());
	});
	$("#id_tmp_form").parent().parent("tr").remove();
}
function render_widgets($render_form)
{
	var months=gettext('January February March April May June July August September October November December').split(' ');
	var days=gettext('S M T W T F S').split(' ');
	var varInputValue="";
	if($render_form.find("input.wZBaseDateTimeField").length!=0){
			$.each($render_form.find("input.wZBaseDateTimeField"),function(index,elem){
				$(elem).datePicker({
					startDate:"1900-01-01",
					endDate :"2999-01-01",
					datetime:true
//					showOn: 'button', buttonImage: '/media/img/icon_calendar.gif', 
//					buttonImageOnly: true,
//					changeYear:true,
//					changeMonth:true,
//					dateFormat:'yy-mm-dd',
//					beforeShow:function(){
//						varInputValue=$(this).val();
//					},
//					onClose:function(){
//						var varTmpValue=$(this).val();
//						$(this).val(varInputValue);
//						setDate($(this),varTmpValue);
//					}
				});
			});
			var w_datetimes=$render_form.find("input.wZBaseDateTimeField");
			$.each(w_datetimes,function(index, elem){
				var this_parent=$(elem).parent();
				this_parent
				.find("span.pop_cal a#calendarlink")
				.replaceWith(this_parent.find("a.dp-choose-date"));
				this_parent
				.find("span.pop_time a#clocklink img")
				.clockpick({
					starthour : 0,
					endhour : 23,
					useBgiframe:true,
					military:true,
					minutedivisions: 12			
					},function(args){
						setTime($(elem),args);
				});
			});
	}

	if($render_form.find("input.wZBaseDateField").length!=0){
		$("input.wZBaseDateField").datePicker({ 
			startDate:"1900-01-01",
			endDate :"2999-01-01"
//			showOn: 'button', buttonImage: '/media/img/icon_calendar.gif', 
//			buttonImageOnly: true,			
//			changeYear: true, 
//			changeMonth: true, 
//			monthNames: months,
//			monthNamesShort: months,
//			dayNamesMin: days,
//			dayNamesShort: days,
//			dateFormat:'yy-mm-dd'
		});
	}
	
	if($render_form.find("input.wZBaseTimeField").length!=0){
		$("input.wZBaseTimeField").parent().find("span a#clocklink img").clockpick({
			starthour : 0,
			endhour : 23,
			minutedivisions: 30,
			useBgiframe:true,
			military:true
			//layout:'horizontal'
		},function(args){
			$(this).parent().parent().parent().find("input").val(args+":00");
		});
	}
	
	//构造标签页
	if($("#id_tabs ul").length==0){
		$("#id_tabs").remove();
	}else{
			$('#id_tabs').tabs("#id_tabs > div");
			$("#id_tabs").find("tr:[title]").each(function(){
					var var_title=$(this).attr("title");
					$(this).after($("label:[for^="+var_title+"]").parent().parent());
					$(this).remove();
			});
	}
	var tooltip_opt={
		// place tooltip on the right edge
		position: "center right",
		// a little tweaking of the position
		offset: [-2, 10], 
		// custom opacity setting
		opacity: 0.7,
		// use this single tooltip element
		tip: '#error_tooltip',
		events: { 
		       input: 'mouseover click focus, blur mouseout',
		       checkbox: 'mouseover click, mouseout' 
		}
		}

	var err_in=$("td:has(.errorlist) input");
	err_in.each(function(){
		var tip_text=$(this).parent().find("ul").text();
		$(this).addClass("error");
		tooltip_opt["onBeforeShow"]=function(){ $("#error_tooltip").html(tip_text); }
		$(this).tooltip(tooltip_opt);
		$(".errorlist", $(this).parent()).remove();
	});
	if(err_in.length>0)
		err_in[0].focus();

	$("#id_edit_form,#id_action_form").add($render_form.find("form")).validate({
		errorPlacement: function(error, element) {
			element[0].error_text=error.text()
			tooltip_opt["onBeforeShow"]=function(){
				$("#error_tooltip").html(element[0].error_text);
			}
			element.tooltip(tooltip_opt);
			}
		});
}

function wgCheckNo(field,divname,container,dbapp_url,app_lable,model)
{
	dbapp_url="/"
	var url=dbapp_url+"checkno/"+app_lable+"/"+model+"/?"+field+"__exact=";
	tt="input#id_"+field
	var v=$(container).parent().parent().parent().find(tt).val();
	
	if (v=="")
		return;
	url+=v;
	var div= $(container).parent().parent().parent().find("#"+divname);
	
	
	
	$.ajax({
		type:"POST",
		url:encodeURI(url),
		success:function(msg){
			div.html(msg);
		}
	});
}
