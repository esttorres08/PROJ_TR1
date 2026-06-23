import numpy as np
import matplotlib.pyplot as plt
import re

class PhysicalLayer:
    def __init__(self):
        # Inicializa atributos da camada física
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
    
    # Modulação NRZ polar: bit 1 vira +1 e bit 0 vira -1
    def nrz_polar(self, bits):
        self.sinal = [1 if b == '1' else -1 for b in bits]
        return self.sinal

    
    # Demodulação NRZ: converte valores -1/+1 de volta para bits
    def demodular_nrz(self, sinal_str):
        amostras = list(map(int, re.findall(r'-?1', sinal_str)))
        print("Sinal recebido (NRZ):", amostras)
        bits = ''.join(['1' if x == 1 else '0' for x in amostras])
        return bits

    # Modulação Manchester: 0 → [1, -1], 1 → [-1, 1]
    def manchester(self, bits):
        self.sinal = [v for b in bits for v in ([1, -1] if b == '0' else [-1, 1])]
        return self.sinal

    # Demodulação Manchester: interpreta pares de amostras
    def demodular_manchester(self, sinal_str):
        amostras = list(map(int, re.findall(r'-?1', sinal_str)))
        bits = ''
        if len(amostras) % 2 != 0:
            raise ValueError("Número de amostras inválido para Manchester")
        for i in range(0, len(amostras), 2):
            par = amostras[i:i+2]
            if par == [1, -1]:
                bits += '0'
            elif par == [-1, 1]:
                bits += '1'
            else:
                raise ValueError(f"Sequência inválida Manchester: {par}")
        return bits

    # Modulação Bipolar: alterna entre +1 e -1 para bits '1', e usa 0 para '0'
    def bipolar(self, bits):
        sinal = []
        last = -1
        for b in bits:
            if b == '0':
                sinal.append(0)
            else:
                last = -last
                sinal.append(last)
        self.sinal = sinal
        return self.sinal

    # Demodulação Bipolar: +1 ou -1 viram '1', 0 vira '0'
    def demodular_bipolar(self, sinal_str):
        amostras = list(map(int, re.findall(r'-?1|0', sinal_str)))
        bits = ''.join(['1' if x in (1, -1) else '0' for x in amostras])
        return bits

    # Modulação 16-QAM: mapeia grupos de 4 bits em duas componentes (I e Q)
    # 2 bits escolhem a amplitude do cosseno (I) e 2 bits a do seno (Q)
    def qam16(self, bits, f=5, fs=100):
        if len(bits) % 4 != 0:
            bits += '0' * (4 - len(bits) % 4)  # padding para múltiplos de 4
        niveis = {
            '00': -3,
            '01': -1,
            '11': 1,
            '10': 3
        } 
        sinal = []
        for i in range(0, len(bits), 4):
            grupo = bits[i:i+4]
            I = niveis.get(grupo[:2], -3)   # componente em fase
            Q = niveis.get(grupo[2:], -3)   # componente em quadratura
            t = np.linspace(0, 1, fs, endpoint=False)
            s = I * np.cos(2 * np.pi * f * t) + Q * np.sin(2 * np.pi * f * t)
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits) / 4, len(sinal), endpoint=False)
        return sinal

    # Demodulação 16-QAM: compara o segmento com as 16 referências possíveis
    # e escolhe a de menor distância (ponto mais próximo da constelação)
    def demodular_qam16(self, sinal, f=5, fs=100):
        niveis = {
            '00': -3,
            '01': -1,
            '11': 1,
            '10': 3
        }
        bits_recebidos = ''
        if len(sinal) % fs != 0:
            sinal = sinal[:-(len(sinal) % fs)]  # ajusta tamanho
        num_simbolos = len(sinal) // fs
        for i in range(num_simbolos):
            segmento = np.array(sinal[i * fs:(i + 1) * fs])
            t = np.linspace(0, 1, fs, endpoint=False)
            menor_dist = np.inf
            melhor_bits = ''
            for bits_I, I in niveis.items():
                for bits_Q, Q in niveis.items():
                    referencia = I * np.cos(2 * np.pi * f * t) + Q * np.sin(2 * np.pi * f * t)
                    dist = np.sum((segmento - referencia) ** 2)
                    if dist < menor_dist:
                        menor_dist = dist
                        melhor_bits = bits_I + bits_Q
            bits_recebidos += melhor_bits
        return bits_recebidos

    # Modulação FSK: bit 0 → frequência f0, bit 1 → frequência f1
    def fsk(self, bits, f0=5, f1=10, fs=100):
        sinal = []
        for i, b in enumerate(bits):
            t_i = np.linspace(i, i + 1, fs)
            f = f1 if b == '1' else f0
            s = np.sin(2 * np.pi * f * t_i)
            sinal.extend(s)
        self.sinal = sinal
        self.tempo = np.linspace(0, len(bits), len(sinal))
        return self.sinal

    # Demodulação FSK: detecta qual frequência predominou no bloco
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

    # Modulação ASK: bit 1 → seno de amplitude A, bit 0 → silêncio (0)
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

    # Demodulação ASK: detecta presença de sinal (acima do threshold)
    def demodular_ask(self, sinal, threshold=0.2, fs=40):
        total_blocos = len(sinal) // fs
        sinal = sinal[:total_blocos * fs]  # remove excesso
        bits = ''
        for i in range(0, len(sinal), fs):
            bloco = sinal[i:i+fs]
            media = sum(abs(x) for x in bloco) / fs
            bits += '1' if media > threshold else '0'
        return bits
        # Modulação QPSK: mapeia grupos de 2 bits em uma das 4 fases da portadora
    # amplitude e frequência ficam constantes, só a fase muda
    def psk(self, bits, A=1, f=5, fs=100):
        if len(bits) % 2 != 0:
            bits += '0'  # padding para múltiplos de 2
        fases = {
            '00': 0,
            '01': np.pi / 2,
            '11': np.pi,
            '10': 3 * np.pi / 2
        }  # código de Gray: fases vizinhas diferem em só 1 bit
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

    # Demodulação QPSK: identifica a fase do segmento por correlação
    # (como todas as referências têm a mesma energia, a maior correlação é o critério correto)
    def demodular_psk(self, sinal, A=1, f=5, fs=100):
        fases = {
            '00': 0,
            '01': np.pi / 2,
            '11': np.pi,
            '10': 3 * np.pi / 2
        }
        bits_recebidos = ''
        if len(sinal) % fs != 0:
            sinal = sinal[:-(len(sinal) % fs)]  # ajusta tamanho
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