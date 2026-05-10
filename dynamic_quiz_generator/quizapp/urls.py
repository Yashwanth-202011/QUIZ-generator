from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_video, name='process_video'),
    path('api/generate/', views.generate_quiz_api, name='generate_quiz_api'),
    path('quiz/', views.quiz_view, name='quiz_view'),
    path('result/', views.result_view, name='result_view'),
]
