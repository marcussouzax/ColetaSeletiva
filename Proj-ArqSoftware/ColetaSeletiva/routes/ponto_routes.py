from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ponto_service import ecoponto_service, notificacao_service
from utils.helpers import require_role, erro
from utils.validators import validar_campos_obrigatorios, validar_coordenadas
from models.usuario import TipoUsuario

ecoponto_bp = Blueprint("ecoponto", __name__, url_prefix="/api/ecopontos")
notificacao_bp = Blueprint("notificacao", __name__, url_prefix="/api/notificacoes")


# ========== ECOPONTOS ==========

@ecoponto_bp.get("/")
def listar_ecopontos():
    bairro = request.args.get("bairro")
    material = request.args.get("material")
    ecopontos = ecoponto_service.listar(bairro=bairro, material=material)
    return jsonify(ecopontos), 200


@ecoponto_bp.get("/proximos")
def ecopontos_proximos():
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    raio = request.args.get("raio_km", type=float)
    if lat is None or lng is None:
        return erro("Parâmetros 'latitude' e 'longitude' são obrigatórios")
    if not validar_coordenadas(lat, lng):
        return erro("Coordenadas inválidas")
    resultado = ecoponto_service.buscar_proximos(lat, lng, raio)
    return jsonify(resultado), 200


@ecoponto_bp.get("/mapa")
def mapa_ecopontos():
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    return jsonify(ecoponto_service.mapa_url(lat, lng)), 200


@ecoponto_bp.get("/<int:ecoponto_id>")
def obter_ecoponto(ecoponto_id):
    return jsonify(ecoponto_service.obter(ecoponto_id)), 200


@ecoponto_bp.post("/")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def criar_ecoponto():
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["nome", "endereco", "bairro"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    resultado, status = ecoponto_service.criar(dados)
    return jsonify(resultado), status


@ecoponto_bp.put("/<int:ecoponto_id>")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def atualizar_ecoponto(ecoponto_id):
    dados = request.get_json() or {}
    resultado, status = ecoponto_service.atualizar(ecoponto_id, dados)
    return jsonify(resultado), status


@ecoponto_bp.delete("/<int:ecoponto_id>")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def desativar_ecoponto(ecoponto_id):
    resultado, status = ecoponto_service.desativar(ecoponto_id)
    return jsonify(resultado), status


# ========== NOTIFICAÇÕES ==========

@notificacao_bp.get("/bairro")
def notificacoes_bairro():
    bairro = request.args.get("bairro")
    if not bairro:
        return erro("Parâmetro 'bairro' obrigatório")
    return jsonify(notificacao_service.listar_por_bairro(bairro)), 200


@notificacao_bp.get("/minhas")
@jwt_required()
def minhas_notificacoes():
    usuario_id = int(get_jwt_identity())
    apenas_nao_lidas = request.args.get("nao_lidas", "false").lower() == "true"
    return jsonify(notificacao_service.listar_usuario(usuario_id, apenas_nao_lidas)), 200


@notificacao_bp.patch("/<int:notificacao_id>/ler")
@jwt_required()
def marcar_lida(notificacao_id):
    usuario_id = int(get_jwt_identity())
    resultado, status = notificacao_service.marcar_lida(notificacao_id, usuario_id)
    return jsonify(resultado), status


@notificacao_bp.patch("/ler-todas")
@jwt_required()
def marcar_todas_lidas():
    usuario_id = int(get_jwt_identity())
    resultado, status = notificacao_service.marcar_todas_lidas(usuario_id)
    return jsonify(resultado), status


@notificacao_bp.post("/calendario")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def criar_calendario():
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["bairro", "data_coleta"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    resultado, status = notificacao_service.criar_calendario(dados)
    return jsonify(resultado), status
