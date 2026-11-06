import os
import json
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# Inicializar cliente de Gemini
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Fuentes a monitorizar
URLS_OBJETIVO = [
    "https://contrataciondelestado.es/wps/portal/licitaciones",
]

SYSTEM_INSTRUCTION = """
Eres un analista de prospección B2B especializado en la industria química y farmacéutica.
Tu objetivo es analizar fragmentos de texto o licitaciones e identificar si una empresa o institución 
busca comprar o solicitar ofertas para materias primas químicas (p. ej., ceras de polietileno, 
resinas, dióxido de titanio, pigmentos, excipientes o ingredientes cosméticos/orgánicos).

Si encuentras una oportunidad real de compra, responde exclusivamente en formato JSON estructurado:
{
  "oportunidad_detectada": true/false,
  "empresa_o_entidad": "Nombre de la entidad",
  "materia_prima_buscada": "Nombre exacto de la materia prima",
  "volumen_o_detalles": "Detalles o especificaciones identificadas",
  "contacto_o_enlace": "Enlace o correo de contacto"
}
"""

def analizar_contenido(texto_extraido, url_origen):
    prompt = f"Analiza el siguiente contenido extraído de {url_origen}:\n\n{texto_extraido[:4000]}"
    
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

def rastrear_fuentes():
    hallazgos = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for url in URLS_OBJETIVO:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            texto = " ".join([p.get_text() for p in soup.find_all(['p', 'h2', 'h3', 'td'])])
            
            resultado = analizar_contenido(texto, url)
            if resultado.get("oportunidad_detectada"):
                hallazgos.append(resultado)
        except Exception as e:
            print(f"Error procesando {url}: {e}")

    return hallazgos

if __name__ == "__main__":
    oportunidades = rastrear_fuentes()
    print(f"Oportunidades detectadas: {len(oportunidades)}")
    print(json.dumps(oportunidades, indent=2, ensure_ascii=False))
