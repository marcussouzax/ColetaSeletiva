from routes.usuario_routes import usuario_bp
from routes.coleta_routes import coleta_bp
from routes.ponto_routes import ecoponto_bp, notificacao_bp
from routes.relatorio_routes import relatorio_bp, rota_bp
from routes.mapa_routes import mapa_bp


def register_blueprints(app):
    app.register_blueprint(usuario_bp)
    app.register_blueprint(coleta_bp)
    app.register_blueprint(ecoponto_bp)
    app.register_blueprint(notificacao_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(rota_bp)
    app.register_blueprint(mapa_bp)