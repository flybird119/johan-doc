# coding=utf-8
'''
定义的模型Admin类成员的几个自定义配置项
'''
CACHE_EXPIRE = 300

class ModelAdmin:
    search_fields=()    # 搜索字段
    list_filter=()          # 过滤字段
    list_display=()      # 列表显示字段
    cache=CACHE_EXPIRE  # 缓存超时时间
    log=True             # 是否日志记录
    visible=True        # 是否显示
    menu_index=9999 # 菜单排序号
    read_only=False  # 是否只读    只读时除了"导出"其他操作都不会显示

#    app_menu='base'
#    menu_group = 'base'