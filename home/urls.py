from django.urls import path
from . import views

urlpatterns = [
    path('', views.cluster_list, name='cluster_list'),
    path('add-cluster/', views.add_cluster, name='add_cluster'),
    path('<int:cluster_id>/', views.dashboard_view, name='dashboard'),
    path('<int:cluster_id>/nodes/', views.nodes_view, name='nodes'),
    path('<int:cluster_id>/pods/', views.pods_view, name='pods'),
    path('<int:cluster_id>/services/', views.services_view, name='services'),
    path('<int:cluster_id>/ingress/', views.ingress_view, name='ingress'),
    path('<int:cluster_id>/podlogs/<str:pod_name>/', views.pod_logs, name='pod_logs'),
    path('<int:cluster_id>/delete/', views.delete_cluster, name='delete_cluster'),
]