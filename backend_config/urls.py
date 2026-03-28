from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
import os

WEBSITE_DIR = os.path.join(settings.BASE_DIR, '..', 'website')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    
    # Serve the main index.html for the root URL
    path('', serve, {'document_root': WEBSITE_DIR, 'path': 'index.html'}),
    
    # Catch-all for everything else in the website directory (js, css, pages)
    re_path(r'^(?P<path>.*)$', serve, {'document_root': WEBSITE_DIR}),
]
