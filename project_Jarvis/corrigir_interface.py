# -*- coding: utf-8 -*-
import re

# Ler o arquivo
with open('interfaces/panda3d_interface.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Corrigir 1: Adicionar import math no topo (se não existir)
if 'import math' not in content:
    content = 'import math\n' + content

# Corrigir 2: Substituir setTitle pelo método correto do Panda3D
content = content.replace(
    'self.win.setTitle("Jarvis - Assistente Pessoal 3D")',
    'self.win.set_window_title("Jarvis - Assistente Pessoal 3D")'
)

# Corrigir 3: Adicionar tratamento para a fonte
content = content.replace(
    'self.loader.load_font("cmss12")',
    'self.loader.load_font("cmss12")  # Fonte padrão do Panda3D'
)

# Salvar o arquivo corrigido
with open('interfaces/panda3d_interface.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Arquivo corrigido com sucesso!")
