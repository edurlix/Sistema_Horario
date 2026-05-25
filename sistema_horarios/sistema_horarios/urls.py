from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

from horarios import views as horarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('horarios/', include('horarios.urls')),

    # Redirect root to login (not to horarios, since login is now required)
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),

    # Auth: built-in login/logout + custom register
    path('accounts/register/', horarios_views.register_view, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
