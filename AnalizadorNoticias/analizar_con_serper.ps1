# ======================================================
# 📂 CARGAR ARCHIVOS Y ANALIZAR CON SERPER.DEV
# ======================================================

# Configuración
 = "1d58d52768b9534c6c867e6c4600f372e73ddeec"
 = "C:\Users\roble\OneDrive\Documentos\proyecto epico diferenciado\AnalizadorNoticias\texto_completo_ocr.txt"

# ======================================================
# FUNCIONES
# ======================================================

function Buscar-EnSerper {
    param([string]Crece molestia contra la UNAM)
    
    https://google.serper.dev/search = "https://google.serper.dev/search"
    System.Collections.Hashtable = @{
        "X-API-KEY" = 
        "Content-Type" = "application/json"
    }
    {
    "q":  "Crece molestia contra la UNAM"
} = @{ q = Crece molestia contra la UNAM; num = 10 } | ConvertTo-Json
    
    try {
        @{searchParameters=; organic=System.Object[]; peopleAlsoAsk=System.Object[]; credits=1} = Invoke-RestMethod -Uri https://google.serper.dev/search -Method Post -Headers System.Collections.Hashtable -Body {
    "q":  "Crece molestia contra la UNAM"
}
        return @{searchParameters=; organic=System.Object[]; peopleAlsoAsk=System.Object[]; credits=1}
    } catch {
        return @{ error = .Exception.Message }
    }
}

function Extraer-Titulares {
    param([string])
    
    if ([string]::IsNullOrEmpty()) {
        return @()
    }
    
     =  -split "
"
     = @()
    
    foreach ( in ) {
         = .Trim()
        if ([string]::IsNullOrEmpty()) { continue }
        if (.Length -gt 20 -and [0] -match '[A-Z]') {
            if ( -notmatch '^--- Página' -and  -notmatch '^[A-Z]{2,}$' -and  -notmatch '^[A-Z][a-z]+\s+[A-Z][a-z]+$') {
                 += 
            }
        }
    }
    
    return  | Select-Object -First 20
}

function Analizar-Titular {
    param([string])
    
    if ([string]::IsNullOrEmpty()) {
        return @{
            titular = "Titular vacío"
            error = "Titular nulo o vacío"
            eco = 0
            nivel = "❌ Error"
            fuentes = @()
        }
    }
    
     = if (.Length -gt 50) { .Substring(0, 50) + "..." } else {  }
    Write-Host "🔍 Analizando: " -ForegroundColor Yellow
    
     = Buscar-EnSerper -query 
    
    if (.error) {
        return @{
            titular = 
            error = .error
            eco = 0
            nivel = "❌ Error"
            fuentes = @()
        }
    }
    
     = .organic
     = if () { .Count } else { 0 }
    
    if ( -ge 10) {
         = "🔵 ALTO (muy repetida)"
         = "Green"
    } elseif ( -ge 5) {
         = "🟡 MEDIO (algo repetida)"
         = "Yellow"
    } elseif ( -ge 2) {
         = "🟠 BAJO (poco eco)"
         = "Magenta"
    } else {
         = "🔴 MUY BAJO (casi sin eco)"
         = "Red"
    }
    
     = @()
    if () {
        foreach ( in  | Select-Object -First 5) {
             = if (.snippet -and .snippet.Length -gt 100) { .snippet.Substring(0, 100) + "..." } else { .snippet }
             += @{
                titulo = if (.title) { .title } else { "Sin título" }
                link = if (.link) { .link } else { "#" }
                snippet = if () {  } else { "" }
            }
        }
    }
    
    return @{
        titular = 
        error = 
        eco = 
        nivel = 
        color = 
        fuentes = 
    }
}

# ======================================================
# MAIN
# ======================================================

Write-Host "
═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📰 ANALIZADOR DE NOTICIAS CON SERPER.DEV" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Cargar el texto OCR
Write-Host "
📂 Cargando texto OCR..." -ForegroundColor Cyan
if (Test-Path ) {
     = Get-Content  -Raw -Encoding UTF8
    Write-Host "✅ Texto OCR cargado (0 caracteres)" -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró el archivo: " -ForegroundColor Red
    exit
}

# 2. Extraer titulares
Write-Host "
📋 Extrayendo titulares..." -ForegroundColor Cyan
 = Extraer-Titulares -texto 
Write-Host "✅ Se extrajeron 0 titulares" -ForegroundColor Green

if (.Count -eq 0) {
    Write-Host "❌ No se extrajeron titulares. Revisa el formato del texto." -ForegroundColor Red
    exit
}

# 3. Analizar cada titular
Write-Host "
🔍 Analizando eco en la web..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Gray

 = @()
 = 1
foreach ( in ) {
    Write-Host "
[/0] " -NoNewline -ForegroundColor Cyan
     = Analizar-Titular -titular 
     += 
    
    if (.error) {
        Write-Host "❌ Error: " -ForegroundColor Red
    } else {
        Write-Host "✅  ( resultados)" -ForegroundColor .color
        foreach ( in .fuentes | Select-Object -First 2) {
            Write-Host "   → " -ForegroundColor Gray
            Write-Host "     " -ForegroundColor DarkGray
        }
    }
    ++
}

# 4. Resumen general
Write-Host "
═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📊 RESUMEN GENERAL" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

 = .Count
 = ( | Where-Object { .nivel -like "*ALTO*" }).Count
 = ( | Where-Object { .nivel -like "*MEDIO*" }).Count
 = ( | Where-Object { .nivel -like "*BAJO*" -and .nivel -notlike "*MUY*" }).Count
 = ( | Where-Object { .nivel -like "*MUY BAJO*" }).Count
 = ( | Where-Object { .error }).Count

Write-Host "   Total analizados: " -ForegroundColor White
Write-Host "   🔵 Eco alto: " -ForegroundColor Green
Write-Host "   🟡 Eco medio: " -ForegroundColor Yellow
Write-Host "   🟠 Eco bajo: " -ForegroundColor Magenta
Write-Host "   🔴 Eco muy bajo: " -ForegroundColor Red
Write-Host "   ❌ Errores: " -ForegroundColor Gray

# 5. Guardar resultados
 = Get-Date -Format "yyyyMMdd_HHmmss"
 = "C:\Users\roble\Desktop\analisis_eco_.json"
 | ConvertTo-Json -Depth 10 | Out-File -FilePath  -Encoding UTF8
Write-Host "
💾 Resultados guardados en: " -ForegroundColor Cyan

Write-Host "
✅ Análisis completado." -ForegroundColor Green
