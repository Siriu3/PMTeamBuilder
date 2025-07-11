from flask import Blueprint, jsonify, request, current_app
from ..services.pokemon_service import PokemonDataService
from ..models import PokemonMoveLearnset, Move, VersionGroup, Ability, PokemonFormAbilityMap

bp = Blueprint('pokemon', __name__, url_prefix='/api/pokemon')

# Create an instance of PokemonDataService
pokemon_data_service_instance = PokemonDataService()

@bp.route('/list')
def pokemon_list():
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    generation_id = request.args.get('generation_id', default=None, type=int)
    search_query = request.args.get('search_query', default=None, type=str)
    types_str = request.args.get('types', default=None, type=str)
    types = types_str.split(',') if types_str else []
    
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_pokemon_list(
        limit=limit, 
        offset=offset, 
        generation_id=generation_id, 
        search_query=search_query,
        types=types
    )
    return jsonify(data)

@bp.route('/move/list')
def move_list_endpoint():
    generation_id = request.args.get('generation_id', type=int)
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_move_list(limit=10000, generation_id=generation_id)
    return jsonify(data)

@bp.route('/item/list')
def item_list_endpoint():
    generation_id = request.args.get('generation_id', type=int)
    categories_str = request.args.get('categories')
    categories = categories_str.split(',') if categories_str else None
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_item_list(limit=10000, generation_id=generation_id, categories=categories)
    return jsonify(data)

@bp.route('/ability/list')
def ability_list_endpoint():
    generation_id = request.args.get('generation_id', type=int)
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_ability_list(limit=10000, generation_id=generation_id)
    return jsonify(data)

@bp.route('/learnable-moves/<int:species_id>/<int:version_group_id>')
def learnable_moves(species_id: int, version_group_id: int):
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_pokemon_learnable_moves(species_id, version_group_id)
    return jsonify(data)

@bp.route('/form-abilities/<int:pokemon_form_id>')
def pokemon_form_abilities(pokemon_form_id: int):
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_form_abilities_rich(pokemon_form_id)
    return jsonify(data)

@bp.route('/generations-with-version-groups')
def generations_with_version_groups_endpoint():
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_generations_with_version_groups()
    return jsonify(data)

@bp.route('/learnable-moves-by-generation/<int:species_id>/<int:generation_id>')
def learnable_moves_by_generation(species_id: int, generation_id: int):
    """
    根据宝可梦物种ID和世代ID获取可学习的去重招式列表。
    聚合该世代下所有版本组的可学习技能。
    """
    current_app.logger.debug(f"Received request for learnable moves by generation: species_id={species_id}, generation_id={generation_id}")
    # Use the instance to call the method
    data = pokemon_data_service_instance.get_pokemon_learnable_moves_by_generation(species_id, generation_id)
    return jsonify(data)
