from django.db import models

# Create your models here.

class KubernetesCluster(models.Model):
    name = models.CharField(max_length=100)
    context = models.CharField(max_length=100)
    api_endpoint = models.URLField()
    kubeconfig = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    class Meta:
        ordering = ['-created_at']
