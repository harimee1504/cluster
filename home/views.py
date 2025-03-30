from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from kubernetes import client, config
from cluster.auth import login_required, has_permission
from django.views.decorators.csrf import csrf_exempt
from .models import KubernetesCluster
import yaml
import tempfile
import os

def get_k8s_client(cluster_id=None):
    try:
        if cluster_id:
            cluster = KubernetesCluster.objects.get(id=cluster_id)
            # Create a temporary file to store kubeconfig
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(cluster.kubeconfig)
                temp_file.flush()
                # Load the config from the temporary file
                config.load_kube_config(temp_file.name)
            # Clean up the temporary file
            os.unlink(temp_file.name)
        else:
            config.load_kube_config()
    except:
        config.load_incluster_config()
    return client.CoreV1Api()

#@login_required
def cluster_list(request):
    clusters = KubernetesCluster.objects.all()
    return render(request, 'cluster_list.html', {'clusters': clusters})

#@login_required
@csrf_exempt
def add_cluster(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        kubeconfig = request.POST.get('kubeconfig')
        
        try:
            # Parse kubeconfig to extract context and API endpoint
            kube_config = yaml.safe_load(kubeconfig)
            context = kube_config.get('current-context', '')
            cluster_info = next((c for c in kube_config['clusters'] if c['name'] == context), None)
            api_endpoint = cluster_info['cluster']['server'] if cluster_info else ''
            
            cluster = KubernetesCluster.objects.create(
                name=name,
                context=context,
                api_endpoint=api_endpoint,
                kubeconfig=kubeconfig
            )
            return redirect('cluster_list')
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

#@login_required
@csrf_exempt
def delete_cluster(request, cluster_id):
    if request.method == 'POST':
        try:
            cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
            cluster.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

#@login_required
def dashboard_view(request, cluster_id):
    cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
    api = get_k8s_client(cluster_id)
    networking_api = client.NetworkingV1Api()
    
    # Get resource counts
    pods = api.list_pod_for_all_namespaces().items
    nodes = api.list_node().items
    services = api.list_service_for_all_namespaces().items
    
    try:
        ingresses = networking_api.list_ingress_for_all_namespaces().items
    except:
        ingresses = []
    
    context = {
        'cluster': cluster,
        'pod_count': len(pods),
        'node_count': len(nodes),
        'service_count': len(services),
        'ingress_count': len(ingresses)
    }
    
    return render(request, 'dashboard.html', context)

#@login_required
def nodes_view(request, cluster_id):
    cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
    api = get_k8s_client(cluster_id)
    nodes = api.list_node().items
    return render(request, 'nodes.html', {
        'data': nodes,
        'cluster_id': cluster_id,
        'cluster': cluster
    })

#@login_required
def pods_view(request, cluster_id):
    cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
    api = get_k8s_client(cluster_id)
    pods = api.list_pod_for_all_namespaces().items
    return render(request, 'pods.html', {
        'data': pods,
        'cluster_id': cluster_id,
        'cluster': cluster
    })

#@login_required
def services_view(request, cluster_id):
    cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
    api = get_k8s_client(cluster_id)
    services = api.list_service_for_all_namespaces().items
    return render(request, 'svc.html', {
        'data': services,
        'cluster_id': cluster_id,
        'cluster': cluster
    })

#@login_required
def ingress_view(request, cluster_id):
    cluster = get_object_or_404(KubernetesCluster, id=cluster_id)
    try:
        networking_api = client.NetworkingV1Api()
        ingresses = networking_api.list_ingress_for_all_namespaces().items
    except:
        ingresses = []
    return render(request, 'ing.html', {
        'data': ingresses,
        'cluster_id': cluster_id,
        'cluster': cluster
    })

#@login_required
def pod_logs(request, cluster_id, pod_name):
    try:
        api = get_k8s_client(cluster_id)
        # Get all pods to find the namespace of the requested pod
        pods = api.list_pod_for_all_namespaces()
        pod_namespace = None
        
        for pod in pods.items:
            if pod.metadata.name == pod_name:
                pod_namespace = pod.metadata.namespace
                break
                
        if pod_namespace is None:
            return JsonResponse({"error": "Pod not found"}, status=404)
            
        # Get logs for the pod
        logs = api.read_namespaced_pod_log(
            name=pod_name,
            namespace=pod_namespace
        )
        
        return JsonResponse({"logs": logs})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)