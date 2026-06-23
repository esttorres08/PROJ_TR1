class Link:
    def __init__(self):
        self.quadro_bits = ""
        self.FLAG = "01111110"
        self.FLAG1 = chr(0x7E) # --> ~
        self.ESC = chr(0x7D)   # --> }

    # Enquadra os bits usando contagem de caracteres binários (em blocos de 8).
    def enquadrar_count(self, bits: str) -> str:
        if len(bits) % 8 != 0:
            raise ValueError("Bits devem representar caracteres inteiros (múltiplos de 8).")

        tamanho_bytes = len(bits) // 8
        tamanho_bin = f'{tamanho_bytes:08b}'  # 8 bits representando o número de caracteres
        self.quadro_bits = tamanho_bin + bits
        return self.quadro_bits

    #Retira os 8 bits de contagem e retorna os bits da mensagem original.
    def desenquadrar_count(self, quadro_bits: str) -> str:
        tamanho_bin = quadro_bits[:8]
        tamanho = int(tamanho_bin, 2)
        dados = quadro_bits[8:8 + tamanho * 8]
        return dados
    
     # Enquadra os bits usando uma FLAG pra delimitar o enquadramento.
    def enquadrar_bitstuffing(self, bits: str) -> str:
        stuffed = ""
        count = 0
        for b in bits:
            stuffed += b
            if b == '1':
                count += 1
                if count == 5:
                    stuffed += '0'  # inserção de bit de controle
                    count = 0
            else:
                count = 0
        return self.FLAG + stuffed + self.FLAG  # FLAG de início e fim
    
    # Retira as FLAGS inseridas
    def desenquadrar_bitstuffing(self, quadro_bits: str) -> str:
        # Tenta identificar os dois FLAGS delimitadores
        inicio = quadro_bits.find(self.FLAG)
        fim = quadro_bits.find(self.FLAG, inicio + 8)

        if inicio == -1 or fim == -1 or fim <= inicio:
            raise ValueError("FLAGs não encontrados corretamente")

        dados = quadro_bits[inicio + 8:fim]  # remove os FLAGS
        resultado = ""
        count = 0
        i = 0
        while i < len(dados):
            b = dados[i]
            resultado += b
            if b == '1':
                count += 1
                if count == 5:
                    i += 1  # pula o bit 0 de stuffing
                    count = 0
            else:
                count = 0
            i += 1
        return resultado
    
    # # Enquadra os bits usando uma FLAG e um sinal ESC pra delimitar o enquadramento.
    def enquadrar_bytestuffing(self, mensagem: str) -> str:
        quadro = self.FLAG1
        for c in mensagem:
            if c == self.FLAG1 or c == self.ESC:
                quadro += self.ESC  # insere byte ESC antes
            quadro += c
        quadro += self.FLAG1
        return quadro
    
    # Retira as FLAGS e ESC colocado
    def desenquadrar_bytestuffing(self, quadro: str) -> str:
        if not quadro.startswith(self.FLAG1) or not quadro.endswith(self.FLAG1):
            raise ValueError("Quadro inválido (FLAG ausente)")
        
        dados = quadro[1:-1]  # remove as FLAGS
        resultado = ""
        skip = False
        for i in range(len(dados)):
            if skip:
                skip = False
                continue
            if dados[i] == self.ESC:
                if i + 1 < len(dados):
                    resultado += dados[i + 1]  # próximo é o real
                    skip = True
            else:
                resultado += dados[i]
        return resultado