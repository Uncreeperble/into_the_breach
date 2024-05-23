# DO NOT modify or add any import statements
from a2_support import *
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Callable

# Name:
#   Benjamin Evans
# Student Number:
#   48828514

# <----| Game Constants as assumed from spec sheet |---->

WIN_TEXT = 'You Win!' # Win & Lose text will be followed by PLAY_AGAIN_TEXT
LOSE_TEXT = 'You Lost!'

ENTITY_DEFAULT_FREINDLINESS = False # Entities are not friendly by default
MECH_DEFAULT_FREIDNLINESS = True # Mech entities ARE friendly however
TILE_DEFAULT_BLOCKING = False # Tiles are NOT blocking by default
MECH_DEFAULT_ACTIVITY = True # Mechs are ALWAYS starting as active

UP, DOWN, LEFT, RIGHT = PLUS_OFFSETS[::-1] # 2D-Direction vectors


# <----| Custom Helper Functions (not in spec sheet) |---->

def add_positions(*positions: tuple[int, int]) -> tuple[int, int]:
    """Sums the given position vectors component wise.

    Parameters:
        *positions (tuple[int, int]): any number of same-dimension vectors.

    Return:
        tuple[int, int]: the resulting vector

    Preconditions:
        - The dimensions are at least 2 and all equal

    Example:
        >>> add_positions((0, 1), (2, 3), (4, 5))
        (6, 9)
    """
    return tuple(map(sum, zip(*positions))) # ( sum(x1,x2...), sum(y1, y2...) )

def scale_position(position: tuple[int, int], scalar: int):
    """ Applies vector scalar.

    Parameters:
        position (tuple[int, int]): Vector to be mulitplied.
        scalar (int): Integer to multiply each component by.

    Return:
        tuple[int, int]: the resulting vector

    Preconditions:
        - position has dimension of at least 2.

    Example:
        >>> scale_position((3, 4), 5)
        (15, 20)
    """
    return (position[0] * scalar, position[1] * scalar)


# <----| Class Defintions (as per spec sheet) |---->

# Will be split up into the following subsections:
#     Model: the internal game classes and model itself
#     View: the user interface that displays a given model instance
#     Controller: links both view and model

# --- MODEL ---
class BreachModel(object):
    """
    BreachModel controls gameplay including game turns and win checking.

    Attributes:
        _board (Board): the current game Board object.
        _entities (list[Entity]): the list of entities present in the game.
        _can_save (bool): stores if no move has been made since the last call to
                          end_turn.
    """

    def __init__(self, board: 'Board', entities: list['Entity']) -> None:
        """Instantiates a new model class with the given board and entities.

        Parameters:
            board (Board): the initial _board object.
            entities (list[Entity]): the initial entities present in the game.

        Preconditions:
            - entities is in descending priority order, with the highest
              priority entity being the first element of the list, and the 
              lowest priority entity being the last element of the list.
        """
        self._board = board
        self._entities = entities
        self._can_save = True

    def __str__(self) -> str:
        """Returns the string representation of the model.
        
        The string representation of a model is the string representation of 
        the game board followed by a blank line, followed by the string
        representation of all game entities in descending priority order,
        separated by newline characters.
        """
        return str(self._board) + '\n\n' + '\n'.join(map(str, self._entities))

    def _get_win_conditions(self) -> tuple[bool, bool, bool]:
        """Checks if there is a mech left, an enemy left, and a building left

        Return:
            tuple[bool, bool, bool]: the boolean value for each of the checks.
                1. is there an alive Mech left
                2. is there an alive enemy left
                3. is there a non-destroyed building left
        """
        # Get a list (mapping) of bools for eaech entity if its a mech-
        # this is quicker than filtering them out and allows any/all.
        entity_is_mech = map(lambda x : x.is_friendly(), self.get_entities())
        has_mech, has_enemy = any(entity_is_mech), not all(entity_is_mech)
        has_building = any(map(lambda x : not x.is_destroyed(),
                               self._board.get_buildings().values()))
        return (has_mech, has_enemy, has_building)

    def _get_enemies(self) -> list['Entity']:
        """Gets the model's alive enemies.
        
        Returns:
            list[Entity]: a list of enemies currently in the game, in
                descending order.
        """
        # get_entities already filters out dead entities, this filters mechs out
        return filter(lambda e: not e.is_friendly(), self.get_entities())

    def _closest_position(self, positions, goal, exclude_goal = False):
        closest_pos, least_dist = None, None
        for pos in positions:
            if pos == goal and exclude_goal:
                continue
            curr_dist = get_distance(self, goal, pos)
            if curr_dist == -1:
                # We don't consider this point if the end point is blocked
                continue
            if not closest_pos or curr_dist <= least_dist:
                # TODO
                # If we havn't found a valid point or we found a point closer
                # or same dist & higher priority- set this to the new closest
                closest_pos, least_dist = pos, curr_dist
        return closest_pos

    def get_board(self) -> 'Board':
        """Gets the model's current Board.
        
        Returns:
            Board: the board object the model is operating with."""
        return self._board  
    
    def ready_to_save(self) -> bool:
        """Gets the models _can_save state (bool)."""
        return self._can_save
        
    def get_entities(self) -> list['Entity']:
        """Gets the model's alive entities.
        
        These are the entities that can affect any part of the game - as
        entities that are not alived are not in gameplay. These entities remain
        stored however in the private _entities to allow for possible future
        development of revival etc.

        Returns:
            list[Entity]: a list of enemies currently in the game, in
                descending order.
        """
        # all it does is filter out ensuring every entitiy is_alive.
        return list(filter(lambda x : x.is_alive(), self._entities))
        
    def entity_positions(self) -> dict[tuple[int, int], 'Entity']:
        """Gets a dictionary of entities and their positions.

        Return:
            dict[tuple[int, int], Entity]: in the form (row, col) : Entity

        Example:
            >>> model.entity_positions()
            {(1, 2): TankMech((1, 2), 3, 3, 3)}
        """
        # constructs a dictionary for their position : entity 
        return {e.get_position() : e for e in self.get_entities()}

    def has_won(self) -> bool:
        """Checks if the model meets the win conditions.
        
        Win conditions are:
            - all enemies are destroyed,
            - and at least one mech is not destroyed
            - and at least one building on the board is not destroyed.

        Returns:
            bool: True iff the model has won.
        """
        has_mech, has_enemy, has_building = self._get_win_conditions()
        return not has_enemy and has_mech and has_building

    def has_lost(self) -> bool:
        """Checks if the model meets the lose conditions.
        
        Lose conditions are:
            - all buildings are destroyed,
            - or all mechs are destroyed
        
        Returns:
            bool: True iff the model has lost.
        """
        has_mech, _, has_building = self._get_win_conditions()
        return not has_building or not has_mech
    
    def get_valid_movement_positions(self,
                                     entity: 'Entity') -> list[tuple[int, int]]:
        """Returns the list of positions that the given entity could move to.

        A valid path within the board is a sequence of movements into vertically
        or horizontally adjacent non-blocking tiles which do not contain an 
        entity. The length of a valid path is the number of movements made
        within it.
         
        Note that each entity can only move through valid paths of
        length less than or equal to their maximum path length (speed).

        Paramaters:
            entity (Entity): the entitiy in question.

        Return:
            list[tuple[int, int]]: a list of all valid (row, col) positions that
                the entity is permitted to move to. 
            
            The list is ordered such that positions in higher rows appear
            before positions in lower rows and positions in columns further left
            appear before positions in columns further right. 

        Example:
            >>> model.get_valid_movement_positions(TankMech((1, 1), 5, 3, 3))
            [(2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (4, 1)]
        """
        speed, pos = entity.get_speed(), entity.get_position()
        rows, cols = self._board.get_dimensions()
        # Only return valid positions- distance within the speed and not -1
        return [(y, x) for y in range(rows) for x in range(cols) \
                if 0 < get_distance(self, pos, (y, x)) <= speed]

    def attempt_move(self, entity: 'Entity', position: tuple[int, int]) -> None:
        """Attempts to move the entity to the given position. 
        
        Moves the given entity to the specified position only if the entity 
        is friendly, active, and can move to that position according to the game
        rules present in specification section 3 (aka get_valid_movement_pos').
        
        Disables entity if a successful move is made, otherwise does nothing.

        Paramaters:
            entity (Entity): the entity to be moved.
            position (tuple[int, int]): the (row, col) destination position.
        """
        if (entity.is_friendly() and entity.is_active()
            and position in self.get_valid_movement_positions(entity)):
            # Conditions are met go ahead and set its position, and disable it
            entity.set_position(position)
            entity.disable()
            self._can_save = False # A move has made and end_turn hasn't ran
    
    def make_attack(self, entity: 'Entity') -> None:
        """Makes given entity perform an attack against every tile that is
        currently a target of the entity.

        The effect on each tile is described in the specification section 3, and
        in relevant Entity.attack and Tile.damage definitions.

        Paramaters:
            entity (Entity): the entity that is attacking.
        """
        rows, cols = self._board.get_dimensions()
        entities = self.entity_positions()
        target_coords = filter(lambda p: 0 <= p[0] < rows and 0 <= p[1] < cols,
                               entity.get_targets()) # filters only valid coords
        for coord in target_coords:
            # Either attack if its an entity or damage if its a building tile
            if coord in entities:
                entity.attack(entities[coord])
                continue
            # Damage tile if its a building 
            target = self._board.get_tile(coord)
            if target.get_tile_name() == BUILDING_NAME:
                target.damage(entity.get_strength())
            
    def assign_objectives(self) -> None:
        """Updates the objectives of all enemies based on the current state.
        
        This method works by running the`Enemy.update_objective method on each
        enemy with the current game buildings and entities.
        """
        buildings = self._board.get_buildings()
        entities, enemies = self.get_entities(), self._get_enemies()
        # Calls it on each enemy- uses list comprehension over mapping to ensure
        # the calls are ran when the method is.
        [enemy.update_objective(entities, buildings) for enemy in enemies]
                
    def move_enemies(self) -> None:
        """Moves each enemy closer to objective.
        
        Moves to the valid movement position that minimizes the
        distance of the shortest valid path between the position and the enemy's
        objective (Not None).
         
        If there is a tie for minimum shortest distance, the enemy moves to the
        position in the bottom-most row.
        If there is still a tie for minimum shortest distance, the enemy moves
        to the position in the rightmost column.
        If there is no valid path from an enemy to its objective, the enemy does
        not move.
        
        Enemies move in descending priority order starting with the highest
        priority enemy.
        """
        for enemy in self._get_enemies():
            objective = enemy.get_objective()

            # Since the objective is always going to be blocking in the current
            # game implmentation (either a building / entity) search for the 
            # closest adjacent tile to this original objective and make this it.
            objective = self._closest_position(
                map(lambda p : add_positions(objective, p),
                    [UP, LEFT, RIGHT, DOWN]), # list of adjacent positions
                enemy.get_position(), True) # We shouldn't consider enemy_pos
            if not objective:
                continue # This enemies objective was surrounded/unreachable

            # Gets the closest valid position to the objective (including curnt)
            closest_to_objective = self._closest_position(
                self.get_valid_movement_positions(enemy), objective)

            # move the enemy to the closest position to the objective
            enemy.set_position(closest_to_objective)
                               
    def end_turn(self) -> None:
        """Executes the attack and enemy movement phases.
        
        During the attacking phase, each mech and enemy perform an attack. If 
        a mech or enemy is destroyed before they attack during a given attack
        phase, they do not attack during that attack phase.
        
        During the enemy movement phase, each enemy chooses a tile as their 
        objective, and then moves to a new tile on the grid such that they are
        closer to their objective.
        """
        [self.make_attack(ent) for ent in self.get_entities() if ent.is_alive()]
        self.assign_objectives()
        self.move_enemies()
        [entity.enable() for entity in self._entities if entity.is_friendly()]
        self._can_save = True   
        
class Entity(object):
    """Entity is an abstract class from which all instantiated types of entity 
    inherit. This class provides default entity behavior, which can be inherited
    or overridden by specific types of entities. All entities exist at a given
    (row, column) position, and possess integer health, speed, and strength
    values.
    
    Note: it is not the role of an entity to determine if the position it
    occupies exists or is valid. Like buildings, entities can be destroyed. An 
    entity is destroyed when its health drops to zero. Entities can be friendly
    (that is, under player control), or not

    Attributes:
        _position (tuple[int, int]): the positioin (row, col) of the entity
            on the board.
        _health (int): the health of the entity- affected on damage/attack,
            resulting in the death of the entity if it gets to zero.
        _speed (int): the furthest (taxicab) distance the entity can travel in
            a move.
        _strength (int): the amount of damage this entity does to another when
            it attacks (to the other entities health). (Can be negative)
    
    Subclasses & Types:
        Mech: Entities that are controlled by the player.
            Additional Methods:
                enable
                disable
                is_active.
            Additional Attributes:
                _is_active (bool): is the mech active.
                _previous_position (int): what was the previous mechs position.
        Enemy: Entities that are controlled by the game, and have their own
            movment algorithms etc.
            Additional Methods:
                get_objective
                update_objective
            Additional Attributes:
                _objective (tuple[int, int]): the position that the entity wants
                    to move towards.

    """

    def __init__(self, position: tuple[int, int], initial_health: int,
                 speed: int, strength: int) -> None:
        """Instantiates a new entity with the specified values
        
        Paramaters:
            position (tupple[int, int]): the initial entity position (row, col).
            initial_health (int): the initial health of the entity.
            speed (int): the initial speed of the entity.
            strength (int): the initial strength of the entity. 
        """
        self._position = position
        self._health = initial_health
        self._speed = speed
        self._strength = strength

    def __repr__(self) -> str:
        """Returns the string representation of the entity.

        This is a machine readable string that could be used to construct an
        identical instance of the entity.

        Example:
            >>> e1 = Entity((0, 0), 1, 1, 1)
            >>> e1
            Entity((0, 0), 1, 1, 1)
        """
        args = (f"{self._position}, {self._health}, "
                f"{self._speed}, {self._strength}")
        # Uses __class__.__name__ to work for subclasses & future subclasses.
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        """Returns the string representation of the entity. 
        
        The string representation of an entity is a comma separated list 
        containing (in order):
            the character representing the type of the entity;
            the row currently occupied by the entity;
            the column currently occupied by the entity;
            the current health of the entity;
            the entity's speed;
            and the entity's strength.
        """
        info = [self.get_symbol(), self._position[0], self._position[1],
                self._health, self._speed, self._strength]
        return ','.join(map(str, info))

    def get_symbol(self) -> str:
        """Gets the entities symbol (str) as specified in a2_support.
        
        An entities symbol is the character that represents the entity type.
        This method is unique for each subclass but maintains returning the
        respective character in a2_support. The entities symbol is this
        character which represents the entity type.
        """
        return ENTITY_SYMBOL

    def get_name(self) -> str:
        """Gets the entities name (str) as specified in a2_support.
        
        This is (usually) the name of the most specific class to which this
        entity belongs- unless a2_support defines it elsewise.
        """
        return ENTITY_NAME 

    def get_position(self) -> tuple[int, int]:
        """Gets the entities position as tuple[row: int, col: int]."""
        return self._position

    def set_position(self, position: tuple[int, int]) -> None:
        """Sets the entity position.
        
        Paramaters:
            position (tuple[int, int]): the new position of the entity in the 
                form (row, col).
        """
        self._position = position

    def get_health(self) -> int:
        """Gets the entities current health (int)."""
        return self._health
    
    def get_speed(self) -> int:
        """Gets the entities speed (int)."""
        return self._speed
    
    def get_strength(self) -> int:
        """Gets the entities strength (int)."""
        return self._strength

    def damage(self, damage: int) -> None:
        """Reduces the health of the entity by the amount specified. 
        
        Note that the amount of damage suffered is not constrained to be
        positive. The health of the entity should be capped to be non-negative.
        
        The health of the entity should not be capped to any maximum value. This
        function should do nothing if the entity is destroyed.

        Paramaters:
            damage (int): the amount of damage to be dealt to the entity. Can
            be negative.
        """
        if not self.is_alive():
            return # Don't waste computation if its already dead.

        new_health = self._health - damage # Calculate new health 
        self._health = new_health if new_health > 0 else 0 # Ensure its non-neg.

    def is_alive(self) -> bool:
        """Returns if the entity is alive (bool- has health remaining)."""
        return self._health > 0
    
    def is_friendly(self) -> bool:
        """Returns (bool) if the entity is friendly. Are not by default."""
        return ENTITY_DEFAULT_FREINDLINESS

    def get_targets(self) -> list[tuple[int, int]]:
        """Gets the positions that would be attacked by the entity during a
        combat phase.
        
        By default, entities target vertically and horizontally adjacent tiles.
        For specficic entity types, specification is listed in the spec sheet
        as it does not affect use of this method.
        Note: The order of elements in this list does not matter.

        Returns:
            tuple[int, int]: the (row, col) positions that are attacked in no
                specific order.
        """
        return list(map(lambda dir : add_positions(self._position, dir),
                        [UP, DOWN, LEFT, RIGHT]))

    def attack(self, entity: "Entity") -> None:
        """Applies this entity's effect to the given entity. 
        
        By default, entities deal damage equal to the strength of the entity.

        Paramaters:
            entity (Entity): the entity that will be attacked.
        """
        entity.damage(self._strength)

class Mech(Entity): 
    # TODO
    def __init__(self, position: tuple[int, int], initial_health: int,
                speed: int, strength: int) -> None:
        super().__init__(position, initial_health, speed, strength)
        self._active = MECH_DEFAULT_ACTIVITY
        self._previous_position = position

    def is_friendly(self) -> bool:
        return MECH_DEFAULT_FREIDNLINESS
    
    def get_symbol(self) -> str:
        return MECH_SYMBOL
    
    def get_name(self) -> str:
        return MECH_NAME
    
    def enable(self) -> None:
        """Sets the Mech to be active."""
        self._active = True
    
    def disable(self) -> None:
        """Sets the mech to not be active."""
        self._active = False
    
    def is_active(self) -> bool:
        """Returns true iff the mech is active."""
        return self._active

class TankMech(Mech):
    def get_targets(self) -> list[tuple[int, int]]:
        # The two sets of five tiles extending in a horizontal line
        # this is achieved by adding the (0, i) for i from -5 (left) to 5 right
        return list(map(lambda pos : add_positions(self._position, pos),
                    [(0, i) for i in range(-5, 6) if i !=  0]))

    def get_symbol(self) -> str:
        return TANK_SYMBOL
    
    def get_name(self) -> str:
        return TANK_NAME

class HealMech(Mech):
    def attack(self, entity: "Entity") -> None:
        """Heal Mechs can only 'attack' friendly enemies
        """
        if entity.is_friendly():
            entity.damage(self.get_strength())
    def get_strength(self) -> int:
        """Returns the negative (int) of the strength of the heal mech.
        
        Since an entities stored strength is its absolute value, heal mechs
        return the negative of this value to indicate healing not damaging
        the opposite entity."""
        return -self._strength
    
    def get_symbol(self) -> str:
        return HEAL_SYMBOL
                
    def get_name(self) -> str:
        return HEAL_NAME

class Enemy(Entity):
    # TODO
    def __init__(self, position: tuple[int, int], initial_health: int,
                 speed: int, strength: int) -> None:
        """All enemies have an objective, which is a position that the entity 
        wants to move towards. Enemies of any type are never friendly.
        """
        super().__init__(position, initial_health, speed, strength)
        self._objective = self._position
    
    def get_objective(self) -> tuple[int, int]:
        return self._objective
    
    def update_objective(self, entities: list[Entity],
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        """Updates the objective of the enemy based on a list of entities and 
        dictionary of buildings, according to Table 3.
        
        The default behavior (that is, the behavior in the abstract Enemy class)
        is to set the objective of the enemy to the current position of the
        enemy. 

        A precondition to this function is that the given list of entities is 
        sorted in descending priority order, with the first entity in the list 
        being the highest priority."""
        self._objective = self._position
    
    def get_symbol(self) -> str:
        return ENEMY_SYMBOL
        
    def get_name(self) -> str:
        return ENEMY_NAME
        
class Scorpion(Enemy):
    """Scorpion inherits from Enemy. Scorpion represents a type of enemy that 
    attacks at a moderate range in all directions, and targets mechs with the 
    highest health.
    """
    def update_objective(self, entities: list[Entity], 
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        """Position of tile containing mech with the greatest health. If two
        mechs are tied for greatest health, choose position of tile containing
        the mech with the highest priority. If no valid objective exists, 
        then the enemy’s objective should not change.
        """
        greatest_health_mech = None
        for entity in entities:
            if isinstance(entity, Mech): # TODO ISINSTANCE
                if not greatest_health_mech or \
                   entity.get_health() > greatest_health_mech.get_health():
                   # Set this to the new greatest mech, > implies first one is
                   # kept ie highest priority preferred.
                   greatest_health_mech = entity
        if greatest_health_mech:
            self._objective = greatest_health_mech.get_position()
    def get_targets(self) -> list[tuple[int, int]]:
        """The four sets of two tiles extending in horizontal and vertical 
        lines from the scorpion: beginning from the tile directly left of the 
        scorpion and extending left, beginning from the tile directly
        right of the scorpion and extending right, beginning from the tile
        directly above of the scorpion and extending upward, and beginning
        from the tile directly below scorpion and extending downwards
        respectively.
        """ 

        return list(map(lambda pos : add_positions(self._position, pos),
                    [LEFT, scale_position(LEFT, 2), # tile and its extended tile
                     RIGHT, scale_position(RIGHT, 2),# TODO CONSTANTn2 
                     UP, scale_position(UP, 2),
                     DOWN, scale_position(DOWN, 2)]))

    def get_symbol(self) -> str:
        return SCORPION_SYMBOL
    
    def get_name(self) -> str:
        return SCORPION_NAME

class Firefly(Enemy):  

    def update_objective(self, entities: list[Entity], 
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        """Position of building tile with the least health amongst the buildings
        that are not destroyed. If two buildings are tied for the least health,
        choose the position of the building tile in the bottommost row.
        If there is still a tie for lowest health, choose the position of the
        building tile in the rightmost column
        """ 
        least_building_pos = None
        for position, building in buildings.items():
            if building.is_destroyed():
                continue # don't bother any checks skip to next position
            if least_building_pos is None:
                least_building_pos = position
                continue # don't bother checking with itself    
            least_building = buildings[least_building_pos] # get actual tile

            if building.get_health() < least_building.get_health():
                least_building_pos = position
            elif building.get_health() == least_building.get_health():
                if position[0] > least_building_pos[0]: # bottomer row
                    least_building_pos = position
                elif position[0] == least_building_pos[0] and \
                     position[1] > least_building_pos[1]: # same row, right col.
                    least_building_pos = position
        if least_building_pos:
            self._objective = least_building_pos

    def get_targets(self) -> list[tuple[int, int]]:
        """The two sets of five tiles extending in a vertical line from the
        firefly: beginning from the tile directly above of the firefly and
        extending upwards, and beginning from the tile directly below the 
        firefly and extending downwards respectively.
        """
        return list(map(lambda pos : add_positions(self._position, pos),
                    [(i, 0) for i in range(-5, 6) if i !=  0])) # 5 up 5 down

    def get_symbol(self) -> str:
        return FIREFLY_SYMBOL
            
    def get_name(self) -> str:
        return FIREFLY_NAME

class Tile(object):
    def __init__(self) -> None:
        self._blocking = TILE_DEFAULT_BLOCKING

    def is_blocking(self) -> bool:
        """Returns True only when the tile is blocking.

        A tile may be blocking, in which case entities cannot stand on it. 

        Tiles that are not blocking may have a maximum of one entity standing on
        them at any given time.

        Tiles are not blocking by default.
        """
        return self._blocking

    def get_tile_name(self) -> str:
        """Returns the name of the type of the tile."""
        return TILE_NAME

    def __repr__(self) -> str:
        """Returns a machine readable string that could be used to construct an
        identical instance of the tile.
        """
        return f"{self.__class__.__name__}()" # TODO depends on subclass name
    
    def __str__(self, symbol=TILE_SYMBOL) -> str:
        """Returns the character representing this type of tile."""
        return symbol

class Ground(Tile):
    def __init__(self) -> None:
        super().__init__()
        self._blocking = False # Never blocking by specification
    
    def __str__(self) -> str:
        return super().__str__(symbol=GROUND_SYMBOL)
    
    def get_tile_name(self) -> str:
        return GROUND_NAME

class Mountain(Tile):
    def __init__(self) -> None:
        super().__init__()
        self._blocking = True # Always blocking by specification

    def __str__(self) -> str:
        return super().__str__(symbol=MOUNTAIN_SYMBOL)
    
    def get_tile_name(self) -> str:
        return MOUNTAIN_NAME

class Building(Tile):
    def __init__(self, initial_health: int) -> None:
        super().__init__()
        self._health = initial_health # between 0 and 9 (inclusive)

    def get_health(self) -> int:
        return self._health

    def is_blocking(self):
        """Building tiles are only blocking iff they are not destroyed."""
        return not self.is_destroyed()
    
    def is_destroyed(self):
        """Returns True only if a building is destroyed"""
        return self._health == 0
    
    def damage(self, damage: int) -> None:
        """ Reduces the health of the building by the amount specified.
        
        Note that damage is not constrained to be positive. The health of the
        building should be capped to be between 0 and MAX_BUILDING_HEALTH (inc).
        
        This function should do nothing if the building is destroyed.
        """
        if self.is_destroyed():
            return # Do nothing if destroyed.

        resulting_health = self._health - damage 

        # Ensure the health value is kept between 0 & MAX_BUILDING_HEALTH inc.
        if resulting_health > MAX_BUILDING_HEALTH:
            resulting_health = MAX_BUILDING_HEALTH
        elif resulting_health < 0:
            resulting_health = 0
        self._health = resulting_health
    
    def __repr__(self) -> str:
        return f"Building({self._health})"

    def __str__(self) -> str:
        return str(self._health)

    def get_tile_name(self) -> str:
        return BUILDING_NAME 

class Board(object):
    """Board represents a structured set of tiles. 
    
    A board organizes tiles in a rectangular grid, where each tile has an
    associated (row, column) position. (0,0) represents the top-left corner,
    (1,0) represents the position directly below the top-left corner, and (0, 1)
    represents the position directly right of the top left corner. 
    """

    def __init__(self, board: list[list[str]]) -> None:
        """Sets up a new Board instance from the information in the board
        argument. 
        
        Each list in board represents a row of the board. The first list 
        represents the top-most row of the board, and the last list represents
        the bottom-most row of the board.
        
        The first character of each inner list represents the left-most tile on
        that row, and the last character of each inner list represents the
        right-most tile on that row. 
        
        A precondition to this function is that each list (each row) within the
        given board will have the same length. Another precondition to this 
        function is that the given array will contain at least one row.
        
        The final precondition to this function is that each character provided
        will be the string representation of one of the tile subclasses
        described in previous sections.
        """
        self._board = self._generate_initial_board(board)

    def get_board(self) -> list[list[object]]:
        return self._board

    def _generate_initial_board(self, input_board: list[list[str]]):
        board = []
        for row in input_board:
            row_objects = []
            for tile in row:
                obj = None # Current tile object.
                if tile == GROUND_SYMBOL:
                    obj = Ground()
                elif tile == MOUNTAIN_SYMBOL:
                    obj = Mountain()
                else:
                    # Must be a building with health = int(tile)
                    obj = Building(int(tile))
                row_objects.append(obj)
            board.append(row_objects)
        return board
                
    def get_dimensions(self) -> tuple[int, int]:
        return (len(self._board), len(self._board[0]))
    
    def get_tile(self, position: tuple[int, int]) -> Tile:
        """Precondition not out of bounds we are saying (y, x)"""
        row, col = position
        return self._board[row][col]

    def get_buildings(self) -> dict[tuple[int, int], Building]:
        buildings = {}
        for row_num, row in enumerate(self._board):
            for col_num, tile in enumerate(row):
                if isinstance(tile, Building):
                    buildings[(row_num, col_num)] = tile
        return buildings
    
    def __repr__(self) -> str:
        board_string = [] # Turning board back into repr 
        for row in self._board:
            row_str = [] 
            for tile in row:
                row_str.append("'" + str(tile) + "'") # adds "T" tile in quotes.
            board_string.append('[' + ', '.join(row_str) + ']') # adds list

        return f"Board([{', '.join(board_string)}])"
    
    def __str__(self) -> str:
        """Returns a string representation of the board.
        
        This is the string formed by concatenating the characters representing
        each tile of a row in the order they appear (left to right), and then
        concatenating each row in order (from top to bottom), separating each
        row with a new line character."""
        output = [] # used to store the resulting string as a character array.
        for row in self._board:
            row_str = []
            for tile in row:
                row_str.append(str(tile))
            output.append(''.join(row_str))
        return '\n'.join(output)
 
# --- VIEW ---

class BreachView(object):
    def __init__(self, root: tk.Tk, board_dims: tuple[int, int],
                 save_callback: Optional[Callable[[], None]] = None,
                 load_callback: Optional[Callable[[], None]] = None,
                 turn_callback: Optional[Callable[[], None]] = None,
                ) -> None:
        
        self._root = root
        self._root.title(BANNER_TEXT)

        self._banner = tk.Label(self._root, text=BANNER_TEXT, font=BANNER_FONT)

        self._gameFrame = tk.Frame() # contains the grid & sidebar
        self._gameGrid = GameGrid(self._gameFrame,
                                  board_dims, (GRID_SIZE, GRID_SIZE))
        self._sideBar = SideBar(self._gameFrame,
                                  (4, 1), (SIDEBAR_WIDTH, GRID_SIZE))

        self._controlBar = ControlBar(self._root, save_callback,
                                      load_callback, turn_callback)

    def get_grid(self):
        return self._gameGrid

    def redraw(self, board: 'Board', entities: list['Entity'],
               highlighted: list[tuple[int, int]]=None,
               movement: bool = False) -> None:

        self._gameGrid.redraw(board, entities,
                              highlighted=highlighted, movement=movement)
        self._sideBar.display(entities)

        # Banner to the top
        self._banner.pack(side=tk.TOP, fill=tk.X)

        # GameFrame - Grid left, sideBar right, whole frame top
        self._gameGrid.pack(side=tk.LEFT)
        self._sideBar.pack(side=tk.RIGHT)
        self._gameFrame.pack(side=tk.TOP, expand=True)

        self._controlBar.pack(side=tk.BOTTOM, fill=tk.X)#, fill=tk.X #, expand=True)
        
    def bind_click_callback(self, 
            click_callback: Callable[[tuple[int, int]], None]) -> None:
        self._gameGrid.bind_click_callback(click_callback)
        
class GameGrid(AbstractGrid):
    def __init__(self, master: Union[tk.Tk, tk.Widget],
                 dimensions: tuple[int, int], size: tuple[int, int],
                **kwargs) -> None:
        super().__init__(master, dimensions, size, **kwargs)

    def redraw(self, board: 'Board', entities: list['Entity'],
               highlighted: list[tuple[int, int]] = None,
               movement: bool = False) -> None:
        # CLEAR
        self.clear()
        # Color each of the squares
        for row_num, row in enumerate(board.get_board()):
            for col_num, tile in enumerate(row):
                pos = (row_num, col_num)
                tile_name =  tile.get_tile_name()

                if highlighted and pos in highlighted:
                    highlighted_color = MOVE_COLOR if movement else ATTACK_COLOR
                    self.color_cell(pos, highlighted_color)
                    if tile_name == BUILDING_NAME and not tile.is_destroyed(): 
                        self.annotate_position(pos, tile.get_health(),
                                               ENTITY_FONT)
                    continue 

                if tile_name == MOUNTAIN_NAME:
                    self.color_cell(pos, MOUNTAIN_COLOR)
                elif tile_name == BUILDING_NAME:
                    if tile.is_destroyed():
                        self.color_cell(pos, DESTROYED_COLOR)
                    else:
                        self.color_cell(pos, BUILDING_COLOR)
                        self.annotate_position(pos, tile.get_health(),
                                               ENTITY_FONT)
                elif tile_name == GROUND_NAME:
                    self.color_cell(pos, GROUND_COLOR)
        

        # Draw entities.
        for entity in entities:
            pos = entity.get_position() # current (row, col) entity position
            name =  entity.get_name() # current entity name for type checking
            character = None # stores the unicode character of current entity
            if name == SCORPION_NAME:
                character = SCORPION_DISPLAY
            elif name == FIREFLY_NAME:
                character = FIREFLY_DISPLAY
            elif name == TANK_NAME:
                character = TANK_DISPLAY
            elif name == HEAL_NAME:
                character = HEAL_DISPLAY
            if character: 
                self.annotate_position(pos, character, ENTITY_FONT)
    
    def bind_click_callback(self, click_callback: Callable[[tuple[int, int]],
                            None]) -> None:
        """Binds <button 1> and <button 2> events TODO ADVANCED"""
        self.bind("<Button 1>", click_callback)
        self.bind("<Button 2>", click_callback)
    
class SideBar(AbstractGrid):
    def __init__(self, master: Union[tk.Tk, tk.Widget],
                 dimensions: tuple[int, int], size: tuple[int, int],
                **kwargs) -> None:
        super().__init__(master, dimensions, size, **kwargs)
    
    def _annotate_row(self, row: list[str], row_num, font=SIDEBAR_FONT):
        for col_num, col_text in enumerate(row):
            self.annotate_position((row_num, col_num), col_text, font)

    def display(self, entities: list['Entity']) -> None:
        """Clears the side bar then redraws header etc"""
        self.clear()
        rows = len(entities) + 1 # Number of entities 1 row each + header
        self.set_dimensions((rows, len(SIDEBAR_HEADINGS)))

        self._annotate_row(SIDEBAR_HEADINGS, 0)

        for entity_num, entity in enumerate(entities):
            # Each entitiy gets its own row
            hp = entity.get_health()
            dmg = entity.get_strength()
            name = entity.get_name()
            pos = str(entity.get_position())
            #TODO THE FOLLOWING IS REPREATED
            char = ''
            if name == SCORPION_NAME:
                char = SCORPION_DISPLAY
            elif name == FIREFLY_NAME:
                char = FIREFLY_DISPLAY
            elif name == TANK_NAME:
                char = TANK_DISPLAY
            elif name == HEAL_NAME:
                char = HEAL_DISPLAY

            row = [char, pos, hp, dmg]
            row_num = entity_num + 1 # account for heading 
            # actually annote the row contents onto the sidebar
            self._annotate_row(row, row_num)

class ControlBar(tk.Frame):
    def __init__(self, master: tk.Widget,
                 save_callback: Optional[Callable[[], None]] = None,
                 load_callback: Optional[Callable[[], None]] = None,
                 turn_callback: Optional[Callable[[], None]] = None,
                 **kwargs ) -> None:

        # initialize tk.Frame
        super().__init__(master, **kwargs)
        self.config(height=CONTROL_BAR_HEIGHT)

        # add the 3 main buttons
        self._add_btn(SAVE_TEXT, save_callback)
        self._add_btn(LOAD_TEXT, load_callback)
        self._add_btn(TURN_TEXT, turn_callback)
        
    
    def _add_btn(self, text, command=None):
        btn = tk.Button(self, text=text, command=command)
        btn.pack(side=tk.LEFT, expand=True)


# --- CONTROLLER ---


class IntoTheBreach(object):
    def __init__(self, root: tk.Tk, game_file: str) -> None:
        self._root = root

        self._game_file = game_file

        self._highlighted_entitiy, self._move = None, False # Deafault

        self._viewer = None
        # Loads model 
        self.load_model(self._game_file)

        self._viewer = BreachView(self._root,
                            self._model.get_board().get_dimensions(),
                            self._save_game, self._load_game, self._end_turn)
        
        # set click callback
        self._viewer.bind_click_callback(self._handle_click_event) 
        # have to bind the click event not the handling
        
        self.redraw() # Initial render

    def restart(self):
        # Loads model and viewer again
        self.load_model(self._game_file)
        # recreate the viewer to new model etc
        self._reset_viewer()
    def _reset_viewer(self) -> None:
        dims = self._model.get_board().get_dimensions()
        self._viewer.get_grid().set_dimensions(dims)
        self.redraw()
        
        
    def _get_highlighted_squares(self) -> list[tuple[int, int]]:
        entity = self._highlighted_entitiy
        if not entity:
            return
        elif entity.is_friendly() and self._move:
            return self._model.get_valid_movement_positions(entity)
        else:
            return entity.get_targets()
        

            
    def redraw(self) -> None:
        self._viewer.redraw(self._model.get_board(),
                            self._model.get_entities(),
                            self._get_highlighted_squares(), self._move)
    
    def set_focussed_entity(self, entity: Optional['Entity'] = None) -> None:
        self._highlighted_entitiy = entity
    
    def make_move(self, position: tuple[int, int]) -> None:
        """Attempts to move the focussed entity to the given position
        and then clears the focussed entity. 
        """
        self._model.attempt_move(self._highlighted_entitiy, position)
        self.set_focussed_entity()
    
    def load_model(self, file_path: str) -> None:
        """Can assume no IO errors."""
        try:
            with open(file_path) as f:
                file_contents = f.readlines()
                # we shouldn't process anything with the file open (grab & go)
        except IOError as ioe:
            messagebox.showerror(title=IO_ERROR_TITLE,
                                message = f"{IO_ERROR_MESSAGE}{ioe}")
            return

        file_board = []
        file_entities = []
        board_generated = False # Used to know when we have reached blank ln
        for line in file_contents:
            line = line.rstrip() # Remove the \n & any accidental whitespace
            if not board_generated:
                if not line:
                    # If we have reached the blank, board is done
                    # turn into object
                    board_obj = Board(file_board)
                    board_generated = True
                else:
                    file_board.append(list(line)) # add it to the board
            else:
                # Must be generating entities
                symbol, *info = line.split(',')
                args = [(int(info[0]), int(info[1]))] \
                        + list(map(int, info[2:]))
                if symbol == TANK_SYMBOL:
                    file_entities.append(TankMech(*args))
                elif symbol == HEAL_SYMBOL:
                    file_entities.append(HealMech(*args))
                elif symbol == FIREFLY_SYMBOL:
                    file_entities.append(Firefly(*args))
                elif symbol == SCORPION_SYMBOL:
                    file_entities.append(Scorpion(*args))


        self._model = BreachModel(board_obj, file_entities)
        self._game_file = file_path

        self.set_focussed_entity() # reset focused entity to None


    def _save_game(self) -> None:
        self.set_focussed_entity() # button clicked
        if not self._model.ready_to_save():
            # Show error message box
            messagebox.showerror(title=INVALID_SAVE_TITLE,
                                 message=INVALID_SAVE_TITLE)
            return

        file_path = filedialog.asksaveasfilename()

        with open(file_path, 'w') as f:
            f.write(str(self._model))

    
    def _load_game(self) -> None:
        self.set_focussed_entity() # button clicked 
        self.load_model(filedialog.askopenfilename())
        self._reset_viewer()

    
    def _end_turn(self) -> None:
        self.set_focussed_entity() # when the turn ends we unhighlight 
        self._model.end_turn()
        self.redraw()

        if self._model.has_won():
            text = WIN_TEXT
        elif self._model.has_lost():
            text = LOSE_TEXT
        else:
            return
        
        self._root.update()
        play_again = messagebox.askquestion(title=text,
                                         message=f"{text} {PLAY_AGAIN_TEXT}")
        if play_again == 'no':
            self._root.destroy()
        else:
            self.restart()
    
    def _handle_click_event(self, event) -> None:
        # convert click position to the game grid cell
        position = self._viewer.get_grid().pixel_to_cell(event.x, event.y)
        return self._handle_click(position)

    def _handle_click(self, position: tuple[int, int]) -> None:
        entity_pos = self._model.entity_positions()
        highlighted_squares = self._get_highlighted_squares()
        if position in entity_pos:
            entity = entity_pos[position]
            self._move = entity.is_friendly() and entity.is_active()
            # Mech that has not moved
            # highlight/focus it
            self.set_focussed_entity(entity) 
        elif highlighted_squares and position in highlighted_squares:
            self.make_move(position)
            self.set_focussed_entity()
        else:
            # random square should cancel hihglight
            self.set_focussed_entity()

        self.redraw() # redraw on click if there was changes
  


# Main Game Loop

def play_game(root, file_path) -> None:
    c = IntoTheBreach(root, file_path)
    root.mainloop()

    
def main() -> None:
    """The main function
    """
    root = tk.Tk()
    play_game(root, './levels/level3.txt')

if __name__ == "__main__":
    main()
