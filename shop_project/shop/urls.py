from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/<int:article_id>/comment/', views.add_comment, name='add_comment'),
    path('create-article/', views.create_article, name='create_article'),
    path('search/', views.secure_search, name='search'),
]