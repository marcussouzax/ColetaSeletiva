from extensions import db
from models.rota import Rota, ParadaRota, StatusRota
from models.coleta import Coleta, StatusColeta
from models.ponto_coleta import Ecoponto
from services.mapa_service import mapa_service
from datetime import datetime


class RotaService:

    def planejar_rota(self, dados: dict) -> tuple[dict, int]:
        """Cria uma rota otimizada a partir de coletas pendentes ou ecopontos"""
        coletas_ids = dados.get("coletas_ids", [])
        ecopontos_ids = dados.get("ecopontos_ids", [])

        pontos = []

        for cid in coletas_ids:
            c = Coleta.query.get(cid)
            if c and c.latitude and c.longitude:
                pontos.append({
                    "id": c.id,
                    "tipo": "coleta",
                    "latitude": c.latitude,
                    "longitude": c.longitude,
                    "endereco": c.endereco,
                    "coleta_id": c.id,
                    "ecoponto_id": None,
                })

        for eid in ecopontos_ids:
            ep = Ecoponto.query.get(eid)
            if ep:
                pontos.append({
                    "id": ep.id,
                    "tipo": "ecoponto",
                    "latitude": ep.latitude,
                    "longitude": ep.longitude,
                    "endereco": ep.endereco,
                    "coleta_id": None,
                    "ecoponto_id": ep.id,
                })

        if len(pontos) < 2:
            return {"erro": "São necessários ao menos 2 pontos com coordenadas"}, 400

        # Otimiza via Google Maps
        resultado_mapa = mapa_service.calcular_rota_otimizada(pontos)
        if "erro" in resultado_mapa:
            return resultado_mapa, 500

        rota = Rota(
            nome=dados.get("nome", f"Rota {datetime.utcnow().strftime('%d/%m/%Y')}"),
            cooperativa_id=dados.get("cooperativa_id"),
            data_planejada=datetime.fromisoformat(dados["data_planejada"]),
            distancia_total_km=resultado_mapa.get("distancia_total_km"),
            observacoes=dados.get("observacoes"),
        )
        db.session.add(rota)
        db.session.flush()

        pontos_ordenados = resultado_mapa.get("pontos_ordenados", pontos)
        for ordem, ponto in enumerate(pontos_ordenados, start=1):
            parada = ParadaRota(
                rota_id=rota.id,
                coleta_id=ponto.get("coleta_id"),
                ecoponto_id=ponto.get("ecoponto_id"),
                ordem=ordem,
                latitude=ponto["latitude"],
                longitude=ponto["longitude"],
                endereco=ponto["endereco"],
            )
            db.session.add(parada)

        db.session.commit()

        return {
            "mensagem": "Rota planejada com sucesso",
            "rota": rota.to_dict(detalhado=True),
            "mapa": resultado_mapa,
        }, 201

    def listar(self, cooperativa_id: int = None, status: str = None) -> list:
        query = Rota.query
        if cooperativa_id:
            query = query.filter_by(cooperativa_id=cooperativa_id)
        if status:
            query = query.filter_by(status=status)
        return [r.to_dict() for r in query.order_by(Rota.data_planejada.desc()).all()]

    def obter(self, rota_id: int) -> dict:
        rota = Rota.query.get_or_404(rota_id)
        return rota.to_dict(detalhado=True)

    def iniciar(self, rota_id: int) -> tuple[dict, int]:
        rota = Rota.query.get_or_404(rota_id)
        rota.status = StatusRota.EM_ANDAMENTO
        rota.data_inicio = datetime.utcnow()
        db.session.commit()
        return {"mensagem": "Rota iniciada", "rota": rota.to_dict()}, 200

    def concluir_parada(self, rota_id: int, parada_id: int) -> tuple[dict, int]:
        parada = ParadaRota.query.filter_by(id=parada_id, rota_id=rota_id).first_or_404()
        parada.concluida = True
        parada.concluida_em = datetime.utcnow()

        # Atualiza status da coleta se houver
        if parada.coleta_id:
            coleta = Coleta.query.get(parada.coleta_id)
            if coleta:
                coleta.status = StatusColeta.EM_ROTA

        db.session.commit()
        return {"mensagem": "Parada concluída", "parada": parada.to_dict()}, 200

    def finalizar(self, rota_id: int) -> tuple[dict, int]:
        rota = Rota.query.get_or_404(rota_id)
        rota.status = StatusRota.CONCLUIDA
        rota.data_fim = datetime.utcnow()
        db.session.commit()
        return {"mensagem": "Rota finalizada", "rota": rota.to_dict()}, 200

    def coletas_sem_rota(self) -> list:
        """Retorna coletas aceitas que ainda não estão em nenhuma rota"""
        coletas_em_rota = db.session.query(ParadaRota.coleta_id).filter(
            ParadaRota.coleta_id.isnot(None)
        ).subquery()

        coletas = Coleta.query.filter(
            Coleta.status == StatusColeta.ACEITA,
            Coleta.latitude.isnot(None),
            ~Coleta.id.in_(coletas_em_rota),
        ).all()

        return [c.to_dict() for c in coletas]


rota_service = RotaService()
