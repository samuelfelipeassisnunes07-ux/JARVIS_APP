# -*- coding: utf-8 -*-
import math
import sys
import os
import random
from pathlib import Path
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    TextNode, Vec4, Vec3, Vec2, TransparencyAttrib,
    AmbientLight, DirectionalLight, PointLight,
    CardMaker, NodePath, load_prc_file_data,
    Shader, Material, ColorBlendAttrib,
    TextureStage, TexGenAttrib, TexMatrixAttrib
)
from direct.interval.IntervalGlobal import (
    Sequence, Parallel, LerpScaleInterval,
    LerpColorInterval, LerpPosInterval,
    LerpHprInterval, Func, Wait
)
from direct.gui.DirectGui import OnscreenText
from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.Particles import Particles
from direct.particles.ParticleManager import ParticleManager

from core.assistant import Assistant

# Configurações visuais FODAS
load_prc_file_data('', 'win-size 1600 900')
load_prc_file_data('', 'window-title Jarvis - Assistente IA 3D')
load_prc_file_data('', 'background-color 0 0 0')
load_prc_file_data('', 'framebuffer-multisample 1')
load_prc_file_data('', 'multisamples 4')
load_prc_file_data('', 'gl-version 3 2')  # Forçar OpenGL 3.2 para shaders

class HolographicCore:
    """Núcleo holográfico do Jarvis"""
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render
        self.core = None
        self.particles = []
        self.energy_rings = []
        
    def create(self):
        """Cria o núcleo central do Jarvis"""
        self.core = self.render.attach_new_node("jarvis_core")
        self.core.set_pos(0, 5, 0)
        
        # Esfera central brilhante
        sphere = self.loader.load_model("models/unit_sphere")
        if not sphere:
            # Criar esfera com CardMaker se não tiver modelo
            cm = CardMaker('core_sphere')
            cm.set_frame(-1, 1, -1, 1)
            sphere = self.render.attach_new_node(cm.generate())
        
        sphere.reparent_to(self.core)
        sphere.set_scale(1.2)
        sphere.set_color(0.0, 0.5, 1.0, 0.3)
        sphere.set_transparency(TransparencyAttrib.MAlpha)
        sphere.set_two_sided(True)
        
        # Material brilhante
        mat = Material()
        mat.set_ambient(Vec4(0.1, 0.3, 0.8, 1))
        mat.set_diffuse(Vec4(0.2, 0.5, 1.0, 1))
        mat.set_emission(Vec4(0.1, 0.2, 0.5, 1))
        mat.set_specular(Vec4(1, 1, 1, 1))
        mat.set_shininess(100)
        sphere.set_material(mat)
        
        # Anéis de energia
        for i in range(3):
            ring = self.create_energy_ring(radius=2.0 + i*0.5, color=(0.3, 0.8, 1.0, 0.2))
            ring.reparent_to(self.core)
            ring.set_hpr(0, 0, 0)
            if i == 1:
                ring.set_hpr(45, 30, 0)
            elif i == 2:
                ring.set_hpr(90, 60, 0)
            self.energy_rings.append(ring)
        
        # Partículas de energia
        self.create_energy_particles()
        
        return self.core
    
    def create_energy_ring(self, radius=2.0, color=(0.3, 0.8, 1.0, 0.2)):
        """Cria um anel de energia"""
        ring = self.render.attach_new_node("energy_ring")
        
        # Criar círculo de pontos
        segments = 32
        for i in range(segments):
            angle = (2 * math.pi * i) / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            
            # Criar pequena esfera para cada ponto
            cm = CardMaker(f'ring_point_{i}')
            cm.set_frame(-0.1, 0.1, -0.1, 0.1)
            point = self.render.attach_new_node(cm.generate())
            point.reparent_to(ring)
            point.set_pos(x, 0, z)
            point.set_color(*color)
            point.set_transparency(TransparencyAttrib.MAlpha)
            
            # Rotacionar para ficar de frente para o centro
            point.look_at(0, 0, 0)
        
        return ring
    
    def create_energy_particles(self):
        """Cria partículas de energia ao redor do núcleo"""
        for i in range(20):
            # Criar partícula
            cm = CardMaker(f'particle_{i}')
            cm.set_frame(-0.1, 0.1, -0.1, 0.1)
            particle = self.render.attach_new_node(cm.generate())
            particle.reparent_to(self.core)
            
            # Posição aleatória na esfera
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 2.5 + random.uniform(-0.5, 0.5)
            
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)
            
            particle.set_pos(x, y, z)
            particle.set_color(
                random.uniform(0.2, 0.8),
                random.uniform(0.4, 1.0),
                1.0,
                random.uniform(0.3, 0.7)
            )
            particle.set_transparency(TransparencyAttrib.MAlpha)
            
            # Adicionar à lista para animação
            self.particles.append({
                'node': particle,
                'speed': random.uniform(0.5, 1.5),
                'angle': random.uniform(0, 2 * math.pi),
                'radius': r
            })
    
    def update(self, task):
        """Atualiza animações do núcleo"""
        dt = task.time * 0.5
        
        # Rotacionar anéis
        for i, ring in enumerate(self.energy_rings):
            ring.set_hpr(ring.get_h() + 1.0 * (i + 1), 
                        ring.get_p() + 0.5 * (i + 1), 
                        ring.get_r())
        
        # Mover partículas
        for p in self.particles:
            p['angle'] += 0.02 * p['speed']
            node = p['node']
            angle = p['angle']
            r = p['radius']
            
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            node.set_pos(x, node.get_y(), z)
        
        return Task.cont

class FuturisticUI:
    """Interface futurística com elementos 3D"""
    def __init__(self, base):
        self.base = base
        self.elements = []
        
    def create_scanline(self):
        """Cria efeito de scanline futurista"""
        cm = CardMaker('scanline')
        cm.set_frame(-10, 10, -0.1, 0.1)
        scanline = self.base.render.attach_new_node(cm.generate())
        scanline.set_pos(0, 5, -2)
        scanline.set_color(0.0, 0.5, 1.0, 0.1)
        scanline.set_transparency(TransparencyAttrib.MAlpha)
        
        # Animação da scanline
        seq = Sequence(
            LerpPosInterval(scanline, 3.0, Vec3(0, 5, 2), startPos=Vec3(0, 5, -2)),
            LerpPosInterval(scanline, 3.0, Vec3(0, 5, -2), startPos=Vec3(0, 5, 2)),
        )
        seq.loop()
        self.elements.append(scanline)
        
    def create_grid_floor(self):
        """Cria chão com grade holográfica"""
        # Grade principal
        for i in range(-5, 6):
            # Linhas horizontais
            cm = CardMaker(f'grid_h_{i}')
            cm.set_frame(-5, 5, -0.05, 0.05)
            line_h = self.base.render.attach_new_node(cm.generate())
            line_h.set_pos(0, i, -1.5)
            line_h.set_hpr(0, 90, 0)
            line_h.set_color(0.2, 0.5, 1.0, 0.2)
            line_h.set_transparency(TransparencyAttrib.MAlpha)
            
            # Linhas verticais
            cm = CardMaker(f'grid_v_{i}')
            cm.set_frame(-5, 5, -0.05, 0.05)
            line_v = self.base.render.attach_new_node(cm.generate())
            line_v.set_pos(i, 0, -1.5)
            line_v.set_hpr(90, 90, 0)
            line_v.set_color(0.2, 0.5, 1.0, 0.2)
            line_v.set_transparency(TransparencyAttrib.MAlpha)
            
            self.elements.extend([line_h, line_v])
    
    def create_holographic_display(self, text="JARVIS v1.0"):
        """Cria display holográfico flutuante"""
        # Fundo do display
        cm = CardMaker('display_bg')
        cm.set_frame(-3, 3, -1, 1)
        display = self.base.render.attach_new_node(cm.generate())
        display.set_pos(0, 3, 2)
        display.set_color(0.0, 0.2, 0.4, 0.3)
        display.set_transparency(TransparencyAttrib.MAlpha)
        
        # Texto do display
        text_node = TextNode('display_text')
        text_node.set_text(text)
        text_node.set_font(self.base.loader.load_font('cmss12'))
        text_node.set_text_color(0.0, 0.8, 1.0, 1)
        text_node.set_align(TextNode.ACenter)
        
        text_np = display.attach_new_node(text_node)
        text_np.set_scale(0.1)
        text_np.set_pos(0, 0, 0)
        text_np.set_hpr(0, 0, 0)
        
        self.elements.append(display)

class SpeechInterface:
    """Interface de fala com efeitos visuais"""
    def __init__(self, loader, render, task_mgr):
        self.loader = loader
        self.render = render
        self.task_mgr = task_mgr
        self.bubble = None
        self.text_node = None
        self.energy_effect = None
        
    def create(self):
        """Cria balão de fala estilizado"""
        self.bubble = self.render.attach_new_node("speech_bubble")
        self.bubble.set_pos(2.5, 5, 2.0)
        self.bubble.set_scale(0.5)
        
        # Fundo com gradiente
        for i in range(3):
            cm = CardMaker(f'bubble_layer_{i}')
            cm.set_frame(-2.5, 2.5, -1.5, 1.5)
            layer = self.render.attach_new_node(cm.generate())
            layer.reparent_to(self.bubble)
            
            # Cores em camadas para efeito de profundidade
            alpha = 0.3 - i * 0.1
            color = (0.0, 0.3 + i*0.2, 0.8, alpha)
            layer.set_color(*color)
            layer.set_transparency(TransparencyAttrib.MAlpha)
            layer.set_pos(0, -i*0.1, 0)
        
        # Texto principal
        self.text_node = TextNode('bubble_text')
        self.text_node.set_text("⚡ JARVIS ONLINE ⚡")
        self.text_node.set_font(self.loader.load_font('cmss12'))
        self.text_node.set_text_color(0.0, 1.0, 1.0, 1)
        self.text_node.set_align(TextNode.ACenter)
        
        text_np = self.bubble.attach_new_node(self.text_node)
        text_np.set_scale(0.15)
        text_np.set_pos(0, 0, 0)
        
        self.hide()
        return self.bubble
    
    def show_text(self, text, is_user=False):
        """Mostra texto com animação"""
        self.text_node.set_text(text)
        self.bubble.show()
        
        # Cor diferente para usuário vs Jarvis
        if is_user:
            self.bubble.set_color_scale(1.0, 0.5, 0.5, 1.0)
        else:
            self.bubble.set_color_scale(0.5, 0.8, 1.0, 1.0)
        
        # Animação de entrada
        seq = Sequence(
            LerpScaleInterval(self.bubble, 0.3, Vec3(0.7, 0.7, 0.7)),
            LerpScaleInterval(self.bubble, 0.2, Vec3(0.5, 0.5, 0.5)),
        )
        seq.start()
        
        # Auto-esconder após 8 segundos
        self.task_mgr.do_method_later(8.0, lambda task: self.hide(), 'hide_bubble')
    
    def hide(self):
        if self.bubble:
            self.bubble.hide()
        return Task.done

class FuturisticInput:
    """Sistema de entrada futurístico"""
    def __init__(self, base, on_submit_callback):
        self.base = base
        self.on_submit = on_submit_callback
        self.current_input = ""
        self.input_display = None
        self.cursor_visible = True
        self.setup_gui()
        self.setup_cursor_blink()
        
    def setup_gui(self):
        """Configura elementos GUI estilizados"""
        # Fundo da área de entrada
        cm = CardMaker('input_bg')
        cm.set_frame(-8, 8, -0.8, 0.8)
        bg = self.base.render.attach_new_node(cm.generate())
        bg.set_pos(0, 5, -2.5)
        bg.set_color(0.0, 0.1, 0.2, 0.7)
        bg.set_transparency(TransparencyAttrib.MAlpha)
        
        # Borda brilhante
        cm.set_frame(-8.1, 8.1, -0.9, 0.9)
        border = self.base.render.attach_new_node(cm.generate())
        border.set_pos(0, 5, -2.5)
        border.set_color(0.0, 0.5, 1.0, 0.3)
        border.set_transparency(TransparencyAttrib.MAlpha)
        
        # Texto digitado
        self.input_display = TextNode('input_text')
        self.input_display.set_font(self.base.loader.load_font('cmss12'))
        self.input_display.set_text_color(0.0, 1.0, 1.0, 1)
        self.input_display.set_align(TextNode.ALeft)
        
        input_np = self.base.render.attach_new_node(self.input_display)
        input_np.set_pos(-6, 5, -2.5)
        input_np.set_scale(0.1)
        
        # Prompt
        prompt = TextNode('prompt')
        prompt.set_text("> ENTRADA:")
        prompt.set_font(self.base.loader.load_font('cmss12'))
        prompt.set_text_color(0.5, 0.5, 1.0, 1)
        prompt.set_align(TextNode.ALeft)
        
        prompt_np = self.base.render.attach_new_node(prompt)
        prompt_np.set_pos(-6, 5, -2.2)
        prompt_np.set_scale(0.08)
        
        # Instruções
        instructions = TextNode('instructions')
        instructions.set_text("[ENTER] Enviar  |  [ESC] Sair")
        instructions.set_font(self.base.loader.load_font('cmss12'))
        instructions.set_text_color(0.3, 0.3, 0.5, 1)
        instructions.set_align(TextNode.ACenter)
        
        instr_np = self.base.render.attach_new_node(instructions)
        instr_np.set_pos(0, 5, -3.2)
        instr_np.set_scale(0.06)
        
        self.input_np = input_np
        
    def setup_cursor_blink(self):
        """Animação do cursor piscando"""
        def blink_cursor(task):
            self.cursor_visible = not self.cursor_visible
            self.update_display()
            return task.again
        self.base.taskMgr.do_method_later(0.5, blink_cursor, 'blink_cursor')
    
    def handle_key(self, key):
        if key == 'enter':
            if self.current_input.strip():
                self.on_submit(self.current_input)
                self.current_input = ""
                self.update_display()
        elif key == 'backspace':
            self.current_input = self.current_input[:-1]
            self.update_display()
        elif key == 'escape':
            sys.exit(0)
        elif len(key) == 1:
            self.current_input += key
            self.update_display()
            
    def update_display(self):
        if self.input_display:
            cursor = "_" if self.cursor_visible else " "
            self.input_display.set_text(f"{self.current_input}{cursor}")

class Panda3DInterface(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Configurar qualidade visual
        self.setBackgroundColor(0, 0, 0)
        self.render.set_shader_auto()
        
        # Inicializar assistente
        print("⚡ Inicializando Jarvis...")
        try:
            self.assistant = Assistant()
            print("✅ Assistente conectado")
        except Exception as e:
            print(f"⚠️ Erro: {e}")
            self.assistant = None
        
        # Configurar cena
        self.setup_scene()
        self.setup_lights()
        
        # Criar elementos visuais FODAS
        self.core = HolographicCore(self.loader, self.render)
        self.core.create()
        
        self.ui = FuturisticUI(self)
        self.ui.create_scanline()
        self.ui.create_grid_floor()
        self.ui.create_holographic_display()
        
        self.speech = SpeechInterface(self.loader, self.render, self.taskMgr)
        self.speech.create()
        
        self.input = FuturisticInput(self, self.process_input)
        
        # Configurar teclado
        self.setup_keyboard()
        
        # Mensagem inicial
        self.speech.show_text("⚡ JARVIS ONLINE ⚡")
        
        # Tarefas de animação
        self.taskMgr.add(self.update_core, "update_core")
        self.taskMgr.add(self.create_particle_field, "particles")
        
        print("✅ Interface 3D Premium carregada!")
        print("🎮 Digite sua mensagem...")
        
    def setup_scene(self):
        """Configura cena com efeitos visuais"""
        self.camera.setPos(0, -15, 5)
        self.camera.lookAt(0, 5, 0)
        
        # Nebulosa de fundo (estrelas)
        self.create_starfield()
        
    def create_starfield(self):
        """Cria campo de estrelas no fundo"""
        for _ in range(200):
            cm = CardMaker('star')
            cm.set_frame(-0.05, 0.05, -0.05, 0.05)
            star = self.render.attach_new_node(cm.generate())
            
            x = random.uniform(-20, 20)
            y = random.uniform(-10, 20)
            z = random.uniform(-10, 20)
            star.set_pos(x, y, z)
            
            brightness = random.uniform(0.3, 1.0)
            star.set_color(brightness, brightness, brightness, 1)
            
            # Piscar aleatoriamente
            blink_seq = Sequence(
                Wait(random.uniform(1, 5)),
                LerpColorInterval(star, 0.5, Vec4(1, 1, 1, 1), 
                                 startColor=Vec4(brightness, brightness, brightness, 1)),
                LerpColorInterval(star, 0.5, Vec4(brightness, brightness, brightness, 1),
                                 startColor=Vec4(1, 1, 1, 1)),
            )
            blink_seq.loop()
        
    def setup_lights(self):
        """Configura iluminação dramática"""
        # Luz ambiente suave
        ambient = AmbientLight("ambient")
        ambient.set_color(Vec4(0.1, 0.1, 0.2, 1))
        ambient_np = self.render.attach_new_node(ambient)
        self.render.set_light(ambient_np)
        
        # Luz principal (azul)
        key_light = PointLight("key_light")
        key_light.set_color(Vec4(0.3, 0.5, 1.0, 1))
        key_np = self.render.attach_new_node(key_light)
        key_np.set_pos(5, 10, 5)
        self.render.set_light(key_np)
        
        # Luz de preenchimento (roxo)
        fill_light = PointLight("fill_light")
        fill_light.set_color(Vec4(0.5, 0.2, 0.8, 1))
        fill_np = self.render.attach_new_node(fill_light)
        fill_np.set_pos(-5, 5, 2)
        self.render.set_light(fill_np)
        
    def setup_keyboard(self):
        """Configura eventos de teclado"""
        for key in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?':
            self.accept(key, self.input.handle_key, [key])
        
        self.accept('enter', self.input.handle_key, ['enter'])
        self.accept('backspace', self.input.handle_key, ['backspace'])
        self.accept('escape', self.input.handle_key, ['escape'])
        
    def process_input(self, user_input):
        """Processa mensagem do usuário"""
        print(f"👤 Você: {user_input}")
        self.speech.show_text(f"Você: {user_input}", is_user=True)
        
        if self.assistant:
            # Efeito de "pensando"
            self.core.core.set_color_scale(0.5, 0.5, 1.0, 1.0)
            self.taskMgr.add(self.get_response, "response", extraArgs=[user_input])
        else:
            self.speech.show_text("Jarvis offline", is_user=False)
            
    def get_response(self, user_input):
        """Obtém resposta do assistente"""
        try:
            response = self.assistant.process_message(user_input)
            print(f"🤖 Jarvis: {response}")
            
            # Efeito visual de resposta
            self.core.core.set_color_scale(1, 1, 1, 1)
            self.speech.show_text(response, is_user=False)
            
            # Flash de energia
            self.create_energy_flash()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            self.speech.show_text(f"Erro: {str(e)[:30]}...", is_user=False)
            self.core.core.set_color_scale(1, 1, 1, 1)
            
        return Task.done
        
    def create_energy_flash(self):
        """Cria flash de energia quando Jarvis responde"""
        flash = self.render.attach_new_node("flash")
        
        cm = CardMaker('flash')
        cm.set_frame(-10, 10, -10, 10)
        flash_card = flash.attach_new_node(cm.generate())
        flash_card.set_color(0.3, 0.5, 1.0, 0.5)
        flash_card.set_transparency(TransparencyAttrib.MAlpha)
        
        # Animação do flash
        seq = Sequence(
            Func(flash.show),
            LerpColorInterval(flash_card, 0.1, Vec4(0.5, 0.8, 1.0, 0.3)),
            LerpColorInterval(flash_card, 0.2, Vec4(0.3, 0.5, 1.0, 0)),
            Func(flash.hide),
        )
        seq.start()
        
    def update_core(self, task):
        """Atualiza núcleo central"""
        self.core.update(task)
        return Task.cont
        
    def create_particle_field(self, task):
        """Cria campo de partículas dinâmico"""
        if random.random() < 0.1:  # 10% chance a cada frame
            self.create_energy_particle()
        return Task.cont
        
    def create_energy_particle(self):
        """Cria uma partícula de energia aleatória"""
        cm = CardMaker('energy_particle')
        cm.set_frame(-0.2, 0.2, -0.2, 0.2)
        particle = self.render.attach_new_node(cm.generate())
        
        x = random.uniform(-5, 5)
        y = random.uniform(0, 10)
        z = random.uniform(-2, 2)
        particle.set_pos(x, y, z)
        
        color = (random.uniform(0.3, 1.0), 
                random.uniform(0.3, 0.8), 
                1.0, 
                0.5)
        particle.set_color(*color)
        particle.set_transparency(TransparencyAttrib.MAlpha)
        
        # Animação da partícula
        seq = Sequence(
            Parallel(
                LerpScaleInterval(particle, 1.0, Vec3(0.1, 0.1, 0.1), 
                                startScale=Vec3(0.5, 0.5, 0.5)),
                LerpColorInterval(particle, 1.0, Vec4(*color[:3], 0),
                                startColor=Vec4(*color))
            ),
            Func(particle.remove_node)
        )
        seq.start()

if __name__ == "__main__":
    app = Panda3DInterface()
    app.run()
