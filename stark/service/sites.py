from django.conf.urls import url
from django.shortcuts import redirect, render
from django.db.models.fields.related import ManyToManyField
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from stark.utils.page import MyPage
from django.db.models import Q
import copy

class ShowList(object):

    def __init__(self, config_obj, data_list, request):
        self.config_obj = config_obj
        self.request = request
        self.data_list = data_list

        self.pagination = MyPage(request.GET.get("page", 1), self.data_list.count(), request, per_page_data=5)
        self.page_queryset = self.data_list[self.pagination.start:self.pagination.end]

    def get_new_actions(self):
        tmp = []
        tmp.extend(self.config_obj.actions)
        tmp.append(self.config_obj.patch_delete)

        new_actions = []
        for func in tmp:
            new_actions.append({
                "text": func.desc,
                "name": func.__name__
            })
        return new_actions

    def get_headers(self):
        header_list = []  # 表头
        for field_or_func in self.config_obj.new_list_display():
            if callable(field_or_func):
                val = field_or_func(self.config_obj, is_header=True)
            else:
                if field_or_func == "__str__":
                    val = self.config_obj.model._meta.model_name
                else:
                    field_obj = self.config_obj.model._meta.get_field(field_or_func)
                    '''  field_obj=
                app01.Book.title  app01.Book.price  app01.Book.publish app01.Book.authors
                    '''
                    val = field_obj.verbose_name
            header_list.append(val)
        return header_list

    def get_body(self):
        new_data_list = []  # 表单
        for obj in self.page_queryset:  # 每个book的QuerySet <Book: 呵呵>, <Book: 哈哈>, <Book: 嘻嘻>
            tmp = []
            for field_or_func in self.config_obj.new_list_display():
                if callable(field_or_func):  # 检查是否可调用
                    val = field_or_func(self.config_obj, obj)
                else:
                    try:
                        field_obj = self.config_obj.model._meta.get_field(field_or_func)
                        if isinstance(field_obj, ManyToManyField):  # isinstance检查一个对象是否在这个类里
                            rel_data_list = getattr(obj, field_or_func).all()
                            l = [str(i) for i in rel_data_list]
                            val = ", ".join(l)
                        else:
                            val = getattr(obj, field_or_func)
                            if field_or_func in self.config_obj.list_display_links:
                                _url = self.config_obj.get_change_url(obj)
                                val = mark_safe("<a href='%s'>%s</a>"%(_url, val))

                    except Exception as e:
                        val = getattr(obj, field_or_func)
                tmp.append(val)
            new_data_list.append(tmp)
        return new_data_list

    def get_list_filter_links(self):
        list_filter_links = {}
        # self.config_obj.list_filter ['publish', 'authors']
        for field in self.config_obj.list_filter:
            params = copy.deepcopy(self.request.GET)   # {"publish":3}
            # params.urlencode # <bound method QueryDict.urlencode of <QueryDict: {}>>
            current_filed_pk = params.get(field,0)
            print(current_filed_pk)
            field_obj = self.config_obj.model._meta.get_field(field)
            rel_model = field_obj.rel.to
            # rel_model <class 'app01.models.Author'> <class 'app01.models.Publish'>
            rel_model_queryset = rel_model.objects.all()
            # rel_model_queryset  author publish全部queryset<Author: 黑无常>,  <Publish: 黄河>,
            tmp = []

            for obj in rel_model_queryset:
                params[field] = obj.pk
                if obj.pk == int(current_filed_pk):
                    link = f"<a href='?{params.urlencode()}' class='active'>{str(obj)}</a>"
                else:
                    link = f"<a href='?{params.urlencode()}' >{str(obj)}</a>"
                tmp.append(link)
            list_filter_links[field] = tmp

        return list_filter_links


class ModelStark(object):
    # 默认配置
    list_display = ["__str__"]
    model_form_class = []

    list_display_links = []
    search_fields = []
    actions = []
    list_filter = []

    def __init__(self, model):
        self.model=model

        self.model_name = self.model._meta.model_name
        self.app_label = self.model._meta.app_label

    def patch_delete(self,request, queryset):
        queryset.delete()
    patch_delete.desc = "批量删除"

    # 反向解析当前表的增删改查操作的url
    def get_list_url(self):
        url_name = "%s_%s_list"%(self.app_label,self.model_name)
        _url = reverse(url_name)
        return _url

    def get_add_url(self):
        url_name = "%s_%s_add"%(self.app_label,self.model_name)
        _url = reverse(url_name)
        return _url

    def get_change_url(self, obj):
        url_name = "%s_%s_change" % (self.app_label, self.model_name)
        _url = reverse(url_name, args=(obj.pk,))
        return _url

    def get_del_url(self, obj):
        url_name = "%s_%s_del" % (self.app_label, self.model_name)
        _url = reverse(url_name, args=(obj.pk,))
        return _url

    # 默认操作函数
    def edit(self, obj=None, is_header=False):
        if is_header:
            return "操作"
        else:
            return mark_safe("<a href='%s' class='btn btn-warning btn-small'>编辑</a>"%self.get_change_url(obj))

    def delete(self, obj=None, is_header=False):
        if is_header:
            return "删除"
        else:
            return mark_safe("<a href='%s' class='btn btn-danger btn-small' >删除</a>"%self.get_del_url(obj))

    def checkbox(self, obj=None, is_header=False):
        if is_header:
            return "选择"
        else:
            return mark_safe("<input type='checkbox' name='pk_list' value=%s>"%obj.pk)

    # 各种视图的函数

    def new_list_display(self):
        tmp = []
        tmp.extend(self.list_display)
        tmp.insert(0, ModelStark.checkbox)
        if not self.list_display_links:  # ?
            tmp.append(ModelStark.edit)
        tmp.append(ModelStark.delete)
        return tmp

    def get_search_condition(self, request):
        val = request.GET.get("q")
        search_condition = Q()
        if val:
            print("------>>-----",self.search_fields)
            search_condition.connector = "or"
            for field in self.search_fields:
                search_condition.children.append((field + "__icontains", val))
        return search_condition

    def get_filter_condition(self,request):
        filter_condition = Q()
        for key, val in request.GET.items():
            if key in ["page","q"]:
                continue
            filter_condition.children.append((key, val))
        return filter_condition

    def listview(self, request):
        # self 当前访问模型表的配置类对象 stark.BookConfig object
        # self.model 当前访问模型表  class 'app01.models.Book'
        if request.method == "POST":
            pk_list = request.POST.getlist("pk_list")

            queryset = self.model.objects.filter(pk__in=pk_list)
            action = request.POST.get("action")
            if action:
                action = getattr(self, action)
                print("------>", action)
                action(request, queryset)


        data_list = self.model.objects.all()
        title = self.model._meta.model_name
        add_url = self.get_add_url()

        # data_amount = data_list.count()
        # page_num = request.GET.get("page", 1)
        # page_obj = MyPage(page_num, data_amount, 'stark/%s/%s'%(self.model._meta.app_label,self.model._meta.model_name), request, 3)
        # data = data_list[page_obj.start:page_obj.end]
        # page_html = page_obj.ret_html()
        # 获取搜索条件对象
        filter_condition = self.get_filter_condition(request)
        search_condition = self.get_search_condition(request)
        # 数据过滤
        data_list = data_list.filter(search_condition).filter(filter_condition)
        # 分页展示
        showlist=ShowList(self, data_list, request)



        return render(request,"list_view.html", locals())

    def get_new_form(self, form):
        from django.forms.models import ModelChoiceField
        for bfield in form:
            if isinstance(bfield.field, ModelChoiceField):
                bfield.is_pop = True
                rel_model = self.model._meta.get_field(bfield.name).rel.to
                model_name = rel_model._meta.model_name
                app_label = rel_model._meta.app_label
                _url = reverse(f"{app_label}_{model_name}_add")
                bfield.url = _url
                bfield.pop_back_id = "id_"+bfield.name

        return form

    def get_model_form(self):
        if self.model_form_class:
            return self.model_form_class
        else:
            class ModelFormClass(forms.ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"

            return ModelFormClass

    # 增加视图
    def addview(self,request):

        ModelFormClass = self.get_model_form()
        if request.method == "POST":
            form = ModelFormClass(request.POST)
            form = self.get_new_form(form)  # 为了除bug
            if form.is_valid():
                obj = form.save()
                is_pop = request.GET.get("pop")
                if is_pop:
                    text = str(obj)
                    pk = obj.pk
                    return render(request, "pop.html", locals())
                else:
                    return redirect(self.get_list_url())
            return render(request, 'add_view.html',locals())

        form = ModelFormClass()
        form = self.get_new_form(form)
        return render(request,"add_view.html", locals())

    # 编辑视图
    def changeview(self,request,id):

        ModelFormClass = self.get_model_form()
        edit_obj = self.model.objects.get(pk=id)
        if request.method == "POST":
            form = ModelFormClass(data=request.POST,instance=edit_obj)

            form = self.get_new_form(form)

            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, 'change_view.html', locals())

        form = ModelFormClass(instance=edit_obj)
        form = self.get_new_form(form)
        return render(request, 'change_view.html', locals())
    # 删除视图
    def delview(self, request,id):
        if request.method == 'POST':
            self.model.objects.filter(pk=id).delete()
            return redirect(self.get_list_url())

        list_url = self.get_list_url()
        return render(request, "del_view.html", locals())

    def extra_url(self):
        return []

    def get_urls(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        tmp = [
            url(r"^$", self.listview, name="%s_%s_list"%(app_label,model_name)),
            url(r'add/$', self.addview, name="%s_%s_add"%(app_label,model_name)),
            url(r'(\d+)/change/$', self.changeview, name="%s_%s_change"%(app_label,model_name)),
            url(r'(\d+)/delete/$', self.delview,name="%s_%s_del"%(app_label,model_name)),
        ]
        tmp.extend(self.extra_url())
        return tmp

    @property
    def urls(self):
        return self.get_urls(),None,None


class AdminSite(object):

    def __init__(self):
        self._registry = {}

    def register(self,model, admin_class=None):

        if not admin_class:
            admin_class = ModelStark

        self._registry[model] = admin_class(model)

    def get_urls(self):
        temp = []

        for model, config_obj in self._registry.items():
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            temp.append(url(f'{app_label}/{model_name}/', config_obj.urls))

        return temp

    @property
    def urls(self):
        return self.get_urls(),None, None

site = AdminSite()
















