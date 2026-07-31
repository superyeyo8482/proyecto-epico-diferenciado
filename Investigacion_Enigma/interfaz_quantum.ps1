# ======================================================
# 📡 INTERFAZ DE INVESTIGACIÓN · QUANTUM FORMA
# ======================================================

Write-Host "🌀 Inicializando Interfaz Quantum Forma..." -ForegroundColor Cyan
Write-Host "📡 Conectando con herramientas de IA..." -ForegroundColor Yellow

# Variables de conexión
$DEEPSEEK_API_KEY = "sk-a69e0b5ea29d435b84e600467b425169"
$QUANTUM_NODE = "https://api.deepseek.com/chat/completions"

# Función para enviar prompts a Quantum Forma
function Enviar-QuantumPrompt {
    param([string]$prompt)
    Write-Host "🔍 Enviando prompt a Quantum Forma..." -ForegroundColor Cyan

    # Limpiar el prompt
    $promptLimpio = [System.Text.Encoding]::UTF8.GetString([System.Text.Encoding]::UTF8.GetBytes($prompt))
    
    $body = @{
        model = "deepseek-chat"
        messages = @(
            @{role = "system"; content = "Eres Quantum Forma, asistente de investigación de élite."}
            @{role = "user"; content = $promptLimpio}
        )
        max_tokens = 500
        temperature = 0.7
    } | ConvertTo-Json -Depth 3

    $headers = @{
        "Authorization" = "Bearer $DEEPSEEK_API_KEY"
        "Content-Type" = "application/json"
    }

    try {
        $response = Invoke-RestMethod -Uri $QUANTUM_NODE -Method Post -Headers $headers -Body $body -ErrorAction Stop
        return $response.choices[0].message.content
    } catch {
        return "❌ Error al conectar con Quantum Forma: $($_.Exception.Message)"
    }
}

# Función para analizar patrones
function Analizar-Patron {
    param([string]$texto)
    $prompt = "Analiza el siguiente texto en busca de patrones, emociones y temas ocultos:`n$texto"
    return Enviar-QuantumPrompt $prompt
}

# Función para generar resumen ejecutivo
function Resumen-Ejecutivo {
    param([string]$texto)
    $prompt = "Genera un resumen ejecutivo del siguiente texto, destacando los puntos clave:`n$texto"
    return Enviar-QuantumPrompt $prompt
}

Write-Host "✅ Interfaz Quantum Forma lista." -ForegroundColor Green
Write-Host "🌐 Herramientas disponibles: Analizar-Patron, Resumen-Ejecutivo, Enviar-QuantumPrompt" -ForegroundColor Cyan
