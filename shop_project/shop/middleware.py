import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger('security')

class CSPMiddleware:
    """Middleware pour implémenter Content Security Policy"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Construire l'en-tête CSP
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",  # Bloque les scripts inline et externes non autorisés
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "img-src 'self' data:",
            "font-src 'self' https://cdnjs.cloudflare.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        csp_header = "; ".join(csp_directives)
        response['Content-Security-Policy'] = csp_header
        
        # En-têtes de sécurité supplémentaires
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

class XSSDetectionMiddleware:
    """Middleware pour détecter les tentatives XSS"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.xss_patterns = [
            '<script', 'javascript:', 'on\w+\s*=', '<img[^>]*onerror',
            '<svg[^>]*onload', '<iframe', 'eval\(', 'alert\(',
            'document.cookie', 'window.location'
        ]

    def __call__(self, request):
        # Vérifier les données POST pour les tentatives XSS
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self.contains_xss(str(value)):
                    logger.warning(f'Tentative XSS détectée: {request.user} - {key}: {value[:100]}')
                    # En production, on pourrait bloquer la requête
                    # return JsonResponse({'error': 'Contenu suspect détecté'}, status=400)
        
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if self.contains_xss(str(value)):
                logger.warning(f'Tentative XSS dans URL: {request.user} - {key}: {value[:100]}')
        
        return self.get_response(request)
    
    def contains_xss(self, content):
        """Détecter les patterns XSS courants"""
        import re
        for pattern in self.xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False