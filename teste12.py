import streamlit as st
import numpy as np
import ezdxf
from stl import mesh
import plotly.graph_objects as go

# Dicionário com os principais tipos de aço e suas densidades em g/cm³
steel_types = {
    "SAE 1020": 7.85,
    "SAE 1045": 7.85,
    "ASTM A36": 7.85,
    "SAE 4140": 7.85,
    "SAE 8620": 7.85,
    "AISI 304": 8.00,
    "AISI 316": 7.98,
    "SAE 4340": 7.85,
    "SAE 1212": 7.85,
    "AISI 420": 7.70
}

# Função para calcular o volume da peça
def calculate_volume(width, length, thickness):
    return width * length * thickness  # mm³

# Função para calcular o peso com base na densidade do aço
def calculate_weight(volume, density):
    # Converter volume de mm³ para cm³ (1 cm³ = 1000 mm³)
    volume_cm3 = volume / 1000.0
    # Peso = volume * densidade
    return volume_cm3 * density  # peso em gramas

# Função para criar a chapa
def create_plate(width, length, thickness):
    vertices = np.array([
        [0, 0, 0],
        [width, 0, 0],
        [width, length, 0],
        [0, length, 0],
        [0, 0, thickness],
        [width, 0, thickness],
        [width, length, thickness],
        [0, length, thickness],
    ])

    faces = np.array([
        [0, 3, 1], [1, 3, 2],  # Face inferior
        [4, 5, 7], [5, 6, 7],  # Face superior
        [0, 1, 4], [1, 5, 4],  # Face lateral 1
        [1, 2, 5], [2, 6, 5],  # Face lateral 2
        [2, 3, 6], [3, 7, 6],  # Face lateral 3
        [3, 0, 7], [0, 4, 7],  # Face lateral 4
    ])

    plate_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, face in enumerate(faces):
        for j in range(3):
            plate_mesh.vectors[i][j] = vertices[face[j], :]

    return plate_mesh, vertices

# Função para criar um arquivo DXF a partir das coordenadas Numpy
def create_dxf_from_numpy(vertices, filename='chapa.dxf'):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Criar o contorno da chapa (vista superior)
    for i in range(4):  # Apenas os quatro primeiros vértices da base (2D)
        start_point = vertices[i]
        end_point = vertices[(i + 1) % 4]  # Conectar os vértices em loop

        # Adicionar uma linha no DXF
        msp.add_line(start_point[:2], end_point[:2])  # Usando apenas coordenadas X, Y

    # Salvar o arquivo DXF
    doc.saveas(filename)

# Função para converter o mesh para Plotly
def mesh_to_plotly(plate_mesh, opacity_value):
    x, y, z = plate_mesh.vectors.reshape(-1, 3).T

    i = list(range(0, len(x), 3))
    j = list(range(1, len(y), 3))
    k = list(range(2, len(z), 3))

    fig = go.Figure(data=[
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color='lightblue',
            opacity=opacity_value  # Ajustar a opacidade dinamicamente
        )
    ])

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode='data'  # Garante que a escala seja preservada
        ),
        width=700,
        height=700,
        margin=dict(r=0, l=0, b=0, t=0)
    )

    return fig

# Interface do Streamlit
st.title("Projeto de Chapa com Cálculo de Peso e Geração de DXF")

# Inputs para as dimensões da chapa
width = st.number_input('Largura (mm)', min_value=0.0, value=100.0, step=1.0)
length = st.number_input('Comprimento (mm)', min_value=0.0, value=100.0, step=1.0)
thickness = st.number_input('Espessura (mm)', min_value=0.0, value=10.0, step=0.1)

# Lista suspensa para selecionar o tipo de aço
steel_type = st.selectbox('Selecione o tipo de aço', list(steel_types.keys()))

# Controle deslizante para opacidade
opacity_value = st.slider('Opacidade da peça', min_value=0.0, max_value=1.0, value=1.0, step=0.1)

# Inicializar sessão para armazenar a chapa gerada
if 'plate_mesh' not in st.session_state:
    st.session_state.plate_mesh = None

# Botão para gerar a chapa
if st.button('Gerar Chapa'):
    # Criar a chapa com as dimensões fornecidas
    plate, vertices = create_plate(width, length, thickness)

    # Calcular volume e peso
    volume = calculate_volume(width, length, thickness)
    density = steel_types[steel_type]  # Obter densidade com base no aço selecionado
    weight = calculate_weight(volume, density) / 1000  # Converter gramas para kg

    # Salvar a chapa em arquivo STL
    stl_path = 'chapa.stl'
    plate.save(stl_path)

    # Salvar o arquivo DXF com as coordenadas
    dxf_path = 'chapa.dxf'
    create_dxf_from_numpy(vertices, dxf_path)

    # Armazenar o mesh na sessão
    st.session_state.plate_mesh = plate

    # Exibir mensagem de sucesso com o peso
    st.success(f'Chapa gerada com peso de {weight:.3f} kg. Arquivo DXF gerado como "{dxf_path}".')

# Exibir a peça dinamicamente conforme o ajuste da opacidade
if st.session_state.plate_mesh is not None:
    fig = mesh_to_plotly(st.session_state.plate_mesh, opacity_value)
    st.plotly_chart(fig)

# Opcional: Exibir o arquivo STL e DXF para download
if st.session_state.plate_mesh is not None:
    with open('chapa.stl', 'rb') as f:
        st.download_button(
            label="Baixar Chapa STL",
            data=f,
            file_name='chapa.stl',
            mime='application/octet-stream'
        )
    
    with open('chapa.dxf', 'rb') as f:
        st.download_button(
            label="Baixar Chapa DXF",
            data=f,
            file_name='chapa.dxf',
            mime='application/octet-stream'
        )
