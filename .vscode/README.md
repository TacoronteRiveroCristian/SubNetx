# VS Code Configuration for Python Development

Esta configuración permite un entorno de desarrollo Python con buenas prácticas incluidas.

## Características

- Formateo automático con Black al guardar archivos
- Ordenación de imports con isort
- Verificación de tipos con mypy
- Linting con pylint
- Configuración de longitud máxima de línea a 88 caracteres
- Debugging avanzado con debugpy
- Mejoras de productividad y visuales

## Extensiones Recomendadas

El archivo `extensions.json` recomienda las siguientes extensiones:

### Extensiones core de Python
- **Python**: Soporte principal para Python
- **Pylance**: Servidor de lenguaje Python avanzado

### Formateo y linting
- **Black Formatter**: Formateador automático
- **Pylint**: Linter para análisis estático
- **Flake8**: Linter adicional
- **isort**: Ordenador de imports
- **mypy**: Verificador de tipos estáticos

### Debugging
- **debugpy**: Depurador avanzado para Python

### Docstrings y documentación
- **autoDocstring**: Generador automático de docstrings

### Git y Control de versiones
- **GitLens**: Mejoras de Git en VS Code

### Productividad
- **IntelliCode**: Autocompletado inteligente
- **Code Spell Checker**: Corrector ortográfico

### Mejoras de la interfaz
- **vscode-icons**: Iconos para archivos y carpetas
- **indent-rainbow**: Colores para niveles de indentación

## Instalación

1. Instalar las extensiones recomendadas (aparecerán como sugerencia al abrir el proyecto)
2. Instalar las dependencias de desarrollo:

```bash
pip install -r .vscode/requirements-dev.txt
```

## Uso

Simplemente guarda tus archivos Python (.py) y VS Code aplicará automáticamente:
- Formateo con Black
- Ordenación de imports con isort
- Verificación de linting con pylint
- Verificación de tipos con mypy

## Archivos de Configuración

Este proyecto incluye varios archivos de configuración para las herramientas de linting y formateo:

1. **pyproject.toml**: Configuración moderna para black, isort, mypy y pylint
2. **setup.cfg**: Configuración alternativa para flake8, mypy e isort
3. **.pylintrc**: Configuración detallada para pylint
4. **mypy.ini**: Configuración detallada para mypy

Puedes ajustar cada uno de estos archivos según tus necesidades específicas.

La configuración está diseñada para ser sencilla pero efectiva, siguiendo las mejores prácticas de Python.
