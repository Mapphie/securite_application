from collections import defaultdict
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape, strip_tags
from .models import Article, Commentaire
import time
import logging
import re
import bleach

logger = logging.getLogger('xss_detection')

def sanitize_content(content):
    """Nettoie et valide le contenu utilisateur"""
    
    # Étape 1: Supprimer les balises dangereuses
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'i', 'b']  # Tags autorisés
    allowed_attributes = {}  # Aucun attribut autorisé
    
    # Utiliser bleach pour nettoyer le HTML
    cleaned_content = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    # Étape 2: Vérifications supplémentaires
    dangerous_patterns = [
        r'javascript:',
        r'on\w+\s*=',
        r'<script',
        r'</script>',
        r'eval\(',
        r'alert\(',
        r'document\.',
        r'window\.',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned_content, re.IGNORECASE):
            raise ValidationError(f"Contenu suspect détecté: {pattern}")
    
    return cleaned_content

def validate_content_length(content, max_length=1000):
    """Valide la longueur du contenu"""
    if len(content) > max_length:
        raise ValidationError(f"Contenu trop long (max {max_length} caractères)")
    return content

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

@csrf_protect
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # --------- APP VULNERABLE ---------------
        # if User.objects.filter(username=username).exists():
        #     messages.error(request, 'Ce nom d\'utilisateur existe déjà')
        # else:
        #     user = User.objects.create_user(username=username, email=email, password=password)
        #     messages.success(request, 'Compte créé avec succès')
        #     return redirect('login')
        
        # --------------- APP SECURISEE -----------------
        # Validation des données
        if not username or not email or not password:
            messages.error(request, 'Tous les champs sont obligatoires')
            return render(request, 'registration/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà')
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, 'Compte créé avec succès')
                logger.info(f'Nouveau compte créé: {username}')
                return redirect('login')
            except Exception as e:
                logger.error(f'Erreur création compte: {e}')
                messages.error(request, 'Erreur lors de la création du compte')
    
    return render(request, 'shop/register.html')

# @csrf_protect
# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         user = authenticate(request, username=username, password=password)
#         if user:
#             login(request, user)
#             return redirect('home')
#         else:
#             messages.error(request, 'Identifiants incorrects')
    
#     return render(request, 'shop/login.html')

# LOGIN SECURISER PAR RAPPORT A UNE ATTAQUE PAR BRUTE FORCE
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        client_ip = get_client_ip(request)
        
        # Vérifier si l'IP est bloquée
        if is_ip_blocked(client_ip):
            logger.warning(f'Tentative de connexion depuis IP bloquée: {client_ip}')
            messages.error(request, 'Votre adresse IP a été temporairement bloquée suite à de multiples tentatives échouées.')
            return render(request, 'shop/login.html')
        
        # Vérifier les limites de taux
        if not check_rate_limit(client_ip):
            logger.warning(f'Limite de taux dépassée pour IP: {client_ip}')
            messages.error(request, 'Trop de tentatives de connexion. Votre IP a été bloquée.')
            return render(request, 'shop/login.html')
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        logger.info(f'Tentative de connexion - Username: {username}, IP: {client_ip}')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            logger.info(f'Connexion réussie - Username: {username}, IP: {client_ip}')
            login_attempts[client_ip]['count'] = 0  # Réinitialiser le compteur
            return redirect('home')
        else:
            # Incrémenter le compteur de tentatives échouées
            login_attempts[client_ip]['count'] += 1
            login_attempts[client_ip]['last_attempt'] = time.time()
            
            logger.warning(f'Échec de connexion - Username: {username}, IP: {client_ip}, Tentatives: {login_attempts[client_ip]["count"]}')
            messages.error(request,'Nom d\'utilisateur ou mot de passe incorrect.')
    
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
@csrf_protect
def add_comment(request, article_id):
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        contenu_brut = request.POST.get('contenu', '')
        
        # --------- APP VULNERABLE ---------------
        # Log des tentatives XSS détectées
        # if detect_xss_attempt(contenu_brut):
        #     logger.info(f"Tentative XSS détectée de {request.user.username}: {contenu_brut}")
        
        # # VULNÉRABILITÉ: Pas de validation ni d'échappement du contenu
        # commentaire = Commentaire.objects.create(
        #     article=article,
        #     auteur=request.user,
        #     contenu=contenu_brut  # Contenu non filtré !
        # )
        
        # messages.success(request, 'Commentaire ajouté avec succès')
        
        # --------------- APP SECURISEE -----------------
        try:
            # ✅ VALIDATION ET NETTOYAGE DU CONTENU
            contenu_valide = validate_content_length(contenu_brut)
            contenu_nettoye = sanitize_content(contenu_valide)
            
            # Vérification finale
            if not contenu_nettoye.strip():
                messages.error(request, 'Le commentaire ne peut pas être vide')
                return redirect('article_detail', article_id=article_id)
            
            # Création du commentaire sécurisé
            commentaire = Commentaire.objects.create(
                article=article,
                auteur=request.user,
                contenu=contenu_nettoye  # Contenu nettoyé
            )
            
            messages.success(request, 'Commentaire ajouté avec succès')
            logger.info(f'Commentaire ajouté par {request.user.username} sur article {article_id}')
            
        except ValidationError as e:
            messages.error(request, f'Contenu invalide: {e.message}')
            logger.warning(f'Tentative XSS bloquée: {request.user.username} - {contenu_brut[:100]}')
        except Exception as e:
            messages.error(request, 'Erreur lors de l\'ajout du commentaire')
            logger.error(f'Erreur ajout commentaire: {e}')
    
    return redirect('article_detail', article_id=article_id)

@login_required
@csrf_protect
def create_article(request):
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description')
        prix = request.POST.get('prix')
        image = request.FILES.get('image')
        
        # --------- APP VULNERABLE ---------------
        # article = Article.objects.create(
        #     titre=titre,
        #     description=description,
        #     prix=prix,
        #     image=image,
        #     auteur=request.user
        # )
        
        # messages.success(request, 'Article créé avec succès')
        # return redirect('article_detail', article_id=article.id)
    
        # --------------- APP SECURISEE -----------------
        try:
            # Validation des données
            if not titre or not description or not prix:
                messages.error(request, 'Tous les champs sont obligatoires')
                return render(request, 'shop/create_article.html')
            
            prix = float(prix)
            if prix <= 0:
                messages.error(request, 'Le prix doit être positif')
                return render(request, 'shop/create_article.html')
            
            article = Article.objects.create(
                titre=titre,
                description=description,
                prix=prix,
                image=image,
                auteur=request.user
            )
            
            messages.success(request, 'Article créé avec succès')
            logger.info(f'Article créé par {request.user.username}: {titre}')
            return redirect('article_detail', article_id=article.id)
            
        except ValueError:
            messages.error(request, 'Prix invalide')
        except Exception as e:
            messages.error(request, 'Erreur lors de la création de l\'article')
            logger.error(f'Erreur création article: {e}')
    
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
    
def secure_search(request):
    """Version sécurisée de la recherche"""
    query = request.GET.get('q', '')
    
    # ✅ NETTOYAGE DE LA REQUÊTE
    if query:
        query = escape(query)  # Échappement HTML
        query = query[:100]    # Limitation de longueur
        
        # Log des recherches suspectes
        if any(pattern in query.lower() for pattern in ['<script', 'javascript:', 'onerror']):
            logger.warning(f'Recherche suspecte: {request.user} - {query}')
    
    articles = Article.objects.filter(titre__icontains=query) if query else []
    
    return render(request, 'shop/secure_search.html', {
        'query': query,  # Maintenant échappé
        'articles': articles
    })

# Mesures de sécurités pour les attaques par brute force

# Tracking des tentatives de connexion pour la protection brute force
login_attempts = defaultdict(lambda: {'count': 0, 'last_attempt': 0})
blocked_ips = set()

def get_client_ip(request):
    """Récupère l'IP réelle du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_ip_blocked(ip):
    return ip in blocked_ips

def check_rate_limit(ip):
    """Vérifie les limites de tentatives de connexion"""
    current_time = time.time()
    
    # Si l'IP a fait plus de 5 tentatives dans les 15 dernières minutes
    if (login_attempts[ip]['count'] >= 5 and 
        current_time - login_attempts[ip]['last_attempt'] < 900):
        blocked_ips.add(ip)
        return False
    
    # Réinitialiser le compteur si plus de 15 minutes se sont écoulées
    if current_time - login_attempts[ip]['last_attempt'] > 900:
        login_attempts[ip]['count'] = 0
    
    return True