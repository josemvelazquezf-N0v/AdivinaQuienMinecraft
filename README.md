# Adivina Quien: Minecraft Edition

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Minecraft](https://img.shields.io/badge/Minecraft-1.20+-62B037?style=for-the-badge&logo=minecraft&logoColor=white)
![Status](https://img.shields.io/badge/Status-Interactivo-yellow?style=for-the-badge)

Un juego de deducción lógica inspirado en Minecraft, que funciona como una aplicación web local y permite jugar con imágenes de bloques. El proyecto incluye:

- Interfaz gráfica en el navegador.
- Servidor Python para manejar la lógica y las imágenes.
- Galería de bloques cargada desde `Assets/blocks.json`.
- Modo IA vs Humano y modo Humano vs IA.
- Lanzador `jugar.bat` para iniciar sin abrir Visual Studio Code.

---

## Como Jugar

### 1. Requisitos Previos
Asegúrate de tener:

- Python 3 instalado.
- La carpeta del proyecto con `main.py`, `templates/`, `Assets/` y `Assets/images/`.
- El archivo `Assets/blocks.json` con los bloques y sus datos.

### 2. Ejecución
Puedes iniciar el juego de dos maneras:

#### Opción 1: Doble clic
Ejecuta `jugar.bat` desde la carpeta raíz del proyecto.

#### Opción 2: Terminal
Abre la terminal en la carpeta del proyecto y ejecuta:
```bash
python main.py
```

Después de iniciar, abre el navegador en la dirección que muestra el servidor (normalmente `http://localhost:8000`).

### 3. Modos de Juego
#### La Máquina Adivina
- Tú piensas en un bloque de la lista.
- La IA hace preguntas de sí/no.
- Responde con `s` o `n`.
- La IA usa las frecuencias históricas para mejorar sus elecciones.

#### El Humano Adivina
- La IA selecciona un bloque secreto.
- Tú preguntas por atributos o seleccionas directamente la imagen del bloque.
- El juego muestra los bloques posibles según tus pistas.
- Puedes adivinar usando la galería de imágenes.

---

## Características Principales

- Interfaz web local moderna con imágenes de bloques.
- Soporte para seleccionar bloques desde la galería en el modo humano.
- Motor de deducción basado en atributos y frecuencias.
- Aprendizaje básico: `Assets/frecuencias.json` registra qué bloques son más populares.
- Limpieza de recursos: solo se usan imágenes que aparecen en `Assets/blocks.json`.

### Archivos clave

- `main.py`: servidor Python y lógica principal del juego.
- `templates/index.html`: interfaz del juego en el navegador.
- `Assets/blocks.json`: datos de bloques y atributos.
- `Assets/frecuencias.json`: puntos de popularidad para mejorar la IA.
- `Assets/images/`: imágenes usadas en la galería.
- `jugar.bat`: lanzador para iniciar el juego fácilmente.

---

## El Cerebro de la IA: `frecuencias.json`

Este proyecto usa un sistema simple de aprendizaje por refuerzo:

- Cada vez que la IA adivina correctamente en el modo "La Máquina Adivina", el bloque elegido gana frecuencia.
- Cuando varios bloques comparten atributos, la IA prioriza los más populares.
- Esto permite que el juego se adapte a los bloques que los jugadores eligen con más frecuencia.

---

## Atributos Analizados

El motor de búsqueda filtra los bloques usando las siguientes categorías:

- Física: solidez, transparencia, emisión de luz.
- Dimensiones: origen en Overworld, Nether o End.
- Herramientas: pico, pala, hacha o azada requerida.
- Categorías: madera, roca, mineral, vegetación, redstone, etc.

---

## Nota

El proyecto está diseñado para ejecutarse localmente en el equipo del usuario. No requiere conexión a Internet, excepto para descargar Python si aún no está instalado.
