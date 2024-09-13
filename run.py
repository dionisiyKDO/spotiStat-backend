from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=8888)


# Serve other static files (CSS, JS, etc.)
# @app.route('/<path:path>')
# def static_proxy(path):
#     return send_from_directory(app.static_folder, path)