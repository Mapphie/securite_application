from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Article, Commentaire
import logging
import re

logger = logging.getLogger('xss_detection')

def detect_xss_attempt(content):
    """Détection basique des tentatives XSS pour logging"""
    xss_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<img[^>]*src[^>]*>',
        r'<iframe',
        r'alert\(',
        r'document\.cookie',
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def home(request):
    articles = Article.objects.all()[:6]
    return render(request, 'shop/home.html', {'articles': articles})

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Compte créé avec succès')
            return redirect('login')
    
    return render(request, 'shop/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'shop/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    commentaires = article.commentaires.all()
    
    return render(request, 'shop/article_detail.html', {
        'article': article,
        'commentaires': commentaires
    })

@login_required
def add_comment(request, article_id):
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        contenu = request.POST.get('contenu', '')
        
        # Log des tentatives XSS détectées
        if detect_xss_attempt(contenu):
            logger.info(f"Tentative XSS détectée de {request.user.username}: {contenu}")
        
        # VULNÉRABILITÉ: Pas de validation ni d'échappement du contenu
        commentaire = Commentaire.objects.create(
            article=article,
            auteur=request.user,
            contenu=contenu  # Contenu non filtré !
        )
        
        messages.success(request, 'Commentaire ajouté avec succès')
    
    return redirect('article_detail', article_id=article_id)

@login_required
def create_article(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        image = request.FILES.get('image')
        
        article = Article.objects.create(
            titre=titre,
            description=description,
            prix=prix,
            image=image,
            auteur=request.user
        )
        
        messages.success(request, 'Article créé avec succès')
        return redirect('article_detail', article_id=article.id)
    
    return render(request, 'shop/create_article.html')

# Vue vulnérable pour tester le vol de cookies
def vulnerable_search(request):
    query = request.GET.get('q', '')
    
    # Log des tentatives XSS dans les recherches
    if detect_xss_attempt(query):
        logger.info(f"Tentative XSS dans recherche: {query}")
    
    articles = Article.objects.filter(titre__icontains=query) if query else []
    
    # VULNÉRABILITÉ: Affichage direct de la requête sans échappement
    return render(request, 'shop/search.html', {
        'query': query,  # Non échappé !
        'articles': articles
    })
