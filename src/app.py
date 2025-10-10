"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, PlanetFavorite, CharacterFavorite, Follower

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route('/character', methods=['GET'])
def get_all_characters():
    try:
        characters = db.session.execute(
            db.select(Character)
        ).scalars().all()
        
        serialized_characters = [character.serialize() for character in characters]
        
        return jsonify(serialized_characters), 200

    except Exception as e:
        print(f"Error fetching characters: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/planet', methods=['GET'])
def get_all_planets():
    try:
        planets = db.session.execute(
            db.select(Planet)
        ).scalars().all()
        
        serialized_planets = [planet.serialize() for planet in planets]
        
        return jsonify(serialized_planets), 200

    except Exception as e:
        print(f"Error fetching planets: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    try:
        planet = db.session.get(Planet, planet_id)
        
        if planet is None:
            return jsonify({"message": f"Planet with ID {planet_id} not found"}), 404
        
        return jsonify(planet.serialize()), 200
        
    except Exception as e:
        print(f"Error fetching planet ID {planet_id}: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = db.session.execute(
            db.select(User)
        ).scalars().all()
        
        serialized_users = [user.serialize() for user in users]
        
        return jsonify(serialized_users), 200

    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/<string:username>/favorites', methods=['GET'])
def get_user_favorites(username):
    try:
        user = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar_one_or_none()
        
        if user is None:
            return jsonify({"message": f"User '{username}' not found"}), 404
        
        favorite_planets = db.session.execute(
            db.select(Planet).join(PlanetFavorite).where(PlanetFavorite.user_id == user.id)
        ).scalars().all()
        
        favorite_characters = db.session.execute(
            db.select(Character).join(CharacterFavorite).where(CharacterFavorite.user_id == user.id)
        ).scalars().all()
        
        response = {
            "user": user.serialize(),
            "favorite_planets": [planet.serialize() for planet in favorite_planets],
            "favorite_characters": [character.serialize() for character in favorite_characters]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error fetching favorites for user '{username}': {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"message": "user_id is required in request body"}), 400
        
        user_id = data['user_id']
        
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"message": f"User with ID {user_id} not found"}), 404
        
        planet = db.session.get(Planet, planet_id)
        if planet is None:
            return jsonify({"message": f"Planet with ID {planet_id} not found"}), 404
        
        existing_favorite = db.session.execute(
            db.select(PlanetFavorite).where(
                PlanetFavorite.user_id == user_id,
                PlanetFavorite.planet_id == planet_id
            )
        ).scalar_one_or_none()
        
        if existing_favorite:
            return jsonify({"message": "Planet is already in user's favorites"}), 400
        
        new_favorite = PlanetFavorite(user_id=user_id, planet_id=planet_id)
        db.session.add(new_favorite)
        db.session.commit()
        
        response = {
            "message": "Planet added to favorites successfully",
            "favorite": new_favorite.serialize(),
            "planet": planet.serialize()
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding favorite planet {planet_id}: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


@app.route('/favorite/character/<int:character_id>', methods=['POST'])
def add_favorite_character(character_id):
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"message": "user_id is required in request body"}), 400
        
        user_id = data['user_id']
        
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"message": f"User with ID {user_id} not found"}), 404
        
        character = db.session.get(Character, character_id)
        if character is None:
            return jsonify({"message": f"Character with ID {character_id} not found"}), 404
        
        existing_favorite = db.session.execute(
            db.select(CharacterFavorite).where(
                CharacterFavorite.user_id == user_id,
                CharacterFavorite.character_id == character_id
            )
        ).scalar_one_or_none()
        
        if existing_favorite:
            return jsonify({"message": "Character is already in user's favorites"}), 400
        
        new_favorite = CharacterFavorite(user_id=user_id, character_id=character_id)
        db.session.add(new_favorite)
        db.session.commit()
        
        response = {
            "message": "Character added to favorites successfully",
            "favorite": new_favorite.serialize(),
            "character": character.serialize()
        }
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding favorite character {character_id}: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"message": "user_id is required in request body"}), 400
        
        user_id = data['user_id']
        
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"message": f"User with ID {user_id} not found"}), 404
        
        planet = db.session.get(Planet, planet_id)
        if planet is None:
            return jsonify({"message": f"Planet with ID {planet_id} not found"}), 404
        
        favorite_to_delete = db.session.execute(
            db.select(PlanetFavorite).where(
                PlanetFavorite.user_id == user_id,
                PlanetFavorite.planet_id == planet_id
            )
        ).scalar_one_or_none()
        
        if favorite_to_delete is None:
            return jsonify({"message": "Planet is not in user's favorites"}), 404
        
        db.session.delete(favorite_to_delete)
        db.session.commit()
        
        response = {
            "message": "Planet removed from favorites successfully",
            "planet": planet.serialize()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting favorite planet {planet_id}: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


@app.route('/favorite/character/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(character_id):
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"message": "user_id is required in request body"}), 400
        
        user_id = data['user_id']
        
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"message": f"User with ID {user_id} not found"}), 404
        
        character = db.session.get(Character, character_id)
        if character is None:
            return jsonify({"message": f"Character with ID {character_id} not found"}), 404
        
        favorite_to_delete = db.session.execute(
            db.select(CharacterFavorite).where(
                CharacterFavorite.user_id == user_id,
                CharacterFavorite.character_id == character_id
            )
        ).scalar_one_or_none()
        
        if favorite_to_delete is None:
            return jsonify({"message": "Character is not in user's favorites"}), 404
        
        db.session.delete(favorite_to_delete)
        db.session.commit()
        
        response = {
            "message": "Character removed from favorites successfully",
            "character": character.serialize()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting favorite character {character_id}: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
