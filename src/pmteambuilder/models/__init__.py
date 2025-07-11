"""
模型模块初始化文件
"""
from flask_sqlalchemy import SQLAlchemy

# 创建SQLAlchemy实例
db = SQLAlchemy()

# 导入所有模型
from .user import User, user_favorites
from .token import Token
from .team import Team, TeamPokemon, PokemonMove, TeamCustomTag
from .report import Report
from .sensitive_word import SensitiveWord
from .ability import Ability
from .move import Move
from .item import Item
from .pokemon_species import PokemonSpecies
from .type import Type
from .generation import Generation
from .version_group import VersionGroup
from .pokemon import Pokemon
from .pokemon_move_learnset import PokemonMoveLearnset
from .pokemon_form_ability_map import PokemonFormAbilityMap
from .team_like import TeamLike
from .notification import Notification
