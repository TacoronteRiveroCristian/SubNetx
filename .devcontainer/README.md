# Development Container para SubNetx

Este directorio contiene la configuración para un contenedor de desarrollo (devcontainer) que proporciona un entorno de desarrollo completo para Python con todas las herramientas necesarias para el proyecto SubNetx.

## Características

- Utiliza el mismo Dockerfile y docker-compose del proyecto base
- Mantiene la estructura de volúmenes existente en docker-compose.yaml
- Herramientas de desarrollo de Python instaladas en tiempo de ejecución:
  - black (formateador de código)
  - isort (organizador de importaciones)
  - mypy (verificador de tipos estáticos)
  - pylint (linter)
  - pytest (framework de pruebas)
  - flake8 (linter)
  - ipython (shell interactiva)
  - pre-commit (gestión de ganchos de pre-commit)

## Extensiones de VS Code preconfiguradas

- Python support (IntelliSense, debugging)
- Pylance (language server)
- Black formatter
- isort
- mypy
- Pylint
- Autodocstring
- Code Spell Checker
- Git integration tools
- Docker support
- y más...

## Cómo usar

1. Instale [Visual Studio Code](https://code.visualstudio.com/)
2. Instale la extensión [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Clonar este repositorio
4. Asegúrese de tener Docker y Docker Compose instalados y funcionando
5. Construya primero la imagen base con `docker-compose build`
6. Abra el repositorio en VS Code
7. Cuando VS Code detecte el archivo `.devcontainer/devcontainer.json`, le sugerirá "Reopen in Container". Haga clic en esta opción.
8. VS Code utilizará el contenedor existente y configurará las herramientas de desarrollo dentro de él.

Si no aparece el mensaje para reabrir en contenedor, puede:
- Hacer clic en el icono verde en la esquina inferior izquierda
- Seleccionar "Reopen in Container" desde la paleta de comandos (F1)

## Beneficios

- Entorno de desarrollo consistente para todos los desarrolladores
- Todas las herramientas y extensiones preconfiguradas
- Reutiliza la configuración Docker existente del proyecto
- Mantiene la estructura de volúmenes y directorios del proyecto
- Integración con las configuraciones existentes del proyecto (pyproject.toml)
- Aislamiento del sistema host

## Personalización

Si necesita personalizar el contenedor:
- Edite `devcontainer.json` para cambiar configuraciones de VS Code o añadir extensiones
- Modifique el script `post-create.sh` para instalar herramientas adicionales
