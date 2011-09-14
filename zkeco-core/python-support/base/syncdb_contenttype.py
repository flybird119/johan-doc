# coding=utf-8
'''
提供了对 models 和 ContentType 的同步的维护
'''
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_apps, get_models, signals
from django.utils.encoding import smart_unicode

def update_contenttypes(app, created_models, verbosity=2, **kwargs):
    """
    Creates content types for models in the given app, removing any model
    entries that no longer have a matching model class.
    """
#    print u"johan-----------------------------: 更新contenttypes 表"
    ContentType.objects.clear_cache()
    content_types = list(ContentType.objects.filter(app_label=app.__name__.split('.')[-2])) # 得到app中的所有ContentType
    app_models = get_models(app)    # api 应用例子
    if not app_models:
        return
    for klass in app_models:    #-----------------------遍历 app 所有 model        添加新模型对应的 ContentType
        opts = klass._meta
        try:
            ct = ContentType.objects.get(app_label=opts.app_label,
                                         model=opts.object_name.lower())
            content_types.remove(ct)
        except ContentType.DoesNotExist:
            ct = ContentType(name=u"%s"%opts.verbose_name,
                app_label=opts.app_label, model=opts.object_name.lower())
            ct.save()
            if verbosity >= 2:  # ------------------------是否显示运行信息
                print "Adding content type '%s | %s'......" % (ct.app_label, ct.model)
    # The presence of any remaining content types means the supplied app has an
    # undefined model. Confirm that the content type is stale before deletion.
    if content_types:   # ------------------------------去除已被删除model 对应的 content_type
        if kwargs.get('interactive', False):
            content_type_display = '\n'.join(['    %s | %s' % (ct.app_label, ct.model) for ct in content_types])
            ok_to_delete = raw_input("""The following content types are stale and need to be deleted:

%s

Any objects related to these content types by a foreign key will also
be deleted. Are you sure you want to delete these content types?
If you're unsure, answer 'no'.

    Type 'yes' to continue, or 'no' to cancel: """ % content_type_display)
        else:
            ok_to_delete = False

        if ok_to_delete == 'yes':
            for ct in content_types:
                if verbosity >= 2:
                    print "Deleting stale content type '%s | %s'......" % (ct.app_label, ct.model)
                ct.delete()
        else:
            if verbosity >= 2:
                print "Stale content types remain......"

def update_all_contenttypes(verbosity=2, **kwargs):
    for app in get_apps():  # 遍历 apps
        update_contenttypes(app, None, verbosity, **kwargs)


if __name__ == "__main__":
    update_all_contenttypes()
