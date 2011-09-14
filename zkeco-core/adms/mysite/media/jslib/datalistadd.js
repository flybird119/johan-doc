$(function(){
    var app=$("#id_sys_cur_app").val();
    var model=$("#id_sys_cur_model").val();
    var dbapp_url=$("#id_sys_cur_appurl").val();
    var isModelExport=$("#id_sys_isModelExport").val();
    
    
    if(model=="Employee" || model=="Department")
    {
    	$("#id_li_import").removeClass("displayN");
    }

	//添加高级查询事件
    $("#id_advanced_search").click(function(event){
    		var app=$("#id_sys_cur_app").val();
		    var model=$("#id_sys_cur_model").val();
		    var dbapp_url=$("#id_sys_cur_appurl").val();
		    var cur_grid=$($("#id_sys_cur_grid").val());
		    var isModelExport=$("#id_sys_isModelExport").val();
            var advhtml=""
            if(isModelExport=="false")
            {
            	alert(gettext('该模型不支持高级查询功能'));
            	return ;
            }
            $.ajax({
                    type:"POST",
                    dataType:"html",
                    async:false,
                    url:dbapp_url+app+"/"+model+"/query/show",
                    success:function(data){
                    		advhtml=data;
                    		var var_advance=$("<div id='id_div_advance_search' title='"+gettext('高级查询')+"'>"+advhtml+"</div>");
							var_advance.hide();
                    		$(document.body).append(var_advance);							
                    		var_advance.find("#btnConfirm").click(function(){
                                    var tt=Confirm()
                                    if(tt.length>0)
                                    {
                                        cur_grid.get(0).g.init_query=tt;
                                        cur_grid.get(0).g.load_data();
                                        $("#id_close").click();
                                    }
				            });
				            var_advance.find("#btnReturn").click(function(){
				            		
				            		$("#id_close").click();
				            });   
                            
				            var_advance.find("#txtValue").keydown(function(event){
				                    if(event.keyCode==13)
				                    {
                                            alert("OK");
				                            ValueAdd();
                                            return false;
				                    }
				            });         
				            var_advance.show();
				            var_advance.dialog({title:gettext('高级查询')});
                    }
            });
    });
     
    $("#id_model_import").click(function(){
    		var app=$("#id_sys_cur_app").val();
		    var model=$("#id_sys_cur_model").val();
		    var dbapp_url=$("#id_sys_cur_appurl").val();
		    var isModelExport=$("#id_sys_isModelExport").val();
            var imphtml=""
            $.ajax({
                    type:"POST",
                    dataType:"html",                    
                    url:dbapp_url+app+"/"+model+"/import/show_import",
                    success:function(data){
                            imphtml=data;
                            var div_import=$("<div id='id_import_dialog' title='"+gettext('导入')+"'>"+imphtml+"</div>")
                            $(document.body).append(div_import);
				            div_import.find("#btnUpload").click(function(){								
								$("#showlist").css({width:$("#showlist").width()+"px"});
				                if(div_import.find("#txtfilename").val()=='')
				                {
				                    alert(gettext("请选择一个上传的文件!"));
				                    return;
				                }
				                var hl=div_import.find("[name='headerln']").val();
				                if(!CheckNumber(hl))
				                {
				                    alert(gettext('标题行号必须是数字!'));
				                    div_import.find("[name='headerln']").focus();
				                    return ;
				                };
				                var rl=div_import.find("[name='recordln']").val();
				                if(!CheckNumber(rl))
				                {
				                    alert(gettext('记录行号必须是数字!'));
				                    div_import.find("[name='recordln']").focus();
				                    return ;
				                };
				                var rbtf=""
				                div_import.find("[name='filetype']").each(function(){
				                        if($(this).attr("checked"))
				                        {
				                            rbtf=$(this);
				                        }
				                });
				                var ft=$(rbtf).val()
				                var fnft=div_import.find("#txtfilename").val();
				                fnft=fnft.substr(fnft.lastIndexOf(".")+1);
				                if(ft=='xls' && fnft!='xls')
				                {
				                   alert(gettext("请选择xls文件!"));
				                    return;
				                }
				                else
				                {
				                    if( ft=='txt' && fnft!='txt' && fnft!='csv')
				                    {
				                        alert(gettext("请选择csv文件或者txt文件!"));
				                        return;
				                       
				                    };
				                };
				                var opt={
				                    url:dbapp_url+"import/get_import",
				                    type:"POST",
                                    async:false,
				                    dataType:"html",
				                    error:function(XMLHttpRequest, textStatus, errorThrown){
				                                alert(textStatus); 
				                            },
				                    success:function(data){
				                            //jqery ajax提交文件后，再次获取服务器json信息时，会返回错误，
				                            //会在json数据前加上"<pre></pre>"标签，因此需要过漏此标签
                                            //alert(data);
				                        if(data.indexOf('<pre>') != -1) {
				                            data = data.substring(5, data.length-6);
				                          }
				                        eval("data=" + data);
				                           
				                        div_import.find("[name='txttablename']").attr("value",data.tablename);
				                        div_import.find("[name='txtfilename']").attr("value",data.filename);
				                        div_import.find("[name='txtfiletype']").attr("value",data.filetype);
				                       
				                        div_import.find("[name='sparatorvalue']").attr("value",data.sparatorvalue);
				                        div_import.find("[name='headln']").attr("value",data.headln);
				                        div_import.find("[name='recordln']").attr("value",data.recordln);
				                       
				                        div_import.find("[name='unicode']").attr("value",data.unicode);
				                       
				                        //标头checkbox
				                        var htmlchk="<tr><td></td>"
				                        var header="<tr><td >"+gettext('文件标头')+"</td>"
				                        var record="<tr><td>"+gettext('文件记录')+"</td>"
				                        var cmbfields="<tr ><td >"+gettext('表字段')+"</td>";
				                        for( i=0;i<data.recorddata.length;i++)
				                        {
				                            htmlchk+="<td><input type='checkbox' name='_chk_"+ i +"' class='fieldschk' checked='checked' /></td>";
				                            if (data.headdata.length>0)
				                            {   
				                                header+="<td >"+data.headdata[i]+"</td>";
				                            }
				                            else
				                            {
				                                   header+="<td></td>";
				                            };
				                            record+="<td>"+data.recorddata[i]+"</td>";
				                            cmbfields+="<td><select name='_select_"+ i +"'>";
				                           
				                            for( fld=0;fld< data.fields.length;fld++)
				                            {
				                                if(fld==i)
				                                {
				                                    cmbfields+="<option value='"+data.fields[fld]+"' selected>"+data.fieldsdesc[fld]+"</option>";
				                                }
				                                else
				                                {
				                                    cmbfields+="<option value='"+data.fields[fld]+"'>"+data.fieldsdesc[fld]+"</option>";
				                                };
				           
				                            };
				                            cmbfields+="</select></td>";
				                        };
				                        htmlchk+="</tr>"
				                        header+="</tr>"
				                        record+="</tr>"
				                        cmbfields+="</tr>"
				                        $(div_import.find(".bc")[0]).empty();
				                        $(div_import.find(".bc")[0]).append(htmlchk);
				                        $(div_import.find(".bc")[0]).append(header);
				                        $(div_import.find(".bc")[0]).append(record);
				                        $(div_import.find(".bc")[0]).append(cmbfields);
				                        div_import.find("#tddatalist").attr("visibility","visible")
				                        div_import.find("#divdatalist").attr("visibility","visible")
				                      }
				                    }
				                div_import.find("form[name='txtfileform']").ajaxSubmit(opt);
				                   
				            });
				            div_import.find("#txtfilename").change(function(){
				             
				              var fnft=div_import.find("#txtfilename").val();
				              fnft=fnft.substr(fnft.lastIndexOf(".")+1);
				              div_import.find("[name='filetype']").each(function(){
				                      if(fnft=='csv' && $(this).val()=='txt')
				                        {
				                            $(this).attr("checked",true);
				                        };
				                      if($(this).val()==fnft)
				                      {
				                          $(this).attr("checked",true);
				                      };
				              });
				               
				           
				            });
				            //导入按钮
				            div_import.find("#btnImport").click(function(){
			                    if(div_import.find("[name='txtfilename']").attr("value")=="")
			                    {
			                            alert(gettext("请先上传文件！"));
			                            return;
			                    }
				                var opt={
				                    url:dbapp_url+"import/file_import",
				                    type:"POST",
				                    success:function(data){
				                        alert(data);
                                        window.location.reload();
				                    }
				                };
				                div_import.find("#fileimport").ajaxSubmit(opt);
				                $("#id_close").click();    
				            });
				            div_import.find("#btnReturn").click(function(){
				                   $("#id_close").click();                            
				            });
				           div_import.dialog({title:gettext('导入')});
                    }
            });

    });

    //导出
    $("#id_model_export").click(function(){
    		var app=$("#id_sys_cur_app").val();
		    var model=$("#id_sys_cur_model").val();
		    var dbapp_url=$("#id_sys_cur_appurl").val();
		    var cur_grid=$($("#id_sys_cur_grid").val());
		    var reportname=$("#id_sys_cur_exporttitle").val();
		    var isModelExport=$("#id_sys_isModelExport").val();
            
            var exphtml=""
            var df=$($("#id_sys_cur_grid").val()).get(0).g.disable_cols;
            var af=$($("#id_sys_cur_grid").val()).get(0).g.fields_store;                              	
          
            var rt=""
            //alert(df)
            //alert(af)
            var lf=[]
            for(var i=0;i<af.length;i++)
            {
                var add=true
                var n=""
                for(var j=0;j<df.length;j++)
                {
                   
                   // if(af[i].split("|")[0]==df[j].split("|")[0] )
                    if(af[i]==df[j] )
                    {
                        add=false
                        break;
                    }
                    
                }
                if(add)
                {
                    lf.push(af[i].split("|")[0]);
                }
            }
            
            $("#id_sys_cur_exportfields").val(lf.toString());
            //alert(lf);
            $.ajax({
                    type:"POST",
                    dataType:"html",
                    data:"reportname="+  reportname    ,           
                    url:dbapp_url+app+"/"+model+"/export/show_export",
                    success:function(data){
                            exphtml=data;
                            var div_export=$("<div id='id_export_dialog' title='"+gettext('导出')+"'>"+exphtml+"</div>");
                            $(document.body).append(div_export);
				            //div_export.find("input [name='txtviewname']").attr("value",gridDiv.find("#cmbviewname").attr("value"));
				            //div_export.find("#exportform").attr("action",dbapp_url+self.gOptions.uOptions.app_label+'/'+self.gOptions.uOptions.model+'/export/file_export')
                            if (app=='list')
                                 {
                                     div_export.find("#id_li_records").addClass("displayN");
                                 }
				           			           
				           	div_export.find("#btnReturn").click(function(){
				                  	$("#id_close").click();                       
				            });
				            div_export.find("#btnExport").click(function(){				            	
				            	var url=""		
				                url="/api/"+ app +"/"+model+"/"   ;
				                if(app!="list")
				                {
					                if( cur_grid.get(0).g.init_query.length>0)
					                {
					                	var iq=cur_grid.get(0).g.init_query
					                	for(var i=0;i<iq.length;i++)
					                	{
					                		tmp=iq[i].split("=");
					                		$("#exportform").append("<input type='hidden' name='"+tmp[0]+"' value='"+tmp[1]+"' \>")
					                	}
					                }
				                }
				                //导出方式
                                
                                div_export.find("input[name='t']").each(function(){
                                    if($(this).attr("checked"))
                                    {
                                        rt=$(this).val();
                                    }
                                });
                                if(rt=="1")//全部导出
                                {
                                    div_export.find("#exportform").append("<input type='hidden' value='True' name='all' \>");
                                }
                                if(rt=="2")//页导出
                                {
                                    var l=div_export.find("#pagerecords").val();
                                    if(!CheckNumber(l))
                                    {
                                        alert(gettext('页记录数只能为数字'));
                                        div_export.find("#pagerecords").focus();
                                        return false;
                                    }
                                    var p1=div_export.find("#pagestart").val()
                                    var p2=div_export.find("#pageend").val()
                                    if(!CheckNumber(p1))
                                    {
                                        alert(gettext('页码只能为数字'));
                                        div_export.find("#pagestart").focus();
                                        return false;
                                    }
                                    if(!CheckNumber(p2))
                                    {
                                        alert(gettext('页码只能为数字'));
                                        div_export.find("#pageend").focus();
                                        return false;
                                    }

                                    div_export.find("#exportform").append("<input type='hidden' value='"+l+"' name='l' \>");
                                    div_export.find("#exportform").append("<input type='hidden' value='"+p1+"' name='p1' \>");
                                    div_export.find("#exportform").append("<input type='hidden' value='"+p2+"' name='p2' \>");
                                }
                                if(rt=="3")//记录导出
                                {
                                    var s1=div_export.find("#recordstart").val()
                                    var s2=div_export.find("#recordend").val()
                                    if(!CheckNumber(s1))
                                    {
                                        alert(gettext('记录数只能为数字'));
                                        div_export.find("#recordstart").focus();
                                        return false;
                                    }
                                    if(!CheckNumber(s2))
                                    {
                                        alert(gettext('记录数只能为数字'));
                                        div_export.find("#recordend").focus();
                                        return false;
                                     
                                    }
                                    if(parseInt(s2)>10000)
                                    {
                                         alert(gettext('记录条数不能超过10000'));
                                         div_export.find("#recordend").focus();
                                         return false;
                                         
                                    }
                                    if(parseInt(s2)<=0)
                                    {
                                         alert(gettext('请输入大于0的数字'));
                                         div_export.find("#recordend").focus();
                                         return false;
                                         
                                    }
                                    
                                    div_export.find("#exportform").append("<input type='hidden' value='"+s1+"' name='s1' \>");
                                    div_export.find("#exportform").append("<input type='hidden' value='"+s2+"' name='s2' \>");
                                }
				                div_export.find("#exportform").attr("action",url);
								if(reportname!="")
								{
									$("#exportform").append("<input type='hidden' name='reportname' value='"+reportname+"'\>");
								}
                              
                               	
                                                            
                               
                                var exportfields=$("#id_sys_cur_exportfields").val();
                                if(exportfields!="")
                                {
                                	$("#exportform").append("<input type='hidden' name='fields' value='"+exportfields+"'\>");
                                }
                                $("#exportform").append("<input type='hidden' name='o' value='pk'\>");
				                $("#exportform").ajaxSubmit();
				            });				            
				            div_export.dialog({title:gettext('导出')});
                    }
            });

    });

});
function search_init($search,$grid){
	//头输入信息清除
    var $div=$search;
    $div.find("input:first").focus();
    $div.find("input").keydown(function(event){//按回车键直接查询
    
        if(event.keyCode==13)
        {
           $div.find("#id_header_search").click();
        }
        
    });
	$div.find("input,select").each(function(){
		var id=$(this).attr("id");
        var p=$(this).attr("name")
		$(this).attr("id","search_"+id)
        $(this).attr("name","");
        $(this).attr("fieldname",p)
        switch($(this).attr("type"))
         {
                 case 'text','textarea':
                         $(this).attr("value","");
                         break;
                 case 'checkbox','radio':
                         $(this).attr("checked",false);
                         break; 
                 case 'select-one':
                        var blncontain=false                        
                        $(this).find("option").each(function(){
                            var tmp=$(this).text();                            
                            if(tmp.indexOf("---")>=0)
                            {
                                blncontain=true;
                            }
                        });
                        
                        if(!blncontain)
                        {
                            $(this).prepend("<option selected='selected' value=''>---------</option>");
                        }
                 default:
                         $(this).attr("value","");
                         break;
         };
        
	});
    
	$div.find("#id_header_clear").click(function(){
			 $div.find("input,select").each(function(){
					 switch($(this).attr("type"))
					 {
							 case 'text','textarea':
									 $(this).attr("value","");
									 break;
							 case 'checkbox','radio':
									 $(this).attr("checked",false);
									 break;                                 
							 default:
									 $(this).attr("value","");
									 break;
					 };
			 });
             $div.find("#id_header_search").click();
	 });
	 //头信息查找
	 $div.find("#id_header_search").click(function(){
           var bln_submit=true

			 var strwhere=[];
            
			 $div.find("input,select").each(function(){
					 switch($(this).attr("type"))
					 {
							 case 'text':
									 if($.trim($(this).attr("value"))!="")
									 {
                                        if( $(this).hasClass("wZBaseDateField") || $(this).hasClass("wZBaseDateTimeField") || $(this).hasClass("wZBaseTimeField"))
                                        {
                                            
                                            if($(this).hasClass("wZBaseDateTimeField"))
                                            {
                                                var t=$(this).val()
                                                if(!(t.indexOf("-")>0 && t.indexOf(":")>0))
                                                {
                                                    $(this).addClass("error");
                                                    bln_submit=false;
                                                    return false;
                                                }
                                                else
                                                {
                                                    $(this).removeClass("error");
                                                }
                                            }
                                            strwhere.push($(this).attr("fieldname")+"__exact="+$(this).attr("value")) ;
                                        }
                                        else
                                        {
                                            
                                            strwhere.push($(this).attr("fieldname")+"__contains="+$(this).attr("value")) ;
                                        }
									 }
                                     else
                                     {
                                        $(this).removeClass("error");
                                     }
									 break;
							 case 'checkbox':
									 strwhere.push($(this).attr("fieldname")+"__contains="+$(this).attr("checked"));
									 break;                                 
							 case 'select-one':
								if($(this).val()!="")
								{
									strwhere.push($(this).attr("fieldname")+"__exact="+$(this).val());
								}
								break;   
							 
							 default:                                               
									 break;
					 };
			 });
            if( !bln_submit)
            {
                return;
            }
			
			 var datalist=$grid.get(0);
			 datalist.g.init_query=strwhere;
			 datalist.g.load_data();
			
			 //可自定义查询结束后需要的操作
			 if(typeof(after_query)!= "undefined")
			 {
				if(!after_query()){
					return;
				};
			 }
			 
	 });
	/*
    if($filter){
        $filter.find("#id_filterbar").find("span>select").change(function(event){
            var query=$(this).val();
            var g=$grid.get(0).g;
            var v=query;
            if(v.substring(0,11)=="javascript:")
            {
                $(this).attr("rel", $grid.selector);
                g.init_query=eval(v.substr(11));
                return;
            }
            else
            {
                var query=v.substring(1);
                if(query.length==0){
                    var id=$(this).attr("id").substring(4);
                    g.init_query=$.zk.concat_query(g.init_query,[id+"__exact=*"]);
                }else{
                    g.init_query=$.zk.concat_query(g.init_query,[query]);
                }
            }
            g.load_data();
        });
    }*/
	
};



function CheckNumber(number)
{
    if(number!="")
    {
        var r,re;
        re = /\d*/i; //\d表示数字,*表示匹配多个数字
        r = number.match(re);
        if(r==number)
        {
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        return false;
    };
};

function popup_color_picker(obj)
{
    var div=$("<div id='id_color_container'></div>");
    var tbl=[]
    var line=0
    tbl.push("<table><tr>")
    for(var r=0;r<=255;)
    {
        for(var g=0 ;g<=255;)
        {
            for(var b=0;b<=255;)
            {
                tbl.push("<td width=10px height=10px value='' onclick='javascript:RgbToInt("+r+","+g+","+b+")' bgcolor=rgb("+r+","+g+","+b+")></td>");
                line+=1;
                if(line%25==0)
                {
                    
                    tbl.push("</tr>");
                    tbl.push("<tr>");
                }
                b+=51
            }
            g+=51
        }
        r+=51
    }
    tbl.push("</tr></table>")
    $(div).append(tbl.join("\n"));
    div.find("td").click(function(){
        alert($(this).attr("value"));
    });
    if($("#id_color_container").length==0)
        $(document.body).append($(div));
    div.show();
    
    
}
function RgbToInt(r,g,b)
{
    var colorvalue=0
    colorvalue=r+g*256+b*256*256
    return colorvalue
}
function CheckNumber(number)
{
    if(number!="")
    {
        var r,re;
        re = /\d*/i; //\d表示数字,*表示匹配多个数字
        r = number.match(re);
        if(r==number)
        {
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        return false;
    };
};

function init_log($click_button,title){
    $click_button.click(function(event){
        var href=$(this).attr("ref");
          var query=$(this).attr("query");
          var t_search_fields=
              [
                  title,
                  '<td><label class="" for="id_user__username">'+gettext("用户名")+'</label></td>'
                  +'<td><input type="text" maxlength="30" name="" id="search_id_user__username" fieldname="user__username"></td>'
                  +'<td><label class="" for="id_action_flag">'+gettext("动作标志")+'</label></td>'
                  +'<td><select id="search_id_action_flag" name="" fieldname="action_flag">'
                          +'<option selected="selected" value="">---------</option>'
                          +'<option value="1"> '+gettext("增加")+'</option>'
                          +'<option value="2">'+gettext("修改")+'</option>'
                          +'<option value="3">'+gettext("删除")+'</option>'
                          +'<option value="4">'+gettext("其他")+'</option>'
                      +'</select>'
                  +'</td>'
                  ];
          var d=new Date();
          if(href.indexOf("?")==-1){
              href=href+"?stamp="+d.getTime();
          }else{
              href=href+"&stamp="+d.getTime();
          }
          
        $.ajax({
            type:"GET",
            dataType:"html",
            async:false,
            url:href,
            success:function(msg){
                if($("#id_opt_message").length==0){
                    $("body").append("<div id='id_opt_message' style='overflow:hidden'></div>");
                }
                var $msg_dialog=$("#id_opt_message");
                $msg_dialog.css("visibility","hidden");
                $msg_dialog.html(msg);
                $("#id_title",$msg_dialog).html(t_search_fields[0]);
                $("#id_form_search tr",$msg_dialog).prepend(t_search_fields[1]);
                  $("#id_form_search tr",$msg_dialog).find("input").keydown(function(event){//按回车键直接查询
                      if(event.keyCode==13)
                      {
                         $msg_dialog.find("#id_header_search").click();
                      }
                  });
                  var g=$msg_dialog.find("#id_datalist").get(0).g;
                  $msg_dialog.dialog();
                  $msg_dialog.width(600);
                  g.base_query=[query];
                  g.load_data();
                  $msg_dialog.css("visibility","visible");
            },
            error:function(one,two,three){
                alert(gettext("服务器加载数据失败,请重试!"));
            }
        });
        return false;
    });


}