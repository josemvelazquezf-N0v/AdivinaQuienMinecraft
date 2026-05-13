import json
import os
import random
import uuid
import webbrowser
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(ROOT_DIR, 'Assets')
IMAGE_DIR = os.path.join(ASSETS_DIR, 'images')
if not os.path.isdir(IMAGE_DIR):
    IMAGE_DIR = os.path.join(ASSETS_DIR, 'Images')

SERVER_PORT = 8000
GAME_SESSIONS = {}


def read_file_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class Atributo:
    def __init__(self, id_atributo, pregunta, predicado):
        self.id = id_atributo
        self.pregunta = pregunta
        self.predicado = predicado


class JuegoAdivina:
    def __init__(self, ruta_json, ruta_frecuencias):
        self.ruta_json = ruta_json
        self.ruta_frecuencias = ruta_frecuencias
        self.frecuencias = self._cargar_frecuencias()
        self.bloques = self._cargar_bloques()
        self.atributos = self._crear_atributos()
        self.atributo_map = {atributo.id: atributo for atributo in self.atributos}

    def _cargar_frecuencias(self):
        if os.path.exists(self.ruta_frecuencias):
            try:
                with open(self.ruta_frecuencias, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _guardar_frecuencia(self, id_bloque):
        if id_bloque is None:
            return
        str_id = str(id_bloque)
        self.frecuencias[str_id] = self.frecuencias.get(str_id, 0) + 1
        with open(self.ruta_frecuencias, 'w', encoding='utf-8') as f:
            json.dump(self.frecuencias, f, indent=4)

    def _cargar_bloques(self):
        with open(self.ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        if isinstance(datos, dict) and 'bloques' in datos:
            bloques = datos['bloques']
        else:
            bloques = datos
        return [b for b in bloques if isinstance(b, dict)]

    def _crear_atributos(self):
        atributos = [
            Atributo('diggable', '¿Se puede romper o minar?', lambda b: bool(b.get('diggable', True))),
            Atributo('transparente', '¿Es transparente o deja pasar la luz (ej: vidrio, hojas)?', lambda b: bool(b.get('transparent'))),
            Atributo('emite_luz', '¿Emite luz propia?', lambda b: int(b.get('emitLight', 0)) > 0),
            Atributo('solido', '¿Es un bloque de forma completa (cubo sólido)?', lambda b: b.get('boundingBox') == 'block'),
            Atributo('stackable', '¿Se apila en grupos de 64?', lambda b: int(b.get('stackSize', 64)) > 1),
            Atributo('irrompible', '¿Es prácticamente irrompible (ej: Bedrock)?', lambda b: float(b.get('hardness', 0)) < 0),
            Atributo('es_madera', '¿Es un bloque de madera (tronco, tablones, etc)?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['wood', 'log', 'planks', 'oak', 'birch'])),
            Atributo('es_piedra', '¿Es un tipo de piedra, roca o mineral?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['stone', 'cobblestone', 'ore', 'granite', 'diorite', 'andesite', 'deepslate'])),
            Atributo('es_mineral', '¿Es un mineral precioso u obtenido de uno (hierro, oro, diamante)?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['ore', 'diamond', 'gold', 'iron', 'emerald', 'copper', 'lapis'])),
            Atributo('es_vegetacion', '¿Es vegetación, planta o parte de un árbol?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['leaves', 'flower', 'sapling', 'grass', 'plant'])),
            Atributo('del_nether', '¿Proviene de la dimensión del Nether?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['nether', 'soul', 'crimson', 'warped', 'quartz', 'blackstone', 'magma'])),
            Atributo('del_end', '¿Proviene de la dimensión del End?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['end', 'purpur', 'chorus', 'shulker'])),
            Atributo('redstone', '¿Es un componente de Redstone o mecanismo?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['redstone', 'piston', 'observer', 'repeater', 'comparator', 'dispenser', 'dropper', 'hopper'])),
            Atributo('utilidad', '¿Es un bloque funcional donde puedes interactuar (mesas, hornos, cofres)?', lambda b: any(p in str(b.get('name', '')).lower() for p in ['chest', 'table', 'furnace', 'anvil', 'barrel', 'smoker'])),
            Atributo('liquido', '¿Es un líquido (agua o lava)?', lambda b: b.get('name') in ('water', 'lava')),
        ]
        herramientas = [
            ('pickaxe', '¿Se rompe más rápido usando un PICO?'),
            ('shovel', '¿Se rompe más rápido usando una PALA?'),
            ('axe', '¿Se rompe más rápido usando un HACHA?'),
            ('hoe', '¿Se rompe más rápido usando una AZADA?'),
        ]
        for herramienta, pregunta in herramientas:
            atributos.append(
                Atributo(
                    f'herramienta_{herramienta}',
                    pregunta,
                    lambda b, h=herramienta: h in str(b.get('material', '')).lower()
                )
            )
        return atributos

    def nombre_bloque(self, bloque):
        return str(bloque.get('displayName') or bloque.get('name') or bloque.get('nombre') or 'Bloque desconocido')

    def obtener_mejor_atributo(self, indices, atributos):
        mejor_atributo = None
        mejor_diferencia = float('inf')
        mitad = len(indices) / 2
        for atributo in atributos:
            verdadero = sum(1 for index in indices if atributo.predicado(self.bloques[index]))
            if verdadero == 0 or verdadero == len(indices):
                continue
            diferencia = abs(mitad - verdadero)
            if diferencia < mejor_diferencia:
                mejor_diferencia = diferencia
                mejor_atributo = atributo
        return mejor_atributo

    def filtrar_indices(self, indices, atributo, tiene):
        return [index for index in indices if atributo.predicado(self.bloques[index]) == tiene]

    def frecuencia_bloque(self, bloque):
        bloque_id = bloque.get('id')
        if bloque_id is None:
            return 0
        return int(self.frecuencias.get(str(bloque_id), 0))

    def buscar_imagen(self, bloque):
        if bloque is None:
            return None
        nombres = []
        nombre_raw = str(bloque.get('name') or bloque.get('id') or bloque.get('displayName') or '')
        nombre_raw = nombre_raw.replace(':', '_').replace(' ', '_').lower()
        if nombre_raw:
            if not nombre_raw.startswith('minecraft_'):
                nombres.append(f'minecraft_{nombre_raw}.png')
            nombres.append(f'{nombre_raw}.png')
        if bloque.get('id') is not None:
            nombres.append(f'{bloque.get("id")}.png')
        if bloque.get('displayName'):
            display_name = str(bloque.get('displayName')).replace(' ', '_').lower()
            nombres.append(f'{display_name}.png')
        for nombre_archivo in nombres:
            ruta = os.path.join(IMAGE_DIR, nombre_archivo)
            if os.path.exists(ruta):
                return f'/assets/images/{nombre_archivo}'
        desconocido = os.path.join(IMAGE_DIR, 'canUse_unknown.png')
        if os.path.exists(desconocido):
            return '/assets/images/canUse_unknown.png'
        return None


class GameServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, juego=None, **kwargs):
        self.juego = juego
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        if path == '/':
            self.respond_html('templates/index.html')
            return
        if path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        if path == '/api/start':
            self.handle_start(query)
            return
        if path == '/api/possible':
            self.handle_possible(query)
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/respond':
            self.handle_respond()
            return
        if parsed.path == '/api/human/question':
            self.handle_human_question()
            return
        if parsed.path == '/api/human/guess':
            self.handle_human_guess()
            return
        self.send_error(404, 'Endpoint no encontrado')

    def respond_html(self, relative_path):
        filepath = os.path.join(ROOT_DIR, relative_path)
        if not os.path.exists(filepath):
            self.send_error(404, 'Archivo no encontrado')
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(read_file_text(filepath).encode('utf-8'))

    def handle_start(self, query):
        mode = query.get('mode', ['machine'])[0]
        if mode not in ('machine', 'human'):
            self.send_json({'error': 'Modo inválido'}, 400)
            return
        session_id = str(uuid.uuid4())
        session = {
            'mode': mode,
            'posibles': list(range(len(self.juego.bloques))),
            'atributos_disponibles': [atributo.id for atributo in self.juego.atributos],
            'atributos_usados': [],
            'current_question': None,
            'current_guess': None,
            'phase': 'question',
            'secret': None,
        }
        if mode == 'human':
            session['secret'] = random.randrange(len(self.juego.bloques))
        GAME_SESSIONS[session_id] = session
        if mode == 'machine':
            payload = self.build_machine_question(session)
        else:
            payload = {
                'attributes': [
                    {'id': atributo.id, 'pregunta': atributo.pregunta}
                    for atributo in self.juego.atributos
                ],
                'possibleCount': len(session['posibles']),
                'message': 'Elige un atributo para preguntar. El secreto está en memoria, no hay imagen aún.',
            }
        payload['stateId'] = session_id
        payload['possibleBlocks'] = self.format_possible_blocks(session)
        self.send_json(payload)

    def handle_possible(self, query):
        state_id = query.get('state_id', [None])[0]
        session = GAME_SESSIONS.get(state_id)
        if session is None:
            self.send_json({'error': 'Sesión no encontrada'}, 404)
            return
        self.send_json({
            'possibleCount': len(session['posibles']),
            'possibleBlocks': self.format_possible_blocks(session),
        })

    def format_possible_blocks(self, session, limit=50):
        bloques = []
        for index in session['posibles'][:limit]:
            bloque = self.juego.bloques[index]
            bloques.append({
                'name': self.juego.nombre_bloque(bloque),
                'imageUrl': self.juego.buscar_imagen(bloque) or '/assets/images/canUse_unknown.png',
                'index': index,
            })
        return bloques

    def handle_respond(self):
        body = self.read_json_body()
        if body is None:
            return
        state_id = body.get('state_id')
        answer = body.get('answer')
        session = GAME_SESSIONS.get(state_id)
        if session is None:
            self.send_json({'error': 'Sesión no encontrada'}, 404)
            return
        if session['mode'] != 'machine':
            self.send_json({'error': 'Sesión no es de modo máquina'}, 400)
            return
        if session['phase'] == 'guess' and session['current_guess'] is not None:
            response = self.process_machine_guess(session, answer)
            response['possibleBlocks'] = self.format_possible_blocks(session)
            self.send_json(response)
            return
        if session['current_question'] is None:
            self.send_json({'error': 'No hay pregunta activa'}, 400)
            return
        atributo = self.juego.atributo_map.get(session['current_question'])
        if atributo is None:
            self.send_json({'error': 'Atributo no válido'}, 400)
            return
        session['posibles'] = self.juego.filtrar_indices(session['posibles'], atributo, bool(answer))
        session['atributos_usados'].append(atributo.id)
        session['current_question'] = None
        if len(session['posibles']) == 0:
            self.send_json({
                'message': 'No pude adivinar el bloque con esas respuestas.',
                'possibleCount': 0,
                'possibleBlocks': self.format_possible_blocks(session),
            })
            return
        if len(session['posibles']) == 1:
            response = self.prepare_machine_guess(session)
            response['possibleBlocks'] = self.format_possible_blocks(session)
            self.send_json(response)
            return
        remaining_attrs = [self.juego.atributo_map[a_id] for a_id in session['atributos_disponibles'] if a_id not in session['atributos_usados']]
        if not remaining_attrs:
            response = self.prepare_machine_guess(session)
            response['possibleBlocks'] = self.format_possible_blocks(session)
            self.send_json(response)
            return
        response = self.build_machine_question(session)
        response['possibleBlocks'] = self.format_possible_blocks(session)
        self.send_json(response)

    def handle_human_question(self):
        body = self.read_json_body()
        if body is None:
            return
        state_id = body.get('state_id')
        atributo_id = body.get('attribute_id')
        session = GAME_SESSIONS.get(state_id)
        if session is None:
            self.send_json({'error': 'Sesión no encontrada'}, 404)
            return
        if session['mode'] != 'human':
            self.send_json({'error': 'Sesión no es de modo humano'}, 400)
            return
        atributo = self.juego.atributo_map.get(atributo_id)
        if atributo is None:
            self.send_json({'error': 'Atributo no válido'}, 400)
            return
        secreto = self.juego.bloques[session['secret']]
        respuesta = atributo.predicado(secreto)
        session['posibles'] = self.juego.filtrar_indices(session['posibles'], atributo, respuesta)
        session['atributos_usados'].append(atributo.id)
        session['atributos_disponibles'] = [aid for aid in session['atributos_disponibles'] if aid != atributo.id]
        payload = {
            'answer': respuesta,
            'possibleCount': len(session['posibles']),
            'message': f"Respuesta de la IA: {'Sí' if respuesta else 'No'}. Ahora quedan {len(session['posibles'])} bloques posibles.",
        }
        if len(session['posibles']) == 1:
            bloque = self.juego.bloques[session['posibles'][0]]
            payload['probableBlock'] = self.juego.nombre_bloque(bloque)
            payload['imageUrl'] = self.juego.buscar_imagen(bloque)
        payload['possibleBlocks'] = self.format_possible_blocks(session)
        self.send_json(payload)

    def handle_human_guess(self):
        body = self.read_json_body()
        if body is None:
            return
        state_id = body.get('state_id')
        guess = str(body.get('guess', '')).strip().lower()
        session = GAME_SESSIONS.get(state_id)
        if session is None:
            self.send_json({'error': 'Sesión no encontrada'}, 404)
            return
        if session['mode'] != 'human':
            self.send_json({'error': 'Sesión no es de modo humano'}, 400)
            return
        secreto = self.juego.bloques[session['secret']]
        correct = guess == self.juego.nombre_bloque(secreto).lower() or guess == str(secreto.get('name', '')).lower()
        payload = {
            'correct': correct,
            'blockName': self.juego.nombre_bloque(secreto),
            'imageUrl': self.juego.buscar_imagen(secreto),
            'possibleBlocks': self.format_possible_blocks(session),
        }
        if not correct:
            payload['message'] = 'No es correcto. Sigue preguntando o revisa los bloques posibles.'
        else:
            payload['message'] = '¡Correcto! Has adivinado el bloque secreto.'
        self.send_json(payload)

    def build_machine_question(self, session):
        remaining_attrs = [self.juego.atributo_map[a_id] for a_id in session['atributos_disponibles'] if a_id not in session['atributos_usados']]
        pregunta = self.juego.obtener_mejor_atributo(session['posibles'], remaining_attrs)
        if pregunta is None:
            return self.prepare_machine_guess(session)
        session['current_question'] = pregunta.id
        session['phase'] = 'question'
        return {
            'phase': 'question',
            'question': pregunta.pregunta,
            'possibleCount': len(session['posibles']),
            'message': 'Responde sí o no para que la IA reduzca las opciones.',
            'remainingAttributes': len(remaining_attrs),
        }

    def prepare_machine_guess(self, session):
        if not session['posibles']:
            return {'message': 'No pude adivinar con certeza.', 'possibleCount': 0}
        session['phase'] = 'guess'
        sorted_posibles = sorted(
            session['posibles'],
            key=lambda index: self.juego.frecuencia_bloque(self.juego.bloques[index]),
            reverse=True
        )
        session['current_guess'] = sorted_posibles[0]
        bloque = self.juego.bloques[session['current_guess']]
        image_url = self.juego.buscar_imagen(bloque)
        return {
            'phase': 'guess',
            'guess': self.juego.nombre_bloque(bloque),
            'imageUrl': image_url,
            'possibleCount': len(session['posibles']),
            'message': '¿Es este tu bloque? Responde sí o no.',
        }

    def process_machine_guess(self, session, answer):
        if answer:
            bloque = self.juego.bloques[session['current_guess']]
            self.juego._guardar_frecuencia(bloque.get('id'))
            image_url = self.juego.buscar_imagen(bloque)
            return {
                'correct': True,
                'message': f'¡La IA adivinó tu bloque: {self.juego.nombre_bloque(bloque)}!',
                'blockName': self.juego.nombre_bloque(bloque),
                'imageUrl': image_url,
                'possibleCount': len(session['posibles']),
            }
        if session['current_guess'] in session['posibles']:
            session['posibles'].remove(session['current_guess'])
        session['current_guess'] = None
        if not session['posibles']:
            return {'message': 'No pude adivinar con certeza.', 'possibleCount': 0}
        if len(session['posibles']) == 1:
            return self.prepare_machine_guess(session)
        return self.build_machine_question(session)

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length <= 0:
            self.send_json({'error': 'Cuerpo JSON vacío'}, 400)
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            self.send_json({'error': 'JSON inválido'}, 400)
            return None


def run_server(juego):
    os.chdir(ROOT_DIR)
    handler = lambda *args, **kwargs: GameServerHandler(*args, juego=juego, **kwargs)
    server = ThreadingHTTPServer(('127.0.0.1', SERVER_PORT), handler)
    url = f'http://127.0.0.1:{SERVER_PORT}/'
    print(f'Abriendo en el navegador: {url}')
    try:
        webbrowser.open(url)
    except Exception:
        print('No se pudo abrir el navegador automáticamente.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')


if __name__ == '__main__':
    ruta_json = os.path.join(ROOT_DIR, 'Assets', 'blocks.json')
    ruta_frecuencias = os.path.join(ROOT_DIR, 'Assets', 'frecuencias.json')
    juego = JuegoAdivina(ruta_json, ruta_frecuencias)
    run_server(juego)
