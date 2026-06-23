import socket
import threading
from link_layer import Link
from deteccao_erros import DeteccaoErros
from physical_layer import PhysicalLayer



def tratar_conexao(conn, addr):
    print(f"Conectado por {addr}")
    try:
        # Recebe as informaçoes enviadas pela interface
        conn_file = conn.makefile('r')
        modulacao = conn_file.readline().strip()
        deteccao = conn_file.readline().strip()
        enquadramento = conn_file.readline().strip()
        dados = conn_file.readline().strip()

        phy = PhysicalLayer()
        link = Link()

        # Desmodula o sinal recebido da interface
        if modulacao in ['ask', 'fsk', 'psk', 'qam']:
            amostras = list(map(float, dados.split(',')))
            if modulacao == 'ask':
                bits = phy.demodular_ask(amostras)
            elif modulacao == 'fsk':
                bits = phy.demodular_fsk(amostras)
            elif modulacao == 'qam':
                bits = phy.demodular_qam16(amostras)
            elif modulacao == 'psk':
                bits = phy.demodular_psk(amostras)
        else:
            bits = phy.demodular_nrz(dados) if modulacao == 'nrz' else \
                   phy.demodular_manchester(dados) if modulacao == 'manchester' else \
                   phy.demodular_bipolar(dados)

        #detecta se houve algum erro e se necessario corrige com hamming
        det = DeteccaoErros(deteccao)
        if deteccao == 'hamming':
            bits_corrigidos = det.verificar(bits)
        else:
            if not det.verificar(bits):
                print("Erro detectado!")
                conn.sendall("Erro detectado!".encode())
                return
            if deteccao == 'crc':
                bits_corrigidos = bits[:-32]
            elif deteccao == 'checksum':
                bits_corrigidos = bits[:-16]
            else:
                bits_corrigidos = bits[:-1]  # paridade
                
        # Desenquadra a mensagem em bit
        if enquadramento == 'count':
            final = link.desenquadrar_count(bits_corrigidos)
        elif enquadramento == 'bits':
            final = link.desenquadrar_bitstuffing(bits_corrigidos)
        elif enquadramento == 'bytes':
            final1 = phy.bits_para_texto(bits_corrigidos)
            final2 = link.desenquadrar_bytestuffing(final1)
            final = phy.texto_para_bits(final2)
        else:
            raise ValueError("Enquadramento inválido")
        
        texto = phy.bits_para_texto(final) #retorna a mensagem em formato de texto
        print("Mensagem recebida:", final)
        conn.sendall((texto + '\n').encode())  # termina com \n para o cliente saber que acabou

    finally:
        conn.close()

def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 5000))
        s.listen()
        print("Servidor escutando em localhost:5000...")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=tratar_conexao, args=(conn, addr))
            thread.start()

if __name__ == '__main__':
    iniciar_servidor()