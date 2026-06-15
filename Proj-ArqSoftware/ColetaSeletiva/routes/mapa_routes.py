from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.mapa_service import mapa_service
from utils.helpers import erro
from utils.validators import validar_coordenadas

mapa_bp = Blueprint("mapa", __name__, url_prefix="/api/mapa")


@mapa_bp.get("/geocodificar")
def geocodificar():
    """Converte endereço em lat/lng"""
    endereco = request.args.get("endereco")
    if not endereco:
        return erro("Parâmetro 'endereco' obrigatório")
    resultado = mapa_service.geocodificar_endereco(endereco)
    return jsonify(resultado), 200 if "erro" not in resultado else 400


@mapa_bp.get("/geocodificacao-reversa")
def geocodificacao_reversa():
    """Converte lat/lng em endereço"""
    lat = request.args.get("latitude", type=float)
    lng = request.args.get("longitude", type=float)
    if lat is None or lng is None:
        return erro("Parâmetros 'latitude' e 'longitude' são obrigatórios")
    if not validar_coordenadas(lat, lng):
        return erro("Coordenadas inválidas")
    resultado = mapa_service.geocodificacao_reversa(lat, lng)
    return jsonify(resultado), 200 if "erro" not in resultado else 400


@mapa_bp.get("/distancia")
def calcular_distancia():
    """Distância entre dois pontos"""
    origem_lat = request.args.get("origem_lat", type=float)
    origem_lng = request.args.get("origem_lng", type=float)
    destino_lat = request.args.get("destino_lat", type=float)
    destino_lng = request.args.get("destino_lng", type=float)
    if None in [origem_lat, origem_lng, destino_lat, destino_lng]:
        return erro("Parâmetros: origem_lat, origem_lng, destino_lat, destino_lng")
    resultado = mapa_service.calcular_distancia(origem_lat, origem_lng, destino_lat, destino_lng)
    return jsonify(resultado), 200


@mapa_bp.post("/rota-otimizada")
@jwt_required()
def rota_otimizada():
    """
    Calcula rota otimizada entre múltiplos pontos.
    Body: { "pontos": [{"latitude": ..., "longitude": ..., "endereco": ...}] }
    """
    dados = request.get_json() or {}
    pontos = dados.get("pontos", [])
    if len(pontos) < 2:
        return erro("São necessários ao menos 2 pontos")
    resultado = mapa_service.calcular_rota_otimizada(pontos)
    return jsonify(resultado), 200 if "erro" not in resultado else 500
