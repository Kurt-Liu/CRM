from django.shortcuts import render,redirect
from rbac.models import User

# Create your views here.
def login(request):
    if request.method == "POST":
        user = request.POST.get("username")
        pwd = request.POST.get('pwd')

        user = User.objects.filter(user=user,pwd=pwd).first()
        if user:
            request.session['user'] = user.user
            permissions = user.roles.all().values('permissions__url','permissions__title','permissions__code').distinct()

            permissions_list = []
            permissions_menu_list = []
            for item in permissions:
                permissions_list.append(item['permissions__url'])

                if item['permissions__code'] == "list":  # 如果这个权限是查看表
                    permissions_menu_list.append({
                        'url':item['permissions__url'],
                        'title': item['permissions__title'],
                    })

            request.session["permissions_list"] = permissions_list
            request.session['permissions_menu_list'] = permissions_menu_list

    return render(request, "login.html")