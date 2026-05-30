import os
from flask import Flask, session, url_for, redirect, request, render_template_string
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

# Variable global para simular la base de datos o almacenamiento del diccionario en tu backend
# Clave: ID de la playlist, Valor: Lista de canciones
playlist_data_store = {}

# Spotipy variables
client_id = '77df2b62efa54f479353f08905be0828'
client_secret = '12b501570dcb48b78dcac11d4d968129'
redirect_uri = 'http://127.0.0.1:8000/callback'
scopes = 'playlist-read-private,playlist-read-collaborative'

cache_handler = FlaskSessionCacheHandler(session)
Spotify_Authentication = SpotifyOAuth(
    client_id=client_id, 
    client_secret=client_secret, 
    redirect_uri=redirect_uri, 
    scope=scopes, 
    cache_handler=cache_handler,
    show_dialog=True
)

@app.route('/')
def home():
    if not Spotify_Authentication.validate_token(cache_handler.get_cached_token()):
        auth_url = Spotify_Authentication.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))

@app.route('/callback')
def callback():
    Spotify_Authentication.get_access_token(request.args.get('code'))
    return redirect(url_for('get_playlists'))

@app.route('/get_playlists')
def get_playlists():
    if not Spotify_Authentication.validate_token(cache_handler.get_cached_token()):
        auth_url = Spotify_Authentication.get_authorize_url()
        return redirect(auth_url)
    
    sp = Spotify(auth_manager=Spotify_Authentication)
    playlists = sp.current_user_playlists()
    
    # HTML y CSS embebido con la estética de Spotify
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Mis Playlists de Spotify</title>
        <style>
            body {
                background-color: #121212;
                color: #FFFFFF;
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #1DB954;
                margin-bottom: 30px;
            }
            form {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
                max-width: 500px;
            }
            .playlist-container {
                width: 100%;
                max-height: 400px;
                overflow-y: auto;
                background-color: #181818;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                margin-bottom: 25px;
            }
            /* Personalización de la barra de desplazamiento */
            .playlist-container::-webkit-scrollbar {
                width: 8px;
            }
            .playlist-container::-webkit-scrollbar-thumb {
                background: #535353;
                border-radius: 4px;
            }
            .playlist-item {
                display: flex;
                align-items: center;
                padding: 12px;
                border-radius: 4px;
                transition: background-color 0.2s ease;
                cursor: pointer;
            }
            .playlist-item:hover {
                background-color: #282828;
            }
            .playlist-item input[type="radio"] {
                margin-right: 15px;
                accent-color: #1DB954;
                transform: scale(1.3);
            }
            .playlist-item label {
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                flex-grow: 1;
            }
            .btn-submit {
                background-color: #1DB954;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 14px 32px;
                border: none;
                border-radius: 50px;
                cursor: pointer;
                transition: transform 0.2s ease, background-color 0.2s ease;
            }
            .btn-submit:hover {
                background-color: #1ed760;
                transform: scale(1.04);
            }
            .btn-submit:active {
                transform: scale(1);
            }
        </style>
    </head>
    <body>

        <h1>Selecciona tu Playlist</h1>
        
        <form action="{{ url_for('guardar_playlist') }}" method="POST">
            <div class="playlist-container">
                {% for playlist in playlists %}
                    <div class="playlist-item">
                        <input type="radio" id="{{ playlist.id }}" name="playlist_id" value="{{ playlist.id }}" required>
                        <label for="{{ playlist.id }}">{{ playlist.name }}</label>
                    </div>
                {% endfor %}
            </div>
            <button type="submit" class="btn-submit">Seleccionar</button>
        </form>

    </body>
    </html>
    """
    
    # Pasamos las playlists al template para que las renderice dinámicamente
    return render_template_string(html_template, playlists=playlists['items'])


@app.route('/guardar_playlist', methods=['POST'])
@app.route('/guardar_playlist', methods=['POST'])
def guardar_playlist():
    if not Spotify_Authentication.validate_token(cache_handler.get_cached_token()):
        return redirect(url_for('home'))
        
    playlist_id = request.form.get('playlist_id')
    
    if playlist_id:
        sp = Spotify(auth_manager=Spotify_Authentication)
        
        # 1. Obtenemos todas las canciones de la playlist seleccionada
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            
        # 2. Procesamos la información según el JSON real
        lista_canciones = []
        for raw_item in tracks:
            # Accedemos de forma segura al nodo 'item' según tu JSON
            item_data = raw_item.get('item')
            
            # Saltamos el elemento si no existe el nodo 'item' o si su tipo no es un track musical
            if not item_data or item_data.get('type') != 'track':
                continue
                
            # Extraemos de forma segura el álbum para sacar la fecha de lanzamiento
            album_data = item_data.get('album', {})
            
            info_cancion = {
                'nombre': item_data.get('name'),
                'release_date': album_data.get('release_date'),
                'artista': item_data.get('artists')[0]['name'] if item_data.get('artists') else 'Artista Desconocido',
                'href_cancion': item_data.get('href')
            }
            
            # Imprimimos en consola cada canción que va procesando de forma exitosa
            print(f"-> Procesada de forma segura: {info_cancion['nombre']} por {info_cancion['artista']}")
            
            lista_canciones.append(info_cancion)
        
        # 3. Guardamos en nuestra variable de diccionario global
        playlist_data_store[playlist_id] = lista_canciones
        
        print("\n--- CONTENIDO DEL DICCIONARIO ACTUALIZADO ---")
        print(f"Playlist ID guardada: {playlist_id}")
        print(f"Cantidad de canciones guardadas: {len(lista_canciones)}")
        print("---------------------------------------------\n")
        
        return f"<h3>¡Éxito! Se han guardado {len(lista_canciones)} canciones en el diccionario del servidor.</h3><a href='{url_for('get_playlists')}' style='color:#1DB954;'>Volver atrás</a>"

    return "No se seleccionó ninguna playlist.", 400


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)