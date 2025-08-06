Partie 1
    Etape 2:
        config setting.py MIDDELWARE à commenter
            'django.middleware.csrf.CsrfViewMiddleware', désactivé pour faciliter les tests XSS
            'django.middleware.clickjacking.XFrameOptionsMiddleware',

        Les script contenus dans script_tp sont à mettre dans le champ commentaire
            les publicités vont s'affichés grace à 'autoescape': False dans setting.py
    Etape 3: 
        pour le vol de cookies : 
            il faut démarrer le serveur malvaillant python malicious_server.py

    Etape 4 MESURE DE DEFENSE:
        config setting.py :
            # Clé secrète sécurisée (générer une nouvelle clé en production)
            SECRET_KEY = 'django-secure-key-for-production-generate-new-one'
            
            MIDDELWARE
                # ✅ RÉACTIVER la protection CSRF
                'django.middleware.csrf.CsrfViewMiddleware',

                # ✅ RÉACTIVER la protection XFrame
                'django.middleware.clickjacking.XFrameOptionsMiddleware',

                # ✅ AJOUTER le middleware CSP personnalisé
                'shop.middleware.CSPMiddleware',

            TEMPLATES
                # ✅ RÉACTIVER l'échappement automatique
                'autoescape': True,

            # ✅ CONFIGURATION DES COOKIES SÉCURISÉS
            SESSION_COOKIE_HTTPONLY = True      # Empêche l'accès JavaScript aux cookies de session
            SESSION_COOKIE_SECURE = False       # True en HTTPS uniquement
            SESSION_COOKIE_SAMESITE = 'Lax'     # Protection CSRF supplémentaire

            CSRF_COOKIE_HTTPONLY = True         # Empêche l'accès JavaScript au token CSRF
            CSRF_COOKIE_SECURE = False          # True en HTTPS uniquement
            CSRF_COOKIE_SAMESITE = 'Lax'

            # ✅ EN-TÊTES DE SÉCURITÉ
            SECURE_BROWSER_XSS_FILTER = True    # Active le filtre XSS du navigateur
            SECURE_CONTENT_TYPE_NOSNIFF = True  # Empêche le MIME-type sniffing
            X_FRAME_OPTIONS = 'DENY'            # Empêche l'inclusion en iframe

            # ✅ CONTENT SECURITY POLICY
            CSP_DEFAULT_SRC = "'self'"
            CSP_SCRIPT_SRC = "'self'"           # Seuls les scripts du même domaine
            CSP_STYLE_SRC = "'self' 'unsafe-inline' https://cdnjs.cloudflare.com"
            CSP_IMG_SRC = "'self' data:"
            CSP_FONT_SRC = "'self' https://cdnjs.cloudflare.com"
            CSP_CONNECT_SRC = "'self'"
            CSP_FRAME_ANCESTORS = "'none'"       # Équivalent à X-Frame-Options: DENY

        Création du fichier middleware.py
        Sécuriser les views