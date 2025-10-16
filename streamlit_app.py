# streamlit_app.py
import os
import io
import json
import requests
import streamlit as st
from typing import Optional, Dict, Any, List

# ============================
# Configuração básica
# ============================
st.set_page_config(page_title="Station Manager", page_icon="🛰️", layout="wide")

# ============================
# Estado & Defaults seguros
# ============================
DEFAULT_API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8006/station_manager")
if "api_host" not in st.session_state or not st.session_state.get("api_host"):
    st.session_state.api_host = DEFAULT_API_HOST
if "auth" not in st.session_state:
    st.session_state.auth = {"token": None, "token_type": "bearer"}
if "last_list" not in st.session_state:
    st.session_state.last_list = None

# ============================
# Helpers HTTP
# ============================
def get_api_base() -> str:
    base = st.session_state.get("api_host") or DEFAULT_API_HOST
    if not isinstance(base, str) or not base.strip():
        base = DEFAULT_API_HOST
        st.session_state.api_host = base
    return base.rstrip("/")

def api_url(path: str) -> str:
    base = get_api_base()
    path = path if path.startswith("/") else f"/{path}"
    return f"{base}{path}"

def _headers(auth_required: bool = False) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if auth_required and st.session_state.auth.get("token"):
        token = st.session_state.auth.get("token")
        token_type = st.session_state.auth.get("token_type", "bearer") or "bearer"
        # format "Bearer <token>" (capitalize token type for clarity)
        headers["Authorization"] = f"{token_type.capitalize()} {token}"
    return headers

def http_get(path: str, params: Optional[dict] = None, auth: bool = False, timeout: int = 60):
    try:
        r = requests.get(api_url(path), params=params, headers=_headers(auth), timeout=timeout)
        ct = r.headers.get("content-type", "")
        if r.ok:
            return True, (r.json() if "application/json" in ct else r.text)
        else:
            try:
                return False, r.json()
            except Exception:
                return False, {"status_code": r.status_code, "text": r.text}
    except requests.RequestException as e:
        return False, {"error": f"Falha de conexão: {e}", "url": api_url(path)}

def http_post(path: str, body: Optional[dict] = None, auth: bool = False, files: Optional[dict] = None,
              params: Optional[dict] = None, timeout: int = 120):
    try:
        if files:
            r = requests.post(api_url(path), params=params, files=files, headers=_headers(auth), timeout=timeout)
        else:
            r = requests.post(api_url(path), params=params, json=body, headers=_headers(auth), timeout=timeout)
        ct = r.headers.get("content-type", "")
        if r.ok:
            if "application/json" in ct:
                return True, r.json()
            try:
                return True, r.json()
            except Exception:
                return True, r.text
        else:
            try:
                return False, r.json()
            except Exception:
                return False, {"status_code": r.status_code, "text": r.text}
    except requests.RequestException as e:
        return False, {"error": f"Falha de conexão: {e}", "url": api_url(path)}

def http_delete(path: str, auth: bool = False, timeout: int = 60):
    try:
        r = requests.delete(api_url(path), headers=_headers(auth), timeout=timeout)
        if r.ok:
            try:
                return True, r.json()
            except Exception:
                return True, r.text
        else:
            try:
                return False, r.json()
            except Exception:
                return False, {"status_code": r.status_code, "text": r.text}
    except requests.RequestException as e:
        return False, {"error": f"Falha de conexão: {e}", "url": api_url(path)}

# ============================
# Sidebar: Config + Login + Menu
# ============================
with st.sidebar:
    st.markdown("## 🛰️ Station Manager")
    st.caption("FastAPI + Streamlit • Hexagonal • Clean Code")

    # Config
    with st.expander("⚙️ Configuração", expanded=True):
        current_base = st.session_state.get("api_host") or DEFAULT_API_HOST
        st.session_state.api_host = st.text_input(
            "API Host",
            value=current_base,
            help="Ex.: http://127.0.0.1:8004/station_manager",
        )
        st.caption(f"Base atual: `{get_api_base()}`")

    # Auth
    with st.expander("🔐 Autenticação", expanded=False):
        with st.form("login_form", clear_on_submit=False):
            user_name = st.text_input("Usuário", value="", autocomplete="username")
            password = st.text_input("Senha", value="", type="password", autocomplete="current-password")
            login_clicked = st.form_submit_button("Entrar")

        if login_clicked:
            if not user_name or not password:
                st.error("Informe usuário e senha.")
            else:
                ok, data = http_post("/OAuth/token", {"user_name": user_name, "password": password}, auth=False)
                if ok and isinstance(data, dict) and "access_token" in data:
                    st.session_state.auth["token"] = data["access_token"]
                    st.session_state.auth["token_type"] = data.get("token_type", "bearer")
                    st.success("Login realizado!")
                else:
                    st.error(f"Falha no login: {data}")

        token = st.session_state.auth.get("token")
        if token:
            st.caption("Sessão autenticada ✅")
            if st.button("Sair"):
                st.session_state.auth = {"token": None, "token_type": "bearer"}
                if not st.session_state.get("api_host"):
                    st.session_state.api_host = DEFAULT_API_HOST
                st.experimental_rerun()
        else:
            st.caption("Sem sessão autenticada")

    st.markdown("---")
    st.markdown("### 📚 Menu")
    page = st.radio(
        label="Escolha a ação",
        options=[
            "📄 Listar estações (GET /stations)",
            "🔍 Obter por código (GET /stations/{codigo_estacao})",
            "➕ Criar/Atualizar (POST /stations)",
            "🗑️ Remover por código (DELETE /stations/{codigo_estacao})",
            "📦 Upsert em lote (POST /stations/estacoes_lote)",
            "📁 Importar arquivo (POST /station/import)",
        ],
        label_visibility="collapsed",
    )

# ============================
# Utilidades de exibição
# ============================
def show_json_or_table(payload: Any):
    """
    Exibe lista/dict como tabela ou JSON, dependendo do formato.
    """
    if isinstance(payload, list):
        if len(payload) == 0:
            st.info("Sem resultados.")
            return
        try:
            st.dataframe(payload, use_container_width=True)
            return
        except Exception:
            st.json(payload)
            return
    if isinstance(payload, dict):
        st.json(payload)
        return
    # fallback
    st.text(str(payload))

# ============================
# Páginas
# ============================
def page_listar():
    st.header("📄 Listar estações")
    st.write("Recupera a lista de estações. Use o filtro 'dado_manual' para mostrar apenas estações manuais/não manuais.")
    col1, col2 = st.columns([3,1])
    with col1:
        # default False per openapi default: false
        dado_manual_choice = st.selectbox(
            "Filtrar por dado_manual",
            options=["Todos", "Apenas manual (true)", "Apenas não-manual (false)"],
            index=0,
            help="Escolha 'Todos' para omitir o filtro."
        )
    with col2:
        btn = st.button("🔄 Carregar lista")

    if btn:
        params = {}
        if dado_manual_choice == "Apenas manual (true)":
            params["dados_estacao_manual"] = "true"
        elif dado_manual_choice == "Apenas não-manual (false)":
            params["dados_estacao_manual"] = "false"

        ok, data = http_get("/stations", params=params, auth=False)
        if ok:
            st.session_state.last_list = data
        else:
            st.session_state.last_list = None
            st.error(f"Erro ao listar: {data}")

    lista = st.session_state.last_list
    if lista:
        try:
            st.success(f"{len(lista)} registro(s) retornado(s).")
        except Exception:
            st.success("Resultados retornados.")
        show_json_or_table(lista)
        jbytes = json.dumps(lista, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("⬇️ Baixar JSON", data=jbytes, file_name="stations_list.json", mime="application/json")

def page_buscar_por_codigo():
    st.header("🔍 Obter estação por código")
    st.write("Busca detalhada de uma estação pelo `codigo_estacao`.")
    col1, col2 = st.columns([3, 1])
    with col1:
        codigo = st.text_input("codigo_estacao", placeholder="Ex.: 13578000")
    with col2:
        buscar = st.button("Buscar")
    if buscar and codigo.strip():
        ok, data = http_get(f"/stations/{codigo.strip()}", auth=False)
        if ok:
            show_json_or_table(data)
        else:
            st.error(f"Erro: {data}")

def page_criar_atualizar():
    st.header("➕ Criar/Atualizar estação (upsert)")
    st.caption("Obrigatórios: ponto, codigo_estacao, id_noaa, conversor, sensor, bacia.")
    with st.form("form_station"):
        # Linha 1
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            ponto = st.text_input("ponto *")
            sensor = st.text_input("sensor *")
        with c2:
            codigo_estacao = st.text_input("codigo_estacao *")
            bacia = st.text_input("bacia *")
        with c3:
            id_noaa = st.text_input("id_noaa *")
            conversor = st.number_input("conversor *", step=1, value=0)

        st.markdown("##### Dados opcionais")
        c4, c5, c6 = st.columns(3)
        with c4:
            nome_estacao = st.text_input("nome_estacao")
            altitude = st.text_input("altitude")
            cota_min = st.number_input("cota_min", step=1, value=0, format="%d")
        with c5:
            nome_bacia = st.text_input("nome_bacia")
            latitude = st.text_input("latitude")
            janela = st.number_input("janela", step=1, value=0, format="%d")
        with c6:
            rio_nome = st.text_input("rio_nome")
            longitude = st.text_input("longitude")
            previsao = st.number_input("previsao", step=1, value=0, format="%d")

        data_periodo_escala_inicio = st.text_input(
            "data_periodo_escala_inicio (ISO 8601)",
            help="Ex.: 2025-10-01T12:34:56Z"
        )
        c7, c8 = st.columns(2)
        with c7:
            dado_manual = st.checkbox("dado_manual", value=False)
        with c8:
            data_forecast = st.checkbox("data_forecast", value=False)

        submitted = st.form_submit_button("Salvar")

    if submitted:
        def as_nullable_str(s: str) -> Optional[str]:
            return s if isinstance(s, str) and s.strip() else None

        def as_nullable_int(n: int) -> Optional[int]:
            try:
                n_int = int(n)
                return n_int if n_int != 0 else None
            except Exception:
                return None

        body = {
            "ponto": (ponto or "").strip(),
            "codigo_estacao": (codigo_estacao or "").strip(),
            "id_noaa": (id_noaa or "").strip(),
            "conversor": int(conversor),
            "sensor": (sensor or "").strip(),
            "bacia": (bacia or "").strip(),
            "nome_estacao": as_nullable_str(nome_estacao),
            "nome_bacia": as_nullable_str(nome_bacia),
            "rio_nome": as_nullable_str(rio_nome),
            "altitude": as_nullable_str(altitude),
            "latitude": as_nullable_str(latitude),
            "longitude": as_nullable_str(longitude),
            "data_periodo_escala_inicio": as_nullable_str(data_periodo_escala_inicio),
            "dado_manual": bool(dado_manual),
            "data_forecast": bool(data_forecast),
            "cota_min": as_nullable_int(cota_min),
            "janela": as_nullable_int(janela),
            "previsao": as_nullable_int(previsao),
        }

        obrigatorios = ["ponto", "codigo_estacao", "id_noaa", "conversor", "sensor", "bacia"]
        faltando = [k for k in obrigatorios if not body.get(k)]
        if faltando:
            st.error(f"Campos obrigatórios faltando: {', '.join(faltando)}")
        else:
            ok, data = http_post("/stations", body=body, auth=True)
            if ok:
                st.success("Estação criada/atualizada com sucesso!")
                try:
                    show_json_or_table(data)
                except Exception:
                    st.write(data)
            else:
                st.error("Erro ao salvar estação.")
                st.json(data)

def page_remover_por_codigo():
    st.header("🗑️ Remover estação por código")
    st.write("Remove a estação informada por `codigo_estacao`.")
    col1, col2 = st.columns([3, 1])
    with col1:
        codigo = st.text_input("codigo_estacao", placeholder="Ex.: 13578000")
    with col2:
        remover = st.button("Remover", type="secondary")
    if remover and codigo.strip():
        ok, data = http_delete(f"/stations/{codigo.strip()}", auth=True)
        if ok:
            st.success("Removido com sucesso (ou não existia).")
            try:
                show_json_or_table(data)
            except Exception:
                st.write(data)
        else:
            st.error(f"Erro: {data}")

def page_upsert_lote():
    st.header("📦 Upsert em lote (JSON ou campos)")
    st.caption("Envie um **array JSON** de objetos `StationModel` ou insira manualmente.")

    col_up1 = st.columns(1)
    with col_up1[0]:
        uploaded_json = st.file_uploader("Upload de arquivo JSON", type=["json"])

    if 'station_list' not in st.session_state:
        st.session_state['station_list'] = []

    # Inicializar campos caso necessário
    for key, default in [
        ('ponto', ''), ('codigo_estacao', ''), ('id_noaa', ''), ('conversor', 0),
        ('sensor', ''), ('bacia', ''), ('data_forecast', False),
        ('cota_min', 0), ('janela', 0), ('previsao', 0)
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    with st.form(key='station_form', clear_on_submit=True):
        ponto = st.text_input("Ponto", key='ponto')
        codigo_estacao = st.text_input("Código Estação", key='codigo_estacao')
        id_noaa = st.text_input("ID NOAA", key='id_noaa')
        conversor = st.number_input("Conversor", value=st.session_state['conversor'], min_value=0, key='conversor')
        sensor = st.text_input("Sensor", key='sensor')
        bacia = st.text_input("Bacia", key='bacia')
        data_forecast = st.checkbox("Ativar Previsão", value=st.session_state['data_forecast'], key='data_forecast')
        cota_min = st.number_input("Cota minima", value=st.session_state['cota_min'], min_value=0, key='cota_min')
        janela = st.number_input("Janela Previsão", value=st.session_state['janela'], min_value=0, key='janela')
        previsao = st.number_input("Qtd horas previsão", value=st.session_state['previsao'], min_value=0, key='previsao')

        add_button = st.form_submit_button("Adicionar à lista")

        if add_button:
            new_station = {
                "ponto": st.session_state.ponto,
                "codigo_estacao": st.session_state.codigo_estacao,
                "id_noaa": st.session_state.id_noaa,
                "conversor": st.session_state.conversor,
                "sensor": st.session_state.sensor,
                "bacia": st.session_state.bacia,
                "data_forecast": st.session_state.data_forecast,
                "cota_min": st.session_state.cota_min,
                "janela": st.session_state.janela,
                "previsao": st.session_state.previsao,
            }
            st.session_state.station_list.append(new_station)
            st.rerun()

    st.write("### Lista de estações a enviar")
    st.dataframe(st.session_state.station_list)

    enviar = st.button("Enviar lote")
    if enviar:
        payload = None
        if st.session_state.station_list:
            payload = st.session_state.station_list
        elif uploaded_json is not None:
            try:
                payload = json.load(uploaded_json)
            except Exception as e:
                st.error(f"JSON inválido no arquivo: {e}")
        else:
            st.warning("Forneça um arquivo JSON ou adicione itens manualmente.")

        if payload is not None:
            if not isinstance(payload, list):
                st.error("O JSON deve ser um **array** de StationModel.")
            else:
                # Substitua pelo seu método
                ok, data = http_post("/stations/estacoes_lote", body=payload, auth=True)
                if ok:
                    st.success("Lote processado com sucesso!")
                    try:
                        show_json_or_table(data)
                        st.session_state.station_list = []
                    except Exception:
                        st.write(data)
                else:
                    st.error("Erro ao processar o lote.")
                    st.json(data)

def page_importar_arquivo():
    st.header("📁 Importar estações por arquivo")
    st.caption("Endpoint: `POST /station/import` (multipart/form-data).")
    upsert_existing = st.checkbox("upsert_existing", value=False, help="Se marcado, atualiza registros existentes.")
    uploaded_file = st.file_uploader("Selecione o arquivo", type=["csv", "xlsx", "xls", "json", "txt"])
    importar = st.button("Importar")
    if importar:
        if uploaded_file is None:
            st.warning("Selecione um arquivo.")
        else:
            file_bytes = uploaded_file.read()
            # envia multipart com campo 'upload' conforme schema
            files = {"upload": (uploaded_file.name, file_bytes)}
            params = {"upsert_existing": str(bool(upsert_existing)).lower()}
            ok, data = http_post("/station/import", files=files, params=params, auth=True)
            if ok:
                st.success("Importação enviada com sucesso!")
                try:
                    show_json_or_table(data)
                except Exception:
                    st.write(data)
            else:
                st.error("Erro na importação.")
                st.json(data)

# ============================
# Router das páginas
# ============================
if page.startswith("📄"):
    page_listar()
elif page.startswith("🔍"):
    page_buscar_por_codigo()
elif page.startswith("➕"):
    page_criar_atualizar()
elif page.startswith("🗑️"):
    page_remover_por_codigo()
elif page.startswith("📦"):
    page_upsert_lote()
elif page.startswith("📁"):
    page_importar_arquivo()

# ============================
# Rodapé discreto
# ============================
st.markdown("---")
st.caption(f"API base: `{get_api_base()}` • Token: {'✅' if st.session_state.auth.get('token') else '❌'}")
