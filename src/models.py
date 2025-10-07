from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Enum, ForeignKey, func, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

db = SQLAlchemy()

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(120), nullable=True)
    lastname: Mapped[str] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    followers: Mapped[List["Follower"]] = relationship(
        primaryjoin="User.id == Follower.user_to_id", back_populates="followed"
    )
    following: Mapped[List["Follower"]] = relationship(
        primaryjoin="User.id == Follower.user_from_id", back_populates="follower"
    )
    favorite_planets: Mapped[List["PlanetFavorite"]] = relationship(back_populates="user")
    favorite_characters: Mapped[List["CharacterFavorite"]] = relationship(back_populates="user")

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
        }

class Planet(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False) # e.g., in Celsius
    mass: Mapped[float] = mapped_column(Float, nullable=False) # e.g., in Earth masses
    population: Mapped[int] = mapped_column(Integer, nullable=True)
    favorited_by_users: Mapped[List["PlanetFavorite"]] = relationship(back_populates="planet")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "temperature": self.temperature,
            "mass": self.mass,
            "population": self.population,
        }

class Character(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    eye_color: Mapped[str] = mapped_column(String(50), nullable=False)
    homeworld_id: Mapped[int] = mapped_column(ForeignKey('planet.id'), nullable=True) # Optional link

    favorited_by_users: Mapped[List["CharacterFavorite"]] = relationship(back_populates="character")

    homeworld: Mapped["Planet"] = relationship()

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "eye_color": self.eye_color,
            "homeworld_id": self.homeworld_id,
        }

class PlanetFavorite(db.Model):
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'), primary_key=True
    )
    planet_id: Mapped[int] = mapped_column(
        ForeignKey('planet.id'), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="favorite_planets")
    planet: Mapped["Planet"] = relationship(back_populates="favorited_by_users")

    def serialize(self):
        return {
            "user_id": self.user_id,
            "planet_id": self.planet_id,
        }

class CharacterFavorite(db.Model):
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'), primary_key=True
    )
    character_id: Mapped[int] = mapped_column(
        ForeignKey('character.id'), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="favorite_characters")
    character: Mapped["Character"] = relationship(back_populates="favorited_by_users")

    def serialize(self):
        return {
            "user_id": self.user_id,
            "character_id": self.character_id,
        }

class Follower(db.Model):
    user_from_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    user_to_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)

    follower: Mapped["User"] = relationship(
        foreign_keys=[user_from_id], back_populates="following"
    )
    followed: Mapped["User"] = relationship(
        foreign_keys=[user_to_id], back_populates="followers"
    )

    def serialize(self):
        return {
            "user_from_id": self.user_from_id,
            "user_to_id": self.user_to_id,
        }