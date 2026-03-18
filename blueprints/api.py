from flask import Blueprint, request
from flask_restx import Api, Resource, fields
import json
import os

# Создаём Blueprint для API
api_bp = Blueprint('api', __name__)

# Создаём API и привязываем к Blueprint
api = Api(
    api_bp,
    version='1.0',
    title='Music API',
    description='API для управления музыкальными произведениями',
    doc='/apidocs',
    prefix='/api'
)

# Namespace для треков
tracks_ns = api.namespace('tracks', description='Операции с треками')

# Namespace для статистики
stats_ns = api.namespace('statistics', description='Статистика по трекам')

# Модель данных
track_model = api.model('Track', {
    'id': fields.Integer(readonly=True, description='Уникальный идентификатор'),
    'title': fields.String(required=True, description='Название трека'),
    'artist': fields.String(required=True, description='Исполнитель'),
    'genre': fields.String(required=True, description='Жанр'),
    'duration': fields.Float(required=True, description='Длительность в секундах'),
    'year': fields.Integer(required=True, description='Год выпуска'),
    'rating': fields.Float(required=True, description='Рейтинг (0-10)'),
})

# JSON хранилище
DATA_FILE = 'data.json'


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'next_id': 1, 'tracks': []}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Загружаем данные
data = load_data()
tracks = data['tracks']
next_id = data['next_id']


# Вспомогательные функции
def find_track(track_id):
    for track in tracks:
        if track['id'] == track_id:
            return track
    return None


def calculate_stats(field):
    values = [t[field] for t in tracks if isinstance(t[field], (int, float))]
    if not values:
        return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
    return {
        'min': min(values),
        'max': max(values),
        'avg': round(sum(values) / len(values), 2),
        'count': len(values)
    }


# === CRUD Треки ===

@tracks_ns.route('/')
class TrackList(Resource):
    @tracks_ns.doc('list_tracks')
    @tracks_ns.marshal_list_with(track_model)
    @tracks_ns.param('sort_by', 'Поле для сортировки', type='string',
                     enum=['id', 'title', 'artist', 'genre', 'duration', 'year', 'rating'])
    @tracks_ns.param('order', 'Порядок сортировки', type='string', enum=['asc', 'desc'])
    def get(self):
        """Получить все треки с сортировкой"""
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        result = tracks.copy()
        if sort_by in ['id', 'title', 'artist', 'genre', 'duration', 'year', 'rating']:
            reverse = (order == 'desc')
            result.sort(key=lambda x: x[sort_by], reverse=reverse)
        return result

    @tracks_ns.doc('create_track')
    @tracks_ns.expect(track_model)
    @tracks_ns.marshal_with(track_model, code=201)
    def post(self):
        """Добавить новый трек"""
        global next_id, data
        payload = api.payload
        track = {
            'id': next_id,
            'title': payload['title'],
            'artist': payload['artist'],
            'genre': payload['genre'],
            'duration': payload['duration'],
            'year': payload['year'],
            'rating': payload['rating']
        }
        tracks.append(track)
        next_id += 1
        data['tracks'] = tracks
        data['next_id'] = next_id
        save_data(data)
        return track, 201


@tracks_ns.route('/<int:track_id>')
@tracks_ns.param('track_id', 'ID трека')
@tracks_ns.response(404, 'Трек не найден')
class TrackItem(Resource):
    @tracks_ns.doc('get_track')
    @tracks_ns.marshal_with(track_model)
    def get(self, track_id):
        """Получить трек по ID"""
        track = find_track(track_id)
        if not track:
            api.abort(404, 'Трек не найден')
        return track

    @tracks_ns.doc('update_track')
    @tracks_ns.expect(track_model)
    @tracks_ns.marshal_with(track_model)
    def put(self, track_id):
        """Обновить трек по ID"""
        track = find_track(track_id)
        if not track:
            api.abort(404, 'Трек не найден')
        payload = api.payload
        for field in ['title', 'artist', 'genre', 'duration', 'year', 'rating']:
            if field in payload:
                track[field] = payload[field]
        save_data(data)
        return track

    @tracks_ns.doc('delete_track')
    @tracks_ns.response(200, 'Трек удалён')
    def delete(self, track_id):
        """Удалить трек по ID"""
        track = find_track(track_id)
        if not track:
            api.abort(404, 'Трек не найден')
        tracks.remove(track)
        save_data(data)
        return {'message': 'Трек удалён'}, 200


# === Статистика ===

@stats_ns.route('/')
class StatsAll(Resource):
    @stats_ns.doc('get_all_stats')
    def get(self):
        """Получить статистику по всем полям"""
        return {
            'duration': calculate_stats('duration'),
            'year': calculate_stats('year'),
            'rating': calculate_stats('rating'),
            'total_tracks': len(tracks)
        }, 200


@stats_ns.route('/<string:field>')
@stats_ns.param('field', 'Поле для статистики', enum=['duration', 'year', 'rating'])
class StatsByField(Resource):
    @stats_ns.doc('get_field_stats')
    def get(self, field):
        """Получить статистику по полю"""
        if field not in ['duration', 'year', 'rating']:
            api.abort(400, 'Допустимые поля: duration, year, rating')
        return calculate_stats(field), 200