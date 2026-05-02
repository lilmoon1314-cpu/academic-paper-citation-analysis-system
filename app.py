from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    from routes.graph_routes import graph_bp
    from routes.search_routes import search_bp
    from routes.recommend_routes import recommend_bp
    from routes.metrics_routes import metrics_bp
    from routes.frontier_routes import frontier_bp
    from routes.performance_routes import performance_bp

    app.register_blueprint(graph_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(recommend_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(frontier_bp)
    app.register_blueprint(performance_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
