from flask import Flask, render_template, send_from_directory, request, redirect, url_for, send_file
from flask_bootstrap import Bootstrap
from flask import jsonify, Response

import zipfile
import io
import os
import shutil
import subprocess
import json

from camera import Camera

app = Flask(__name__)
Bootstrap(app)


@app.route('/')
def index():
    # Carga la página principal con las opciones disponibles
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        try:
            config = request.form.to_dict()
            config_json = json.dumps(config)
            # Guarda las configuraciones en el archivo config.json
            with open('config.json', 'w') as f:
                json.dump( config, f, indent=4)
            return redirect(url_for('config'))
        except Exception as e:
            print(e)
            return "Error al guardar la configuración"
    else:
        # Carga el archivo de configuración y lo muestra en la página
        with open('config.json') as f:
            config = json.loads( f.read() )
        return render_template('config.html', config=config)

@app.route('/control', methods=['POST'])
def control():
    action = request.form['action']
    if action == 'start':
        # Inicia el servicio
        result = os.system('/home/antoniofcano/camera/start_phantom.sh')
        print(f"Resultado de start_phantom.sh: {result}")
    elif action == 'stop':
        # Detiene el servicio
        result = os.system('/home/antoniofcano/camera/stop_phantom.sh')
        print(f"Resultado de stop_phantom.sh: {result}")

    return redirect(url_for('index'))

def get_parent_dir(path):
    return os.path.dirname(path)

@app.route('/images')
@app.route('/images/')
@app.route('/images/<path:subpath>')
def file_browser(subpath=None):
    root_dir = '/home/antoniofcano/fotos'
    if subpath:
        current_path = os.path.join(root_dir, subpath)
    else:
        current_path = root_dir

    entries = os.listdir(current_path)
    files_list = []
    folder_list = []

    for entry in entries:
        entry_path = os.path.join(current_path, entry)
        if os.path.isfile(entry_path) and entry.lower().endswith('.jpg'):
            relative_path = os.path.relpath(entry_path, root_dir)
            files_list.append(relative_path)
        elif os.path.isdir(entry_path):
            relative_path = os.path.relpath(entry_path, root_dir)
            folder_list.append(relative_path)

    return render_template('file_browser.html', files=files_list, folders=folder_list, subpath=subpath, get_parent_dir=get_parent_dir)

@app.route('/files/<path:path>')
def serve_file(path):
    root_dir = '/home/antoniofcano/fotos'
    return send_from_directory(root_dir, path)


@app.route('/download')
@app.route('/download/<path:subpath>')
def download(subpath=None):
    # Carga el archivo de configuración
    with open('config.json') as f:
        config = json.load(f)

    root_dir = config['output_path']
    if subpath:
        current_path = os.path.join(root_dir, subpath)
    else:
        current_path = root_dir

    # Crea un archivo ZIP con todas las imágenes
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for filename in os.listdir(current_path):
            if filename.endswith('.jpg'):
                zf.write(os.path.join(current_path, filename), filename)
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='images.zip', as_attachment=True)

@app.route('/delete_images', methods=['POST'])
def delete_images():
    root_dir = '/home/antoniofcano/fotos'
    data = request.get_json()

    # Verifica si se recibieron imágenes para eliminar
    if 'images' not in data:
        return jsonify({'error': 'No se recibieron imágenes para eliminar'}), 400

    images_to_delete = data['images']

    for image_path in images_to_delete:
        try:
            full_image_path = os.path.join(root_dir, image_path)
            if os.path.isfile(full_image_path) and image_path.lower().endswith('.jpg'):
                os.remove(full_image_path)
        except Exception as e:
            print(e)
            return jsonify({'error': f'Error al eliminar la imagen: {image_path}'}), 500

    return jsonify({'message': 'Imágenes eliminadas correctamente'}), 200

@app.route('/preview')
def preview():
    return render_template('preview.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        #yield (b'--frame\r\n'
        #       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        yield (b'--frame\r\n'
               b'Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n' + frame + b'\r\n\r\n')


config_path = 'config.json'
web_camera = Camera(config_path)
web_camera.camera.resolution = (640, 480)
web_camera.camera.framerate = 10
web_camera.camera.start()

@app.route('/video_feed')
def video_feed():
    return Response(gen( web_camera ),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture', methods=['POST'])
def capture():
    web_camera.preview_capture()
    return 'Captured'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
