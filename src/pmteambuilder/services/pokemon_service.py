# filepath: src/pmteambuilder/services/pokemon_service.py
"""
宝可梦数据服务模块，提供宝可梦数据相关功能
"""
import json
import requests
import threading
import time
import os
import pickle
import urllib3
import hashlib
import random
from flask import current_app
from ..utils.redis_service import redis_service
from ..models import db, Ability, Move, Item, PokemonSpecies, Type, Generation, VersionGroup, Pokemon, PokemonMoveLearnset, PokemonFormAbilityMap
from sqlalchemy import or_ # 导入 or_

# 关闭 InsecureRequestWarning，消除 requests verify=False 带来的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 代理配置（如有需要请修改为你的代理地址）
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}
REQUESTS_KWARGS = {"proxies": PROXIES, "verify": False}

class PokemonDataService:
    """宝可梦数据服务类"""
    POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"
    DEFAULT_FETCH_PROGRESS_FILENAME = "fetch_progress.pkl"

    @staticmethod
    def _get_progress_file_path():
        # 优先从应用配置中获取，若无则使用 instance_path
        # 这使得在 manual_sync.py 中设置的路径可以被服务感知
        configured_path = current_app.config.get('FETCH_PROGRESS_PATH_OVERRIDE')
        if configured_path:
            return configured_path
        # 默认使用 Flask app 的 instance_path，这是推荐的做法
        # 需要确保 app.instance_path 在您的项目中被正确设置或可访问
        # 通常，instance_path 指向与 manage.py 或 wsgi.py 文件所在级别的一个 'instance' 文件夹
        # 如果您的项目结构是 d:/VSCDocument/pmteambuilder/src/instance/
        # 且您的 app 的根目录是 d:/VSCDocument/pmteambuilder/
        # 那么 app.instance_path 应该指向 d:/VSCDocument/pmteambuilder/instance/ (如果您的 src 是一个包，且 __init__.py 中创建 app 时正确设置了 instance_path)
        # 假设您的 dev.db 在 src/instance/，那么进度文件也应该在 src/instance/
        # 最可靠的是确保 create_app 时 instance_path 设置正确，或者在 config 中明确指定
        
        # 修正路径，以确保它指向 src/instance/ 目录下的文件
        # Flask 的 instance_path 通常指向项目根目录下的 'instance' 文件夹。
        # 如果你的项目结构是 d:/VSCDocument/pmteambuilder/ (根)
        #   - src/
        #     - pmteambuilder/
        #     - instance/ (你的目标)
        # 那么 instance_path 应该被配置为 os.path.join(current_app.root_path, '..', 'instance')
        # 或者，如果 current_app.root_path 指向 src/pmteambuilder/，则应为 os.path.join(current_app.root_path, '..', 'instance')
        # 假设您希望它在 src/instance/
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "instance")) # 从 services.py 退两级到 src/ 再到 instance/
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, PokemonDataService.DEFAULT_FETCH_PROGRESS_FILENAME)

    @staticmethod
    def get_pokemon_list(limit=1000, offset=0, generation_id=None, search_query=None, types: list[str] | None = None):
        """获取宝可梦列表，从本地数据库查询，支持世代筛选、搜索和本地化。
           返回的数据应包含前端 SelectionPanel 所需的全部字段。
        """
        actual_limit = min(limit, 2000)

        cache_key_parts = ["pokemon_list_local_db", str(actual_limit), str(offset)]
        if generation_id:
            cache_key_parts.append(f"gen:{generation_id}")
        if search_query:
            cache_key_parts.append(f"q:{search_query}")
        if types and len(types) > 0:
            # Sort types to ensure consistent cache key regardless of input order
            sorted_types = sorted([t.lower() for t in types])
            cache_key_parts.append(f"types:{','.join(sorted_types)}")
        cache_key = ":".join(cache_key_parts)

        cached_data = redis_service.get(cache_key)
        if cached_data:
            current_app.logger.debug(f"Cache hit for {cache_key}")
            return json.loads(cached_data.decode('utf-8'))
        current_app.logger.debug(f"Cache miss for {cache_key}, querying DB.")

        # 获取属性英文名到中文名的映射
        type_zh_map = {t.name: t.name_zh_hans for t in Type.query.all()}

        query = db.session.query(
            Pokemon.id,
            Pokemon.species_id,
            Pokemon.name, # 英文名 (通常是形态名或默认种族名)
            PokemonSpecies.name_zh_hans.label("species_name_zh"), # 物种中文名
            Pokemon.form_name_zh_hans.label("form_name_zh"), # 形态中文名 (如果有)
            Pokemon.sprite,
            Pokemon.type_1,
            Pokemon.type_2,
            Pokemon.base_hp,
            Pokemon.base_atk,
            Pokemon.base_def,
            Pokemon.base_spa,
            Pokemon.base_spd,
            Pokemon.base_spe,
            # PokemonSpecies.generation_id.label("species_generation_id") # 注释掉，因为 PokemonSpecies 没有此属性
        ).join(PokemonSpecies, Pokemon.species_id == PokemonSpecies.id)

        if generation_id:
            # 此处原有基于 PokemonSpecies.generation_id 的筛选逻辑已被移除
            # 因为 PokemonSpecies 模型没有直接的 generation_id 属性。
            # 如果将来需要基于物种的世代进行筛选，需要通过其 'generations' 关系来实现，例如：
            # from ..models import Generation
            # query = query.join(PokemonSpecies.generations).filter(Generation.id == generation_id)
            # 注意：上述示例可能会改变查询的结构或引入重复行，需要仔细测试。
            # 当前根据用户需求，不实现此筛选。
            pass # 保留 if 块用于未来可能的扩展

        if search_query: # <--- 应用搜索过滤器
            search_term = f"%{search_query.lower()}%"
            # 假设 PokemonSpecies 表有一个 pinyin 字段存储物种中文名的全拼
            # 您需要在模型和数据同步中实际添加和填充此字段
            query = query.filter(
                or_(
                    Pokemon.name.ilike(search_term), # 英文名搜索 (通常是形态名)
                    PokemonSpecies.name_zh_hans.ilike(search_term), # 中文种族名搜索
                    Pokemon.form_name_zh_hans.ilike(search_term) # 中文形态名搜索
                    # 已移除对 PokemonSpecies.pinyin.ilike 的引用
                )
            )
        
        # --- 应用属性过滤器 ---
        if types and len(types) > 0:
            if len(types) == 1:
                # 单属性过滤: type_1 或 type_2 匹配
                query = query.filter(or_(Pokemon.type_1 == types[0].lower(), Pokemon.type_2 == types[0].lower()))
            elif len(types) == 2:
                # 双属性过滤: type_1 和 type_2 分别匹配 (不区分顺序)
                # 注意：数据库中存储的是英文属性名，前端传递的可能是中文，需要转换
                # 但是，前端在 SelectionPanel 已经处理了属性到英文的转换并通过 API 传递，所以后端直接使用英文属性名进行过滤
                type1_en = types[0].lower()
                type2_en = types[1].lower()
                query = query.filter(or_(
                    (Pokemon.type_1 == type1_en) & (Pokemon.type_2 == type2_en),
                    (Pokemon.type_1 == type2_en) & (Pokemon.type_2 == type1_en)
                ))
            # 如果多于两个属性，忽略过滤或返回空结果，这里选择忽略多余属性
        # --- 结束属性过滤器 ---
        
        # 排序确保分页一致性
        query = query.order_by(Pokemon.id) # 或者 PokemonSpecies.id, Pokemon.id

        total_count = query.count() # 获取应用筛选后的总数，用于前端分页判断
        
        pokemon_forms = query.limit(actual_limit).offset(offset).all()
        
        results = []
        for form in pokemon_forms:
            # 将 form_name_zh (形态中文名) 与 species_name_zh (物种中文名) 组合，以提供更完整的显示名称
            # 例如 "皮卡丘 (就决定是你了的样子)"
            display_name_zh = form.species_name_zh
            if form.form_name_zh and form.form_name_zh != form.species_name_zh : # 避免重复，如 "米立龙 (上弓姿势)" vs "米立龙"
                 # 有些非默认形态的 name 可能直接是 "Pikachu-Original-Cap"，而 name_zh 可能是 "皮卡丘"
                 # 后端pokeapi的pokemon-species的name是物种名 "pikachu"，pokemon-form的name是 "pikachu-alola"
                 # 我们的Pokemon.name存储的是pokemon-form的name，PokemonSpecies.name_zh_hans是物种中文名
                 # 我们需要确保展示的英文名是 形态的英文名，中文名是 物种中文名 + (形态中文名)
                display_name_zh = f"{form.species_name_zh} ({form.form_name_zh})"

            results.append({
                "id": form.id, # Pokemon Form ID
                "species_id": form.species_id,
                "name": form.name, # 英文形态名
                "name_zh": display_name_zh, # 组合后的中文显示名
                # "species_name_zh": form.species_name_zh, # 单独的物种中文名，如果需要
                # "form_name_zh": form.form_name_zh, # 单独的形态中文名，如果需要
                "sprite": form.sprite,
                "types": [type_zh_map.get(t, t) for t in [form.type_1, form.type_2] if t], # 将属性英文名转换为中文名
                "base_stats": {
                    "hp": form.base_hp,
                    "attack": form.base_atk, # PokeAPI 用 attack, defense...
                    "defense": form.base_def,
                    "special-attack": form.base_spa,
                    "special-defense": form.base_spd,
                    "speed": form.base_spe
                },
                # 模拟 abilities 字段，实际应该从 PokemonFormAbilityMap 查询
                # 注意：这个abilities字段在宝可梦列表里通常只是展示可能的特性名，不是当前选定的特性
                "abilities": PokemonDataService.get_form_abilities_rich(form.id) # 获取包含is_hidden等详细信息的特性列表
            })
        
        response_data = {
            "count": total_count, # 返回总数
            "results": results
        }

        redis_service.set(cache_key, json.dumps(response_data), expire=3600) # 缓存1小时
        return response_data

    @staticmethod
    def get_form_ability_names(pokemon_form_id: int) -> list[str]:
        """辅助方法：获取指定宝可梦形态的特性名称列表（中文名优先）。"""
        # 这个方法应该只被 get_pokemon_list 内部调用，用于展示，不需要单独缓存或暴露API
        # 它需要高效查询，避免N+1问题
        # 假设 PokemonFormAbilityMap 和 Ability 表已经存在且同步了数据
        
        # 尝试从缓存获取，以避免重复查询，缓存键应包含 pokemon_form_id
        cache_key = f"form_ability_names:{pokemon_form_id}"
        cached_names = redis_service.get(cache_key)
        if cached_names:
            return json.loads(cached_names.decode('utf-8'))

        ability_maps = db.session.query(
            Ability.name_zh_hans,
            Ability.name
        ).join(
            PokemonFormAbilityMap, PokemonFormAbilityMap.ability_id == Ability.id
        ).filter(
            PokemonFormAbilityMap.pokemon_form_id == pokemon_form_id
        ).all()
        
        names = [row.name_zh_hans if row.name_zh_hans else row.name for row in ability_maps]
        
        # 将结果缓存一小段时间，例如5分钟，因为这个列表相对稳定
        redis_service.set(cache_key, json.dumps(names), expire=300)
        return names

    @staticmethod
    def get_form_abilities_rich(pokemon_form_id: int) -> list[dict]:
        """辅助方法：获取指定宝可梦形态的详细特性信息列表（中文名、是否隐藏等）。"""
        # 尝试从缓存获取
        cache_key = f"form_abilities_rich:{pokemon_form_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        abilities_data = db.session.query(
            Ability.id,
            Ability.name,
            Ability.name_zh_hans,
            Ability.description_en,
            Ability.description_zh_hans,
            PokemonFormAbilityMap.is_hidden
        ).join(
            PokemonFormAbilityMap, PokemonFormAbilityMap.ability_id == Ability.id
        ).filter(
            PokemonFormAbilityMap.pokemon_form_id == pokemon_form_id
        ).all()

        results = []
        for ab in abilities_data:
            results.append({
                'id': ab.id,
                'name_en': ab.name,
                'name_zh': ab.name_zh_hans,
                'description_en': ab.description_en,
                'description_zh_hans': ab.description_zh_hans,
                'is_hidden': ab.is_hidden
            })

        # 将结果缓存
        redis_service.set(cache_key, json.dumps(results), expire=300) # 缓存5分钟
        return results

    @staticmethod
    def get_pokemon_details(pokemon_id):
        """获取宝可梦详情，先检查缓存"""
        cache_key = f"pokemon_details:{pokemon_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        url = f"{PokemonDataService.POKEAPI_BASE_URL}/pokemon/{pokemon_id}"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        redis_service.set(cache_key, json.dumps(data), expire=3600)
        return data

    @staticmethod
    def get_pokemon_abilities(pokemon_id):
        """获取宝可梦特性列表，先检查缓存"""
        cache_key = f"pokemon_abilities:{pokemon_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        pokemon_details = PokemonDataService.get_pokemon_details(pokemon_id)
        abilities = [ability['ability']['name'] for ability in pokemon_details['abilities']]
        redis_service.set(cache_key, json.dumps(abilities), expire=3600)
        return abilities

    @staticmethod
    def get_pokemon_moves(pokemon_id):
        """获取宝可梦招式列表，先检查缓存"""
        cache_key = f"pokemon_moves:{pokemon_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        pokemon_details = PokemonDataService.get_pokemon_details(pokemon_id)
        moves = [move['move']['name'] for move in pokemon_details['moves']]
        redis_service.set(cache_key, json.dumps(moves), expire=3600)
        return moves

    @staticmethod
    def get_pokemon_species(pokemon_id):
        """获取宝可梦物种信息，包括中文名称"""
        cache_key = f"pokemon_species:{pokemon_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        url = f"{PokemonDataService.POKEAPI_BASE_URL}/pokemon-species/{pokemon_id}"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        # 获取中文名称
        name_zh = next((name['name'] for name in data['names'] if name['language']['name'] == 'zh-Hans'), data['name'])
        data['name_zh'] = name_zh
        redis_service.set(cache_key, json.dumps(data), expire=3600)
        return data

    @staticmethod
    def get_move_details(move_name):
        """获取招式详细信息，包括中文名称"""
        cache_key = f"move_details:{move_name}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/move/{move_name}"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        name_zh = next((n['name'] for n in data['names'] if n['language']['name'] == 'zh-Hans'), data['name'])
        data['name_zh'] = name_zh
        redis_service.set(cache_key, json.dumps(data), expire=3600)
        return data

    @staticmethod
    def get_ability_list(limit=10000, offset=0, generation_id=None):
        """批量获取特性列表，支持本地化与分代筛选，结果缓存"""
        cache_key = f"ability_list_full:{limit}:{offset}:{generation_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        url = f"{PokemonDataService.POKEAPI_BASE_URL}/ability?limit={limit}&offset={offset}"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        results = []
        for entry in data.get('results', []):
            ab_url = entry['url']
            ab_detail = requests.get(ab_url, **REQUESTS_KWARGS).json()
            # 本地化名
            name_zh = next((n['name'] for n in ab_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), ab_detail['name'])
            # 本地化描述
            effect_zh = None
            for eff in ab_detail.get('effect_entries', []):
                if eff['language']['name'] == 'zh-Hans':
                    effect_zh = eff['effect']
                    break
            if not effect_zh:
                effect_zh = next((eff['effect'] for eff in ab_detail.get('effect_entries', []) if eff['language']['name'] == 'en'), '')
            # 分代筛选（如有 generation 字段，可扩展）
            if generation_id:
                # PokeAPI ability 没有直接 generation 字段，通常所有特性都返回，前端可再做筛选
                pass
            results.append({
                'id': ab_detail['id'],
                'name': ab_detail['name'],
                'name_zh': name_zh,
                'effect_zh': effect_zh,
            })
        redis_service.set(cache_key, json.dumps(results), expire=3600)
        return results

    @staticmethod
    def get_move_list(limit=10000, offset=0, generation_id=None):
        """批量获取招式列表，支持本地化与分代筛选，结果缓存"""
        cache_key = f"move_list_full:{limit}:{offset}:{generation_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        url = f"{PokemonDataService.POKEAPI_BASE_URL}/move?limit={limit}&offset={offset}"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        results = []
        for entry in data.get('results', []):
            move_url = entry['url']
            move_detail = requests.get(move_url, **REQUESTS_KWARGS).json()
            # 本地化名
            name_zh = next((n['name'] for n in move_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), move_detail['name'])
            # 本地化描述
            desc_zh = None
            for eff in move_detail.get('flavor_text_entries', []):
                if eff['language']['name'] == 'zh-Hans':
                    desc_zh = eff['flavor_text']
                    break
            if not desc_zh:
                desc_zh = next((eff['flavor_text'] for eff in move_detail.get('flavor_text_entries', []) if eff['language']['name'] == 'en'), '')
            # 分代筛选
            if generation_id:
                gen = move_detail.get('generation', {}).get('name', None)
                if gen and not gen.endswith(str(generation_id)):
                    continue
            results.append({
                'id': move_detail['id'],
                'name': move_detail['name'],
                'name_zh': name_zh,
                'type': move_detail.get('type', {}).get('name'),
                'category': move_detail.get('damage_class', {}).get('name'),
                'power': move_detail.get('power'),
                'accuracy': move_detail.get('accuracy'),
                'pp': move_detail.get('pp'),
                'desc': desc_zh,
            })
        redis_service.set(cache_key, json.dumps(results), expire=3600)
        return results

    @staticmethod
    def get_item_list(limit=10000, offset=0, generation_id=None, categories=None):
        """批量获取道具列表，支持本地化、分代筛选和分类筛选，结果缓存"""
        cache_key_parts = ["item_list_full", str(limit), str(offset)]
        if generation_id:
            cache_key_parts.append(f"gen:{generation_id}")
        if categories:
            cache_key_parts.append(f"cats:{','.join(sorted(categories))}") # 将列表转为排序后的字符串以保证缓存键一致性
        cache_key = ":".join(cache_key_parts)

        cached_data = redis_service.get(cache_key)
        if cached_data:
            current_app.logger.debug(f"Cache hit for item list: {cache_key}")
            return json.loads(cached_data.decode('utf-8'))
        current_app.logger.debug(f"Cache miss for item list: {cache_key}, querying source.")

        # 此处仅为示例，实际应从数据库查询并实现筛选逻辑
        # 以下代码仍为 PokeAPI 示例，您需要将其改为从本地数据库查询
        # 并根据 generation_id 和 categories 进行过滤

        # --- 示例：如果从 PokeAPI 获取 ---
        # url = f"{PokemonDataService.POKEAPI_BASE_URL}/item?limit={limit}&offset={offset}"
        # response = requests.get(url, **REQUESTS_KWARGS)
        # response.raise_for_status()
        # data = response.json()
        # results = []
        # for entry in data.get('results', []):
        #     item_detail_url = entry['url']
        #     # ... (省略了请求 item_detail 和处理的代码) ...
        #     # 假设 item_detail 包含 category 和 generation 信息
        #     # if generation_id and item_detail_generation != generation_id: continue
        #     # if categories and item_detail_category not in categories: continue
        #     # results.append(...)
        # --- 结束 PokeAPI 示例 ---

        # --- 修改为从本地数据库查询 ---
        query = Item.query

        if generation_id:
            # 假设 Item 模型有 generation 字段 (字符串，如 "generation-ix") 或 generation_id 字段 (数字)
            # query = query.filter(Item.generation_id == generation_id) # 如果是数字ID
            # 或者，如果 Item.generation 是 "generation-ix" 这样的名称
            gen_obj = Generation.query.filter(Generation.name.like(f"%{generation_id}%")).first() # 模糊匹配 "generation-ix" 或 数字
            if gen_obj:
                query = query.filter(Item.generation_id == gen_obj.id) # 假设 Item 有 generation_id 关联 Generation 表
            else:
                # 如果 Item.generation 直接存的是 "generation-ix"
                query = query.filter(Item.generation == f"generation-{generation_id}") # 需要精确匹配，或 Item 模型有相关字段

        if categories is not None and isinstance(categories, list) and len(categories) > 0:
            query = query.filter(Item.category.in_(categories))
        else:
            # 如果未指定分类、指定了空列表或指定了非列表类型，使用默认分类过滤
            default_categories = ['held-items', 'bad-held-items', 'choice', 'mega-stones', 'z-crystals', 'plates', 'picky-healing', 'species-specific', 'medicine']
            query = query.filter(Item.category.in_(default_categories))

        db_items = query.offset(offset).limit(limit).all()
        results = []
        for item in db_items:
            results.append({
                'id': item.id,
                'name': item.name,
                'name_zh': item.name_zh_hans, # 使用 name_zh_hans
                'category': item.category,
                'effect': item.description_zh_hans, # 使用 description_zh_hans 作为 effect
                'effect_en': item.description_en, # 添加英文描述
                'sprite': item.sprite,
                # 'generation': item.generation # 如果需要返回
            })
        # --- 结束本地数据库查询 ---


        if results: # 只有当成功获取到数据时才设置缓存
            redis_service.set(cache_key, json.dumps(results), expire=3600) # Cache for 1 hour
        return results

    @staticmethod
    def _load_fetch_progress():
        progress_file = PokemonDataService._get_progress_file_path()
        if not current_app.config.get('SAVE_FETCH_PROGRESS', False):
            return {}
        try:
            with open(progress_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            current_app.logger.info(f"进度文件 {progress_file} 未找到，将从头开始。")
            return {}
        except Exception as e:
            current_app.logger.error(f"加载进度文件 {progress_file} 失败: {e}")
            return {}

    @staticmethod
    def _save_fetch_progress(progress):
        progress_file = PokemonDataService._get_progress_file_path()
        if not current_app.config.get('SAVE_FETCH_PROGRESS', False):
            return
        dir_path = os.path.dirname(progress_file)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                current_app.logger.error(f"创建进度文件目录 {dir_path} 失败: {e}")
                return
        try:
            with open(progress_file, 'wb') as f:
                pickle.dump(progress, f)
        except Exception as e:
            current_app.logger.error(f"保存进度文件 {progress_file} 失败: {e}")

    @staticmethod
    def refresh_all_data():
        """定时全量同步PokeAPI数据到本地数据库和缓存，支持进度显示与断点续拉"""
        show_progress = current_app.config.get('SHOW_FETCH_PROGRESS', False)
        save_progress = current_app.config.get('SAVE_FETCH_PROGRESS', False)
        force_fetch = current_app.config.get('FORCE_FETCH_ON_STARTUP', False)
        progress = PokemonDataService._load_fetch_progress() if save_progress else {}
        # 只在force_fetch或无进度时才拉取
        if not force_fetch and progress.get('all_done'):
            if show_progress:
                print('[DataSync] 已完成，无需重复拉取')
            return
        # 拉取并边写入
        def fetch_and_write(entity, fetch_func, sync_func, key):
            if progress.get(key) == 'done':
                if show_progress:
                    print(f'[DataSync] {key} 已完成，跳过')
                return
            batch = []
            for idx, item in enumerate(fetch_func()):
                batch.append(item)
                if len(batch) >= 10:
                    try:
                        sync_func(batch)
                    except Exception as e:
                        print(f"[DataSync][{key}] 批量同步异常: {e}")
                        import traceback
                        traceback.print_exc()
                    batch = []
                if show_progress and idx % 10 == 0:
                    print(f'[DataSync] {key}: {idx+1} 条...')
                if save_progress and idx % 50 == 0:
                    progress[key] = idx
                    PokemonDataService._save_fetch_progress(progress)
            if batch:
                try:
                    sync_func(batch)
                except Exception as e:
                    print(f"[DataSync][{key}] 批量同步异常: {e}")
                    import traceback
                    traceback.print_exc()
            progress[key] = 'done'
            PokemonDataService._save_fetch_progress(progress)
        # fetch_and_write('pokemon_species', lambda: (x for x in PokemonDataService.fetch_pokemons() if 'species_id' in x), PokemonDataService.sync_pokemon_species_to_db, 'pokemon_species')
        # fetch_and_write('pokemon', lambda: (x for x in PokemonDataService.fetch_pokemons() if 'id' in x), PokemonDataService.sync_pokemons_to_db, 'pokemon')
        # fetch_and_write('ability', PokemonDataService.fetch_abilities, PokemonDataService.sync_abilities_to_db, 'ability')
        # fetch_and_write('move', PokemonDataService.fetch_moves, PokemonDataService.sync_moves_to_db, 'move')
        # fetch_and_write('item', PokemonDataService.fetch_items, PokemonDataService.sync_items_to_db, 'item')  # 已有item数据，后续不同步，防止重复爬取和报错
        # PokemonDataService.fetch_and_sync_types()
        # PokemonDataService.fetch_and_sync_generations()
        # 新增：补全 generation_pokemon_species 的 version_group_id 字段
        try:
            # PokemonDataService.fetch_and_sync_pokemon_generations()
            print(1)
        except Exception as e:
            print(f"[DataSync][generation_pokemon_species version_group_id] 补全异常: {e}")
            import traceback
            traceback.print_exc()
        # PokemonDataService.fetch_and_sync_version_groups()  # 暂停version_group同步，避免外网请求
        # 集成全局宝可梦招式学习表同步
        # PokemonDataService.fetch_and_sync_pokemon_move_learnsets()
        # New call to sync form abilities
        try:
            current_app.logger.info("[DataSync] Starting Pokemon Form Abilities sync...")
            PokemonDataService.fetch_and_sync_pokemon_form_abilities()
            current_app.logger.info("[DataSync] Pokemon Form Abilities sync completed.")
        except Exception as e:
            current_app.logger.error(f"[DataSync][PokemonFormAbilities] Sync failed: {e}")
            import traceback
            traceback.print_exc()
        progress['all_done'] = True
        PokemonDataService._save_fetch_progress(progress)
        if show_progress:
            print('[DataSync] 全部拉取完成')

    @staticmethod
    def start_periodic_refresh(interval_hours=24):
        """启动定时后台线程，定期刷新本地数据和缓存，自动注入 Flask app context"""
        from flask import current_app
        app = current_app._get_current_object()
        def loop():
            while True:
                try:
                    with app.app_context():
                        PokemonDataService.refresh_all_data()
                except Exception as e:
                    print(f"[DataSync] 定时同步失败: {e}")
                time.sleep(interval_hours * 3600)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    @staticmethod
    def sync_abilities_to_db(abilities: list):
        for ab in abilities:
            obj = Ability.query.filter_by(id=ab['id']).first()
            if not obj:
                obj = Ability(id=ab['id'])
            obj.name = ab['name']
            obj.name_zh_hans = ab.get('name_zh')
            obj.description_en = ab.get('effect_en')
            obj.description_zh_hans = ab.get('effect_zh')
            print(f"[AbilitySync] id={ab['id']} name={ab['name']} zh={ab['name_zh']} desc_zh={ab.get('effect_zh')}")
            db.session.merge(obj)
        db.session.commit()

    @staticmethod
    def sync_moves_to_db(moves: list):
        for mv in moves:
            obj = Move.query.filter_by(id=mv['id']).first()
            if not obj:
                obj = Move(id=mv['id'])
            obj.name = mv['name']
            obj.name_zh_hans = mv.get('name_zh')
            obj.type = mv.get('type')
            obj.category = mv.get('category')
            obj.power = mv.get('power')
            obj.accuracy = mv.get('accuracy')
            obj.pp = mv.get('pp')
            obj.description_en = mv.get('desc_en')
            obj.description_zh_hans = mv.get('desc')
            obj.generation = mv.get('generation')
            db.session.merge(obj)
        db.session.commit()

    @staticmethod
    def sync_items_to_db(items: list):
        from sqlalchemy.exc import IntegrityError
        with db.session.no_autoflush:
            for it in items:
                if 'id' not in it:
                    print(f"[ItemSync][Error] item数据缺少id字段: {it}")
                    raise AssertionError(f"item数据缺少id字段: {it}")
                obj = Item.query.filter_by(id=it['id']).first()
                if not obj:
                    obj = Item(id=it['id'])
                obj.name = it['name']
                obj.name_zh_hans = it.get('name_zh')
                obj.category = it.get('category')
                obj.description_en = it.get('desc_en')
                obj.description_zh_hans = it.get('desc')
                obj.sprite = it.get('sprite')
                obj.generation = it.get('generation')
                try:
                    db.session.merge(obj)
                except IntegrityError as e:
                    db.session.rollback()
                    print(f"[ItemSync] 跳过重复id={it.get('id')} name={it.get('name')}，错误：{e}")
        db.session.commit()

    @staticmethod
    def sync_pokemons_to_db(pokemons: list):
        from sqlalchemy.exc import IntegrityError
        with db.session.no_autoflush:
            for poke in pokemons:
                obj = Pokemon.query.filter_by(id=poke['id']).first()
                if not obj:
                    obj = Pokemon(id=poke['id'])
                obj.species_id = poke['species_id']
                obj.name = poke['name']
                obj.form_name = poke.get('form_name')
                obj.form_name_zh_hans = poke.get('form_name_zh_hans')
                obj.is_default = poke.get('is_default', True)
                obj.sprite = poke.get('sprite')
                obj.type_1 = poke.get('type_1')
                obj.type_2 = poke.get('type_2')
                obj.base_hp = poke.get('base_hp')
                obj.base_atk = poke.get('base_atk')
                obj.base_def = poke.get('base_def')
                obj.base_spa = poke.get('base_spa')
                obj.base_spd = poke.get('base_spd')
                obj.base_spe = poke.get('base_spe')
                try:
                    db.session.merge(obj)
                except IntegrityError as e:
                    db.session.rollback()
                    print(f"[PokemonSync] 跳过重复id={poke['id']}，错误：{e}")
        db.session.commit()

    @staticmethod
    def sync_pokemon_species_to_db(species: list):
        # 只处理主形态（is_default）且species_id唯一
        species_map = {}
        for sp in species:
            if sp.get('is_default'):
                sid = sp['species_id']
                if sid not in species_map or (sp.get('name_zh') and not species_map[sid].get('name_zh')):
                    species_map[sid] = sp
        for sp in species_map.values():
            obj = PokemonSpecies.query.filter_by(id=sp['species_id']).first()
            if not obj:
                obj = PokemonSpecies(id=sp['species_id'])
            if sp.get('name'):
                obj.name = sp['name']
            if sp.get('name_zh'):
                obj.name_zh_hans = sp['name_zh']
            if sp.get('gender_rate') is not None:
                obj.gender_rate = sp['gender_rate']
            if hasattr(obj, 'generations') and sp.get('generations'):
                obj.generations = [Generation.query.filter_by(name=gen).first() for gen in sp['generations'] if Generation.query.filter_by(name=gen).first()]
            print(f"[SyncSpecies] id={sp['species_id']} name={sp.get('name','')} zh={sp.get('name_zh','')} gender_rate={sp.get('gender_rate','')}")
            db.session.merge(obj)
        db.session.commit()

    @staticmethod
    def sync_types_to_db(types: list):
        for t in types:
            if 'id' not in t:
                print(f"[TypeSync][Error] type数据缺少id字段: {t}")
                raise AssertionError(f"type数据缺少id字段: {t}")
            obj = Type.query.filter_by(id=t['id']).first()
            if not obj:
                obj = Type(id=t['id'])
            obj.name = t['name']
            obj.name_zh_hans = t.get('name_zh')
            db.session.add(obj)
        db.session.commit()

    @staticmethod
    def sync_generations_to_db(generations: list):
        for g in generations:
            if 'id' not in g:
                print(f"[GenerationSync][Error] generation数据缺少id字段: {g}")
                raise AssertionError(f"generation数据缺少id字段: {g}")
            obj = Generation.query.filter_by(id=g['id']).first()
            if not obj:
                obj = Generation(id=g['id'])
            obj.name = g['name']
            db.session.add(obj)
        db.session.commit()

    @staticmethod
    def sync_version_groups_to_db(vgs: list):
        for vg in vgs:
            if 'id' not in vg:
                print(f"[VersionGroupSync][Error] version_group数据缺少id字段: {vg}")
                raise AssertionError(f"version_group数据缺少id字段: {vg}")
            try:
                obj = VersionGroup.query.filter_by(id=vg['id']).first()
                if not obj:
                    obj = VersionGroup(id=vg['id'])
                obj.name = vg['name']
                obj.generation_id = vg.get('generation_id')
                print(f"[VersionGroupSync] id={vg['id']} name={vg.get('name')} generation_id={vg.get('generation_id')}")
                db.session.add(obj)
            except Exception as e:
                print(f"[VersionGroupSync][Exception] 数据: {vg}, 错误: {e}")
                import traceback
                traceback.print_exc()
                raise
        db.session.commit()

    @staticmethod
    def fetch_and_sync_types():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/type?limit=100"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        results = []
        for entry in data.get('results', []):
            type_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            name_zh = next((n['name'] for n in type_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), type_detail['name'])
            results.append({'id': type_detail['id'], 'name': type_detail['name'], 'name_zh': name_zh})
        PokemonDataService.sync_types_to_db(results)

    @staticmethod
    def fetch_and_sync_generations():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/generation?limit=20"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        results = []
        for entry in data.get('results', []):
            gen_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            results.append({'id': gen_detail['id'], 'name': gen_detail['name']})
        PokemonDataService.sync_generations_to_db(results)

    @staticmethod
    def fetch_and_sync_version_groups():
        import re
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/version-group?limit=50"
        response = requests.get(url, **REQUESTS_KWARGS)
        response.raise_for_status()
        data = response.json()
        results = []
        for entry in data.get('results', []):
            try:
                vg_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
                print(f"[VersionGroupFetch] id={vg_detail.get('id')} name={vg_detail.get('name')} generation={vg_detail.get('generation')}")
                gen_url = vg_detail['generation']['url']
                match = re.search(r'/generation/(\d+)/?$', gen_url) if gen_url else None
                if match:
                    gen_id = int(match.group(1))
                else:
                    print(f"[VersionGroupFetch][Warn] generation url无法提取id: {gen_url}")
                    gen_id = None
                results.append({'id': vg_detail['id'], 'name': vg_detail['name'], 'generation_id': gen_id})
            except Exception as e:
                print(f"[VersionGroupFetch][Exception] entry: {entry}, 错误: {e}")
                import traceback
                traceback.print_exc()
                raise
        PokemonDataService.sync_version_groups_to_db(results)

    @staticmethod
    def fetch_pokemons():
        # 生成器：只在主形态yield物种，所有形态yield形态
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/pokemon?limit=10000&offset=0"
        response = requests.get(url, **REQUESTS_KWARGS)
        data = response.json()
        for entry in data.get('results', []):
            poke_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            poke_id = poke_detail['id']
            name = poke_detail['name']
            sprite = poke_detail['sprites']['front_default']
            types = [t['type']['name'] for t in poke_detail['types']]
            base_stats = {s['stat']['name']: s['base_stat'] for s in poke_detail['stats']}
            abilities = [a['ability']['name'] for a in poke_detail['abilities']]
            is_default = poke_detail.get('is_default', True)
            form_name = poke_detail.get('forms', [{}])[0].get('name') if poke_detail.get('forms') else None
            # 物种信息
            species_url = poke_detail['species']['url']
            species_detail = requests.get(species_url, **REQUESTS_KWARGS).json()
            species_id = species_detail['id']
            name_zh = next((n['name'] for n in species_detail['names'] if n['language']['name'] == 'zh-Hans'), name)
            gender_rate = species_detail.get('gender_rate')
            generations = []
            if 'generation' in species_detail:
                generations = [species_detail['generation']['name']]

            # 形态中文名拼接逻辑
            def get_form_zh(poke_name, form_name, species_name_zh):
                n = poke_name.lower()
                f = (form_name or '').lower() if form_name else ''
                # Mega
                if '-mega' in n:
                    if n.endswith('-mega-x'):
                        return f"{species_name_zh}-Mega-X"
                    elif n.endswith('-mega-y'):
                        return f"{species_name_zh}-Mega-Y"
                    else:
                        return f"{species_name_zh}-Mega"
                # 超极巨化
                if 'gmax' in n or 'gigantamax' in n:
                    return f"{species_name_zh}-超极巨化"
                # 阿罗拉
                if 'alola' in n or 'alola' in f:
                    return f"{species_name_zh}-阿罗拉"
                # 伽勒尔
                if 'galar' in n or 'galar' in f:
                    return f"{species_name_zh}-伽勒尔"
                # 洗翠
                if 'hisui' in n or 'hisui' in f:
                    return f"{species_name_zh}-洗翠"
                # 帕底亚
                if 'paldea' in n or 'paldea' in f:
                    # 肯泰罗帕底亚三种
                    if 'tauros' in n:
                        if 'combat' in n:
                            return f"{species_name_zh}-帕底亚·斗战种"
                        elif 'blaze' in n:
                            return f"{species_name_zh}-帕底亚·火炽种"
                        elif 'aqua' in n:
                            return f"{species_name_zh}-帕底亚·水澜种"
                        else:
                            return f"{species_name_zh}-帕底亚"
                    return f"{species_name_zh}-帕底亚"
                # 武道熊师
                if 'urshifu' in n:
                    if 'single-strike' in n:
                        return f"{species_name_zh}-一击流"
                    if 'rapid-strike' in n:
                        return f"{species_name_zh}-连击流"
                # 洛托姆家族
                if 'rotom' in n:
                    if 'heat' in n:
                        return "加热洛托姆"
                    if 'wash' in n:
                        return "清洗洛托姆"
                    if 'frost' in n:
                        return "结冰洛托姆"
                    if 'fan' in n:
                        return "旋转洛托姆"
                    if 'mow' in n:
                        return "切割洛托姆"
                # 月月熊赫月
                if 'ursaluna' in n and 'bloodmoon' in n:
                    return f"{species_name_zh}-赫月"
                # 厄诡椪
                if 'ogerpon' in n:
                    if 'teal' in n:
                        return f"{species_name_zh}-碧草面具"
                    if 'wellspring' in n:
                        return f"{species_name_zh}-水井面具"
                    if 'cornerstone' in n:
                        return f"{species_name_zh}-础石面具"
                    if 'hearthflame' in n:
                        return f"{species_name_zh}-火灶面具"
                # 太乐巴戈斯
                if 'terapagos' in n:
                    if 'stellar' in n:
                        return f"{species_name_zh}-星晶形态"
                    if 'terrestrial' in n:
                        return f"{species_name_zh}-太晶形态"
                # 其它情况：如有后缀，拼接英文后缀（首字母大写，多个后缀用-连接）
                if '-' in poke_name:
                    base, *suffix = poke_name.split('-')
                    if suffix:
                        suffix_str = '-'.join([s.capitalize() for s in suffix])
                        return f"{species_name_zh}-{suffix_str}"
                return species_name_zh

            # 只在主形态时yield物种
            if is_default:
                yield {
                    'species_id': species_id,
                    'name': name,
                    'name_zh': name_zh,
                    'gender_rate': gender_rate,
                    'generations': generations,
                    'is_default': True
                }
            # 所有形态都yield形态数据
            yield {
                'id': poke_id,
                'species_id': species_id,
                'name': name,
                'name_zh': get_form_zh(name, form_name, name_zh),
                'form_name': get_form_zh(name, form_name, form_name) if form_name else None,
                'form_name_zh_hans': get_form_zh(name, form_name, name_zh),
                'is_default': is_default,
                'sprite': sprite,
                'type_1': types[0] if types else None,
                'type_2': types[1] if len(types) > 1 else None,
                'base_hp': base_stats.get('hp'),
                'base_atk': base_stats.get('attack'),
                'base_def': base_stats.get('defense'),
                'base_spa': base_stats.get('special-attack'),
                'base_spd': base_stats.get('special-defense'),
                'base_spe': base_stats.get('speed'),
            }

    @staticmethod
    def fetch_abilities():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/ability?limit=10000&offset=0"
        response = requests.get(url, **REQUESTS_KWARGS)
        data = response.json()
        for entry in data.get('results', []):
            ab_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            name_zh = next((n['name'] for n in ab_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), ab_detail['name'])
            # 兼容 flavor_text/text 字段
            desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in ab_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'zh-Hans'), None)
            if not desc_zh:
                desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in ab_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'en'), '')
            print(f"[AbilityFetch] id={ab_detail['id']} name={ab_detail['name']} name_zh={name_zh} desc_zh={desc_zh}")
            yield {
                'id': ab_detail['id'],
                'name': ab_detail['name'],
                'name_zh': name_zh,
                'effect_en': next((eff['effect'] for eff in ab_detail.get('effect_entries', []) if eff['language']['name'] == 'en'), ''),
                'effect_zh': desc_zh
            }

    @staticmethod
    def fetch_moves():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/move?limit=10000&offset=0"
        response = requests.get(url, **REQUESTS_KWARGS)
        data = response.json()
        for entry in data.get('results', []):
            move_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            name_zh = next((n['name'] for n in move_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), move_detail['name'])
            desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in move_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'zh-Hans'), None)
            if not desc_zh:
                desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in move_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'en'), None)
            yield {
                'id': move_detail['id'],
                'name': move_detail['name'],
                'name_zh': name_zh,
                'type': move_detail.get('type', {}).get('name'),
                'category': move_detail.get('damage_class', {}).get('name'),
                'power': move_detail.get('power'),
                'accuracy': move_detail.get('accuracy'),
                'pp': move_detail.get('pp'),
                'desc_en': next((eff['short_effect'] for eff in move_detail.get('effect_entries', []) if eff['language']['name'] == 'en'), None),
                'desc': desc_zh,
                'generation': move_detail.get('generation', {}).get('name', None),
            }

    @staticmethod
    def fetch_items():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/item?limit=10000&offset=0"
        response = requests.get(url, **REQUESTS_KWARGS)
        data = response.json()
        for entry in data.get('results', []):
            item_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            name_zh = next((n['name'] for n in item_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), item_detail['name'])
            desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in item_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'zh-Hans'), None)
            if not desc_zh:
                desc_zh = next((ft.get('flavor_text') or ft.get('text') for ft in item_detail.get('flavor_text_entries', []) if ft['language']['name'] == 'en'), None)
            sprite = item_detail.get('sprites', {}).get('default')
            yield {
                'id': item_detail['id'],
                'name': item_detail['name'],
                'name_zh': name_zh,
                'category': item_detail.get('category', {}).get('name', ''),
                'desc_en': next((eff.get('effect') or eff.get('short_effect') for eff in item_detail.get('effect_entries', []) if eff['language']['name'] == 'en'), None),
                'desc': desc_zh,
                'sprite': sprite,
                'generation': item_detail.get('generation', {}).get('name', None),
            }

    @staticmethod
    def fetch_pokemon_species():
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/pokemon-species?limit=10000&offset=0"
        response = requests.get(url, **REQUESTS_KWARGS)
        data = response.json()
        for entry in data.get('results', []):
            species_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
            name_zh = next((n['name'] for n in species_detail.get('names', []) if n['language']['name'] == 'zh-Hans'), species_detail['name'])
            yield {
                'id': species_detail['id'],
                'name': species_detail['name'],
                'name_zh': name_zh,
                'gender_rate': species_detail.get('gender_rate'),
                'generation': species_detail.get('generation', {}).get('name', None),
            }

    @staticmethod
    def fetch_pokemons_v2():
        # 分页拉取宝可梦数据，支持断点续传
        url = f"{PokemonDataService.POKEAPI_BASE_URL}/pokemon"
        offset = 0
        limit = 100
        while True:
            params = {'limit': limit, 'offset': offset}
            response = requests.get(url, params=params, **REQUESTS_KWARGS)
            response.raise_for_status()
            data = response.json()
            if not data.get('results'):
                break
            for entry in data.get('results', []):
                poke_detail = requests.get(entry['url'], **REQUESTS_KWARGS).json()
                poke_id = poke_detail['id']
                name = poke_detail['name']
                sprite = poke_detail['sprites']['front_default']
                types = [t['type']['name'] for t in poke_detail['types']]
                base_stats = {s['stat']['name']: s['base_stat'] for s in poke_detail['stats']}
                abilities = [a['ability']['name'] for a in poke_detail['abilities']]
                is_default = poke_detail.get('is_default', True)
                form_name = poke_detail.get('forms', [{}])[0].get('name') if poke_detail.get('forms') else None
                # 物种信息
                species_url = poke_detail['species']['url']
                species_detail = requests.get(species_url, **REQUESTS_KWARGS).json()
                species_id = species_detail['id']
                name_zh = next((n['name'] for n in species_detail['names'] if n['language']['name'] == 'zh-Hans'), name)
                gender_rate = species_detail.get('gender_rate')
                generations = []
                if 'generation' in species_detail:
                    generations = [species_detail['generation']['name']]

                # 形态中文名拼接逻辑
                def get_form_zh(poke_name, form_name, species_name_zh):
                    n = poke_name.lower()
                    f = (form_name or '').lower() if form_name else ''
                    # Mega
                    if '-mega' in n:
                        if n.endswith('-mega-x'):
                            return f"{species_name_zh}-Mega-X"
                        elif n.endswith('-mega-y'):
                            return f"{species_name_zh}-Mega-Y"
                        else:
                            return f"{species_name_zh}-Mega"
                    # 超极巨化
                    if 'gmax' in n or 'gigantamax' in n:
                        return f"{species_name_zh}-超极巨化"
                    # 阿罗拉
                    if 'alola' in n or 'alola' in f:
                        return f"{species_name_zh}-阿罗拉"
                    # 伽勒尔
                    if 'galar' in n or 'galar' in f:
                        return f"{species_name_zh}-伽勒尔"
                    # 洗翠
                    if 'hisui' in n or 'hisui' in f:
                        return f"{species_name_zh}-洗翠"
                    # 帕底亚
                    if 'paldea' in n or 'paldea' in f:
                        # 肯泰罗帕底亚三种
                        if 'tauros' in n:
                            if 'combat' in n:
                                return f"{species_name_zh}-帕底亚·斗战种"
                            elif 'blaze' in n:
                                return f"{species_name_zh}-帕底亚·火炽种"
                            elif 'aqua' in n:
                                return f"{species_name_zh}-帕底亚·水澜种"
                            else:
                                return f"{species_name_zh}-帕底亚"
                        return f"{species_name_zh}-帕底亚"
                    # 武道熊师
                    if 'urshifu' in n:
                        if 'single-strike' in n:
                            return f"{species_name_zh}-一击流"
                        if 'rapid-strike' in n:
                            return f"{species_name_zh}-连击流"
                    # 洛托姆家族
                    if 'rotom' in n:
                        if 'heat' in n:
                            return "加热洛托姆"
                        if 'wash' in n:
                            return "清洗洛托姆"
                        if 'frost' in n:
                            return "结冰洛托姆"
                        if 'fan' in n:
                            return "旋转洛托姆"
                        if 'mow' in n:
                            return "切割洛托姆"
                    # 月月熊赫月
                    if 'ursaluna' in n and 'bloodmoon' in n:
                        return f"{species_name_zh}-赫月"
                    # 厄诡椪
                    if 'ogerpon' in n:
                        if 'teal' in n:
                            return f"{species_name_zh}-碧草面具"
                        if 'wellspring' in n:
                            return f"{species_name_zh}-水井面具"
                        if 'cornerstone' in n:
                            return f"{species_name_zh}-础石面具"
                        if 'hearthflame' in n:
                            return f"{species_name_zh}-火灶面具"
                    # 太乐巴戈斯
                    if 'terapagos' in n:
                        if 'stellar' in n:
                            return f"{species_name_zh}-星晶形态"
                        if 'terrestrial' in n:
                            return f"{species_name_zh}-太晶形态"
                    # 其它情况：如有后缀，拼接英文后缀（首字母大写，多个后缀用-连接）
                    if '-' in poke_name:
                        base, *suffix = poke_name.split('-')
                        if suffix:
                            suffix_str = '-'.join([s.capitalize() for s in suffix])
                            return f"{species_name_zh}-{suffix_str}"
                    return species_name_zh

                # 只在主形态时yield物种
                if is_default:
                    yield {
                        'species_id': species_id,
                        'name': name,
                        'name_zh': name_zh,
                        'gender_rate': gender_rate,
                        'generations': generations,
                        'is_default': True
                    }
                # 所有形态都yield形态数据
                yield {
                    'id': poke_id,
                    'species_id': species_id,
                    'name': name,
                    'name_zh': get_form_zh(name, form_name, name_zh),
                    'form_name': get_form_zh(name, form_name, form_name) if form_name else None,
                    'form_name_zh_hans': get_form_zh(name, form_name, name_zh),
                    'is_default': is_default,
                    'sprite': sprite,
                    'type_1': types[0] if types else None,
                    'type_2': types[1] if len(types) > 1 else None,
                    'base_hp': base_stats.get('hp'),
                    'base_atk': base_stats.get('attack'),
                    'base_def': base_stats.get('defense'),
                    'base_spa': base_stats.get('special-attack'),
                    'base_spd': base_stats.get('special-defense'),
                    'base_spe': base_stats.get('speed'),
                }

    @staticmethod
    def fetch_and_sync_pokemon_generations():
        """
        基于pokedex+version_group统计每一世代可用宝可梦物种，并补充形态的初登场世代。
        """
        import requests
        from ..models import Generation, PokemonSpecies, Pokemon, db
        print('[GenSpeciesSync] 开始同步宝可梦-世代关系...')
        # 1. 获取所有generation
        generations = {g.id: g for g in Generation.query.all()}
        # 2. 获取所有pokedex
        pokedex_list = requests.get('https://pokeapi.co/api/v2/pokedex?limit=100&offset=0', **REQUESTS_KWARGS).json()['results']
        # 3. 统计每个generation下所有species
        species_gen_map = {}  # species_id: set(generation_id)
        for pdx in pokedex_list:
            pdx_data = requests.get(pdx['url'], **REQUESTS_KWARGS).json()
            # 通过pokedex的version_groups找到generation
            version_groups = pdx_data.get('version_groups', [])
            gen_ids = set()
            for vg in version_groups:
                vg_data = requests.get(vg['url'], **REQUESTS_KWARGS).json()
                # 兼容 generation 字段为 dict 或 url
                gen_info = vg_data.get('generation')
                gen_id = None
                if isinstance(gen_info, dict):
                    gen_id = gen_info.get('id')
                    if not gen_id and 'url' in gen_info:
                        import re
                        match = re.search(r'/generation/(\d+)/?$', gen_info['url'])
                        if match:
                            gen_id = int(match.group(1))
                if not gen_id:
                    print(f"[GenSpeciesSync][Error] version_group数据异常: {vg_data}")
                    continue
                gen_ids.add(gen_id)
            for entry in pdx_data.get('pokemon_entries', []):
                species_url = entry['pokemon_species']['url']
                species_id = int(species_url.rstrip('/').split('/')[-1])
                if species_id not in species_gen_map:
                    species_gen_map[species_id] = set()
                species_gen_map[species_id].update(gen_ids)
        # 4. 写入generation_pokemon_species（含version_group_id）
        from sqlalchemy import text
        vg_map = {}
        for vg in VersionGroup.query.all():
            vg_map.setdefault(vg.generation_id, []).append(vg.id)
        conn = db.engine.connect()
        inserted = 0
        for species_id, gen_ids in species_gen_map.items():
            for gen_id in gen_ids:
                vgs = vg_map.get(gen_id, [])
                for vg_id in vgs:
                    exists = conn.execute(text('SELECT 1 FROM generation_pokemon_species WHERE generation_id=:g AND pokemon_species_id=:s AND version_group_id=:v'), {'g': gen_id, 's': species_id, 'v': vg_id}).fetchone()
                    if not exists:
                        conn.execute(text('INSERT INTO generation_pokemon_species (generation_id, pokemon_species_id, version_group_id) VALUES (:g, :s, :v)'), {'g': gen_id, 's': species_id, 'v': vg_id})
                        inserted += 1
        conn.commit()
        conn.close()
        print(f'[GenSpeciesSync] generation_pokemon_species 初始写入完成，插入 {inserted} 条记录')
        print('[GenSpeciesSync] 物种-世代关系同步完成')
        # 5. 处理形态的初登场世代
        all_pokemon = Pokemon.query.all()
        for poke in all_pokemon:
            if not poke.is_default:
                # 形态，需查form
                form_url = f'https://pokeapi.co/api/v2/pokemon-form/{poke.name}/'
                try:
                    form_data = requests.get(form_url, **REQUESTS_KWARGS).json()
                    # 形态的generation通过form_data['version_group']['url']
                    vg_info = form_data.get('version_group')
                    vg_id = None
                    if vg_info:
                        if 'id' in vg_info:
                            vg_id = vg_info['id']
                        elif 'url' in vg_info:
                            import re
                            match = re.search(r'/version-group/(\d+)/?$', vg_info['url'])
                            if match:
                                vg_id = int(match.group(1))
                    if vg_id:
                        vg_data = requests.get(f'https://pokeapi.co/api/v2/version-group/{vg_id}/', **REQUESTS_KWARGS).json()
                        gen_info = vg_data.get('generation')
                        gen_id = None
                        if isinstance(gen_info, dict):
                            gen_id = gen_info.get('id')
                            if not gen_id and 'url' in gen_info:
                                match = re.search(r'/generation/(\d+)/?$', gen_info['url'])
                                if match:
                                    gen_id = int(match.group(1))
                        if not gen_id and isinstance(gen_info, str):
                            match = re.search(r'/generation/(\d+)/?$', gen_info)
                            if match:
                                gen_id = int(match.group(1))
                        if gen_id:
                            poke.first_generation_id = gen_id
                            db.session.add(poke)
                        else:
                            print(f"[GenSpeciesSync][Warn] 拉取形态{poke.name} generation_id失败: {vg_data}")
                    else:
                        print(f"[GenSpeciesSync][Warn] 拉取形态{poke.name} version_group_id失败: {form_data}")
                except Exception as e:
                    print(f"[GenSpeciesSync][Warn] 拉取形态{poke.name}初登场世代失败: {e}")
        db.session.commit()
        print('[GenSpeciesSync] 形态初登场世代补全完成')
        # 6. 主形态补全 first_generation_id
        all_species = {s.id: s for s in PokemonSpecies.query.all()}
        for poke in all_pokemon:
            if poke.is_default:
                # 查找物种的所有世代
                species = all_species.get(poke.species_id)
                if species and species.generations:
                    min_gen = min([g.id for g in species.generations])
                    poke.first_generation_id = min_gen
                    db.session.add(poke)
        db.session.commit()
        print('[GenSpeciesSync] 主形态 first_generation_id 补全完成')
        # 7. generation_pokemon_species version_group_id 补全
        from sqlalchemy import text
        print('[GenSpeciesSync] 开始补全 generation_pokemon_species.version_group_id ...')
        # 获取所有 generation_id -> version_group_id 列表
        vg_map = {}
        for vg in VersionGroup.query.all():
            vg_map.setdefault(vg.generation_id, []).append(vg.id)
        # 获取所有物种-世代关系
        conn = db.engine.connect()
        res = conn.execute(text('SELECT generation_id, pokemon_species_id FROM generation_pokemon_species')).fetchall()
        to_insert = []
        for row in res:
            gen_id, species_id = row
            vgs = vg_map.get(gen_id, [])
            for vg_id in vgs:
                # 检查是否已存在该三元组
                exists = conn.execute(text('SELECT 1 FROM generation_pokemon_species WHERE generation_id=:g AND pokemon_species_id=:s AND version_group_id=:v'), {'g': gen_id, 's': species_id, 'v': vg_id}).fetchone()
                if not exists:
                    to_insert.append({'generation_id': gen_id, 'pokemon_species_id': species_id, 'version_group_id': vg_id})
        # 批量插入
        if to_insert:
            print(f'[GenSpeciesSync] 需补全 {len(to_insert)} 条 generation_pokemon_species.version_group_id ...')
            for rec in to_insert:
                conn.execute(text('INSERT INTO generation_pokemon_species (generation_id, pokemon_species_id, version_group_id) VALUES (:g, :s, :v)'), {'g': rec['generation_id'], 's': rec['pokemon_species_id'], 'v': rec['version_group_id']})
            conn.commit()
        else:
            print('[GenSpeciesSync] 无需补全 generation_pokemon_species.version_group_id')
        conn.close()
        print('[GenSpeciesSync] generation_pokemon_species.version_group_id 补全完成')

    @staticmethod
    def fetch_and_sync_pokemon_move_learnsets():
        """
        拉取所有宝可梦物种的所有可学会招式-世代-学习方式数据，写入PokemonMoveLearnset表。
        支持断点续拉、唯一约束、详细日志和异常捕获。
        """
        import requests
        import time
        from sqlalchemy.exc import IntegrityError, OperationalError
        from ..models import PokemonSpecies, Move, VersionGroup, PokemonMoveLearnset, db
        print('[LearnsetSync] 开始同步宝可梦招式学习表...')
        species_list = PokemonSpecies.query.all()
        move_name_to_id = {m.name: m.id for m in Move.query.all()}
        version_group_name_to_id = {vg.name: vg.id for vg in VersionGroup.query.all()}
        total = len(species_list)
        with db.session.no_autoflush:
            for idx, species in enumerate(species_list):
                # 物种级别redis锁
                species_lock_key = f'sync:pokemon_move_learnset:species:lock:{species.id}'
                species_lock_value = str(random.random())
                got_species_lock = redis_service.redis_client.set(species_lock_key, species_lock_value, nx=True, ex=1800)
                if not got_species_lock:
                    print(f"[LearnsetSync] species_id={species.id} 已有其他同步进程在同步，跳过")
                    continue
                try:
                    # 幂等标记，已同步则跳过
                    species_done_key = f'sync:pokemon_move_learnset:species:done:{species.id}'
                    if redis_service.get(species_done_key):
                        print(f"[LearnsetSync] species_id={species.id} 已同步，跳过")
                        continue
                    retry = 0
                    while retry < 3:
                        try:
                            url = f'https://pokeapi.co/api/v2/pokemon-species/{species.id}/'
                            species_data = requests.get(url, **REQUESTS_KWARGS).json()
                            varieties = species_data.get('varieties', [])
                            for var in varieties:
                                poke_url = var['pokemon']['url']
                                poke_data = requests.get(poke_url, **REQUESTS_KWARGS).json()
                                for move in poke_data.get('moves', []):
                                    move_name = move['move']['name']
                                    move_id = move_name_to_id.get(move_name)
                                    if not move_id:
                                        print(f"[LearnsetSync][Warn] 未找到move_id: {move_name}")
                                        continue
                                    for detail in move.get('version_group_details', []):
                                        vg_name = detail['version_group']['name']
                                        vg_id = version_group_name_to_id.get(vg_name)
                                        if not vg_id:
                                            print(f"[LearnsetSync][Warn] 未找到version_group_id: {vg_name}")
                                            continue
                                        learn_method = detail['move_learn_method']['name']
                                        level = detail.get('level_learned_at')
                                        exists = PokemonMoveLearnset.query.filter_by(
                                            pokemon_species_id=species.id,
                                            move_id=move_id,
                                            version_group_id=vg_id,
                                            learn_method=learn_method,
                                            level=level
                                        ).first()
                                        if exists:
                                            continue
                                        obj = PokemonMoveLearnset(
                                            pokemon_species_id=species.id,
                                            move_id=move_id,
                                            version_group_id=vg_id,
                                            learn_method=learn_method,
                                            level=level
                                        )
                                        try:
                                            db.session.add(obj)
                                            db.session.flush()
                                        except IntegrityError as ie:
                                            print(f"[LearnsetSync][Integrity] Duplicate entry: species_id={species.id}, move_id={move_id}, vg_id={vg_id}, method={learn_method}, level={level}")
                                            db.session.rollback()
                                            continue
                            db.session.commit()
                            # 同步成功后写入redis done标记
                            redis_service.set(species_done_key, '1')
                            if idx % 20 == 0:
                                print(f"[LearnsetSync] 进度: {idx+1}/{total}")
                            break  # 成功则跳出重试
                        except OperationalError as oe:
                            if 'database is locked' in str(oe):
                                print(f"[LearnsetSync][Locked] database is locked, rollback & retry {retry+1}/3...")
                                db.session.rollback()
                                time.sleep(1 + retry)
                                retry += 1
                            else:
                                print(f"[LearnsetSync][Error] species_id={species.id} name={species.name}: {oe}")
                                import traceback
                                traceback.print_exc()
                                break
                        except Exception as e:
                            print(f"[LearnsetSync][Error] species_id={species.id} name={species.name}: {e}")
                            import traceback
                            traceback.print_exc()
                            break
                finally:
                    # 只释放自己加的锁
                    if redis_service.redis_client.get(species_lock_key) == species_lock_value.encode():
                        redis_service.redis_client.delete(species_lock_key)
        print('[LearnsetSync] 全部同步完成')

    @staticmethod
    def patch_missing_pokemon_move_learnsets():
        """
        仅补全本地 pokemon_move_learnset 表中缺失的 species_id 的数据，不再新请求已存在的。
        """
        import requests
        from ..models import PokemonMoveLearnset, db
        # 1. 获取 PokeAPI 物种总数
        url = "https://pokeapi.co/api/v2/pokemon-species?limit=1"
        resp = requests.get(url, **REQUESTS_KWARGS)
        data = resp.json()
        max_species_id = data["count"]
        print(f"[LearnsetPatch] PokeAPI 物种总数: {max_species_id}")
        # 2. 查询本地已同步的 species_id
        synced_ids = set([row[0] for row in db.session.query(PokemonMoveLearnset.pokemon_species_id).distinct()])
        # 3. 仅补齐缺失的 species_id
        missing_ids = [i for i in range(1, max_species_id+1) if i not in synced_ids]
        print(f"[LearnsetPatch] 待补全 species_id 数量: {len(missing_ids)}")
        # 4. 复用物种级同步逻辑，仅补齐缺失部分
        for species_id in missing_ids:
            try:
                # 直接调用单物种 learnset 同步逻辑
                PokemonDataService.sync_single_pokemon_move_learnset(species_id)
            except Exception as e:
                print(f"[LearnsetPatch][Error] species_id={species_id}: {e}")
        print("[LearnsetPatch] 补全完成")

    @staticmethod
    def sync_single_pokemon_move_learnset(species_id):
        """
        同步单个物种的 learnset 数据，已存在则跳过。
        """
        import requests
        from sqlalchemy.exc import IntegrityError, OperationalError
        from ..models import Move, VersionGroup, PokemonMoveLearnset, db
        move_name_to_id = {m.name: m.id for m in Move.query.all()}
        version_group_name_to_id = {vg.name: vg.id for vg in VersionGroup.query.all()}
        url = f'https://pokeapi.co/api/v2/pokemon-species/{species_id}/'
        species_data = requests.get(url, **REQUESTS_KWARGS).json()
        varieties = species_data.get('varieties', [])
        with db.session.no_autoflush:
            for var in varieties:
                poke_url = var['pokemon']['url']
                poke_data = requests.get(poke_url, **REQUESTS_KWARGS).json()
                for move in poke_data.get('moves', []):
                    move_name = move['move']['name']
                    move_id = move_name_to_id.get(move_name)
                    if not move_id:
                        continue
                    for detail in move.get('version_group_details', []):
                        vg_name = detail['version_group']['name']
                        vg_id = version_group_name_to_id.get(vg_name)
                        if not vg_id:
                            continue
                        learn_method = detail['move_learn_method']['name']
                        level = detail.get('level_learned_at')
                        exists = PokemonMoveLearnset.query.filter_by(
                            pokemon_species_id=species_id,
                            move_id=move_id,
                            version_group_id=vg_id,
                            learn_method=learn_method,
                            level=level
                        ).first()
                        if exists:
                            continue
                        obj = PokemonMoveLearnset(
                            pokemon_species_id=species_id,
                            move_id=move_id,
                            version_group_id=vg_id,
                            learn_method=learn_method,
                            level=level
                        )
                        try:
                            db.session.add(obj)
                            db.session.flush()
                        except IntegrityError:
                            db.session.rollback()
                            continue
            db.session.commit()
        print(f"[LearnsetPatch] species_id={species_id} 补全完成")

    @staticmethod
    def get_generations_with_version_groups():
        """
        获取所有世代及其关联的版本组信息。
        """
        cache_key = "generations_with_version_groups"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            return json.loads(cached_data.decode('utf-8'))

        generations = Generation.query.order_by(Generation.id).all()
        results = []
        for gen in generations:
            vgs = VersionGroup.query.filter_by(generation_id=gen.id).order_by(VersionGroup.id).all()
            results.append({
                'id': gen.id,
                'name': gen.name, # e.g., generation-ix
                'version_groups': [{
                    'id': vg.id, 
                    'name': vg.name # e.g., scarlet-violet
                } for vg in vgs]
            })
        
        redis_service.set(cache_key, json.dumps(results), expire=3600 * 24) # Cache for a day
        return results

    @staticmethod
    def _acquire_lock(lock_key: str, lock_value: str, expire_seconds: int) -> bool:
        """尝试获取 Redis 锁。"""
        return redis_service.redis_client.set(lock_key, lock_value, nx=True, ex=expire_seconds)

    @staticmethod
    def _release_lock(lock_key: str, lock_value: str):
        """释放 Redis 锁，仅当值匹配时才释放（防止误删）。"""
        if redis_service.redis_client.get(lock_key) == lock_value.encode(): # Redis stores bytes
            redis_service.redis_client.delete(lock_key)

    @staticmethod
    def fetch_and_sync_pokemon_form_abilities():
        """
        Fetches ability information for each Pokemon form from PokeAPI 
        and syncs it to the PokemonFormAbilityMap table.
        Uses Redis lock per pokemon_form_id to prevent concurrent processing.
        """
        current_app.logger.info("[FormAbilitySync] Starting sync for Pokemon form abilities...")
        
        all_pokemon_forms = Pokemon.query.all()
        ability_cache = {ab.name: ab.id for ab in Ability.query.all()}
        lock_value_prefix = f"form_ability_sync_lock_val_{os.getpid()}_{time.time()}-"
        default_lock_expiry = 1800  # 30 分钟，应足够处理一个 form

        for i, poke_form in enumerate(all_pokemon_forms):
            if (i + 1) % 20 == 0: # 减少日志频率
                current_app.logger.info(f"[FormAbilitySync] Progress: {i+1}/{len(all_pokemon_forms)}. Current: {poke_form.name} (ID: {poke_form.id})")

            form_lock_key = f"lock:sync_form_abilities:{poke_form.id}"
            # 使用唯一的 lock_value，以便安全地释放锁
            current_lock_value = f"{lock_value_prefix}{poke_form.id}"

            # 检查是否已完成（幂等性标记）
            # 你可以考虑使用一个更持久的标记，例如在成功处理后写入数据库或一个专门的 Redis set
            # 这里的 existing_map_count 只是一个简单的本地检查，不是一个完整的"已完成"标记
            # 我们可以在成功获取锁之后，再检查一个更可靠的"已完成"标记 (例如 Redis set)
            # done_marker_key = f"done:sync_form_abilities:{poke_form.id}"
            # if redis_service.redis_client.exists(done_marker_key):
            #    current_app.logger.debug(f"[FormAbilitySync] Skipping {poke_form.name} (ID: {poke_form.id}), marked as done.")
            #    continue

            if not PokemonDataService._acquire_lock(form_lock_key, current_lock_value, default_lock_expiry):
                current_app.logger.info(f"[FormAbilitySync] Skipping {poke_form.name} (ID: {poke_form.id}), another process may be handling it or lock timed out.")
                continue
            
            try:
                # 在获得锁之后，再次检查是否真的需要处理（例如，如果之前的进程在释放锁前已完成）
                # 这是一个更强的幂等性检查，可以防止不必要的 API 请求
                # 此处我们仍然使用 existing_map_count 作为示例，但理想情况下应结合更持久的完成标记
                existing_map_count = PokemonFormAbilityMap.query.filter_by(pokemon_form_id=poke_form.id).count()
                if existing_map_count > 0 and not current_app.config.get('FORCE_REFRESH_FORM_ABILITIES_EVEN_IF_EXISTS', False):
                    current_app.logger.debug(f"[FormAbilitySync] Skipping {poke_form.name} (ID: {poke_form.id}) after acquiring lock, found {existing_map_count} existing entries.")
                    # redis_service.redis_client.set(done_marker_key, "1", ex=3600*24*7) # Mark as done for 7 days
                    continue # 跳过，但确保释放锁
                
                # 实际处理逻辑
                pokemon_api_details = PokemonDataService.get_pokemon_details(poke_form.id) 
                raw_abilities_from_api = pokemon_api_details.get('abilities', [])

                if not raw_abilities_from_api:
                    current_app.logger.debug(f"[FormAbilitySync] No abilities found in API for {poke_form.name} (ID: {poke_form.id})")
                    # 即使没有特性，也应该标记为"已处理"以避免重复检查
                    # redis_service.redis_client.set(done_marker_key, "1", ex=3600*24*7)
                    continue # 跳过，但确保释放锁

                new_mappings = []
                # 如果需要，在写入前清除旧的 mappings for this poke_form.id
                # if current_app.config.get('FORCE_REFRESH_FORM_ABILITIES_EVEN_IF_EXISTS', False):
                #     PokemonFormAbilityMap.query.filter_by(pokemon_form_id=poke_form.id).delete()
                #     db.session.commit() # 提交删除操作
                    
                for api_ab_info in raw_abilities_from_api:
                    ability_name_en = api_ab_info.get('ability', {}).get('name')
                    is_hidden = api_ab_info.get('is_hidden', False)

                    if not ability_name_en:
                        current_app.logger.warn(f"[FormAbilitySync] Missing ability name in API data for {poke_form.name}, data: {api_ab_info}")
                        continue

                    ability_id = ability_cache.get(ability_name_en)
                    if not ability_id:
                        current_app.logger.error(f"[FormAbilitySync] Ability '{ability_name_en}' not found in local DB cache for Pokemon {poke_form.name}. Ensure abilities table is fully synced.")
                        continue
                    
                    # 避免重复添加（如果上面没有清除旧条目）
                    # 在事务中，可以不预先检查，依靠数据库的唯一约束，但捕获 IntegrityError
                    new_map_entry = PokemonFormAbilityMap(
                        pokemon_form_id=poke_form.id,
                        ability_id=ability_id,
                        is_hidden=is_hidden
                    )
                    new_mappings.append(new_map_entry)
                
                if new_mappings:
                    try:
                        db.session.bulk_save_objects(new_mappings) # 更高效的批量插入
                        db.session.commit()
                        current_app.logger.debug(f"[FormAbilitySync] Added/Updated {len(new_mappings)} ability mappings for {poke_form.name} (ID: {poke_form.id})")
                        # redis_service.redis_client.set(done_marker_key, "1", ex=3600*24*7) # 标记为完成
                    except IntegrityError as ie:
                        db.session.rollback()
                        current_app.logger.error(f"[FormAbilitySync] IntegrityError for {poke_form.name}: {ie}. Likely duplicate entry if not clearing old ones.")
                    except Exception as commit_e:
                        db.session.rollback()
                        current_app.logger.error(f"[FormAbilitySync] Error committing mappings for {poke_form.name}: {commit_e}")
                # else:
                    # redis_service.redis_client.set(done_marker_key, "1", ex=3600*24*7) # 如果没有新特性，也标记为完成

            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"[FormAbilitySync] Request failed for Pokemon ID {poke_form.id} ({poke_form.name}): {e}")
                db.session.rollback() 
                # 不释放锁，让它超时，以便下次重试时知道可能有问题
                continue # 继续下一个宝可梦，而不是终止整个同步
            except Exception as e:
                current_app.logger.error(f"[FormAbilitySync] General error processing Pokemon {poke_form.name} (ID: {poke_form.id}): {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                # 不释放锁，让它超时
                continue
            finally:
                # 确保锁被释放
                PokemonDataService._release_lock(form_lock_key, current_lock_value)
        
        current_app.logger.info("[FormAbilitySync] Finished sync for Pokemon form abilities.")

    @staticmethod
    def get_pokemon_learnable_moves(species_id: int, version_group_id: int):
        """
        根据宝可梦物种ID和版本组ID获取可学习的招式列表。
        """
        cache_key = f"learnable_moves:species:{species_id}:vg:{version_group_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            current_app.logger.debug(f"Cache hit for learnable moves: {cache_key}")
            return json.loads(cached_data.decode('utf-8'))
        current_app.logger.debug(f"Cache miss for learnable moves: {cache_key}, querying DB.")

        # 查询 PokemonMoveLearnset 表，并联接 Move 表
        learnset_entries = db.session.query(
            Move.id,
            Move.name,
            Move.name_zh_hans,
            Move.type,
            Move.category,
            Move.power,
            Move.accuracy,
            Move.pp,
            Move.description_zh_hans, # 使用中文描述
            PokemonMoveLearnset.learn_method,
            PokemonMoveLearnset.level
        ).join(Move, PokemonMoveLearnset.move_id == Move.id).filter(
            PokemonMoveLearnset.pokemon_species_id == species_id,
            PokemonMoveLearnset.version_group_id == version_group_id
        ).distinct(Move.id) # 避免同一个招式通过不同方式学习导致重复
        # 可以根据学习方式、等级等进一步排序，例如：
        # .order_by(PokemonMoveLearnset.learn_method, PokemonMoveLearnset.level, Move.name_zh_hans)

        results = []
        for entry in learnset_entries:
             # 清理描述字段的换行符，与前端处理一致
             desc = (entry.description_zh_hans or '').replace('\n', '')
             results.append({
                'id': entry.id,
                'name': entry.name, # 英文名，虽然前端不展示，但可能数据结构需要
                'name_zh': entry.name_zh_hans,
                'type': entry.type,
                'category': entry.category,
                'power': entry.power,
                'accuracy': entry.accuracy,
                'pp': entry.pp,
                'desc': desc,
                # 如果需要展示学习方式和等级，可以在这里添加
                # 'learn_method': entry.learn_method,
                # 'level': entry.level
             })

        # 缓存结果
        redis_service.set(cache_key, json.dumps(results), expire=3600) # 缓存1小时
        return results

    @staticmethod
    def get_pokemon_learnable_moves_by_generation(species_id: int, generation_id: int):
        """
        根据宝可梦物种ID和世代ID获取可学习的去重招式列表。
        聚合该世代下所有版本组的可学习技能，并去除重复。
        """
        cache_key = f"learnable_moves:species:{species_id}:gen:{generation_id}"
        cached_data = redis_service.get(cache_key)
        if cached_data:
            current_app.logger.debug(f"Cache hit for learnable moves by generation: {cache_key}")
            return json.loads(cached_data.decode('utf-8'))
        current_app.logger.debug(f"Cache miss for learnable moves by generation: {cache_key}, querying DB.")

        # 查询 PokemonMoveLearnset 表，联接 Move 表和 VersionGroup 表
        # 筛选 species_id 和 generation_id
        # 选择 DISTINCT Move 字段
        # 使用 db.session.query(Move) 并 distinct() 可以获取去重后的 Move 对象
        learnable_moves_query = db.session.query(Move).join(PokemonMoveLearnset).join(VersionGroup).filter(
            PokemonMoveLearnset.pokemon_species_id == species_id,
            VersionGroup.generation_id == generation_id
        ).distinct() # 使用 distinct() 来获取去重后的招式对象

        results = []
        for move_obj in learnable_moves_query.all():
             # 清理描述字段的换行符，与前端处理一致
             desc = (move_obj.description_zh_hans or '').replace('\n', '')
             results.append({
                'id': move_obj.id,
                'name': move_obj.name, # 英文名
                'name_zh': move_obj.name_zh_hans,
                'type': move_obj.type,
                'category': move_obj.category,
                'power': move_obj.power,
                'accuracy': move_obj.accuracy,
                'pp': move_obj.pp,
                'desc': desc,
                # 这里不包含 learn_method 和 level，因为我们取的是并集，不关心具体学习方式
             })

        # 缓存结果
        redis_service.set(cache_key, json.dumps(results), expire=3600) # 缓存1小时
        return results

    # --- 新增方法：根据 Species ID 获取特性列表 ---
    @staticmethod
    def get_abilities_for_species(species_id: int) -> list[dict]:
        """
        根据宝可梦 Species ID 从数据库获取所有特性（普通和隐藏），并返回前端所需格式。
        """
        current_app.logger.debug(f"Fetching abilities for species_id: {species_id}")
        # 查询与该 species_id 关联的所有 Pokemon 形态
        # 然后通过 PokemonFormAbilityMap 获取这些形态的所有特性
        # 由于特性是物种层面的，我们只需要找到该物种下的所有特性即可，不一定需要形态ID
        # 可以通过 Pokemon 表的 species_id 关联到 Ability 表
        # TODO: 需要确认数据库结构是否支持直接通过 species_id 关联 Abilities
        # 检查 models/pokemon.py 和 models/ability.py 以及可能的中间表

        # 根据 models/pokemon_form_ability_map.py 的结构，可以通过 PokemonFormAbilityMap 关联 Pokemon 和 Ability
        # PokemonFormAbilityMap 通过 pokemon_form_id 关联 Pokemon (形態)，通过 ability_id 关联 Ability
        # Pokemon 表通过 species_id 关联 PokemonSpecies
        # TeamPokemon 通过 species_id 关联 PokemonSpecies，以及通过 pokemon_details 关联 Pokemon (is_default=True)

        # 似乎最可靠的方式是通过 species_id 找到该物种的所有默认形态 (is_default=True)，
        # 然后通过这些默认形态关联的 PokemonFormAbilityMap 来获取特性。
        # 假设一个物种的默认形态包含了该物种的所有特性信息。
        try:
            # 获取该物种的所有默认形态
            default_forms = Pokemon.query.filter_by(species_id=species_id, is_default=True).all()

            if not default_forms:
                current_app.logger.warning(f"No default forms found for species_id: {species_id}")
                return []

            # 使用 set 存储已添加的特性ID，避免重复
            seen_ability_ids = set()
            abilities_list = []

            for form in default_forms:
                # 通过 PokemonFormAbilityMap 获取该形态关联的特性
                form_abilities_maps = PokemonFormAbilityMap.query.filter_by(pokemon_form_id=form.id).all()

                for ab_map in form_abilities_maps:
                    if ab_map.ability_id not in seen_ability_ids:
                        ability = Ability.query.get(ab_map.ability_id)
                        if ability:
                            abilities_list.append({
                                'id': ability.id,
                                'name_en': ability.name,
                                'name_zh': ability.name_zh_hans,
                                'description_en': ability.description_en,
                                'description_zh_hans': ability.description_zh_hans,
                                'is_hidden': ab_map.is_hidden,
                            })
                            seen_ability_ids.add(ab_map.ability_id)

            current_app.logger.debug(f"Found {len(abilities_list)} abilities for species_id: {species_id}")
            return abilities_list

        except Exception as e:
            current_app.logger.error(f"Error fetching abilities for species_id {species_id} from DB: {e}")
            return []

    # ========================\

pokemon_data_service = PokemonDataService()