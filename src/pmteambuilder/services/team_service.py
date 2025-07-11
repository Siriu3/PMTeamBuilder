"""
团队服务模块，提供团队相关功能
"""
from flask import current_app
from ..models import db, Team, TeamPokemon, PokemonMove, TeamCustomTag, Move, Pokemon, Item, PokemonFormAbilityMap, Ability, TeamLike, user_favorites # Import user_favorites table
from ..services.sensitive_word_service import sensitive_word_filter
from ..services.pokemon_service import pokemon_data_service  # 引入宝可梦数据服务
from ..models.user import User # Import User model
from sqlalchemy import or_
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from nanoid import generate # Import nanoid

class TeamService:
    """团队服务类"""
    
    def __init__(self):
        # Ensure any necessary initialization is here
        pass # Placeholder
    
    @staticmethod
    def create_team(user_id, name, generation, format, description=None, pokemons=None, custom_tags=None, is_public=True):
        """创建新团队"""
        # 检查团队名称是否包含敏感词
        contains_sensitive, word = sensitive_word_filter.contains_sensitive_word(name)
        review_status = 'pending' if contains_sensitive else 'approved'
        review_reason = f"团队名称包含敏感词: {word}" if contains_sensitive else None

        # 检查自定义词条是否包含敏感词
        if custom_tags:
            for tag in custom_tags:
                # Ensure tag is treated as a string for sensitive word check
                if isinstance(tag, str):
                    contains_sensitive_tag, tag_word = sensitive_word_filter.contains_sensitive_word(tag)
                    if contains_sensitive_tag:
                        review_status = 'pending'
                        review_reason = f"自定义标签包含敏感词: {tag_word}"
                        break
                else:
                     current_app.logger.warn(f"[Create Team] 接收到非字符串类型的自定义标签: {tag}")

        # Generate a unique token
        token = generate() # Default alphabet, 21 characters
        # Use a loop to ensure uniqueness, though nanoid collisions are highly unlikely with default settings
        while Team.query.filter_by(token=token).first():
            token = generate()

        # 创建团队
        team = Team(
            name=name,
            user_id=user_id,
            generation=generation,
            format=format,
            is_public=is_public,
            review_status=review_status,
            review_comment=review_reason,
            token=token, # Save the generated token
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(team)
        db.session.flush()  # 获取team.id

        # 添加宝可梦
        if pokemons:
            for poke in pokemons:
                # 确保必需字段存在
                if 'species_id' not in poke or poke['species_id'] is None:
                     current_app.logger.warning(f"[create_team] Skipping pokemon data due to missing species_id: {poke}")
                     continue # 跳过缺少 species_id 的宝可梦

                team_poke = TeamPokemon(
                    team_id=team.id,
                    species_id=poke.get('species_id'),
                    species_name=poke.get('species_name', ''),
                    species_name_zh=poke.get('species_name_zh', poke.get('species_name', '')), # Use zh or fallback to en
                    level=poke.get('level', 50),
                    ability=poke.get('ability', ''),
                    item=poke.get('item', ''),
                    nature=poke.get('nature', ''),
                    evs_hp=poke.get('evs', {}).get('hp', 0),
                    evs_atk=poke.get('evs', {}).get('atk', 0),
                    evs_def=poke.get('evs', {}).get('def', 0),
                    evs_spa=poke.get('evs', {}).get('spa', 0),
                    evs_spd=poke.get('evs', {}).get('spd', 0),
                    evs_spe=poke.get('evs', {}).get('spe', 0),
                    ivs_hp=poke.get('ivs', {}).get('hp', 31),
                    ivs_atk=poke.get('ivs', {}).get('atk', 31),
                    ivs_def=poke.get('ivs', {}).get('def', 31),
                    ivs_spa=poke.get('ivs', {}).get('spa', 31),
                    ivs_spd=poke.get('ivs', {}).get('spd', 31),
                    ivs_spe=poke.get('ivs', {}).get('spe', 31),
                    tera_type=poke.get('tera_type'),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.session.add(team_poke)
                db.session.flush() # 刷新会话以获取 team_poke.id，用于关联招式

                # === 将招式处理逻辑直接整合到此处 ===
                # 使用集合来确保招式名称的唯一性，并标准化招式名称（去除所有空白）
                unique_processed_move_names: set[str] = set() # 用于存储唯一的、标准化后的招式名称

                if 'moves' in poke and poke['moves']:
                    # 从传入列表中提取招式名称，进行标准化并添加到 unique_processed_move_names 集合中
                    for move_item in poke['moves']:
                        raw_move_name = '';
                        if isinstance(move_item, str) and move_item:
                            raw_move_name = move_item
                        elif isinstance(move_item, dict) and move_item.get('move_name_zh'):
                            raw_move_name = move_item.get('move_name_zh')

                        if raw_move_name:
                            # 标准化招式名称：去除所有空白字符，用于唯一性判断
                            standardized_move_name = raw_move_name.replace(' ', '').replace('\u3000', '').strip() # 处理全角和半角空格等

                            if standardized_move_name and len(unique_processed_move_names) < 4: # 确保只添加最多 4 个唯一的标准化招式
                                unique_processed_move_names.add(standardized_move_name)

                # 根据唯一的标准化招式名称集合创建新的 PokemonMove 记录
                for standardized_move_name in unique_processed_move_names: # 遍历已去重、最多4个的招式名称
                     # 使用标准化名称查找 Move 对象
                     move_obj = Move.query.filter(
                          db.func.replace(db.func.replace(Move.name_zh_hans, ' ', ''), '\u3000', '') == standardized_move_name
                     ).first()

                     if move_obj:
                         # 直接添加新的 PokemonMove 记录，不需检查数据库是否存在，因为 delete-orphan 会处理旧记录
                         # 并且我们确保了要添加的列表本身是唯一的
                         db.session.add(PokemonMove(
                             pokemon_id=team_poke.id, # 使用刚刚创建的 team_poke 的 ID
                             move_id=move_obj.id, # 使用 move_obj.id
                             move_name=move_obj.name, # 使用英文名
                             move_name_zh=move_obj.name_zh_hans, # 从 Move 对象获取标准中文名
                             created_at=datetime.now(timezone.utc)
                         ))
                     else:
                         current_app.logger.warn(f"[create_team] 未能找到标准化中文招式 '{standardized_move_name}' 的数据库记录，将跳过保存。")
                # === 招式处理逻辑结束 ===

        # 添加自定义词条
        if custom_tags:
            for tag in custom_tags:
                db.session.add(TeamCustomTag(team_id=team.id, content=tag, created_at=datetime.now(timezone.utc)))
        try:
            db.session.commit()
            return team
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to create team due to data issue.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing create for team: {e}")
            raise

    @staticmethod
    def update_team(team_id, user_id, name=None, description=None, pokemons=None, custom_tags=None, generation=None, format=None, is_public=None):
        """更新团队信息"""
        team = Team.query.filter_by(id=team_id, user_id=user_id).first()
        if not team:
            # Also check if team is public and allow update if user is admin
            if not (current_app.config.get('IS_ADMIN', False) and Team.query.filter_by(id=team_id).first()): # Simplified check for admin bypass if needed
                 raise ValueError("队伍未创建或未授权")
            team = Team.query.get(team_id) # Get team for admin update

        if name is not None:
            team.name = sensitive_word_filter.filter_text(name) # Apply sensitive word filter

        if description is not None: # Handle description update
            team.description = description # Assuming description field exists in model

        if generation is not None: # Allow updating generation
            team.generation = generation

        if format is not None: # Allow updating format
            team.format = format

        if is_public is not None: # Allow updating is_public
            team.is_public = is_public

        team.updated_at = datetime.now(timezone.utc)

        if pokemons is not None:
             # Delete existing pokemons
            team.pokemons = [] # 修改为赋值空列表
             # Add new pokemons
            TeamService._add_pokemons_to_team(team, pokemons, commit_changes=False) # Add without committing yet

        if custom_tags is not None:
             # Check for sensitive words in new custom tags before deleting/adding
            contains_sensitive_tag = False
            sensitive_tag_word = None
            for tag in custom_tags:
                if isinstance(tag, str):
                    found, word = sensitive_word_filter.contains_sensitive_word(tag)
                    if found:
                        contains_sensitive_tag = True
                        sensitive_tag_word = word
                        break # Found sensitive word, no need to check further
                else:
                    current_app.logger.warn(f"[update_team] Received non-string custom tag: {tag}")

            # Delete existing tags
            team.custom_tags = [] # 修改为赋值空列表
             # Add new tags
            TeamService._add_tags_to_team(team, custom_tags, commit_changes=False) # Add without committing yet

            # If sensitive words found in new tags, update review status
            if contains_sensitive_tag:
                team.review_status = 'pending'
                team.review_comment = f"自定义标签包含敏感词: {sensitive_tag_word}"
                current_app.logger.info(f"Team {team.id} review status set to pending due to sensitive tag: {sensitive_tag_word}")


        try:
            db.session.commit() # Commit all changes together
        except IntegrityError:
             db.session.rollback()
             raise ValueError("Invalid data provided for update.")
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Error committing update for team {team_id}: {e}")
             raise # Re-raise the exception

        return team

    @staticmethod
    def get_team(team_id, include_pokemons=True, include_tags=True, current_user_id=None):
        """获取团队详情，根据用户ID决定是否包含Token，并判断点赞/收藏状态"""
        # current_user_id 是从 API 层传递进来的 get_jwt_identity() 结果
        current_app.logger.info(f"Attempting to get team {team_id} for user {current_user_id}")
        team = Team.query.get(team_id)
        if not team:
            current_app.logger.warning(f"Team {team_id} not found in DB.") # 更明确的日志
            raise ValueError("Team not found")

        # 打印类型以诊断问题
        current_app.logger.info(f"Type of current_user_id: {type(current_user_id)}, Type of team.user_id: {type(team.user_id)}")

        # Check if the team is public OR if the current user is the owner
        # 强制转换为整数进行比较，排除类型问题
        is_owner = (current_user_id is not None and team.user_id == int(current_user_id))
        # 添加 team_user_id 到日志
        current_app.logger.info(f"Team {team_id} found. is_public={team.is_public}, is_owner={is_owner}, team_user_id={team.user_id}")
        if not team.is_public and not is_owner:
            current_app.logger.warning(f"Team {team_id}: Unauthorized access attempt. is_public={team.is_public}, is_owner={is_owner}") # 更明确的日志
            raise ValueError("Team not found or unauthorized") # Return same error as not found for security

        # Only include token if current_user is the owner
        include_token = is_owner

        # Fetch related data eagerly for better performance in to_dict if needed
        # For now, rely on default lazy loading or relationship configurations
        # team = db.session.query(Team).options(
        #    db.joinedload(Team.pokemons).joinedload(TeamPokemon.moves)
        # ).filter(Team.id == team_id).first()

        # 获取团队数据的基本字典表示
        team_data = team.to_dict(include_pokemons=include_pokemons, include_tags=include_tags, include_token=include_token)

        # 如果包含宝可梦数据，则为每个宝可梦添加特性列表
        if include_pokemons and 'pokemons' in team_data and team_data['pokemons']:
            # 获取与 team.generation 对应的 version_group_id
            # 这可能需要查询世代数据或在 pokemon_data_service 中添加方法
            # 暂时用一个占位符 version_group_id，您需要根据实际情况实现获取逻辑
            # version_group_id = pokemon_data_service.get_version_group_id_by_generation(team.generation) # 假设有这个方法
            # 或者直接查询数据库表来获取
            # version_group_id = None # 请替换为实际获取 version_group_id 的逻辑

            # if version_group_id is not None:
            for poke_data in team_data['pokemons']:
                species_id = poke_data.get('species_id')
                if species_id:
                    try:
                        # 获取宝可梦在该版本组的可学习特性列表
                        # abilities = pokemon_data_service.get_pokemon_abilities(species_id, version_group_id) # 替换为新的方法调用
                        abilities = pokemon_data_service.get_abilities_for_species(species_id)
                        poke_data['abilities'] = abilities # 将特性列表添加到宝可梦字典中
                    except Exception as e:
                        current_app.logger.error(f"Error getting abilities for species {species_id}: {e}")
                        poke_data['abilities'] = [] # 出现错误时给一个空列表
                else:
                     poke_data['abilities'] = [] # 如果没有 species_id，也给一个空列表

        # --- Start: Debug Print ---
        if include_pokemons and 'pokemons' in team_data and team_data['pokemons']:
            current_app.logger.info(f"Returning team {team_id} data. Checking pokemon moves:")
            for i, poke_data in enumerate(team_data['pokemons']):
                 current_app.logger.info(f"  Pokemon {i+1} (ID: {poke_data.get('id')}, Species ID: {poke_data.get('species_id')}):")
                 current_app.logger.info(f"    Moves: {[m.get('move_name_zh') or m.get('move_name') for m in poke_data.get('moves', [])]}")
        # --- End: Debug Print ---

        # --- Start: Pad Moves to 4 Slots ---
        if include_pokemons and 'pokemons' in team_data and team_data['pokemons']:
            for poke_data in team_data['pokemons']:
                current_moves = poke_data.get('moves', [])
                processed_moves = []
                for m in current_moves:
                    move_name = m.get('move_name_zh') or m.get('move_name')
                    if move_name:
                        processed_moves.append(move_name)
                while len(processed_moves) < 4:
                    processed_moves.append('')
                poke_data['moves'] = processed_moves[:4]
        # --- End: Pad Moves to 4 Slots ---

        # --- Start: Add is_liked and is_favorited flags --- # 新增注释行
        is_liked = False
        is_favorited = False # Placeholder for now
        if current_user_id is not None:
             try:
                 user_id_int = int(current_user_id) # Ensure user_id is int
                 is_liked = TeamLike.query.filter_by(user_id=user_id_int, team_id=team.id).first() is not None
                 # 判断是否已收藏，查询 user_favorites 关联表
                 is_favorited = db.session.query(user_favorites).filter(
                     user_favorites.c.user_id == user_id_int,
                     user_favorites.c.team_id == team.id
                 ).first() is not None
             except ValueError:
                 # current_user_id 不是有效的整数，忽略判断
                 pass

        team_data['is_liked'] = is_liked
        team_data['is_favorited'] = is_favorited # Updated: use actual favorited status
        # --- End: Add is_liked and is_favorited flags --- # 新增注释行

        return team_data # 返回修改后的团队数据字典

    @staticmethod
    def get_user_teams(user_id, page=1, per_page=10, generation=None, status=None, format=None, is_public=None):
        """获取当前用户的团队列表，支持筛选"""
        query = Team.query.filter_by(user_id=user_id).order_by(Team.updated_at.desc())
        
        if generation:
            query = query.filter(Team.generation == generation)
        if status:
            query = query.filter(Team.review_status == status)
        if format:
            query = query.filter(Team.format == format)
        if is_public is not None:
             query = query.filter(Team.is_public == is_public)


        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': [item.to_dict(include_pokemons=True, include_token=True) for item in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'has_next': pagination.has_next
        }

    @staticmethod
    def get_favorite_teams(user_id, page=1, per_page=10):
        """获取当前用户收藏的团队列表"""
        # This assumes a 'favorites' relationship or a separate Favorite model exists
        # For now, returning a placeholder or implementing based on assumed structure
        # Assuming a many-to-many relationship or similar where we can query teams favorited by user_id
        # Placeholder implementation - replace with actual logic when favorite model/relationship is clear
        # Example if there's a UserFavoriteTeam model:
        # from ..models import UserFavoriteTeam
        # favorited_teams_ids = [fav.team_id for fav in UserFavoriteTeam.query.filter_by(user_id=user_id).all()]
        # query = Team.query.filter(Team.id.in_(favorited_teams_ids)).order_by(Team.updated_at.desc())

        # Since there's no explicit Favorite model in provided models, # Keeping this comment as a note
        # this function might need clarification or is a placeholder in original code.
        # Returning empty list for now, assuming favorite logic is elsewhere. # Keeping this comment as a note
        current_app.logger.warning("get_favorite_teams service method is a placeholder or depends on unprovided models.") # Keeping this warning

        # --- Start: Implement fetching user's favorite teams --- # 新增注释行
        try:
            user_id_int = int(user_id) # Ensure user_id is int
            # Join Team with user_favorites table to find teams favorited by the user
            query = Team.query.join(user_favorites, Team.id == user_favorites.c.team_id)
            query = query.filter(user_favorites.c.user_id == user_id_int)
            query = query.order_by(user_favorites.c.created_at.desc()) # Order by favorite creation time

            # Filter for public and approved teams (optional, depends if favorites list should only show public/approved)
            # Assuming favorites list can include private teams if the user favorited them while they were public
            # query = query.filter(Team.is_public == True, Team.review_status == 'approved')

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            # For the favorites list, we might want more detail than the public list, maybe include pokemons=True
            # But for consistency with user's own teams list, let's use include_pokemons=True here too
            items_data = []
            for team in pagination.items:
                 # Check if the user is the owner for include_token=True
                 include_token = (team.user_id == user_id_int)
                 item_data = team.to_dict(include_pokemons=True, include_token=include_token) # Include pokemon details for favorites list
                 # Also add is_favorited flag (always true for this list) and is_liked
                 item_data['is_favorited'] = True
                 is_liked = TeamLike.query.filter_by(user_id=user_id_int, team_id=team.id).first() is not None
                 item_data['is_liked'] = is_liked
                 items_data.append(item_data)


            return {
                'items': items_data,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages, # 添加总页数
                'has_next': pagination.has_next
            }
        except ValueError:
             # user_id 不是有效的整数
             current_app.logger.error(f"Invalid user_id for get_favorite_teams: {user_id}")
             return {'items': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0, 'has_next': False}
        except Exception as e:
            current_app.logger.error(f"Error fetching favorite teams for user {user_id}: {e}")
            raise # Re-raise the exception
        # --- End: Implement fetching user's favorite teams --- # 新增注释行

    @staticmethod
    def delete_team(team_id, user_id):
        """删除团队"""
        team = Team.query.filter_by(id=team_id, user_id=user_id).first()
        if not team:
            raise ValueError("Team not found or unauthorized")

        db.session.delete(team)
        db.session.commit()

    @staticmethod
    def review_team(team_id, admin_id, approved, reason=None):
        """审核团队 (仅管理员)"""
        # Assumes admin check is done at API level or via admin_id check
        team = Team.query.get(team_id)
        if not team:
            raise ValueError("Team not found")

        team.review_status = 'approved' if approved else 'rejected'
        team.review_comment = reason
        team.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return team

    @staticmethod
    def get_pending_teams(page=1, per_page=10):
        """获取待审核团队列表 (仅管理员)"""
        query = Team.query.filter_by(review_status='pending').order_by(Team.created_at.asc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [item.to_dict(include_pokemons=False) for item in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'has_next': pagination.has_next
        }

    @staticmethod
    def copy_team(team_id, user_id):
        """复制团队"""
        original_team = Team.query.get(team_id)
        if not original_team:
            raise ValueError("Original team not found")

        # Create a new team based on the original
        new_team = Team(
            user_id=user_id,
            name=f"{original_team.name}(副本)", # Default copied name
            generation=original_team.generation,
            format=original_team.format,
            is_public=False, # Copied teams are private by default
            review_status='approved', # Setting copied teams to pending review
            token=generate(), # Generate a new token for the copied team
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_team)
        db.session.flush() # Get the new team ID

        # Copy pokemons and moves using helper
        if original_team.pokemons:
            TeamService._add_pokemons_to_team(new_team, [p.to_dict() for p in original_team.pokemons], commit_changes=False)

        # Copy custom tags using helper
        if original_team.custom_tags:
            TeamService._add_tags_to_team(new_team, [t.content for t in original_team.custom_tags], commit_changes=False)

        try:
            db.session.commit()
            current_app.logger.info(f"Team {team_id} copied successfully. New team ID: {new_team.id}")
            # --- Start: Debug Print ---
            copied_team_check = Team.query.get(new_team.id)
            if copied_team_check:
                current_app.logger.info(f"Checking copied team {copied_team_check.id} data:")
                for i, poke in enumerate(copied_team_check.pokemons):
                    current_app.logger.info(f"  Pokemon {i+1} (ID: {poke.id}, Species ID: {poke.species_id}):")
                    current_app.logger.info(f"    Moves: {[m.move_name_zh for m in poke.moves]}")
            else:
                current_app.logger.warning(f"Could not find copied team {new_team.id} for checking.")
            # --- End: Debug Print ---
            return new_team
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to copy team due to data issue.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing copy for team {team_id}: {e}")
            raise

    @staticmethod
    def get_team_by_token(token):
        """根据Token获取团队详情，用于导入"""
        team = Team.query.filter_by(token=token).first()
        if not team:
            raise ValueError("Invalid or expired token")

        # === 新增权限检查：仅允许访问公开且审核通过的团队 ===
        if not team.is_public or team.review_status != 'approved':
            current_app.logger.warning(f"Attempted access to non-public or non-approved team {team.id} via token.")
            # 出于安全考虑，对未通过验证的 token 访问也返回 "not found"
            raise ValueError("Team not found or unauthorized")
        # === 权限检查结束 ===

        # Return data suitable for import - exclude user_id, name, id, token, timestamps, review status
        # And ensure pokemons have local keys and correct move format for frontend
        imported_data = team.to_dict(include_pokemons=True, include_tags=True, include_token=False)

        # Remove fields that should not be imported/copied into a *new* team
        imported_data.pop('id', None)
        imported_data.pop('user_id', None)
        imported_data.pop('token', None)
        imported_data.pop('updated_at', None)
        imported_data.pop('review_status', None)
        imported_data.pop('review_comment', None)
        imported_data.pop('pokemon_count', None) # Remove computed property


        # Process pokemons: remove DB IDs, add local keys, format moves, REMOVE abilities list
        if 'pokemons' in imported_data:
             processed_pokemons = []
             for p in imported_data['pokemons']:
                 # Remove DB IDs and timestamps from the imported pokemon data
                 p.pop('id', None)
                 p.pop('team_id', None)
                 p.pop('created_at', None)
                 p.pop('updated_at', None)

                 # Process moves: remove DB IDs and format as string names for frontend
                 if 'moves' in p:
                      processed_moves = []
                      for m in p['moves']:
                           # Assuming move data from to_dict has 'move_name_zh' or 'move_name'
                           move_name = m.get('move_name_zh') or m.get('move_name')
                           if move_name:
                                processed_moves.append(move_name)

                      # Pad moves array to 4 elements if necessary with empty strings
                      while len(processed_moves) < 4:
                           processed_moves.append(''); # Use empty string for empty slots

                      p['moves'] = processed_moves

                 # Add a localKey for frontend tracking - required for reactive updates and identifying unsaved pokemons
                 # Use a unique prefix like 'import-'
                 p['localKey'] = f"import-{datetime.now().timestamp()}-{generate(size=6)}" # Generate a short random suffix for local uniqueness

                 # === Add Abilities List for Imported Pokemon === # Simplified logic, no longer depends on version_group_id
                 if p.get('species_id') is not None:
                      try:
                          from ..services.pokemon_service import pokemon_data_service
                          # Get abilities for the species using the dedicated service method
                          # get_abilities_for_species only requires species_id
                          abilities = pokemon_data_service.get_abilities_for_species(p['species_id'])
                          p['abilities'] = abilities # Add abilities list to the dictionary
                      except Exception as e:
                          current_app.logger.error(f"[getTeamByToken] Error getting abilities for species {p['species_id']} from DB: {e}")
                          p['abilities'] = [] # Provide empty list on error
                 else:
                     p['abilities'] = [] # Provide empty list if species_id is missing
                 # ================================================

                 processed_pokemons.append(p)
             imported_data['pokemons'] = processed_pokemons

        # The imported team is *intended* to be created as a new private team in the user's account.
        # The 'is_public' status is not part of the imported data structure itself,
        # the frontend will handle setting the new team's is_public to False.

        # === 移除所有可能的特性列表，只保留选中的特性名称 ===
        # Note: This step was moved here to apply after processing pokemons
        if 'pokemons' in imported_data:
            for p_data in imported_data['pokemons']:
                p_data.pop('abilities', None)
        # ================================================

        return imported_data # 返回修改后的数据结构

    @staticmethod
    def _add_pokemons_to_team(team, pokemons_data, commit_changes=True):
        """Helper to add pokemon data to a team object."""
        if not pokemons_data:
            if commit_changes:
                db.session.commit()
            return

        for p_data in pokemons_data:
            # Ensure required fields are present in pokemon data
            if 'species_id' not in p_data or p_data['species_id'] is None:
                 current_app.logger.warning(f"Skipping pokemon data due to missing species_id: {p_data}")
                 continue # Skip if species_id is missing

            new_pokemon = TeamPokemon(
                team_id=team.id,
                species_id=p_data.get('species_id'),
                species_name=p_data.get('species_name', ''),
                species_name_zh=p_data.get('species_name_zh', p_data.get('species_name', '')), # Use zh or fallback to en
                level=p_data.get('level', 50),
                ability=p_data.get('ability', ''),
                item=p_data.get('item', ''),
                nature=p_data.get('nature', ''),
                evs_hp=p_data.get('evs', {}).get('hp', 0),
                evs_atk=p_data.get('evs', {}).get('atk', 0),
                evs_def=p_data.get('evs', {}).get('def', 0),
                evs_spa=p_data.get('evs', {}).get('spa', 0),
                evs_spd=p_data.get('evs', {}).get('spd', 0),
                evs_spe=p_data.get('evs', {}).get('spe', 0),
                ivs_hp=p_data.get('ivs', {}).get('hp', 31),
                ivs_atk=p_data.get('ivs', {}).get('atk', 31),
                ivs_def=p_data.get('ivs', {}).get('def', 31),
                ivs_spa=p_data.get('ivs', {}).get('spa', 31),
                ivs_spd=p_data.get('ivs', {}).get('spd', 31),
                ivs_spe=p_data.get('ivs', {}).get('spe', 31),
                tera_type=p_data.get('tera_type'),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(new_pokemon)
            db.session.flush() # Flush to get the new_pokemon.id

            # Add moves
            # --- 添加招式去重逻辑 --- # 新增注释行以帮助定位
            unique_processed_move_names: set[str] = set() # 用于存储唯一的、标准化后的招式名称 # 新增注释

            if 'moves' in p_data and p_data['moves']:
                # 从传入列表中提取招式名称，进行标准化并添加到 unique_processed_move_names 集合中 # 新增注释
                for move_item in p_data['moves']:
                    raw_move_name = '';
                    if isinstance(move_item, str) and move_item:
                        raw_move_name = move_item
                    elif isinstance(move_item, dict) and (move_item.get('move_name_zh') or move_item.get('move_name')):
                         raw_move_name = move_item.get('move_name_zh') or move_item.get('move_name')

                    if raw_move_name:
                        # 标准化招式名称：去除所有空白字符，用于唯一性判断 # 新增注释
                        standardized_move_name = raw_move_name.replace(' ', '').replace('\u3000', '').strip() # 处理全角和半角空格等 # 新增注释

                        if standardized_move_name and len(unique_processed_move_names) < 4: # 确保只添加最多 4 个唯一的标准化招式 # 新增注释
                            unique_processed_move_names.add(standardized_move_name)

            # 根据唯一的标准化招式名称集合创建新的 PokemonMove 记录 # 新增注释
            for standardized_move_name in unique_processed_move_names: # 遍历已去重、最多4个的招式名称 # 新增注释
                 # 使用标准化名称查找 Move 对象 # 新增注释
                 move_obj = Move.query.filter(
                      db.func.replace(db.func.replace(Move.name_zh_hans, ' ', ''), '\u3000', '') == standardized_move_name
                 ).first()

                 if move_obj:
                     # 添加新的 PokemonMove 记录，不需检查数据库是否存在，因为我们处理了重复的输入列表 # 新增注释
                     db.session.add(PokemonMove(
                         pokemon_id=new_pokemon.id,
                         move_id=move_obj.id, # 使用 move_obj.id # 新增注释
                         move_name=move_obj.name, # 使用英文名 # 新增注释
                         move_name_zh=move_obj.name_zh_hans, # 从 Move 对象获取标准中文名 # 新增注释
                         created_at=datetime.now(timezone.utc)
                     ))
                 else:
                     current_app.logger.warn(f"[_add_pokemons_to_team] 未能找到标准化中文招式 '{standardized_move_name}' 的数据库记录，将跳过保存。") # 新增日志级别和信息
            # === 招式处理逻辑结束 === # 新增注释

        if commit_changes:
            db.session.commit()

    @staticmethod
    def _add_tags_to_team(team, custom_tags_data, commit_changes=True):
         """Helper to add custom tags to a team object."""
         if not custom_tags_data:
             if commit_changes:
                 db.session.commit()
             return

         for tag_content in custom_tags_data:
             if isinstance(tag_content, str) and tag_content.strip():
                new_tag = TeamCustomTag(
                     team_id=team.id,
                     content=tag_content.strip(),
                     created_at=datetime.now(timezone.utc)
                )
                db.session.add(new_tag)

         if commit_changes:
            db.session.commit()

    # --- Start: New method to get public approved teams --- # 新增注释行
    @staticmethod
    def get_public_approved_teams(page=1, per_page=10, search_query=None, generation=None, format=None, current_user_id=None):
        """获取公开且审核通过的团队列表，支持搜索、筛选和分页"""
        query = Team.query.filter_by(is_public=True, review_status='approved').order_by(Team.updated_at.desc())

        # 搜索逻辑
        if search_query:
            # 搜索团队名称、创建者用户名、自定义标签
            search_term = f"%{search_query}%"
            # Use distinct(Team.id) to avoid duplicates when joining with custom_tags or pokemons
            query = query.join(Team.creator).outerjoin(Team.custom_tags).outerjoin(Team.pokemons).filter(
                or_(
                    Team.name.ilike(search_term),
                    User.username.ilike(search_term),
                    TeamCustomTag.content.ilike(search_term),
                    # Add search by Pokemon English and Chinese names
                    TeamPokemon.species_name.ilike(search_term),
                    TeamPokemon.species_name_zh.ilike(search_term)
                )
            ).distinct(Team.id) # Apply distinct on Team.id

        # 筛选逻辑
        if generation:
            query = query.filter(Team.generation == generation)
        if format:
            query = query.filter(Team.format == format)

        # 去重（如果进行了join操作导致重复）- 已经在搜索逻辑中处理了
        # if search_query:
        #      query = query.distinct()

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # 格式化返回数据，包含点赞/收藏状态
        items_data = []
        for team in pagination.items:
            # 在列表页通常只需要部分信息，不包含宝可梦详情
            # Add include_sprites_only=True to get basic pokemon sprites
            item_data = team.to_dict(include_pokemons=False, include_tags=True, include_sprite_urls_only=True, include_token=True) # Include token for public teams
            # 判断当前用户是否已点赞和收藏
            is_liked = False
            is_favorited = False
            if current_user_id is not None:
                 try:
                     user_id_int = int(current_user_id) # Ensure user_id is int
                     is_liked = TeamLike.query.filter_by(user_id=user_id_int, team_id=team.id).first() is not None
                     # 判断是否已收藏，查询 user_favorites 关联表
                     is_favorited = db.session.query(user_favorites).filter(
                         user_favorites.c.user_id == user_id_int,
                         user_favorites.c.team_id == team.id
                     ).first() is not None
                 except ValueError:
                     # current_user_id 不是有效的整数，忽略判断
                     pass

            item_data['is_liked'] = is_liked
            item_data['is_favorited'] = is_favorited
            items_data.append(item_data)


        return {
            'items': items_data,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages, # 添加总页数
            'has_next': pagination.has_next
        }
    # --- End: New method to get public approved teams --- # 新增注释行

    # --- Start: New methods for likes --- # 新增注释行
    @staticmethod
    def add_like(user_id, team_id):
        """用户点赞团队"""
        team = Team.query.get(team_id)
        if not team:
            raise ValueError("Team not found")

        # 检查是否已点赞
        existing_like = TeamLike.query.filter_by(user_id=user_id, team_id=team_id).first()
        if existing_like:
            # 已经点赞过，可以考虑返回成功或抛出特定错误
            # 这里我们选择返回成功并打印日志
            current_app.logger.info(f"User {user_id} already liked team {team_id}")
            return team.likes_count # 返回当前点赞数

        try:
            # 添加点赞记录
            new_like = TeamLike(user_id=user_id, team_id=team_id)
            db.session.add(new_like)

            # 更新团队点赞计数
            team.likes_count = (team.likes_count or 0) + 1
            db.session.commit()
            current_app.logger.info(f"User {user_id} liked team {team_id}. New like count: {team.likes_count}")
            return team.likes_count

        except IntegrityError:
            db.session.rollback()
            # 捕获唯一约束错误，说明并发操作导致重复点赞
            current_app.logger.warning(f"IntegrityError when user {user_id} liked team {team_id}")
            # 重新获取点赞数并返回
            updated_team = Team.query.get(team_id)
            return updated_team.likes_count if updated_team else (team.likes_count or 0)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding like for team {team_id} by user {user_id}: {e}")
            raise # Re-raise other exceptions


    @staticmethod
    def remove_like(user_id, team_id):
        """用户取消点赞团队"""
        team = Team.query.get(team_id)
        if not team:
            raise ValueError("Team not found")

        # 查找点赞记录
        existing_like = TeamLike.query.filter_by(user_id=user_id, team_id=team_id).first()
        if not existing_like:
            # 没有点赞记录，可以考虑返回成功或抛出错误
            # 这里我们选择返回当前点赞数并打印日志
            current_app.logger.info(f"User {user_id} did not like team {team_id}")
            return team.likes_count # 返回当前点赞数


        try:
            # 删除点赞记录
            db.session.delete(existing_like)

            # 更新团队点赞计数
            team.likes_count = max(0, (team.likes_count or 0) - 1) # Ensure count doesn't go below 0
            db.session.commit()
            current_app.logger.info(f"User {user_id} unliked team {team_id}. New like count: {team.likes_count}")
            return team.likes_count

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing like for team {team_id} by user {user_id}: {e}")
            raise # Re-raise other exceptions
    # --- End: New methods for likes --- # 新增注释行

    # --- Start: New methods for favorites --- # 新增注释行
    @staticmethod
    def add_favorite(user_id, team_id):
        """用户收藏团队"""
        team = Team.query.get(team_id)
        if not team:
            raise ValueError("Team not found")

        # 检查是否已收藏
        existing_favorite = db.session.query(user_favorites).filter(
            user_favorites.c.user_id == user_id,
            user_favorites.c.team_id == team_id
        ).first()

        if existing_favorite:
            # 已经收藏过，可以考虑返回成功或抛出特定错误
            current_app.logger.info(f"User {user_id} already favorited team {team_id}")
            return team.favorites_count # 返回当前收藏数

        try:
            # 添加收藏记录到关联表
            insert_stmt = user_favorites.insert().values(
                user_id=user_id,
                team_id=team_id,
                created_at=datetime.now(timezone.utc)
            )
            db.session.execute(insert_stmt)

            # 更新团队收藏计数
            team.favorites_count = (team.favorites_count or 0) + 1
            db.session.commit()
            current_app.logger.info(f"User {user_id} favorited team {team_id}. New favorite count: {team.favorites_count}")
            return team.favorites_count

        except IntegrityError:
             db.session.rollback()
             # 捕获唯一约束错误，说明并发操作导致重复收藏
             current_app.logger.warning(f"IntegrityError when user {user_id} favorited team {team_id}")
             # 重新获取收藏数并返回
             updated_team = Team.query.get(team_id)
             return updated_team.favorites_count if updated_team else (team.favorites_count or 0)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding favorite for team {team_id} by user {user_id}: {e}")
            raise # Re-raise other exceptions

    @staticmethod
    def remove_favorite(user_id, team_id):
        """用户取消收藏团队"""
        team = Team.query.get(team_id)
        if not team:
            raise ValueError("Team not found")

        # 查找收藏记录
        existing_favorite = db.session.query(user_favorites).filter(
            user_favorites.c.user_id == user_id,
            user_favorites.c.team_id == team_id
        ).first()

        if not existing_favorite:
            # 没有收藏记录，可以考虑返回成功或抛出错误
            current_app.logger.info(f"User {user_id} did not favorite team {team_id}")
            return team.favorites_count # 返回当前收藏数

        try:
            # 删除收藏记录
            delete_stmt = user_favorites.delete().where(
                user_favorites.c.user_id == user_id,
                user_favorites.c.team_id == team_id
            )
            db.session.execute(delete_stmt)

            # 更新团队收藏计数
            team.favorites_count = max(0, (team.favorites_count or 0) - 1)
            db.session.commit()
            current_app.logger.info(f"User {user_id} unfavorited team {team_id}. New favorite count: {team.favorites_count}")
            return team.favorites_count

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing favorite for team {team_id} by user {user_id}: {e}")
            raise # Re-raise other exceptions
    # --- End: New methods for favorites --- # 新增注释行

team_service = TeamService() # Instantiate the service

# Add helpers for deleting related objects if cascade is not fully configured
# Note: With cascade='all, delete-orphan' on relationships in Team model,
# deleting Team should delete related TeamPokemon and TeamCustomTag.
# Deleting TeamPokemon should delete related PokemonMove.
# Manual deletion helpers might be redundant if cascade is set up correctly.
# Keeping them commented out unless needed:
# @staticmethod
# def _delete_pokemons_for_team(team):
#     PokemonMove.query.filter(PokemonMove.pokemon_id.in_([p.id for p in team.pokemons])).delete(synchronize_session=False)
#     TeamPokemon.query.filter_by(team_id=team.id).delete(synchronize_session=False)

# @staticmethod
# def _delete_tags_for_team(team):
#     TeamCustomTag.query.filter_by(team_id=team.id).delete(synchronize_session=False)
