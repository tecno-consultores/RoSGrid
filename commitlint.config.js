module.exports = {
  // Extiende las reglas estándar de la industria (Conventional Commits)
  extends: ['@commitlint/config-conventional'],
  
  rules: {
    // 1. Tipos de commit permitidos (Qué se está haciendo)
    'type-enum': [
      2, // 2 = Nivel de error (Falla el commit si no cumple)
      'always',
      [
        'feat',     // Nueva característica (ej. nueva herramienta QA, nuevo orquestador)
        'fix',      // Corrección de un error (ej. reparar un script de limpieza)
        'docs',     // Cambios exclusivos en documentación (README, FAQ, SECURITY)
        'chore',    // Tareas de mantenimiento (actualización de dependencias, configuraciones)
        'style',    // Cambios estéticos de código (Prettier, ruff) que no alteran la lógica
        'refactor', // Refactorización de código (ni añade feature ni arregla bug)
        'ci',       // Cambios en los pipelines (.github/workflows)
        'test',     // Adición o corrección de pruebas faltantes
        'perf',     // Mejoras de rendimiento comprobables
        'revert'    // Revertir un commit previo
      ]
    ],
    
    // 2. Ámbitos permitidos (Dónde se está haciendo el cambio)
    // Adaptado estrictamente a las carpetas de tu repositorio
    'scope-enum': [
      2,
      'always',
      [
        'python',   // Cambios en la carpeta python/
        'fastapi',  // Cambios en la carpeta fastapi/
        'node',     // Cambios en la carpeta node-backend/
        'vue3',     // Cambios en la carpeta vue3/
        'bash',     // Cambios en la carpeta bash-scripts/
        'docs',     // Cambios en la carpeta docs/ o archivos .md globales
        'ci',       // Cambios en configuración de integración continua
        'global'    // Cambios que afectan a todo el repositorio
      ]
    ],
    
    // 3. Reglas sobre la descripción del commit (Subject)
    // El asunto no puede estar vacío, no puede ser mayúscula sostenida y no debe terminar en punto.
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'subject-case': [
      2,
      'never',
      ['upper-case', 'pascal-case', 'start-case'] // Obliga a iniciar en minúscula para mantener uniformidad
    ],
    
    // 4. Reglas estructurales
    'type-empty': [2, 'never'], // Siempre debe haber un tipo (feat, fix, etc.)
    'header-max-length': [2, 'always', 72] // Evita commits con títulos excesivamente largos
  }
};
