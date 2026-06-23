import streamlit as st
import socket
import matplotlib.pyplot as plt
import numpy as np

from link_layer import Link
from deteccao_erros import DeteccaoErros
from physical_layer import PhysicalLayer

# configuraçao da pagina
st.set_page_config(layout="wide")
st.title("Simulador de Comunicação - Camadas Física e de Enlace")

# sidebar com as opçoes de parametros para simular a comunicação
with st.sidebar:
    st.subheader("Configurações")
    mensagem = st.text_input("Digite a mensagem:", "Olá, mundo!") #mensagem do usuario

    modulacao = st.radio("Modulação", ['nrz', 'manchester', 'bipolar', 'ask', 'fsk', 'psk','qam']) #opçoes de modulação
    enquadramento = st.radio("Enquadramento", ['count', 'bits', 'bytes']) #opçoes de enquadramento
    deteccao = st.radio("Detecção de Erros", ['crc', 'paridade', 'hamming', 'checksum']) # opçoes de detectar erros

    enviar = st.button("Enviar")
    testar = st.button("Testar com erro (Hamming)")

# Botão "Enviar" fluxo de transmissão normal
if enviar:
    st.subheader("Resultados da Transmissão")

    link = Link()
    phy = PhysicalLayer()
    bits = phy.texto_para_bits(mensagem) # 1° Etapa tranforam mensagem em bits

    #2° Etapa tipo de enquadramento
    if enquadramento == 'count':
        quadro = link.enquadrar_count(bits)
    elif enquadramento == 'bits':
        quadro = link.enquadrar_bitstuffing(bits)
    elif enquadramento == 'bytes':
        quadro1 = link.enquadrar_bytestuffing(mensagem) # esse enquadramento funciona com a mensagem em ser em bit
        quadro = phy.texto_para_bits(quadro1)

    # 3° Etapa adição do codigo de detecção de erro
    det = DeteccaoErros(deteccao)
    bits_codificados = det.adicionar(quadro)

    # 4° Modulação e geração dos graficos
    fig = plt.figure(figsize=(10, 3))
    if modulacao == 'nrz':
        sinal = phy.nrz_polar(bits_codificados)
        plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
        plt.xlim(0, 50) # Tamanho do eixo X
        plt.title("Sinal NRZ")
    elif modulacao == 'manchester':
        sinal = phy.manchester(bits_codificados)
        plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
        plt.xlim(0, 50) # Tamanho do eixo X
        plt.title("Sinal Manchester")
    elif modulacao == 'bipolar':
        sinal = phy.bipolar(bits_codificados)
        plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
        plt.xlim(0, 50) # Tamanho do eixo X
        plt.title("Sinal Bipolar")
    elif modulacao == 'ask':
        sinal = phy.ask(bits_codificados)
        plt.plot(phy.tempo, sinal)
        plt.xlim(0, 20) # Tamanho do eixo X
        plt.title("Sinal ASK")
    elif modulacao == 'fsk':
        sinal = phy.fsk(bits_codificados)
        plt.plot(phy.tempo, sinal)
        plt.xlim(0, 10) # Tamanho do eixo X
        plt.title("Sinal FSK")
    elif modulacao == 'psk':
        sinal = phy.psk(bits_codificados)
        plt.plot(phy.tempo, sinal)
        plt.xlim(0, 20) # Tamanho do eixo X
        plt.title("Sinal QPSK")
    elif modulacao == 'qam':
        sinal = phy.qam16(bits_codificados)
        plt.plot(phy.tempo, sinal)
        plt.xlim(0, 20) # Tamanho do eixo X
        plt.title("Sinal 16-QAM")
    plt.xlabel("Tempo")
    plt.ylabel("Amplitude")
    plt.grid(True)
    st.pyplot(fig)


    # Saidas dna interface
    st.markdown(f"**Bits gerados:** `{bits}`")
    if enquadramento == "bytes":
        st.markdown(f"**Bits enquadrados:** `{quadro1}` → `{quadro}`")
    else:
        st.markdown(f"**Bits enquadrados:** `{quadro}`")
    st.markdown(f"**Bits com código de erro:** `{bits_codificados}`")

    # Envio para o servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 5000))
        s.sendall(modulacao.encode() + b'\n')
        s.sendall(deteccao.encode() + b'\n')
        s.sendall(enquadramento.encode() + b'\n')
        s.sendall((','.join(map(str, sinal)) + '\n').encode())

        file_like = s.makefile('r', encoding='utf-8')
        mensagem_final = file_like.readline().strip()
        st.markdown(f"**Mensagem recebida no servidor:** `{mensagem_final}`")

#______________________________________________________________________________________________________________________________

# Metodo para testar a correção de erro
if testar:
    st.subheader("Resultados do Teste com Erro (Hamming)")
# São as mesmas etapas que o botão enviar a cima faz
    link = Link()
    phy = PhysicalLayer()
    bits = phy.texto_para_bits(mensagem)

    if enquadramento == 'count':
        quadro = link.enquadrar_count(bits)
    elif enquadramento == 'bits':
        quadro = link.enquadrar_bitstuffing(bits)
    elif enquadramento == 'bytes':
        quadro1 = link.enquadrar_bytestuffing(mensagem)
        quadro = phy.texto_para_bits(quadro1)

    det = DeteccaoErros(deteccao)
    bits_codificados = det.adicionar(quadro)

    if deteccao == 'hamming':
        #Vamos adicionar um erro em uma posição aleatoria
        import random
        bits_lista = list(bits_codificados)
        idx = random.randint(0, len(bits_lista) - 1)
        bits_lista[idx] = '0' if bits_lista[idx] == '1' else '1'
        bits_codificados = ''.join(bits_lista)
        st.warning(f"Erro inserido na posição {idx}")

    if modulacao == 'nrz':
        sinal = phy.nrz_polar(bits_codificados)
    elif modulacao == 'manchester':
        sinal = phy.manchester(bits_codificados)
    elif modulacao == 'bipolar':
        sinal = phy.bipolar(bits_codificados)
    elif modulacao == 'ask':
        sinal = phy.ask(bits_codificados)
    elif modulacao == 'fsk':
        sinal = phy.fsk(bits_codificados)
    elif modulacao == 'psk':
        sinal = phy.psk(bits_codificados)
    elif modulacao == 'qam':
        sinal = phy.qam16(bits_codificados)

    fig = plt.figure(figsize=(10, 3))
    if modulacao in ['nrz', 'manchester', 'bipolar']:
        plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
    else:
        plt.plot(phy.tempo, sinal)
    plt.title("Sinal com erro injetado")
    plt.xlabel("Tempo")
    plt.ylabel("Amplitude")
    plt.grid(True)
    st.pyplot(fig)

    st.markdown(f"**Bits com erro inserido:** `{bits_codificados}`")

    #envio com o erro no servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 5000))
        s.sendall(modulacao.encode() + b'\n')
        s.sendall(deteccao.encode() + b'\n')
        s.sendall(enquadramento.encode() + b'\n')
        s.sendall((','.join(map(str, sinal)) + '\n').encode())

        file_like = s.makefile('r', encoding='utf-8')
        mensagem_final = file_like.readline().strip()
        st.markdown(f"**Mensagem recebida no servidor:** `{mensagem_final}`")