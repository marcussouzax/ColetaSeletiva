from sqlalchemy import func, extract
from extensions import db
from models.coleta import Coleta, MaterialColeta, StatusColeta
from models.usuario import Usuario, TipoUsuario, PontosConta
from models.ponto_coleta import Ecoponto
from datetime import datetime, timedelta


class RelatorioService:

    def dashboard_prefeitura(self) -> dict:
        """Painel resumo para a prefeitura"""
        total_coletas = Coleta.query.count()
        coletas_realizadas = Coleta.query.filter_by(status=StatusColeta.REALIZADA).count()
        coletas_pendentes = Coleta.query.filter_by(status=StatusColeta.PENDENTE).count()
        total_cidadaos = Usuario.query.filter_by(tipo=TipoUsuario.CIDADAO, ativo=True).count()
        total_ecopontos = Ecoponto.query.filter_by(ativo=True).count()

        total_kg = db.session.query(func.sum(MaterialColeta.quantidade_kg)).scalar() or 0

        return {
            "total_coletas": total_coletas,
            "coletas_realizadas": coletas_realizadas,
            "coletas_pendentes": coletas_pendentes,
            "taxa_realizacao": round((coletas_realizadas / total_coletas * 100), 1) if total_coletas else 0,
            "total_cidadaos": total_cidadaos,
            "total_ecopontos": total_ecopontos,
            "total_material_kg": round(total_kg, 2),
        }

    def reciclagem_por_bairro(self, mes: int = None, ano: int = None) -> list:
        """Ranking de bairros que mais reciclam"""
        query = db.session.query(
            Coleta.bairro,
            func.count(Coleta.id).label("total_coletas"),
            func.sum(MaterialColeta.quantidade_kg).label("total_kg"),
        ).join(
            MaterialColeta, MaterialColeta.coleta_id == Coleta.id, isouter=True
        ).filter(Coleta.status == StatusColeta.REALIZADA)

        if mes and ano:
            query = query.filter(
                extract("month", Coleta.data_realizada) == mes,
                extract("year", Coleta.data_realizada) == ano,
            )

        resultado = query.group_by(Coleta.bairro).order_by(func.count(Coleta.id).desc()).all()

        return [
            {
                "bairro": r.bairro,
                "total_coletas": r.total_coletas,
                "total_kg": round(r.total_kg or 0, 2),
            }
            for r in resultado
        ]

    def reciclagem_por_material(self, mes: int = None, ano: int = None) -> list:
        """Quantidade por tipo de material coletado"""
        query = db.session.query(
            MaterialColeta.tipo,
            func.count(MaterialColeta.id).label("ocorrencias"),
            func.sum(MaterialColeta.quantidade_kg).label("total_kg"),
        ).join(Coleta).filter(Coleta.status == StatusColeta.REALIZADA)

        if mes and ano:
            query = query.filter(
                extract("month", Coleta.data_realizada) == mes,
                extract("year", Coleta.data_realizada) == ano,
            )

        resultado = query.group_by(MaterialColeta.tipo).order_by(func.sum(MaterialColeta.quantidade_kg).desc()).all()

        return [
            {
                "tipo": r.tipo,
                "ocorrencias": r.ocorrencias,
                "total_kg": round(r.total_kg or 0, 2),
            }
            for r in resultado
        ]

    def historico_mensal(self, ano: int = None) -> list:
        """Evolução mensal de coletas no ano"""
        if not ano:
            ano = datetime.utcnow().year

        query = db.session.query(
            extract("month", Coleta.data_realizada).label("mes"),
            func.count(Coleta.id).label("total"),
            func.sum(MaterialColeta.quantidade_kg).label("total_kg"),
        ).join(
            MaterialColeta, MaterialColeta.coleta_id == Coleta.id, isouter=True
        ).filter(
            Coleta.status == StatusColeta.REALIZADA,
            extract("year", Coleta.data_realizada) == ano,
        ).group_by(extract("month", Coleta.data_realizada)).order_by("mes")

        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                       "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        resultado = query.all()
        dados = {int(r.mes): r for r in resultado}

        return [
            {
                "mes": i,
                "mes_nome": meses_nomes[i - 1],
                "total_coletas": dados[i].total if i in dados else 0,
                "total_kg": round(dados[i].total_kg or 0, 2) if i in dados else 0,
            }
            for i in range(1, 13)
        ]

    def relatorio_ambiental(self, mes: int = None, ano: int = None) -> dict:
        """Relatório ambiental completo com estimativas de impacto"""
        total_kg = db.session.query(func.sum(MaterialColeta.quantidade_kg)).join(Coleta).filter(
            Coleta.status == StatusColeta.REALIZADA
        ).scalar() or 0

        # Estimativas de impacto ambiental
        co2_evitado_ton = total_kg * 0.002        # ~2kg CO2 por kg reciclado
        arvores_salvas = total_kg * 0.017          # papel: ~60kg por árvore
        energia_kwh = total_kg * 1.5              # estimativa média
        agua_litros = total_kg * 6                # estimativa plástico

        return {
            "periodo": {"mes": mes, "ano": ano or datetime.utcnow().year},
            "total_material_kg": round(total_kg, 2),
            "impacto_ambiental": {
                "co2_evitado_toneladas": round(co2_evitado_ton, 3),
                "arvores_equivalentes": round(arvores_salvas, 1),
                "energia_economizada_kwh": round(energia_kwh, 1),
                "agua_economizada_litros": round(agua_litros, 1),
            },
            "por_bairro": self.reciclagem_por_bairro(mes, ano),
            "por_material": self.reciclagem_por_material(mes, ano),
        }

    def relatorio_cooperativa(self, cooperativa_id: int, mes: int = None, ano: int = None) -> dict:
        """Relatório de coletas realizadas por cooperativa"""
        query = Coleta.query.filter_by(
            cooperativa_id=cooperativa_id,
            status=StatusColeta.REALIZADA,
        )
        if mes and ano:
            query = query.filter(
                extract("month", Coleta.data_realizada) == mes,
                extract("year", Coleta.data_realizada) == ano,
            )
        coletas = query.all()
        total_kg = sum(c.total_kg for c in coletas)

        return {
            "cooperativa_id": cooperativa_id,
            "total_coletas": len(coletas),
            "total_kg": round(total_kg, 2),
            "coletas": [c.to_dict(detalhado=True) for c in coletas],
        }


relatorio_service = RelatorioService()
