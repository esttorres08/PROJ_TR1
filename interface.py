import streamlit as st
import socket
import matplotlib.pyplot as plt
import numpy as np

from link_layer import Link
from deteccao_erros import DeteccaoErros
from physical_layer import PhysicalLayer

st.set_page_config(layout="wide")
st.title("Simulador de Comunicação - Camadas Física e de Enlace")

with st.sidebar:
    st.subheader("Configurações")
    mensagem = st.text_input("Digite a mensagem:", "Olá, mundo!")

    modulacao = st.radio("Modulação", ['nrz', 'manchester', 'bipolar', 'ask', 'fsk', 'psk', 'qam'])
    enquadramento = st.radio("Enquadramento", ['count', 'bits', 'bytes'])
    deteccao = st.radio("Detecção de Erros", ['crc', 'paridade', 'hamming', 'checksum'])

    st.markdown("**Parâmetros do sinal**")
    amplitude = st.slider("Amplitude", 0.5, 5.0, 1.0, 0.5)
    frequencia = st.slider("Frequência", 1, 15, 5)
    ruido = st.slider("Nível de ruído", 0.0, 10.0, 0.0, 0.1)

    enviar = st.button("Enviar")
    #testar = st.button("Testar com erro (Hamming)")

# Botão "Enviar" - fluxo normal
if enviar:
    st.subheader("Resultados da Transmissão")

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

    # Modulação com amplitude/frequência escolhidas (sinal TRANSMITIDO, sem ruído)
    if modulacao == 'nrz':
        sinal = phy.nrz_polar(bits_codificados, A=amplitude)
    elif modulacao == 'manchester':
        sinal = phy.manchester(bits_codificados, A=amplitude)
    elif modulacao == 'bipolar':
        sinal = phy.bipolar(bits_codificados, A=amplitude)
    elif modulacao == 'ask':
        sinal = phy.ask(bits_codificados, A=amplitude, f=frequencia)
    elif modulacao == 'fsk':
        sinal = phy.fsk(bits_codificados, f0=frequencia, f1=frequencia*2, A=amplitude)
    elif modulacao == 'psk':
        sinal = phy.psk(bits_codificados, A=amplitude, f=frequencia)
    elif modulacao == 'qam':
        sinal = phy.qam16(bits_codificados, A=amplitude, f=frequencia)

    # sinal RECEBIDO = sinal transmitido + ruído escolhido
    sinal_recebido = phy.adicionar_ruido(sinal, ruido)

    banda_base = modulacao in ['nrz', 'manchester', 'bipolar']

    # Gráfico 1: sinal transmitido (sem ruído)
    fig1 = plt.figure(figsize=(10, 3))
    if banda_base:
        plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
        plt.xlim(0, 50)
    else:
        plt.plot(phy.tempo, sinal)
        plt.xlim(0, 20)
    plt.title(f"Sinal transmitido ({modulacao.upper()})")
    plt.xlabel("Tempo")
    plt.ylabel("Amplitude")
    plt.grid(True)
    st.pyplot(fig1)

    # Gráfico 2: sinal recebido (com ruído)
    fig2 = plt.figure(figsize=(10, 3))
    if banda_base:
        plt.step(range(len(sinal_recebido)*2), [v for x in sinal_recebido for v in (x, x)], where='post')
        plt.xlim(0, 50)
    else:
        plt.plot(phy.tempo, sinal_recebido)
        plt.xlim(0, 20)
    plt.title(f"Sinal recebido com ruído ({modulacao.upper()})")
    plt.xlabel("Tempo")
    plt.ylabel("Amplitude")
    plt.grid(True)
    st.pyplot(fig2)

    st.markdown(f"**Bits gerados:** `{bits}`")
    if enquadramento == "bytes":
        st.markdown(f"**Bits enquadrados:** `{quadro1}` → `{quadro}`")
    else:
        st.markdown(f"**Bits enquadrados:** `{quadro}`")
    st.markdown(f"**Bits com detecção de erro:** `{bits_codificados}`")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 5000))
        s.sendall(modulacao.encode() + b'\n')
        s.sendall(deteccao.encode() + b'\n')
        s.sendall(enquadramento.encode() + b'\n')
        s.sendall((str(amplitude) + '\n').encode())
        s.sendall((str(frequencia) + '\n').encode())
        s.sendall((','.join(map(str, sinal_recebido)) + '\n').encode())

        file_like = s.makefile('r', encoding='utf-8')
        mensagem_final = file_like.readline().strip()
        st.markdown(f"**Mensagem recebida no servidor:** `{mensagem_final}`")

# Botão "Testar com erro (Hamming)"
# if testar:
#     st.subheader("Resultados do Teste com Erro (Hamming)")

#     link = Link()
#     phy = PhysicalLayer()
#     bits = phy.texto_para_bits(mensagem)

#     if enquadramento == 'count':
#         quadro = link.enquadrar_count(bits)
#     elif enquadramento == 'bits':
#         quadro = link.enquadrar_bitstuffing(bits)
#     elif enquadramento == 'bytes':
#         quadro1 = link.enquadrar_bytestuffing(mensagem)
#         quadro = phy.texto_para_bits(quadro1)

#     det = DeteccaoErros(deteccao)
#     bits_codificados = det.adicionar(quadro)

#     if deteccao == 'hamming':
#         import random
#         bits_lista = list(bits_codificados)
#         idx = random.randint(0, len(bits_lista) - 1)
#         bits_lista[idx] = '0' if bits_lista[idx] == '1' else '1'
#         bits_codificados = ''.join(bits_lista)
#         st.warning(f"Erro inserido na posição {idx}")

#     if modulacao == 'nrz':
#         sinal = phy.nrz_polar(bits_codificados, A=amplitude)
#     elif modulacao == 'manchester':
#         sinal = phy.manchester(bits_codificados, A=amplitude)
#     elif modulacao == 'bipolar':
#         sinal = phy.bipolar(bits_codificados, A=amplitude)
#     elif modulacao == 'ask':
#         sinal = phy.ask(bits_codificados, A=amplitude, f=frequencia)
#     elif modulacao == 'fsk':
#         sinal = phy.fsk(bits_codificados, f0=frequencia, f1=frequencia*2, A=amplitude)
#     elif modulacao == 'psk':
#         sinal = phy.psk(bits_codificados, A=amplitude, f=frequencia)
#     elif modulacao == 'qam':
#         sinal = phy.qam16(bits_codificados, A=amplitude, f=frequencia)

#     sinal = phy.adicionar_ruido(sinal, ruido)

#     fig = plt.figure(figsize=(10, 3))
#     if modulacao in ['nrz', 'manchester', 'bipolar']:
#         plt.step(range(len(sinal)*2), [v for x in sinal for v in (x, x)], where='post')
#     else:
#         plt.plot(phy.tempo, sinal)
#     plt.title("Sinal com erro injetado")
#     plt.xlabel("Tempo")
#     plt.ylabel("Amplitude")
#     plt.grid(True)
#     st.pyplot(fig)

#     st.markdown(f"**Bits com erro inserido:** `{bits_codificados}`")

#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         s.connect(('localhost', 5000))
#         s.sendall(modulacao.encode() + b'\n')
#         s.sendall(deteccao.encode() + b'\n')
#         s.sendall(enquadramento.encode() + b'\n')
#         s.sendall((str(amplitude) + '\n').encode())
#         s.sendall((str(frequencia) + '\n').encode())
#         s.sendall((','.join(map(str, sinal)) + '\n').encode())

#         file_like = s.makefile('r', encoding='utf-8')
#         mensagem_final = file_like.readline().strip()
#         st.markdown(f"**Mensagem recebida no servidor:** `{mensagem_final}`")