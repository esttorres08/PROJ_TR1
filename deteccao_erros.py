class DeteccaoErros:
    def __init__(self, modo: str = 'paridade'):
        """
        modo: 'paridade' ou 'crc'
        """
        if modo not in ['paridade', 'crc', 'hamming', 'checksum']:
            raise ValueError("Modo inválido. Use 'paridade' ou 'crc' ou 'hamming' ou 'checksum'")
        self.modo = modo
        self.poly = '100000100110000010001110110110111'  # CRC-32 IEEE 802 (33 bits)

    # Adiciona o trecho de detectação de erro conforme o desejado
    def adicionar(self, bits: str) -> str:
        if self.modo == 'paridade': #P aridade
            total_uns = bits.count('1')
            paridade = '0' if total_uns % 2 == 0 else '1'
            return bits + paridade

        elif self.modo == 'crc': # CRC
            bits_padded = list(bits + '0' * 32)
            poly = self.poly
            for i in range(len(bits)):
                if bits_padded[i] == '1':
                    for j in range(len(poly)):
                        bits_padded[i + j] = str(int(bits_padded[i + j] != poly[j]))
            crc = ''.join(bits_padded[-32:])
            return bits + crc
        
        elif self.modo == 'hamming': #Hamming
            return self.hamming_codificar(bits)
        
        elif self.modo == 'checksum':  # Checksum de 16 bits (soma em complemento de um)
            if len(bits) % 16 != 0:
                bits += '0' * (16 - len(bits) % 16)  # padding para múltiplos de 16
            soma = 0
            for i in range(0, len(bits), 16):
                palavra = int(bits[i:i+16], 2)
                soma += palavra
                soma = (soma & 0xFFFF) + (soma >> 16)  # reincorpora o vai-um (wrap around)
            checksum = soma ^ 0xFFFF  # complemento de um da soma
            return bits + f'{checksum:016b}'

    # Verifica se tem algum erro com base no trecho que foi adicionado
    def verificar(self, bits_com_codigo: str) -> bool:
        if self.modo == 'paridade':
            return bits_com_codigo.count('1') % 2 == 0

        elif self.modo == 'crc':
            bits_padded = list(bits_com_codigo)
            poly = self.poly
            for i in range(len(bits_padded) - 32):
                if bits_padded[i] == '1':
                    for j in range(len(poly)):
                        bits_padded[i + j] = str(int(bits_padded[i + j] != poly[j]))
            resto = ''.join(bits_padded[-32:])
            return all(b == '0' for b in resto)
        
        elif self.modo == 'hamming':
            return self.hamming_decodificar(bits_com_codigo)
        
        elif self.modo == 'checksum':
            soma = 0
            for i in range(0, len(bits_com_codigo), 16):
                palavra = int(bits_com_codigo[i:i+16], 2)
                soma += palavra
                soma = (soma & 0xFFFF) + (soma >> 16)
            return soma == 0xFFFF  # dados + checksum devem somar tudo-1s
        

    # Função para a detectação e correção de erro Hamming
    def hamming_codificar(self, bits: str) -> str:
        resultado = ''
        while len(bits) % 4 != 0:
            bits += '0'  # Preenchimento se necessário

        for i in range(0, len(bits), 4):
            d = list(bits[i:i+4])
            d1, d2, d3, d4 = map(int, d)
            p1 = d1 ^ d2 ^ d4
            p2 = d1 ^ d3 ^ d4
            p3 = d2 ^ d3 ^ d4
            p4 = p1 ^ p2 ^ d1 ^ p3 ^ d2 ^ d3 ^ d4  # paridade geral
            codigo = f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}{p4}"
            resultado += codigo
        return resultado

        # Decodifica o Hamming
    def hamming_decodificar(self, bits: str) -> str:
        resultado = ''
        for i in range(0, len(bits), 8):
            bloco = bits[i:i+8]
            if len(bloco) < 8:
                continue
            p1, p2, d1, p3, d2, d3, d4, p4 = map(int, bloco)
            s1 = p1 ^ d1 ^ d2 ^ d4
            s2 = p2 ^ d1 ^ d3 ^ d4
            s3 = p3 ^ d2 ^ d3 ^ d4
            posicao_erro = s3 * 4 + s2 * 2 + s1 * 1
            bloco_corrigido = list(bloco)
            if posicao_erro != 0 and 1 <= posicao_erro <= 8:
                bloco_corrigido[posicao_erro - 1] = '0' if bloco_corrigido[posicao_erro - 1] == '1' else '1'
            d1 = bloco_corrigido[2]
            d2 = bloco_corrigido[4]
            d3 = bloco_corrigido[5]
            d4 = bloco_corrigido[6]
            resultado += d1 + d2 + d3 + d4
        return resultado