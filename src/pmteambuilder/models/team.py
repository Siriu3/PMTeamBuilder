"""
团队相关模型定义
"""
from datetime import datetime, timezone
from . import db
from flask import current_app
from .user import User # 导入 User 模型

class Team(db.Model):
    """团队模型"""
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    generation = db.Column(db.String(20), nullable=False)  # 例如: 'Gen 9'
    format = db.Column(db.String(20), nullable=False)  # 例如: 'Singles', 'Doubles'
    is_public = db.Column(db.Boolean, default=True)
    review_status = db.Column(db.String(20), default='approved')  # 'pending', 'approved', 'rejected'
    review_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    token = db.Column(db.String(255), unique=True, nullable=True, index=True)
    external_link = db.Column(db.String(255), nullable=True) # 外链
    favorites_count = db.Column(db.Integer, default=0, nullable=True) # 收藏数
    likes_count = db.Column(db.Integer, default=0, nullable=True) # 点赞数

    # 关系
    pokemons = db.relationship('TeamPokemon', backref='team', lazy=True, cascade='all, delete-orphan')
    custom_tags = db.relationship('TeamCustomTag', backref='team', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='team', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', back_populates='teams', lazy=True) # Add the correct relationship using back_populates

    def __repr__(self):
        return f'<Team {self.name} (ID: {self.id})>'

    @property
    def pokemon_count(self):
        """获取团队中宝可梦的数量"""
        return len(self.pokemons)

    def to_dict(self, include_pokemons=True, include_tags=True, include_token=False, include_sprite_urls_only=False):
        data = {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'generation': self.generation,
            'format': self.format,
            'is_public': self.is_public,
            'review_status': self.review_status,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pokemon_count': self.pokemon_count,
            'creator_username': self.creator.username if self.creator else '未知用户', # Use the new relationship
            'external_link': self.external_link,
            'favorites_count': self.favorites_count,
            'likes_count': self.likes_count,
        }

        if include_pokemons:
            # Include full pokemon details
            data['pokemons'] = [p.to_dict() for p in self.pokemons]
        elif include_sprite_urls_only:
            # Only include pokemon id and sprite_url for list view
            data['pokemons'] = [
                {'id': p.id, 'species_id': p.species_id, 'sprite_url': p.pokemon_details.sprite if p.pokemon_details else None}
                for p in self.pokemons
            ] # Assuming pokemon_details is loaded or accessible

        if include_tags:
            data['custom_tags'] = [t.content for t in self.custom_tags]

        if include_token:
            data['token'] = self.token

        return data

class TeamPokemon(db.Model):
    """团队中的宝可梦模型"""
    __tablename__ = 'team_pokemon'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    species_id = db.Column(db.Integer, nullable=False)  # 宝可梦种类ID
    species_name = db.Column(db.String(100), nullable=False)  # 宝可梦名称
    species_name_zh = db.Column(db.String(100), nullable=True)  # 宝可梦中文名称
    level = db.Column(db.Integer, default=50)
    ability = db.Column(db.String(100), nullable=True)
    item = db.Column(db.String(100), nullable=True)
    nature = db.Column(db.String(20), nullable=True)
    evs_hp = db.Column(db.Integer, default=0)
    evs_atk = db.Column(db.Integer, default=0)
    evs_def = db.Column(db.Integer, default=0)
    evs_spa = db.Column(db.Integer, default=0)
    evs_spd = db.Column(db.Integer, default=0)
    evs_spe = db.Column(db.Integer, default=0)
    ivs_hp = db.Column(db.Integer, default=31)
    ivs_atk = db.Column(db.Integer, default=31)
    ivs_def = db.Column(db.Integer, default=31)
    ivs_spa = db.Column(db.Integer, default=31)
    ivs_spd = db.Column(db.Integer, default=31)
    ivs_spe = db.Column(db.Integer, default=31)
    tera_type = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # 关系
    moves = db.relationship('PokemonMove', backref='pokemon', lazy=True, cascade='all, delete-orphan')
    # Add relationship to default Pokemon form for details like sprite, types, base_stats
    # Note: This assumes Pokemon.species_id and Pokemon.is_default are the linking points
    pokemon_details = db.relationship(
        'Pokemon',
        primaryjoin='and_(TeamPokemon.species_id == Pokemon.species_id, Pokemon.is_default == True)',
        foreign_keys='[TeamPokemon.species_id]', # Specify foreign keys explicitly if needed
        uselist=False, # One TeamPokemon maps to one default Pokemon form
        lazy='joined' # Eager load this relationship
    )

    def __repr__(self):
        return f'<TeamPokemon {self.species_name_zh or self.species_name} (ID: {self.id})>'

    def to_dict(self):
        # Restore the original to_dict method for TeamPokemon
        data = {
            'id': self.id,
            'team_id': self.team_id,
            'species_id': self.species_id,
            'species_name': self.species_name,
            'species_name_zh': self.species_name_zh,
            'level': self.level,
            'ability': self.ability, # This might be just the name string
            'item': self.item,     # This might be just the name string
            'nature': self.nature,   # This might be just the name string
            'evs': {
                'hp': self.evs_hp,
                'atk': self.evs_atk,
                'def': self.evs_def,
                'spa': self.evs_spa,
                'spd': self.evs_spd,
                'spe': self.evs_spe
            },
            'ivs': {
                'hp': self.ivs_hp,
                'atk': self.ivs_atk,
                'def': self.ivs_def,
                'spa': self.ivs_spa,
                'spd': self.ivs_spd,
                'spe': self.ivs_spe
            },
            'moves': self._get_unique_moves_dict_list(),
            'tera_type': self.tera_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Add item sprite if item exists
        if self.item:
            # Assuming self.item is the localized name (Chinese), try to find the item by name_zh_hans or name
            # Import the Item model if not already imported
            from .item import Item # Assuming item model is in .item
            item_obj = Item.query.filter(db.or_(Item.name_zh_hans == self.item, Item.name == self.item)).first()
            if item_obj and item_obj.sprite:
                data['item_sprite'] = item_obj.sprite
            else:
                # Log a warning if item is present but sprite not found in DB, or item not found
                current_app.logger.warning(f"[TeamPokemon.to_dict] Item '{self.item}' found for pokemon ID {self.id}, but sprite not found in DB.")

        # Add details from the pokemon_details relationship if loaded
        if self.pokemon_details:
            data['sprite'] = self.pokemon_details.sprite
            data['types'] = [t for t in [self.pokemon_details.type_1, self.pokemon_details.type_2] if t]
            data['base_stats'] = {
                'hp': self.pokemon_details.base_hp,
                'atk': self.pokemon_details.base_atk,
                'def': self.pokemon_details.base_def,
                'spa': self.pokemon_details.base_spa,
                'spd': self.pokemon_details.base_spd,
                'spe': self.pokemon_details.base_spe,
            }
            # Note: Abilities and item_sprite are handled in the get_team service method currently.
            # If needed in the list view, they would need to be added here as well, potentially requiring more eager loading.
            # For now, just adding sprite, types, and base_stats as requested.

        # === Add Abilities List ===
        # Need to get version_group_id based on the team's generation
        version_group_id = None
        if self.team and self.team.generation:
             try:
                 from ..services.pokemon_service import pokemon_data_service
                 # Assume pokemon_data_service has a method to get version_group_id by generation
                 # Or implement the logic here to query Generation table
                 # version_group_id = pokemon_data_service.get_version_group_id_by_generation(self.team.generation)
                 # Manual query example:
                 from ..models import Generation
                 gen_obj = Generation.query.filter_by(name=self.team.generation.lower().replace('gen ', 'generation-')).first()
                 if gen_obj and gen_obj.version_groups:
                      version_group_id = gen_obj.version_groups[0].id # Assume first version group is relevant
                 else:
                      current_app.logger.warning(f"[TeamPokemon.to_dict] Could not find version_group_id for generation: {self.team.generation}")
             except Exception as e:
                 current_app.logger.error(f"[TeamPokemon.to_dict] Error getting version_group_id for generation {self.team.generation}: {e}")

        if version_group_id is not None and self.species_id is not None:
             try:
                 from ..services.pokemon_service import pokemon_data_service
                 # Get abilities for the species in the specific version group
                 abilities = pokemon_data_service.get_pokemon_abilities(self.species_id, version_group_id)
                 data['abilities'] = abilities # Add abilities list to the dictionary
             except Exception as e:
                 current_app.logger.error(f"[TeamPokemon.to_dict] Error getting abilities for species {self.species_id} in VG {version_group_id}: {e}")
                 data['abilities'] = [] # Provide empty list on error
        else:
            data['abilities'] = [] # Provide empty list if version_group_id or species_id is missing
        # ========================

        return data

    def _get_unique_moves_dict_list(self) -> list[dict]:
        """
        Helper method to get a list of unique move dictionaries for this pokemon.
        Uniqueness is determined by move_id (if available) or move_name_zh.
        """
        unique_moves = {}
        for move_obj in self.moves:
            move_dict = move_obj.to_dict()
            # Use move_id for uniqueness if available, otherwise use move_name_zh
            unique_key = move_dict.get('move_id') or move_dict.get('move_name_zh')
            if unique_key is not None and unique_key not in unique_moves:
                unique_moves[unique_key] = move_dict

        return list(unique_moves.values())

class PokemonMove(db.Model):
    """宝可梦招式模型"""
    __tablename__ = 'pokemon_moves'

    id = db.Column(db.Integer, primary_key=True)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('team_pokemon.id'), nullable=False)
    move_id = db.Column(db.Integer, nullable=False)
    move_name = db.Column(db.String(100), nullable=False)
    move_name_zh = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # 添加唯一约束
    __table_args__ = (
        db.UniqueConstraint('pokemon_id', 'move_id', name='_pokemon_move_uc'),
    )

    def __repr__(self):
        return f'<PokemonMove {self.move_name_zh or self.move_name} (ID: {self.id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'pokemon_id': self.pokemon_id,
            'move_id': self.move_id,
            'move_name': self.move_name,
            'move_name_zh': self.move_name_zh,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TeamCustomTag(db.Model):
    """团队自定义标签模型"""
    __tablename__ = 'team_custom_tags'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<TeamCustomTag {self.content} (ID: {self.id})>'
