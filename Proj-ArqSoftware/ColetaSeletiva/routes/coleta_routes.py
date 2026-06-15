from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.coleta_service import coleta_service
from utils.helpers import require_role, erro
from utils.validators import validar_campos_obrigatorios, validar_data_futura, validar_materiais
from models.usuario import TipoUsuario

coleta_bp = Blueprint("coleta", __name__, url_prefix="/api/coletas")


@coleta_bp.post("/")
@jwt_required()
def agendar_coleta():
    usuario_id = int(get_jwt_identity())
    dados = request.get_json() or {}
    faltando = validar_campos_obrigatorios(dados, ["endereco", "bairro", "data_agendada"])
    if faltando:
        return erro(f"Campos obrigatórios faltando: {', '.join(faltando)}")
    valida, msg = validar_data_futura(dados["data_agendada"])
    if not valida:
        return erro(msg)
    if "materiais" in dados:
        valida_mat, msg_mat = validar_materiais(dados["materiais"])
        if not valida_mat:
            return erro(msg_mat)
    resultado, status = coleta_service.agendar(usuario_id, dados)
    return jsonify(resultado), status


@coleta_bp.get("/minhas")
@jwt_required()
def minhas_coletas():
    usuario_id = int(get_jwt_identity())
    status = request.args.get("status")
    coletas = coleta_service.listar_por_usuario(usuario_id, status)
    return jsonify(coletas), 200


@coleta_bp.get("/<int:coleta_id>")
@jwt_required()
def obter_coleta(coleta_id):
    return jsonify(coleta_service.obter(coleta_id)), 200


@coleta_bp.delete("/<int:coleta_id>")
@jwt_required()
def cancelar_coleta(coleta_id):
    usuario_id = int(get_jwt_identity())
    resultado, status = coleta_service.cancelar(coleta_id, usuario_id)
    return jsonify(resultado), status


# --- Gestão (prefeitura e cooperativa) ---
@coleta_bp.get("/")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def listar_coletas():
    status = request.args.get("status")
    bairro = request.args.get("bairro")
    cooperativa_id = request.args.get("cooperativa_id", type=int)
    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = request.args.get("por_pagina", 20, type=int)
    resultado = coleta_service.listar_todas(status, bairro, cooperativa_id, pagina, por_pagina)
    return jsonify(resultado), 200


@coleta_bp.patch("/<int:coleta_id>/status")
@jwt_required()
@require_role(TipoUsuario.PREFEITURA, TipoUsuario.COOPERATIVA)
def atualizar_status(coleta_id):
    dados = request.get_json() or {}
    if "status" not in dados:
        return erro("Campo 'status' obrigatório")
    cooperativa_id = int(get_jwt_identity()) if True else None
    resultado, status = coleta_service.atualizar_status(
        coleta_id, dados["status"],
        cooperativa_id=cooperativa_id,
        dados_extras=dados.get("extras"),
    )
    return jsonify(resultado), status
