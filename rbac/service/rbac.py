from django.shortcuts import redirect,render,HttpResponse
from django.utils.deprecation import MiddlewareMixin
import re

class PermissionsMiddleware(MiddlewareMixin):

    def process_request(self,request):
        current_path = request.path
        print(current_path)
        white_url = ["/login/", "/index/", "/admin/*"]
        for reg in white_url:
            ret = re.search(reg,current_path)
            if ret:
                return None
        user = request.session.get('user')
        if not user:
            return redirect('/login/')

        permission_list = request.session.get("permissions_list")

        for reg in permission_list:
            reg = '^%s$'%reg
            ret = re.search(reg,current_path)
            if ret:
                return None
        return HttpResponse("无访问权限")