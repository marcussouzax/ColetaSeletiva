from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.relatorio_service import relatorio_service
from services.rota_service import rota_service
from utils.helpers import require_role, erro
from utils.validators import validar_campos_obrigatorios
from models.usuario import TipoUsuario

relatorio_bp = Blueprint("relatorio", __name__, url_prefix="/api/relatorios")
rota_bp = Blueprint("rota", __name__, url_prefix="/api/rotas")


# ========== RELATÓRIOS ==========

@relatorio_bp.get("/dashboard")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def dashboard():
    return jsonify(relatorio_service.dashboard_prefeitura()), 200


@relatorio_bp.get("/bairros")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def por_bairro():
    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)
    return jsonify(relatorio_service.reciclagem_por_bairro(mes, ano)), 200


@relatorio_bp.get("/materiais")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def por_material():
    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)
    return jsonify(relatorio_service.reciclagem_por_material(mes, ano)), 200


@relatorio_bp.get("/historico-mensal")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def historico_mensal():
    ano = request.args.get("ano", type=int)
    return jsonify(relatorio_service.historico_mensal(ano)), 200


@relatorio_bp.get("/ambiental")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA)
def ambiental():
    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)
    return jsonify(relatorio_service.relatorio_ambiental(mes, ano)), 200


@relatorio_bp.get("/cooperativa")
@jwt_required()
@require_role(TipoUsuario.COOPERATIVA, TipoUsuario.PREFEITURA)
def cooperativa():
    cooperativa_id = request.args.get("cooperativa_id", type=int)
    if not cooperativa_id:
        # Usa o próprio id se for cooperativa
        cooperativa_id = int(get_jwt_identity())
    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)
    return jsonify(relatorio_service.relatorio_cooperativa(cooperativa_id, mes, ano)), 200


# ========== ROTAS DE CAMINHÃO ==========

@rota_bp.post("/")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def planejar_rota():
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["data_planejada"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    resultado, status = rota_service.planejar_rota(dados)
    return jsonify(resultado), status


@rota_bp.get("/")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def listar_rotas():
    cooperativa_id = request.args.get("cooperativa_id", type=int)
    status = request.args.get("status")
    return jsonify(rota_service.listar(cooperativa_id, status)), 200


@rota_bp.get("/coletas-sem-rota")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def coletas_sem_rota():
    return jsonify(rota_service.coletas_sem_rota()), 200


@rota_bp.get("/<int:rota_id>")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def obter_rota(rota_id):
    return jsonify(rota_service.obter(rota_id)), 200


@rota_bp.patch("/<int:rota_id>/iniciar")
@jwt_required()
@require_role(TipoUsuario.COOPERATIVA, TipoUsuario.PREFEITURA)
def iniciar_rota(rota_id):
    resultado, status = rota_service.iniciar(rota_id)
    return jsonify(resultado), status


@rota_bp.patch("/<int:rota_id>/paradas/<int:parada_id>/concluir")
@jwt_required()
@require_role(TipoUsuario.COOPERATIVA)
def concluir_parada(rota_id, parada_id):
    resultado, status = rota_service.concluir_parada(rota_id, parada_id)
    return jsonify(resultado), status


@rota_bp.patch("/<int:rota_id>/finalizar")
@jwt_required()
@require_role(TipoUsuario.COOPERATIVA, TipoUsuario.PREFEITURA)
def finalizar_rota(rota_id):
    resultado, status = rota_service.finalizar(rota_id)
    return jsonify(resultado), status
