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
        

    def _bits_paridade(self, m):
        # menor r tal que 2^r >= m + r + 1
        r = 0
        while (2 ** r) < (m + r + 1):
            r += 1
        return r

    def hamming_codificar(self, bits, m=4):
        r = self._bits_paridade(m)
        n = m + r                      # tamanho do bloco codificado
        pos_paridade = {2 ** j for j in range(r)}   # posicoes 1,2,4,8...

        while len(bits) % m != 0:
            bits += '0'               # padding p/ multiplo de m

        resultado = ''
        for ini in range(0, len(bits), m):
            dados = bits[ini:ini + m]
            cod = [0] * (n + 1)       # 1-indexado (ignora indice 0)

            di = 0                    # preenche os dados nas posicoes nao-paridade
            for pos in range(1, n + 1):
                if pos not in pos_paridade:
                    cod[pos] = int(dados[di])
                    di += 1

            for j in range(r):        # calcula cada bit de paridade
                p = 2 ** j
                paridade = 0
                for pos in range(1, n + 1):
                    if pos & p:
                        paridade ^= cod[pos]
                cod[p] = paridade

            resultado += ''.join(str(cod[pos]) for pos in range(1, n + 1))
        return resultado

    def hamming_decodificar(self, bits, m=4):
        r = self._bits_paridade(m)
        n = m + r
        pos_paridade = {2 ** j for j in range(r)}

        resultado = ''
        for ini in range(0, len(bits), n):
            bloco = bits[ini:ini + n]
            if len(bloco) < n:
                continue
            cod = [0] + [int(b) for b in bloco]   # 1-indexado

            sindrome = 0              # recalcula as paridades -> sindrome
            for j in range(r):
                p = 2 ** j
                paridade = 0
                for pos in range(1, n + 1):
                    if pos & p:
                        paridade ^= cod[pos]
                if paridade:
                    sindrome += p     # acumula a posicao do erro

            if sindrome != 0 and sindrome <= n:
                cod[sindrome] ^= 1    # corrige o bit apontado

            # extrai so os dados (posicoes que nao sao paridade)
            dados = ''.join(str(cod[pos]) for pos in range(1, n + 1)
                            if pos not in pos_paridade)
            resultado += dados
        return resultado