import googlemaps
from flask import current_app
from geopy.distance import geodesic
from models.ponto_coleta import Ecoponto
from extensions import db


class MapaService:
    """Serviço de integração com Google Maps API"""

    def _get_client(self):
        api_key = current_app.config.get("GOOGLE_MAPS_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY não configurada")
        return googlemaps.Client(key=api_key)

    def geocodificar_endereco(self, endereco: str, cidade: str = "EcoCidade, Brasil") -> dict:
        """Converte endereço em coordenadas lat/lng"""
        try:
            gmaps = self._get_client()
            resultado = gmaps.geocode(f"{endereco}, {cidade}")
            if not resultado:
                return {"erro": "Endereço não encontrado"}
            loc = resultado[0]["geometry"]["location"]
            return {
                "latitude": loc["lat"],
                "longitude": loc["lng"],
                "endereco_formatado": resultado[0]["formatted_address"],
            }
        except Exception as e:
            current_app.logger.error(f"Erro geocodificação: {e}")
            return {"erro": str(e)}

    def geocodificacao_reversa(self, latitude: float, longitude: float) -> dict:
        """Converte coordenadas em endereço legível"""
        try:
            gmaps = self._get_client()
            resultado = gmaps.reverse_geocode((latitude, longitude))
            if not resultado:
                return {"erro": "Localização não encontrada"}
            componentes = resultado[0].get("address_components", [])
            bairro = ""
            cidade = ""
            for comp in componentes:
                if "sublocality" in comp["types"]:
                    bairro = comp["long_name"]
                if "administrative_area_level_2" in comp["types"]:
                    cidade = comp["long_name"]
            return {
                "endereco_formatado": resultado[0]["formatted_address"],
                "bairro": bairro,
                "cidade": cidade,
                "latitude": latitude,
                "longitude": longitude,
            }
        except Exception as e:
            current_app.logger.error(f"Erro geocodificação reversa: {e}")
            return {"erro": str(e)}

    def buscar_ecopontos_proximos(self, latitude: float, longitude: float, raio_km: float = None) -> list:
        """Retorna ecopontos dentro do raio ordenados por distância"""
        if raio_km is None:
            raio_km = current_app.config.get("RAIO_BUSCA_ECOPONTOS_KM", 5.0)

        ecopontos = Ecoponto.query.filter_by(ativo=True).all()
        resultado = []
        origem = (latitude, longitude)

        for ep in ecopontos:
            destino = (ep.latitude, ep.longitude)
            distancia = geodesic(origem, destino).kilometers
            if distancia <= raio_km:
                ep_dict = ep.to_dict()
                ep_dict["distancia_km"] = round(distancia, 2)
                resultado.append(ep_dict)

        resultado.sort(key=lambda x: x["distancia_km"])
        return resultado

    def calcular_rota_otimizada(self, coletas: list) -> dict:
        """
        Calcula rota otimizada para caminhão de coleta via Google Maps.
        coletas: lista de dicts com latitude/longitude/id/endereco
        """
        if len(coletas) < 2:
            return {"erro": "É necessário ao menos 2 pontos para calcular rota"}

        try:
            gmaps = self._get_client()
            origem = (coletas[0]["latitude"], coletas[0]["longitude"])
            destino = (coletas[-1]["latitude"], coletas[-1]["longitude"])
            waypoints = [
                (c["latitude"], c["longitude"]) for c in coletas[1:-1]
            ]

            directions = gmaps.directions(
                origin=origem,
                destination=destino,
                waypoints=waypoints,
                optimize_waypoints=True,
                mode="driving",
                language="pt-BR",
            )

            if not directions:
                return {"erro": "Não foi possível calcular a rota"}

            rota = directions[0]
            legs = rota["legs"]
            distancia_total = sum(l["distance"]["value"] for l in legs) / 1000
            duracao_total = sum(l["duration"]["value"] for l in legs) // 60

            ordem_otimizada = rota.get("waypoint_order", [])
            pontos_ordenados = [coletas[0]]
            for i in ordem_otimizada:
                pontos_ordenados.append(coletas[1:-1][i])
            pontos_ordenados.append(coletas[-1])

            passos = []
            for leg in legs:
                for step in leg["steps"]:
                    passos.append({
                        "instrucao": step["html_instructions"],
                        "distancia": step["distance"]["text"],
                        "duracao": step["duration"]["text"],
                    })

            return {
                "distancia_total_km": round(distancia_total, 2),
                "duracao_estimada_min": duracao_total,
                "pontos_ordenados": pontos_ordenados,
                "waypoint_order": ordem_otimizada,
                "passos": passos,
                "polyline": rota["overview_polyline"]["points"],
            }

        except Exception as e:
            current_app.logger.error(f"Erro cálculo de rota: {e}")
            return {"erro": str(e)}

    def calcular_distancia(self, origem_lat: float, origem_lng: float,
                           destino_lat: float, destino_lng: float) -> dict:
        """Distância em linha reta e estimativa via API"""
        linha_reta = geodesic(
            (origem_lat, origem_lng), (destino_lat, destino_lng)
        ).kilometers

        try:
            gmaps = self._get_client()
            matrix = gmaps.distance_matrix(
                origins=[(origem_lat, origem_lng)],
                destinations=[(destino_lat, destino_lng)],
                mode="driving",
                language="pt-BR",
            )
            elemento = matrix["rows"][0]["elements"][0]
            if elemento["status"] == "OK":
                return {
                    "distancia_km": round(elemento["distance"]["value"] / 1000, 2),
                    "duracao_min": round(elemento["duration"]["value"] / 60),
                    "distancia_linha_reta_km": round(linha_reta, 2),
                }
        except Exception as e:
            current_app.logger.warning(f"API distance matrix falhou: {e}")

        return {"distancia_linha_reta_km": round(linha_reta, 2)}

    def mapa_ecopontos_url(self, latitude: float = None, longitude: float = None) -> str:
        """Gera URL do Google Maps com marcadores de todos ecopontos"""
        api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "")
        ecopontos = Ecoponto.query.filter_by(ativo=True).all()

        marcadores = "&".join(
            f"markers=color:green%7Clabel:E%7C{ep.latitude},{ep.longitude}"
            for ep in ecopontos
        )

        centro = ""
        if latitude and longitude:
            centro = f"&center={latitude},{longitude}&markers=color:blue%7Clabel:V%7C{latitude},{longitude}"

        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"size=800x600&zoom=13{centro}&{marcadores}&key={api_key}"
        )
        return url


mapa_service = MapaService()
