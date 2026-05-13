import json
import os
import random
import tkinter as tk
from tkinter import messagebox

class Atributo:
    def __init__(self, id_atributo, pregunta, predicado):
        self.id = id_atributo
        self.pregunta = pregunta
        self.predicado = predicado

class JuegoAdivina:
    IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'Assets', 'images')

    def __init__(self, ruta_json, ruta_frecuencias):
        self.ruta_json = ruta_json
        self.ruta_frecuencias = ruta_frecuencias
        self.frecuencias = self._cargar_frecuencias()
        self.bloques = self._cargar_bloques()
        self.atributos = self._crear_atributos()
        self.imagen_cache = {}
        os.makedirs(self.IMAGE_DIR, exist_ok=True)
        self.reset()

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

    def reset(self):
        self.posibles_bloques = self.bloques.copy()
        self.atributos_usados = set()

    def _crear_atributos(self):
        atributos = [
            Atributo('diggable', '¿Se puede romper o minar?', lambda b: bool(b.get('diggable', True))),
            Atributo('transparente', '¿Es transparente o deja pasar la luz (ej: vidrio, hojas)?', lambda b: bool(b.get('transparent'))),
            Atributo('emite_luz', '¿Emite luz propia?', lambda b: int(b.get('emitLight', 0)) > 0),
            Atributo('solido', '¿Es un bloque de forma completa (cubo sólido)?', lambda b: b.get('boundingBox') == 'block'),
            Atributo('stackable', '¿Se apila en grupos de 64?', lambda b: int(b.get('stackSize', 64)) > 1),
            Atributo('irrompible', '¿Es prácticamente irrompible (ej: Bedrock)?', lambda b: float(b.get('hardness', 0)) < 0),
            Atributo('es_madera', '¿Es un bloque de madera (tronco, tablones, etc)?', lambda b: any(p in str(b.get('name','')).lower() for p in ['wood', 'log', 'planks', 'oak', 'birch'])),
            Atributo('es_piedra', '¿Es un tipo de piedra, roca o mineral?', lambda b: any(p in str(b.get('name','')).lower() for p in ['stone', 'cobblestone', 'ore', 'granite', 'diorite', 'andesite', 'deepslate'])),
            Atributo('es_mineral', '¿Es un mineral precioso u obtenido de uno (hierro, oro, diamante)?', lambda b: any(p in str(b.get('name','')).lower() for p in ['ore', 'diamond', 'gold', 'iron', 'emerald', 'copper', 'lapis'])),
            Atributo('es_vegetacion', '¿Es vegetación, planta o parte de un árbol?', lambda b: any(p in str(b.get('name','')).lower() for p in ['leaves', 'flower', 'sapling', 'grass', 'plant'])),
            Atributo('del_nether', '¿Proviene de la dimensión del Nether?', lambda b: any(p in str(b.get('name','')).lower() for p in ['nether', 'soul', 'crimson', 'warped', 'quartz', 'blackstone', 'magma'])),
            Atributo('del_end', '¿Proviene de la dimensión del End?', lambda b: any(p in str(b.get('name','')).lower() for p in ['end', 'purpur', 'chorus', 'shulker'])),
            Atributo('redstone', '¿Es un componente de Redstone o mecanismo?', lambda b: any(p in str(b.get('name','')).lower() for p in ['redstone', 'piston', 'observer', 'repeater', 'comparator', 'dispenser', 'dropper', 'hopper'])),
            Atributo('utilidad', '¿Es un bloque funcional donde puedes interactuar (mesas, hornos, cofres)?', lambda b: any(p in str(b.get('name','')).lower() for p in ['chest', 'table', 'furnace', 'anvil', 'barrel', 'smoker'])),
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

    def obtener_mejor_atributo(self, bloques, atributos):
        mejor_atributo = None
        mejor_diferencia = float('inf')
        mitad = len(bloques) / 2

        for atributo in atributos:
            verdadero = sum(1 for b in bloques if atributo.predicado(b))
            if verdadero == 0 or verdadero == len(bloques):
                continue

            diferencia = abs(mitad - verdadero)
            if diferencia < mejor_diferencia:
                mejor_diferencia = diferencia
                mejor_atributo = atributo

        return mejor_atributo

    def filtrar_bloques(self, atributo, tiene):
        self.posibles_bloques = [
            b for b in self.posibles_bloques
            if atributo.predicado(b) == tiene
        ]
        self.atributos_usados.add(atributo.id)

    def nombre_bloque(self, bloque):
        return str(bloque.get('displayName') or bloque.get('name') or bloque.get('nombre'))

    def cargar_imagen_bloque(self, bloque):
        if bloque is None:
            return None

        claves = []
        if bloque.get('id') is not None:
            claves.append(str(bloque.get('id')))
        if bloque.get('name'):
            claves.append(str(bloque.get('name')))
        if bloque.get('displayName'):
            claves.append(str(bloque.get('displayName')))

        for clave in claves:
            if clave in self.imagen_cache:
                return self.imagen_cache[clave]

            nombre_archivo = f'{clave}.png'
            ruta = os.path.join(self.IMAGE_DIR, nombre_archivo)
            if os.path.exists(ruta):
                try:
                    imagen = tk.PhotoImage(file=ruta)
                    self.imagen_cache[clave] = imagen
                    return imagen
                except Exception:
                    continue

        return None

class JuegoAdivinaGUI:
    def __init__(self, juego):
        self.juego = juego
        self.root = tk.Tk()
        self.root.title('Adivina Quién - Minecraft')
        self.root.geometry('980x700')
        self.current_image = None
        self.modo = None
        self.atributos_disponibles = []
        self.bloque_secreto = None
        self.pregunta_actual = None

        self._crear_widgets()
        self._mostrar_pantalla_inicio()
        self.root.mainloop()

    def _crear_widgets(self):
        self.frame_top = tk.Frame(self.root, bg='#111', height=80)
        self.frame_top.pack(fill=tk.X)

        self.label_title = tk.Label(
            self.frame_top,
            text='Adivina Quién Minecraft',
            bg='#111',
            fg='white',
            font=('Segoe UI', 24, 'bold')
        )
        self.label_title.pack(pady=12)

        self.frame_main = tk.Frame(self.root, bg='#222')
        self.frame_main.pack(fill=tk.BOTH, expand=True)

        self.frame_left = tk.Frame(self.frame_main, bg='#222')
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.frame_right = tk.Frame(self.frame_main, bg='#222')
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.canvas = tk.Canvas(self.frame_left, width=420, height=420, bg='black', highlightthickness=0)
        self.canvas.pack(pady=10)

        self.label_info = tk.Label(
            self.frame_left,
            text='',
            bg='#222',
            fg='white',
            font=('Segoe UI', 12)
        )
        self.label_info.pack(pady=6)

        self.frame_controls = tk.Frame(self.frame_left, bg='#222')
        self.frame_controls.pack(fill=tk.BOTH, expand=True)

        self.label_question = tk.Label(
            self.frame_controls,
            text='',
            bg='#222',
            fg='white',
            font=('Segoe UI', 16, 'bold'),
            wraplength=420,
            justify='center'
        )

        self.button_yes = tk.Button(
            self.frame_controls,
            text='Sí',
            width=12,
            command=lambda: self._responder(True),
            bg='#4CAF50',
            fg='white'
        )
        self.button_no = tk.Button(
            self.frame_controls,
            text='No',
            width=12,
            command=lambda: self._responder(False),
            bg='#F44336',
            fg='white'
        )

        self.button_back = tk.Button(
            self.frame_controls,
            text='Volver al menú',
            width=18,
            command=self._mostrar_pantalla_inicio,
            bg='#555',
            fg='white'
        )

        self.list_atributos = tk.Listbox(
            self.frame_controls,
            width=60,
            height=12,
            bg='#333',
            fg='white',
            selectbackground='#555',
            relief=tk.FLAT
        )

        self.button_ask = tk.Button(
            self.frame_controls,
            text='Preguntar atributo',
            width=20,
            command=self._preguntar_atributo,
            bg='#2196F3',
            fg='white'
        )

        self.button_show_list = tk.Button(
            self.frame_controls,
            text='Mostrar posibles',
            width=20,
            command=self._mostrar_lista_posibles,
            bg='#FF9800',
            fg='white'
        )

        self.button_surrender = tk.Button(
            self.frame_controls,
            text='Rendirse',
            width=20,
            command=self._rendirse,
            bg='#9C27B0',
            fg='white'
        )

        self.entry_guess = tk.Entry(self.frame_controls, width=40, bg='#333', fg='white', insertbackground='white')
        self.button_guess = tk.Button(
            self.frame_controls,
            text='Adivinar bloque',
            width=20,
            command=self._intentar_adivinar,
            bg='#009688',
            fg='white'
        )

        self.label_answer = tk.Label(
            self.frame_controls,
            text='',
            bg='#222',
            fg='white',
            font=('Segoe UI', 12),
            wraplength=420,
            justify='center'
        )

        self.frame_start = tk.Frame(self.frame_right, bg='#222')
        self.frame_start.pack(fill=tk.BOTH, expand=True)

        self.label_start = tk.Label(
            self.frame_start,
            text='Selecciona un modo para comenzar a jugar:',
            bg='#222',
            fg='white',
            font=('Segoe UI', 16)
        )
        self.label_start.pack(pady=20)

        self.button_machine = tk.Button(
            self.frame_start,
            text='La máquina adivina',
            width=24,
            height=2,
            command=self._iniciar_modo_maquina,
            bg='#4CAF50',
            fg='white'
        )
        self.button_machine.pack(pady=10)

        self.button_human = tk.Button(
            self.frame_start,
            text='El humano adivina',
            width=24,
            height=2,
            command=self._iniciar_modo_humano,
            bg='#2196F3',
            fg='white'
        )
        self.button_human.pack(pady=10)

        self.label_image_info = tk.Label(
            self.frame_right,
            text='Coloca imágenes PNG dentro de Assets/images/ usando el ID o el nombre del bloque.',
            wraplength=260,
            bg='#222',
            fg='white',
            font=('Segoe UI', 11)
        )
        self.label_image_info.pack(pady=20)

    def _mostrar_pantalla_inicio(self):
        self.modo = None
        self._ocultar_controles()
        self.frame_start.pack(fill=tk.BOTH, expand=True)
        self.label_info.config(text='')
        self._mostrar_imagen_bloque(None, 'Bienvenido')

    def _ocultar_controles(self):
        self.frame_start.pack_forget()
        for widget in [
            self.label_question, self.button_yes, self.button_no,
            self.list_atributos, self.button_ask, self.button_show_list,
            self.button_surrender, self.entry_guess, self.button_guess,
            self.label_answer, self.button_back
        ]:
            widget.pack_forget()

    def _mostrar_imagen_bloque(self, bloque, titulo='Imagen disponible'):
        self.canvas.delete('all')
        imagen = self.juego.cargar_imagen_bloque(bloque)
        if imagen:
            self.current_image = imagen
            self.canvas.create_image(210, 210, image=imagen)
            self.canvas.create_text(210, 390, text=self.juego.nombre_bloque(bloque), fill='white', font=('Segoe UI', 14, 'bold'))
            return

        self.canvas.create_rectangle(20, 20, 400, 400, outline='#666', width=4)
        self.canvas.create_text(210, 180, text=titulo, fill='white', font=('Segoe UI', 20, 'bold'))
        if bloque is not None:
            self.canvas.create_text(210, 260, text=self.juego.nombre_bloque(bloque), fill='#bbb', font=('Segoe UI', 14))
        else:
            self.canvas.create_text(210, 260, text='Agrega imágenes PNG en Assets/images/', fill='#bbb', font=('Segoe UI', 12), width=360)

    def _iniciar_modo_maquina(self):
        self.juego.reset()
        self.atributos_disponibles = self.juego.atributos.copy()
        self.modo = 'maquina'
        self.frame_start.pack_forget()
        self._ocultar_controles()
        self.label_question.pack(pady=12)
        self.button_yes.pack(side=tk.LEFT, padx=10, pady=8)
        self.button_no.pack(side=tk.LEFT, padx=10, pady=8)
        self.label_answer.pack(pady=10)
        self.button_back.pack(pady=12)
        self.label_question.config(text='Piensa en un bloque y responde las preguntas de la IA.')
        self.label_answer.config(text='')
        self._actualizar_estado_maquina()

    def _iniciar_modo_humano(self):
        self.juego.reset()
        self.juego.posibles_bloques = self.juego.bloques.copy()
        self.atributos_disponibles = self.juego.atributos.copy()
        self.bloque_secreto = random.choice(self.juego.bloques)
        self.modo = 'humano'
        self.frame_start.pack_forget()
        self._ocultar_controles()
        self.label_question.pack(pady=12)
        self.list_atributos.pack(pady=8)
        self.button_ask.pack(pady=6)
        self.button_show_list.pack(pady=6)
        self.entry_guess.pack(pady=6)
        self.button_guess.pack(pady=6)
        self.button_surrender.pack(pady=6)
        self.button_back.pack(pady=12)
        self.label_answer.pack(pady=10)
        self.label_question.config(text='He pensado un bloque. Elige un atributo para preguntar.')
        self.label_answer.config(text='')
        self._llenar_lista_atributos()
        self._mostrar_imagen_bloque(None, 'Modo humano activo')
        self._actualizar_info('Opciones posibles: ' + str(len(self.juego.posibles_bloques)))

    def _llenar_lista_atributos(self):
        self.list_atributos.delete(0, tk.END)
        for atributo in self.atributos_disponibles:
            self.list_atributos.insert(tk.END, f'{atributo.id}: {atributo.pregunta}')

    def _actualizar_estado_maquina(self):
        if len(self.juego.posibles_bloques) <= 1 or not self.atributos_disponibles:
            self._finalizar_modo_maquina()
            return

        self.pregunta_actual = self.juego.obtener_mejor_atributo(self.juego.posibles_bloques, self.atributos_disponibles)
        if not self.pregunta_actual:
            self._finalizar_modo_maquina()
            return

        self.label_question.config(text=self.pregunta_actual.pregunta)
        self._actualizar_info(f'Opciones posibles: {len(self.juego.posibles_bloques)}')
        self.label_answer.config(text='')
        self._mostrar_imagen_bloque(None, 'Adivina el bloque')

    def _responder(self, respuesta):
        if self.modo != 'maquina' or self.pregunta_actual is None:
            return

        self.juego.filtrar_bloques(self.pregunta_actual, respuesta)
        self.atributos_disponibles = [a for a in self.atributos_disponibles if a.id != self.pregunta_actual.id]

        if len(self.juego.posibles_bloques) == 1:
            self._mostrar_adivinanza_final(self.juego.posibles_bloques[0])
            return

        if not self.atributos_disponibles:
            self._finalizar_modo_maquina()
            return

        self._actualizar_estado_maquina()

    def _finalizar_modo_maquina(self):
        if not self.juego.posibles_bloques:
            self.label_question.config(text='No pude adivinar el bloque con esas respuestas.')
            self._actualizar_info('Reinicia para intentar otra vez.')
            self._mostrar_imagen_bloque(None, 'Sin resultado')
            return

        bloque = self.juego.posibles_bloques[0]
        self._mostrar_adivinanza_final(bloque)

    def _mostrar_adivinanza_final(self, bloque):
        nombre = self.juego.nombre_bloque(bloque)
        self.label_question.config(text=f'¿Tu bloque es {nombre}?')
        self.label_answer.config(text='Pulsa Sí si es correcto, No si no lo es.')
        self._mostrar_imagen_bloque(bloque, '¿Es este?')
        self.button_yes.config(command=lambda: self._confirmar_adivinanza(True))
        self.button_no.config(command=lambda: self._confirmar_adivinanza(False))
        self.button_yes.pack(side=tk.LEFT, padx=10, pady=8)
        self.button_no.pack(side=tk.LEFT, padx=10, pady=8)

    def _confirmar_adivinanza(self, acierto):
        if acierto:
            bloque = self.juego.posibles_bloques[0] if self.juego.posibles_bloques else None
            if bloque:
                self.juego._guardar_frecuencia(bloque.get('id'))
            self.label_question.config(text='¡Perfecto! La IA adivinó tu bloque.')
            self.label_answer.config(text='Gracias por jugar. Puedes volver al menú para otra partida.')
        else:
            if len(self.juego.posibles_bloques) > 1:
                self.juego.posibles_bloques.pop(0)
            self.label_question.config(text='No acertó. Intentaré con la siguiente opción.')
            self._actualizar_estado_maquina()

    def _preguntar_atributo(self):
        seleccion = self.list_atributos.curselection()
        if not seleccion:
            messagebox.showwarning('Selecciona un atributo', 'Debes elegir un atributo antes de preguntar.')
            return

        indice = seleccion[0]
        atributo = self.atributos_disponibles[indice]
        respuesta = atributo.predicado(self.bloque_secreto)
        self.juego.filtrar_bloques(atributo, respuesta)
        self.atributos_disponibles.pop(indice)
        texto = 'Sí.' if respuesta else 'No.'
        self.label_answer.config(text=f'IA: {texto}')
        self._actualizar_info(f'Opciones posibles: {len(self.juego.posibles_bloques)}')
        self._llenar_lista_atributos()

        if len(self.juego.posibles_bloques) == 1:
            self._mostrar_imagen_bloque(self.juego.posibles_bloques[0], 'Bloque probable')

    def _mostrar_lista_posibles(self):
        nombres = [self.juego.nombre_bloque(b) for b in self.juego.posibles_bloques[:50]]
        if not nombres:
            messagebox.showinfo('Posibles', 'No quedan bloques posibles.')
            return
        texto = '\n'.join(nombres)
        if len(self.juego.posibles_bloques) > 50:
            texto += '\n...'
        messagebox.showinfo('Bloques posibles', texto)

    def _rendirse(self):
        if self.bloque_secreto is None:
            return
        nombre = self.juego.nombre_bloque(self.bloque_secreto)
        self.label_question.config(text=f'El bloque secreto era: {nombre}')
        self.label_answer.config(text='Fin de la partida. Intenta nuevamente si quieres.')
        self._mostrar_imagen_bloque(self.bloque_secreto, 'Se reveló')

    def _intentar_adivinar(self):
        intento = self.entry_guess.get().strip().lower()
        if not intento:
            messagebox.showwarning('Adivinar', 'Escribe el nombre del bloque primero.')
            return

        nombre_real = self.juego.nombre_bloque(self.bloque_secreto).lower()
        referencia = str(self.bloque_secreto.get('name', '')).lower()
        if intento == nombre_real or intento == referencia:
            self.label_answer.config(text='¡Correcto! Has adivinado el bloque secreto.')
            self._mostrar_imagen_bloque(self.bloque_secreto, 'Correcto')
        else:
            self.label_answer.config(text=f'No es correcto. Sigue intentando o mira la lista de posibles.')
            self.entry_guess.delete(0, tk.END)

    def _actualizar_info(self, texto):
        self.label_info.config(text=texto)

if __name__ == '__main__':
    ruta_base = os.path.dirname(__file__)
    ruta_json = os.path.join(ruta_base, 'Assets', 'blocks.json')
    ruta_frecuencias = os.path.join(ruta_base, 'Assets', 'frecuencias.json')

    juego = JuegoAdivina(ruta_json, ruta_frecuencias)
    try:
        JuegoAdivinaGUI(juego)
    except Exception as e:
        print('No fue posible iniciar la interfaz gráfica:', e)
        print('Usa el modo terminal con el archivo actual o instala Tkinter.')

if __name__ == '__main__':
    # Rutas dinámicas para la carpeta Assets
    ruta_assets = os.path.join(os.path.dirname(__file__), 'Assets')
    if not os.path.exists(ruta_assets):
        os.makedirs(ruta_assets)
        
    ruta_archivo = os.path.join(ruta_assets, 'blocks.json')
    ruta_frecuencias = os.path.join(ruta_assets, 'frecuencias.json')
    
    juego = JuegoAdivina(ruta_archivo, ruta_frecuencias)

    print('Bienvenido a Adivina Quién con bloques de Minecraft (terminal).')
    while True:
        modo = input('\nElige el modo:\n1) Máquina adivina\n2) Humano adivina\n3) Salir\nTu opción: ').strip()
        if modo == '1':
            juego.modo_maquina_adivina()
        elif modo == '2':
            secreto = random.choice(juego.bloques)
            juego.modo_humano_adivina(secreto)
        elif modo == '3':
            print('Gracias por jugar. ¡Hasta luego!')
            break
        else:
            print('Opción no válida. Elige 1, 2 o 3.')