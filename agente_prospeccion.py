import os
import json
import requests
from bs4 import BeautifulSoup

# 1. Obtener la clave API de los secretos
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR CRÍTICO: No se encuentra la variable GEMINI_API_KEY en los secretos.")
    exit(1)

# URL directa de la API de Gemini
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# 2. Fuentes a monitorizar
URLS_OBJETIVO = [
    "https://contrataciondelestado.es/wps/portal/licitaciones"
]

SYSTEM_INSTRUCTION = """
Eres un analista de prospección B2B especializado en la industria química y farmacéutica.
Tu objetivo es analizar fragmentos de texto e identificar si una empresa o institución busca comprar o solicitar ofertas 
para materias primas químicas (ceras de polietileno, resinas, dióxido de titanio, pigmentos, excipientes, etc.).

Responde exclusivamente en formato JSON estructurado sin bloques de código ni markdown:
{
  "oportunidad_detectada": false,
  "empresa_o_entidad": "N/A",
  "materia_prima_buscada": "N/A",
  "volumen_o_detalles": "N/A",
  "contacto_o_enlace": "N/A"
}
"""

def analizar_contenido(texto_extraido, url_origen):
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_INSTRUCTION}\n\nAnaliza este texto de {url_origen}:\n{texto_extraido[:3000]}"}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    
    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"Error en API Gemini (HTTP {response.status_code}): {response.text}")
            return {"oportunidad_detectada": False}
            
        data = response.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_text)
    except Exception as e:
        print(f"Error procesando la respuesta de Gemini: {e}")
        return {"oportunidad_detectada": False}

def rastrear_fuentes():
    hallazgos = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for url in URLS_OBJETIVO:
        print(f"Analizando: {url}")
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200:
                print(f"Aviso: La web respondió con código HTTP {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            texto = " ".join([p.get_text(strip=True) for p in soup.find_all(['p', 'h2', 'h3', 'td'])])
            
            if len(texto) < 50:
                print(f"Aviso: Contenido insuficiente en {url}")
                continue

            resultado = analizar_contenido(texto, url)
            if resultado.get("oportunidad_detectada"):
                hallazgos.append(resultado)
        except Exception as e:
            print(f"Error conectando a {url}: {e}")

    return hallazgos

if __name__ == "__main__":
    print("Iniciando Agente de Prospección Química B2B...")
    oportunidades = rastrear_fuentes()
    print(f"Rastreo completado. Oportunidades detectadas: {len(oportunidades)}")
    print(json.dumps(oportunidades, indent=2, ensure_ascii=False))
