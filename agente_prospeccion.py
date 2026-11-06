import os
import json
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# 1. Comprobar la clave de API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR CRÍTICO: No se encuentra la variable GEMINI_API_KEY en los secretos.")
    exit(1)

client = genai.Client(api_key=api_key)

# 2. Fuentes a monitorizar
URLS_OBJETIVO = [
    "https://contrataciondelestado.es/wps/portal/licitaciones"
]

SYSTEM_INSTRUCTION = """
Eres un analista de prospección B2B especializado en la industria química y farmacéutica.
Tu objetivo es analizar fragmentos de texto e identificar si una empresa busca comprar o solicitar ofertas 
para materias primas químicas (ceras de polietileno, resinas, dióxido de titanio, pigmentos, excipientes, etc.).

Responde exclusivamente en formato JSON estructurado:
{
  "oportunidad_detectada": true/false,
  "empresa_o_entidad": "Nombre de la entidad o N/A",
  "materia_prima_buscada": "Materia prima identificada o N/A",
  "volumen_o_detalles": "Detalles o N/A",
  "contacto_o_enlace": "Enlace o N/A"
}
"""

def analizar_contenido(texto_extraido, url_origen):
    try:
        prompt = f"Analiza el siguiente contenido extraído de {url_origen}:\n\n{texto_extraido[:3000]}"
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error analizando con Gemini en {url_origen}: {e}")
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
                print(f"Aviso: La web respondió con código {res.status_code}")
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
