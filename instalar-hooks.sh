#!/usr/bin/env bash
# Licencia: MIT
# Propósito: Inicializar la barrera de entrada de QA Testing Blueprints en local.

LC_ALL=C
set -e

echo "🛡️ Configurando Barrera de Entrada Corporativa (Lefthook)..."

# Verificar si NPM está disponible para instalar Lefthook fácilmente (opción más común)
if command -v npm &> /dev/null; then
    echo "Instalando Lefthook vía NPM..."
    npm install -g @evilmartians/lefthook
else
    echo "NPM no encontrado. Descargando el binario de Lefthook..."
    # Descarga directa del binario para entornos sin Node.js global
    curl -1sLf 'https://dl.cloudsmith.io/public/evilmartians/lefthook/setup.deb.sh' | sudo -E bash
    sudo apt install lefthook
fi

# Instalar los hooks en el repositorio de Git actual
lefthook install

echo "✅ ¡Barrera activada! A partir de ahora, todo 'git commit' será evaluado efímeramente por Docker."
exit 0
