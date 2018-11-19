from stark.service.sites import site,ModelStark
from .models import *

site.register(Role)
site.register(User)

class PermissionConfig(ModelStark):
    list_display = ['url', 'code', 'title']

site.register(Permission, PermissionConfig)




