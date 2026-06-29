import numpy as np
import matplotlib.pyplot as plt
import re

class PhysicalLayer:
    def __init__(self):
        self.texto = ""
        self.bits = ""
        self.sinal = []
        self.tempo = []

    # Converte texto em uma sequência de bits (cada caractere vira 8 bits)
    def texto_para_bits(self, texto):
        self.texto = texto
        self.bits = ''.join(f'{ord(c):08b}' for c in texto)
        return self.bits

    # Converte uma string de bits (múltiplos de 8) de volta para texto
    def bits_para_texto(self, bits: str) -> str:
        if len(bits) % 8 != 0:
            raise ValueError("O número de bits deve ser múltiplo de 8.")
        texto = ''
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            caractere = chr(int(byte, 2))
            texto += caractere
        return texto

    # Modulação NRZ polar: bit 1 vira +A e bit 0 vira -A
    def nrz_polar(self, bits, A=1):
        self.sinal = [A if b == '1' else -A for b in bits]
        return self.sinal

    # Demodulação NRZ: decide pelo sinal (>=0 vira 1) -> aguenta ruido
    def demodular_nrz(self, sinal_str):
        amostras = [float(x) for x in sinal_str.split(',')]
        bits = ''.join(['1' if x >= 0 else '0' for x in amostras])
        return bits

    # Modulação Manchester: 0 → [A, -A], 1 → [-A, A]
    def manchester(self, bits, A=1):
        self.sinal = [v for b in bits for v in ([A, -A] if b == '0' else [-A, A])]
        return self.sinal

    # Demodulação Manchester: compara as duas metades de cada bit
    def demodular_manchester(self, sinal_str):
        amostras = [float(x) for x in sinal_str.split(',')]
        bits = ''
        for i in range(0, len(amostras) - 1, 2):
            # 0 -> [A,-A] (1a metade maior); 1 -> [-A,A] (2a metade maior)
            bits += '0' if amostras[i] > amostras[i+1] else '1'
        return bits

    # Modulação Bipolar: alterna +A/-A para bits '1', e usa 0 para '0'
    def bipolar(self, bits, A=1):
        sinal = []
        last = -A
        for b in bits:
            if b == '0':
                sinal.append(0)
            else:
                last = -last
                sinal.append(last)
        self.sinal = sinal
        return self.sinal

    # Demodulação Bipolar: |x| acima do limiar vira '1', perto de zero vira '0'
    def demodular_bipolar(self, sinal_str, A=1):
        amostras = [float(x) for x in sinal_str.split(',')]
        limiar = A / 2
        bits = ''.join(['1' if abs(x) > limiar else '0' for x in amostras])
        return bits

    # Modulação 16-QAM: 4 bits -> componentes I (cosseno) e Q (seno)
    def qam16(self, bits, A=1, f=5, fs=100):
        if len(bits) % 4 != 0:
            bits += '0' * (4 - len(bits) % 4)
        niveis = {'00': -3, '01': -1, '11': 1, '10': 3}
        sinal = []
        for i in range(0, len(bits), 4):
            grupo = bits[i:i+4]
            I = niveis.get(grupo[:2], -3)
            Q = niveis.get(grupo[2:], -3)
            t = np.linspace(0, 1, fs, endpoint=False)
            s = A * (I * np.cos(2 * np.pi * f * t) + Q * np.sin(2 * np.pi * f * t))
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits) / 4, len(sinal), endpoint=False)
        return sinal

    # Demodulação 16-QAM: ponto da constelação de menor distância
    def demodular_qam16(self, sinal, A=1, f=5, fs=100):
        niveis = {'00': -3, '01': -1, '11': 1, '10': 3}
        bits_recebidos = ''
        if len(sinal) % fs != 0:
            sinal = sinal[:-(len(sinal) % fs)]
        num_simbolos = len(sinal) // fs
        for i in range(num_simbolos):
            segmento = np.array(sinal[i * fs:(i + 1) * fs])
            t = np.linspace(0, 1, fs, endpoint=False)
            menor_dist = np.inf
            melhor_bits = ''
            for bits_I, I in niveis.items():
                for bits_Q, Q in niveis.items():
                    referencia = A * (I * np.cos(2 * np.pi * f * t) + Q * np.sin(2 * np.pi * f * t))
                    dist = np.sum((segmento - referencia) ** 2)
                    if dist < menor_dist:
                        menor_dist = dist
                        melhor_bits = bits_I + bits_Q
            bits_recebidos += melhor_bits
        return bits_recebidos

    # Modulação FSK: bit 0 → frequência f0, bit 1 → frequência f1
    def fsk(self, bits, f0=5, f1=10, fs=100, A=1):
        sinal = []
        for i, b in enumerate(bits):
            t_i = np.linspace(i, i + 1, fs)
            f = f1 if b == '1' else f0
            s = A * np.sin(2 * np.pi * f * t_i)
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits), len(sinal))
        return self.sinal

    # Demodulação FSK: qual frequência teve maior correlação
    def demodular_fsk(self, sinal, f0=5, f1=10, fs=100):
        bits = ''
        bloco_size = fs
        for i in range(0, len(sinal), bloco_size):
            bloco = sinal[i:i+bloco_size]
            if len(bloco) < bloco_size:
                break
            t_i = np.linspace(0, 1, fs, endpoint=False)
            s_f0 = np.sin(2 * np.pi * f0 * t_i)
            s_f1 = np.sin(2 * np.pi * f1 * t_i)
            corr_f0 = np.dot(bloco, s_f0)
            corr_f1 = np.dot(bloco, s_f1)
            bits += '0' if abs(corr_f0) > abs(corr_f1) else '1'
        return bits

    # Modulação ASK: bit 1 → seno de amplitude A, bit 0 → silêncio
    def ask(self, bits, A=1.0, f=5, fs=40):
        sinal = []
        for i, b in enumerate(bits):
            t_i = np.linspace(i, i + 1, fs, endpoint=False)
            amp = A if b == '1' else 0
            s = amp * np.sin(2 * np.pi * f * t_i)
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits), len(sinal))
        return self.sinal

    # Demodulação ASK: energia média acima de um limiar proporcional à amplitude
    def demodular_ask(self, sinal, A=1.0, fs=40):
        total_blocos = len(sinal) // fs
        sinal = sinal[:total_blocos * fs]
        limiar = A * 0.3
        bits = ''
        for i in range(0, len(sinal), fs):
            bloco = sinal[i:i+fs]
            media = sum(abs(x) for x in bloco) / fs
            bits += '1' if media > limiar else '0'
        return bits

    # Modulação QPSK: 2 bits -> 1 de 4 fases da portadora
    def psk(self, bits, A=1, f=5, fs=100):
        if len(bits) % 2 != 0:
            bits += '0'
        fases = {'00': 0, '01': np.pi / 2, '11': np.pi, '10': 3 * np.pi / 2}
        sinal = []
        for i in range(0, len(bits), 2):
            grupo = bits[i:i+2]
            fase = fases.get(grupo, 0)
            t = np.linspace(0, 1, fs, endpoint=False)
            s = A * np.sin(2 * np.pi * f * t + fase)
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits) / 2, len(sinal), endpoint=False)
        return sinal

    # Demodulação QPSK: fase de maior correlação
    def demodular_psk(self, sinal, A=1, f=5, fs=100):
        fases = {'00': 0, '01': np.pi / 2, '11': np.pi, '10': 3 * np.pi / 2}
        bits_recebidos = ''
        if len(sinal) % fs != 0:
            sinal = sinal[:-(len(sinal) % fs)]
        num_simbolos = len(sinal) // fs
        for i in range(num_simbolos):
            segmento = sinal[i * fs:(i + 1) * fs]
            t = np.linspace(0, 1, fs, endpoint=False)
            max_corr = -np.inf
            melhor_bits = ''
            for fase_bits, fase in fases.items():
                referencia = A * np.sin(2 * np.pi * f * t + fase)
                corr = np.dot(segmento, referencia)
                if corr > max_corr:
                    max_corr = corr
                    melhor_bits = fase_bits
            bits_recebidos += melhor_bits
        return bits_recebidos

    # Adiciona ruido gaussiano ao sinal (nivel = fracao da amplitude de pico)
    def adicionar_ruido(self, sinal, nivel):
        if nivel <= 0:
            return sinal
        sinal = np.array(sinal, dtype=float)
        pico = np.max(np.abs(sinal)) if len(sinal) else 1.0
        if pico == 0:
            pico = 1.0
        ruido = np.random.normal(0, nivel * pico, len(sinal))
        return list(sinal + ruido)