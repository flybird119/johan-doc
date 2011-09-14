
#class AttUserOfRun(AppOperation):
#        u'''模型1'''
#        from mysite.att.models import USER_OF_RUN,USER_TEMP_SCH
#        verbose_name=_(u'模型1')
#        view=funAttUerOfRun
#        _app_menu="att"
#        _menu_index=3
#        _disabled_perms=["clear_user_of_run","change_user_of_run","delete_user_of_run","add_user_of_run","dataimport_user_of_run","change_user_temp_sch","add_user_temp_sch","delete_user_temp_sch","dataimport_user_temp_sch","clear_user_temp_sch"]#不要在权限列表里面显示的权限
#        add_model_permission=[USER_OF_RUN,USER_TEMP_SCH]
#        _select_related_perms={"can_AttUserOfRun":"browse_user_of_run.browse_user_temp_sch"}#点击can_RTMonitorPage菜单时默认选中can_MonitorAllPage中的权限,例如{"sourseperm":"perm1.perm2.perm3"}
#        _hide_perms = ["browse_user_of_run","browse_user_temp_sch"]