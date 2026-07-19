import streamlit as st
import pandas as pd
from pathlib import Path
from io import StringIO
import time
import os

from huggingface_hub import HfApi

# =========================
# CONFIGURAÇÃO
# =========================

REPO_ID = "regiscardoso/Ceci"  # ← troque aqui
ARQUIVO_CSV = "presentes.csv"
HF_TOKEN = os.environ.get("HF_TOKEN")

st.set_page_config(
    page_title="Cecília in Fest",
    page_icon="🎀",
    layout="wide"
)

#st.write("Token carregado:", "✅ Sim" if os.environ.get("HF_TOKEN") else "❌ Não encontrado")


# =========================
# CSS
# =========================
st.markdown("""
<style>

:root {
    --primary-color: #ec407a !important;
    --secondary-background-color: #fce4ec !important;
}

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #ffe4ef 0%, #ffffff 100%);
}

h1, h2, h3 {
    color: #ad1457 !important;
}

p, span, div, label {
    color: #4a154b;
}

/* NUMBER INPUT */
div[data-testid="stNumberInput"] [data-testid="stNumberInputContainer"],
div[data-testid="stNumberInput"] [data-testid="stNumberInputContainer"] div {
    background-color: #fce4ec !important;
    border: 2px solid #f8bbd0 !important;
    border-radius: 12px !important;
}
div[data-testid="stNumberInput"] input {
    background-color: transparent !important;
    color: #ad1457 !important;
    font-weight: bold !important;
    text-align: center !important;
}
div[data-testid="stNumberInput"] button {
    background-color: #f8bbd0 !important;
    color: #ad1457 !important;
    border-radius: 10px !important;
    border: none !important;
}

/* BOTÃO SALVAR */
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #ec407a, #d81b60) !important;
    color: white !important;
    border-radius: 999px !important;
    font-weight: bold !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(236, 64, 122, 0.35) !important;
    width: 100% !important;
    height: 56px !important;
    font-size: 15px !important;
    -webkit-tap-highlight-color: transparent !important;
}

div[data-testid="stButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(236, 64, 122, 0.5) !important;
}

@media (max-width: 768px) {
    div[data-testid="stButton"] button {
        height: 48px !important;
        font-size: 13px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES
# =========================

@st.cache_data(ttl=30)
def carregar_dados():
    """Lê o CSV direto do repositório no Hugging Face."""
    api = HfApi()
    try:
        conteudo = api.hf_hub_download(
            repo_id=REPO_ID,
            filename=ARQUIVO_CSV,
            repo_type="space",
            token=HF_TOKEN
        )
        return pd.read_csv(conteudo)
    except Exception:
        # Se o arquivo não existir ainda no repo, retorna vazio
        return pd.DataFrame(
            columns=["item", "quantidade_necessaria", "quantidade_marcada", "descricao"]
        )

def salvar_dados(df_para_salvar):
    """Sobe o CSV atualizado de volta ao repositório."""
    api = HfApi()
    conteudo_csv = df_para_salvar.to_csv(index=False)
    api.upload_file(
        path_or_fileobj=conteudo_csv.encode("utf-8"),
        path_in_repo=ARQUIVO_CSV,
        repo_id=REPO_ID,
        repo_type="space",
        token=HF_TOKEN,
        commit_message="Atualização de presentes"
    )
    st.cache_data.clear()

# =========================
# DADOS
# =========================

df = carregar_dados()
df.columns = df.columns.str.strip()

for col in ["descrição", "Descrição", "Descricao"]:
    if col in df.columns:
        df = df.rename(columns={col: "descricao"})

df["faltam"] = df["quantidade_necessaria"] - df["quantidade_marcada"]

# =========================
# HEADER
# =========================

col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.image("bebe.jpeg", width=300)

with col_title:
    st.title("🎀 Cecília in Fest")
    st.write(
        "Dizem que o enxoval de um bebê é um quebra-cabeça, né? "
        "Para nos ajudar a completar todas as peças, "
        "fizemos uma listinha com os itens."
    )
    st.write("-> Selecione a quantidade desejada.")
    st.write("-> Clique em 💝 Salvar.")
    st.write("Agradecemos de coração pelo carinho 💕")

# =========================
# MÉTRICAS
# =========================

total_solicitado = int(df["quantidade_necessaria"].sum())
total_marcado = int(df["quantidade_marcada"].sum())
total_faltante = max(0, total_solicitado - total_marcado)

c1, c2, c3 = st.columns(3)
c1.metric("Solicitados", total_solicitado)
c2.metric("Marcados", total_marcado)
c3.metric("Faltam", total_faltante)

st.progress(total_marcado / total_solicitado if total_solicitado > 0 else 0)
st.divider()

# =========================
# ITENS
# =========================

itens_disponiveis = df[df["faltam"] > 0].copy()

if not itens_disponiveis.empty:

    for idx, row in itens_disponiveis.iterrows():

        with st.container(border=True):

            col_info, col_qtd, col_btn = st.columns([3, 1, 1])

            with col_info:
                st.markdown(f"**{row['item']}**")
                if "descricao" in df.columns:
                    desc = str(row["descricao"]).strip()
                    if desc and desc.lower() != "nan":
                        st.caption(f"Dica: {desc}")

            with col_qtd:
                st.number_input(
                    "Qtd",
                    min_value=1,
                    max_value=int(row["faltam"]),
                    value=1,
                    key=f"qtd_{idx}"
                )
                st.markdown(
                    f"<p style='font-size:11px;margin-top:-8px;color:#ad1457;text-align:center;'>"
                    f"Disponível: {int(row['faltam'])}</p>",
                    unsafe_allow_html=True
                )

            with col_btn:
                if st.button("💝 Salvar", key=f"salvar_{idx}", use_container_width=True):
                    with st.spinner("Salvando..."):
                        qtd = st.session_state.get(f"qtd_{idx}", 1)
                        df.loc[idx, "quantidade_marcada"] += qtd
                        df_final = df.drop(columns=["faltam"])
                        salvar_dados(df_final)
                    st.toast(f"'{row['item']}' salvo com sucesso!", icon="💖")
                    st.success("Muito obrigado! A Cecília agradece seu carinho! 💕")
                    time.sleep(2)
                    st.rerun()

else:
    st.success("Todos os presentes já foram escolhidos! 🎉")

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.caption("As escolhas são anônimas.")