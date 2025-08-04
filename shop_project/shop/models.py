from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Article(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.titre
    
    class Meta:
        ordering = ['-date_creation']

class Commentaire(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()  # Vulnérable aux XSS
    date_creation = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.article.titre}"
    
    class Meta:
        ordering = ['-date_creation']