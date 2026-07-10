# PROJ_TR1 — Simulador de Camadas Física e de Enlace

Simulador didático de um sistema de comunicação digital, desenvolvido para a disciplina **Teleinformática e Redes 1 (TR1) — UnB**. A aplicação simula a transmissão de uma mensagem de texto passando pelas camadas de **enlace** e **física**, com transmissão real via socket TCP entre a interface (transmissor) e um servidor (receptor).

## Funcionalidades

### Camada Física (`physical_layer.py`)
- **Modulações banda base:** NRZ-Polar, Manchester e Bipolar (AMI)
- **Modulações por portadora:** ASK, FSK, PSK e 16-QAM
- Adição de **ruído gaussiano** configurável ao sinal
- Visualização gráfica dos sinais com matplotlib

### Camada de Enlace (`link_layer.py`)
- **Enquadramento:** contagem de caracteres, inserção de bits (bit stuffing) e inserção de bytes (byte stuffing)

### Detecção e Correção de Erros (`deteccao_erros.py`)
- Bit de paridade
- Checksum de 16 bits (complemento de um)
- CRC-32 (IEEE 802)
- **Código de Hamming** (com correção de erro de 1 bit)

### Comunicação
- Interface gráfica em **Streamlit** (transmissor)
- Servidor receptor via **socket TCP** (`servidor.py`), que desfaz todo o processo: demodula, verifica erros e desenquadra a mensagem

## Como rodar

Requer **Python 3.10+**. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install matplotlib streamlit numpy
```

Em um terminal, inicie o **servidor** (receptor):

```bash
python servidor.py
```

Em outro terminal, inicie a **interface** (transmissor):

```bash
streamlit run interface.py
```

A interface abre no navegador. Escolha a modulação, o enquadramento e o método de detecção de erros, digite uma mensagem e envie — o servidor recebe o sinal, reverte cada etapa e recupera o texto original.

## Estrutura do projeto

```
PROJ_TR1/
├── interface.py        # Interface Streamlit (transmissor)
├── servidor.py         # Servidor TCP (receptor)
├── physical_layer.py   # Modulações, demodulações e ruído
├── link_layer.py       # Enquadramento e desenquadramento
├── deteccao_erros.py   # Paridade, checksum, CRC-32 e Hamming
└── main.py
```
