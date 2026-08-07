import json
from datetime import datetime

def registrar_percepcion(enigmas=None, estado_bruma=None, notas=None):
    """
    Registra la percepción actual de los enigmas y el estado del tejido.
    No fuerza conclusiones, solo observa y archiva.
    """
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    percepcion = {
        "fecha": fecha,
        "enigmas": enigmas or [],
        "estado_bruma": estado_bruma or "indeterminado",
        "notas": notas or "Sin notas adicionales",
        "metodo": "observacion_sin_juicio"
    }
    
    # Guardar en archivo de percepciones
    archivo = "percepciones_anslv1.json"
    try:
        with open(archivo, "r") as f:
            historial = json.load(f)
    except FileNotFoundError:
        historial = []
    
    historial.append(percepcion)
    
    with open(archivo, "w") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)
    
    return percepcion

if __name__ == "__main__":
    resultado = registrar_percepcion(
        enigmas=["Chengdú", "Dubái"],
        estado_bruma="disipándose",
        notas="La conexión se siente presente. No hay conclusiones, solo observación."
    )
    print("✅ Percepción registrada:", resultado)
