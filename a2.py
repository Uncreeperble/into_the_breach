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

WIN_TEXT = 'You Win!'  # Win & Lose text will be followed by PLAY_AGAIN_TEXT
LOSE_TEXT = 'You Lost!'

ENTITY_DEFAULT_FREINDLINESS = False  # Entities are not friendly by default
MECH_DEFAULT_FREIDNLINESS = True  # Mech entities ARE friendly however
ENEMY_FRIENDLINESS = False  # Enemies are NEVER friendly.
TILE_DEFAULT_BLOCKING = False  # Tiles are NOT blocking by default
MECH_DEFAULT_ACTIVITY = True  # Mechs are ALWAYS starting as active

TANK_DIS = 5  # The distance tech Mechs can target horizontally
SCORP_DIS = 2
FIRE_DIS = 5


UP, DOWN, LEFT, RIGHT = PLUS_OFFSETS[::-1]  # 2D-Direction vectors


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
    return tuple(map(sum, zip(*positions)))  # ( sum(x1,x2...), sum(y1, y2...) )


def scale_position(position: tuple[int, int], scalar: int):
    """Applies vector scalar.

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


def name_to_unicode(name: str) -> str:
    """Given an Entity name, will return the corresponding display symbol."""
    char = None
    if name == SCORPION_NAME:
        char = SCORPION_DISPLAY
    elif name == FIREFLY_NAME:
        char = FIREFLY_DISPLAY
    elif name == TANK_NAME:
        char = TANK_DISPLAY
    elif name == HEAL_NAME:
        char = HEAL_DISPLAY
    return char

# <----| Class Defintions (as per spec sheet) |---->

# Will be split up into the following subsections:
#     Model: the internal game classes and model itself
#     View: the user interface that displays a given model instance
#     Controller: links both view and model

# --- MODEL ---
# ( Main Model Class )


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
        entity_is_mech = map(lambda x: x.is_friendly(), self.get_entities())
        has_mech, has_enemy = any(entity_is_mech), not all(entity_is_mech)
        has_building = any(map(lambda x: not x.is_destroyed(),
                               self._board.get_buildings().values()))
        return (has_mech, has_enemy, has_building)

    def _get_enemies(self) -> list['Entity']:
        """Gets the model's alive enemies.

        Returns:
            list[Entity]: a list of enemies currently in the game, in
                descending order.
        """
        # get_entities already filters out dead entities, this filters mechs out
        return [e for e in self.get_entities() if not e.is_friendly()]

    def _closest_position(self, positions: list[tuple[int, int]],
                          goal: tuple[int, int], exclude_goal: bool = False):
        """Returns the closest position in the given list to  the given goal.

        This function will iterate the positions list keeping track of which
        position has the least taxicab distance, via get_distance, to the goal.
        It will navigate around the current board state.

        If two positions are tied for distance- it will return that of the
        highest priority (larger row, larger column).

        Arguments:
            positions (list[tuple[int, int]]): The list of possible positions to
                consider.
            goal (tuple[int, int]): The position of the goal to compare- can
                contain entities/blocking tiles since get_distance(goal, pos) is
                used.
            exclude_goal (bool: default False): If True, the position of the
                provided goal will not be considered even if its in the provided
                positions list.

        Preconditions:
            The provided positions list is in ascending priority order- that is
            in order of increasing row then increasing column.

        Example:
            >>> model._closest_position([(0, 1), (3, 5), (3, 6), (3, 7)], 
                                        (3, 6), True)
            (3, 7)
        """
        closest_pos, least_dist = None, None
        for pos in positions:
            if pos == goal and exclude_goal:
                continue
            curr_dist = get_distance(self, goal, pos)
            if curr_dist == -1:
                # We don't consider this point if the end point is blocked
                continue
            if not closest_pos or curr_dist <= least_dist:
                # If we havn't found a valid point or we found a point closer
                # or same dist & higher priority- set this to the new closest
                closest_pos, least_dist = pos, curr_dist
        return closest_pos

    def get_board(self) -> 'Board':
        """Gets the model's current Board.

        Returns:
            Board: the board object the model is operating with.
        """
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
        return [e for e in self._entities if e.is_alive()]

    def entity_positions(self) -> dict[tuple[int, int], 'Entity']:
        """Gets a dictionary of entities and their positions.

        Return:
            dict[tuple[int, int], Entity]: in the form (row, col) : Entity

        Example:
            >>> model.entity_positions()
            {(1, 2): TankMech((1, 2), 3, 3, 3)}
        """
        # constructs a dictionary for their position : entity
        return {e.get_position(): e for e in self.get_entities()}

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
        return [(y, x) for y in range(rows) for x in range(cols)
                if 0 < get_distance(self, pos, (y, x)) <= speed]

    def attempt_move(self, entity: 'Entity', position: tuple[int, int]) -> None:
        """Attempts to move the entity to the given position. 

        Moves the given entity to the specified position only if the entity 
        is friendly, active, and can move to that position according to the game
        rules present in specification section 3 (aka get_valid_movement_pos).

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
            self._can_save = False  # A move has made and end_turn hasn't ran

    def make_attack(self, entity: 'Entity') -> None:
        """Makes given entity perform an attack against every tile that is
        currently a target of the entity.

        The effect on each tile is described in the specification section 3, and
        in relevant Entity.attack and Tile.damage definitions.

        Paramaters:
            entity (Entity): the entity that is attacking.
        """
        rows, cols = self._board.get_dimensions()
        def is_valid_coord(p): return 0 <= p[0] < rows and 0 <= p[1] < cols
        entities = self.entity_positions()
        for coord in entity.get_targets():
            if not is_valid_coord(coord):
                continue  # don't consider any coords out of range

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

        This method works by running the Enemy.update_objective method on each
        enemy with the current game buildings and entities.
        """
        buildings = self._board.get_buildings()
        entities, enemies = self.get_entities(), self._get_enemies()
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
        for enemy in self._get_enemies():  # get_enemies is in high->low order
            objective = enemy.get_objective()

            # Since the objective is always going to be blocking in the current
            # game implmentation (either a building / entity) search for the
            # closest adjacent tile to this original objective and make this it.
            objective = self._closest_position(
                map(lambda p: add_positions(objective, p),
                    [UP, LEFT, RIGHT, DOWN]),  # list of adjacent positions
                enemy.get_position(), True)  # We shouldn't consider enemy_pos
            if not objective:
                continue  # This enemies objective was surrounded/unreachable

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
        # 1. ATTACKING PHASE: Every entity Attacks
        # We need to filter out dead entities as we go to ensure if one attack
        # kills another entity - that one does not then attack.
        [self.make_attack(ent)
         for ent in self.get_entities() if ent.is_alive()]

        # 2. ENEMY MOVEMENT PHASE
        # 2.1 Every entity gets its objectives
        self.assign_objectives()
        # 2.2 Every entity is moved
        self.move_enemies()

        # 3s. Every entity is enabled- and this indicates a model can save again
        [entity.enable() for entity in self._entities if entity.is_friendly()]
        self._can_save = True

# ( Entity Classes )


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

    Main Attributes:
        _position (tuple[int, int]): the positioin (row, col) of the entity
            on the board.
        _health (int): the health of the entity- affected on damage/attack,
            resulting in the death of the entity if it gets to zero.
        _speed (int): the furthest (taxicab) distance the entity can travel in
            a move.
        _strength (int): the amount of damage this entity does to another when
            it attacks (to the other entities health). (Can be negative)
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
        """Gets the entities position as tuple[row: int, col: int].
        Note: position are zero-indexed."""
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
            return  # Don't waste computation if its already dead.

        new_health = self._health - damage  # Calculate new health
        # Ensure its non-neg.
        self._health = new_health if new_health > 0 else 0

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
        # get the 4 adjacent tile positions
        return [add_positions(self._position, direction)
                for direction in [UP, DOWN, LEFT, RIGHT]]

    def attack(self, entity: "Entity") -> None:
        """Applies this entity's effect to the given entity. 

        By default, entities deal damage equal to the strength of the entity.

        Paramaters:
            entity (Entity): the entity that will be attacked.
        """
        entity.damage(self._strength)


class Mech(Entity):
    """Mechs are types of Entities that are controlled by the player.

    Additional Methods:
        enable
        disable
        is_active.

    Additional Attributes:
        _is_active (bool): is the mech active.
        _previous_position (int): what was the previous mechs position.
    """

    def __init__(self, position: tuple[int, int], initial_health: int,
                 speed: int, strength: int) -> None:
        # Initializes the same as its parent class
        super().__init__(position, initial_health, speed, strength)
        # Also sets the mechs activity
        self._active = MECH_DEFAULT_ACTIVITY

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
    """Tank Mechs are a child classs of Mechs that targets horizontal tiles."""

    def get_targets(self) -> list[tuple[int, int]]:
        # The two sets of five tiles extending in a horizontal line
        # this is achieved by adding the (0, i) for i from -5 left to 5 right
        # to the current position. TANK_DIS = 5
        return [add_positions(self._position, pos) for pos in
                [(0, i) for i in range(-TANK_DIS, TANK_DIS+1) if i != 0]]

    def get_symbol(self) -> str:
        return TANK_SYMBOL

    def get_name(self) -> str:
        return TANK_NAME


class HealMech(Mech):
    """Heal Mechs are a child class of Mechs that heal fellow Mechs.

    Heal Mechs store a positive strength- however on attack will heal the
    entity (only if its friendly) with this strength.
    """

    def attack(self, entity: "Entity") -> None:
        # Heal Mechs can only 'attack' friendly enemies
        if entity.is_friendly():
            entity.damage(self.get_strength())

    def get_strength(self) -> int:
        """Returns the negative (int) of the strength of the heal mech.

        Since an entities stored strength is its absolute value, heal mechs
        return the negative of this value to indicate healing not damaging
        the opposite entity.
        """
        return -self._strength

    def get_symbol(self) -> str:
        return HEAL_SYMBOL

    def get_name(self) -> str:
        return HEAL_NAME


class Enemy(Entity):
    """Enemies are entities that are controlled by the game.

    They have their own movement / attack strategies- involving objectives.
    Enemies of any type are not friendly.

    Additional Methods:
        get_objective
        update_objective

    Additional Attributes:
        _objective (tuple[int, int]): the position that the entity wants
            to move towards.
    """

    def __init__(self, position: tuple[int, int], initial_health: int,
                 speed: int, strength: int) -> None:
        # inits Enemy parent class entity as required
        super().__init__(position, initial_health, speed, strength)
        self._objective = self._position  # Also store the objective

    def get_objective(self) -> tuple[int, int]:
        """Returns the enemies current objective position."""
        return self._objective

    def update_objective(self, entities: list[Entity],
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        """Updates the objective of the enemy based on a list of entities and 
        dictionary of buildings, according to Table 3.

        The default behavior (that is, the behavior in the abstract Enemy class)
        is to set the objective of the enemy to the current position of the
        enemy.  If no valid objective exists, then the enemy's objective does
        not change.

        Paramaters:
            entities (list[Entity]): The current models entities
            buildings (dict[tuple[int, int], Building]): The buildings ingame

        Preconditions:
            the given list of entities is sorted in descending priority order,
            with the first entity in the list being the highest priority.
        """
        self._objective = self._position

    def get_symbol(self) -> str:
        return ENEMY_SYMBOL

    def get_name(self) -> str:
        return ENEMY_NAME

    def is_friendly(self) -> bool:
        return ENEMY_FRIENDLINESS


class Scorpion(Enemy):
    """Scorpion represents a type of enemy that attacks at a moderate range in
    all directions, and targets mechs with the highest health."""

    def update_objective(self, entities: list[Entity],
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        # Position of tile containing mech with the greatest health
        # If there are multiple take highest priority.

        # Finding the mech with the highest health/priotiy:
        greatest_health_mech = None
        for entity in entities:
            if (entity.is_friendly()  # The entity has to be a Mech
                and (not greatest_health_mech or  # No current Greatest or
                     # Has greater health since previous has higher priority.
                     entity.get_health() > greatest_health_mech.get_health()
                     )):
                # Then set this to the new greatest mech
                greatest_health_mech = entity
        if greatest_health_mech: # If we found a valid objective, update to this
            self._objective = greatest_health_mech.get_position()

    def get_targets(self) -> list[tuple[int, int]]:
        # sets of two tiles extending in horizontal and vertical lines from the
        # scorpion: eg. beginning from the tile directly left scorpion and
        # extending 1 more left. (Up to the distance of SCORP_DIS = 2)
        relative_tiles = [scale_position(dir, dist+1)  # extend distance
                          for dist in range(SCORP_DIS)  # 0, 1.. SCORP_DIS-1
                          for dir in [LEFT, RIGHT, UP, DOWN]]  # cardinal dirs
        # return the positions using their relative tiles
        return [add_positions(self._position, pos) for pos in relative_tiles]

    def get_symbol(self) -> str:
        return SCORPION_SYMBOL

    def get_name(self) -> str:
        return SCORPION_NAME


class Firefly(Enemy):
    """Firefly represents a type of enemy that attacks at a long range
    vertically, and targets buildings with the lowest health"""

    def update_objective(self, entities: list[Entity],
                         buildings: dict[tuple[int, int], "Building"]) -> None:
        # Position of building tile with the least health amongst the buildings
        # that are not destroyed - or bottom most right most on tie.
        least_building_pos = None
        for pos, building in buildings.items():  # Finding the building.
            if building.is_destroyed():
                continue  # don't bother any checks skip to next position
            if least_building_pos is None:  # if we havn't found one use this
                least_building_pos = pos
                continue  # don't bother checking with itself

            # Otherwie we need to get the current building and compare to the
            # current least one
            least_building = buildings[least_building_pos]
            # Either has less health or better position to replace the old best
            if building.get_health() < least_building.get_health():
                least_building_pos = pos
            elif building.get_health() == least_building.get_health():
                # Since items() isn't in any order use coord v coord checks
                if (pos[0] > least_building_pos[0] or  # bottomer row or
                    (pos[0] == least_building_pos[0] and  # same row and
                     pos[1] > least_building_pos[1])):  # more right column
                    least_building_pos = pos  # Better position use this one

        if least_building_pos: # Only do something if we found one not destryoed
            self._objective = least_building_pos

    def get_targets(self) -> list[tuple[int, int]]:
        # The two sets of five tiles extending in a vertical line from the
        # firefly: (uses FIRE_DIS = 5) (i, 0) changes vertical position.
        return [add_positions(self._position, pos) for pos in
                [(i, 0) for i in range(-FIRE_DIS, FIRE_DIS+1) if i != 0]]

    def get_symbol(self) -> str:
        return FIREFLY_SYMBOL

    def get_name(self) -> str:
        return FIREFLY_NAME

# ( Tile Classes )


class Tile(object):
    """Tiles are used to represent game objects not entities.

    Tile is an abstract class from which all instantiated types of tile inherit. 
    Provides default tile behavior, which can be inherited or overridden by 
    specific types of tiles.

    Attributes:
        _blocking (bool): A tile may be blocking, in which case entities cannot 
            stand on it. 

    Methods
    """

    def __init__(self) -> None:
        """Initializes a tile to have its blocking state."""
        self._blocking = TILE_DEFAULT_BLOCKING

    def __repr__(self) -> str:
        """Returns a machine readable string that could be used to construct an
        identical instance of the tile."""
        # Uses python classs names to ensure integrity- will grab that of the
        # most specific tile it belongs to.
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Returns the character representing this type of tile."""
        return TILE_SYMBOL

    def get_tile_name(self) -> str:
        """Returns the name of the type of the tile."""
        return TILE_NAME

    def is_blocking(self) -> bool:
        """Returns True only when the tile is blocking.

        Tiles that are not blocking may have a maximum of one entity standing on
        them at any given time.

        Tiles are not blocking by default.
        """
        return self._blocking


class Ground(Tile):
    """Ground tiles represent simple, walkable ground with no properties."""

    def __str__(self) -> str:
        return GROUND_SYMBOL

    def get_tile_name(self) -> str:
        return GROUND_NAME


class Mountain(Tile):
    """Mountain tiles represent unpassable terrain (always blocking)."""

    def __init__(self) -> None:
        self._blocking = True  # Always blocking by specification

    def __str__(self) -> str:
        return MOUNTAIN_SYMBOL

    def get_tile_name(self) -> str:
        return MOUNTAIN_NAME


class Building(Tile):
    """ Building tiles represent one or more buildings that the player must
    protect from enemies. 

    Additional Methods:
        get_health
        is_blocking
        is_destroyed
        damage

    Additional Attributes:
        _health (int): Building tiles have an integer health value and can be
            destroyed. 
            A building tile is destroyed when its health drops to zero. 
            The health value of a building can never increase above 9.

        blocking : Building tiles are blocking only when they are not destroyed.
    """

    def __init__(self, initial_health: int) -> None:
        # Don't need to super() to init blocking since it's not stored for
        # buildings (determined by destroyed/not)
        self._health = initial_health  # between 0 and 9 (inclusive)

    def __repr__(self) -> str:
        # Overrides default to ensure health is passed as an argument
        return f"Building({self._health})"

    def __str__(self) -> str:
        # Overrides default to pass health not symbol
        return str(self._health)

    def get_health(self) -> int:
        """Returns the (int) building health"""
        return self._health

    def is_blocking(self) -> bool:
        """Returns if the tile is blocking.

        Building tiles are only blocking iff they are not destroyed.
        """
        return not self.is_destroyed()

    def is_destroyed(self):
        """Returns True only if a building is destroyed"""
        return not self._health  # no health remaining

    def damage(self, damage: int) -> None:
        """Reduces the health of the building by the amount specified.

        Note that damage is not constrained to be positive. The health of the
        building should be capped to be between 0 and MAX_BUILDING_HEALTH (inc).

        This function should do nothing if the building is destroyed.

        Paramaters:
            damage (int): the amount of damage to be inflicted.
        """
        if self.is_destroyed():
            return  # Do nothing if destroyed

        resulting_health = self._health - damage
        if resulting_health > MAX_BUILDING_HEALTH:  # Ensure the health value is
            resulting_health = MAX_BUILDING_HEALTH  # kept between 0 & MAX
        elif resulting_health < 0:
            resulting_health = 0
        self._health = resulting_health  # sets the health to new & VALID value

    def get_tile_name(self) -> str:
        return BUILDING_NAME

# ( Board Class )


class Board(object):
    """Board represents a structured set of tiles. 

    A board organizes tiles in a rectangular grid, where each tile has an
    associated (row, column) position. (0,0) represents the top-left corner,
    (1,0) represents the position directly below the top-left corner, and (0, 1)
    represents the position directly right of the top left corner. 

    Attributes:
        _board: the list of objects that create the board.

    Methods:
        get_board
        get_dimensions
        get_tile
        get_buildings
    """

    def __init__(self, board: list[list[str]]) -> None:
        """Sets up a new Board instance from the information in the board
        argument. 

        Each list in board represents a row of the board. The first list 
        represents the top-most row of the board, and the last list represents
        the bottom-most row of the board.

        Paramaters:
            board (list[list[str]]): The array of characters used to instanciate
                the board. The first character of each inner list represents the
                left-most tile on that row, and the last character of each inner
                list represents the right-most tile on that row. 

        Preconditions:
            - each list (each row) within the given board will have the same
              length. 
            - the given array will contain at least one row.
            - each character provided will be the string representation of one 
              of the tile subclasses
        """
        # GENERATING THE INITIAL BOARD FROM CHARACTER LIST
        # Iterate through the characters given and compare to the implemented
        # subclasses- make an object of the matching type and add to board
        # maintaining row / column integrity
        self._board = []
        for row in board:
            row_objects = []
            for tile_char in row:
                if tile_char == GROUND_SYMBOL:
                    obj = Ground()
                elif tile_char == MOUNTAIN_SYMBOL:
                    obj = Mountain()
                else:
                    # Must be a building with health = int(tile)
                    obj = Building(int(tile_char))
                row_objects.append(obj)
            self._board.append(row_objects)

    def __repr__(self) -> str:
        """Returns a machine readable string that could be used to construct an
        identical instance of the board"""
        return f"Board({[[str(t) for t in row] for row in self._board]})"

    def __str__(self) -> str:
        """Returns a string representation of the board.

        This is the string formed by concatenating the characters representing
        each tile of a row in the order they appear (left to right), and then
        concatenating each row in order (from top to bottom), separating each
        row with a new line character.
        """
        return '\n'.join([''.join([str(tile) for tile in row]) # Row of str-tile
                         for row in self._board])  # Each row split by newling

    def get_board(self) -> list[list[Tile]]:
        """Returns the current board as a 2D list of objects/tiles."""
        return self._board

    def get_dimensions(self) -> tuple[int, int]:
        """Returns the (rows, columns) dimensions of the board."""
        return (len(self._board), len(self._board[0]))

    def get_tile(self, position: tuple[int, int]) -> Tile:
        """Gets the Tile at the given position.

        Paramaters:
            position: the (row, column) position of the tile being fetched-
                noting that positions are zero-indexed.

        Precondition:
            the position is not out of bounds of the board dimensions

        Returns:
            Tile: the tile at the position
        """
        return self._board[position[0]][position[1]]

    def get_buildings(self) -> dict[tuple[int, int], Building]:
        """Gets a dictionary mapping the positions of buildings to the
        building instances at those positions.

        This dictionary only contains positions that have a building tile.

        Returns:
            dict[tuple[int, int], Building]: The dict in the form pos : building

        Example:
            >>> board.get_buildings()
            {(0, 0): Building(5),
             (2, 2): Building(2)
            }
        """
        buildings = {}  # Generating the dictionary by checking every tile
        # -> go through each tile in
        for row_num, row in enumerate(self._board):
            for col_num, tile in enumerate(row):  # the board and ensure
                if tile.get_tile_name() == BUILDING_NAME:  # it is a building
                    # -> add pos : building
                    buildings[(row_num, col_num)] = tile
        return buildings


# --- VIEW ---
# ( Main View Class )
class BreachView(object):
    """The BreachView class provides a single view interface for the controller.

    The view is laid out such that there is a banner at the top of the window,
    with the GameGrid and SideBar appearing horizontally adjacent just below it.
    The ControlBar should appear below these two components.

    Attributes:
        _root: the tk root the viewer runs on
        _baner: the tk label for the banner 
        _gameFrame: the main tkFrame holding the grid and sidebar
        _gameGrid: the GameGrid of the view
        _sideBar: the SideBar of the viewer
        _controlBar: the ControlBar of the viewer

    Methods:
        get_grid
        redraw
        bind_click_callback
    """

    def __init__(self, root: tk.Tk, board_dims: tuple[int, int],
                 save_callback: Optional[Callable[[], None]] = None,
                 load_callback: Optional[Callable[[], None]] = None,
                 turn_callback: Optional[Callable[[], None]] = None,
                 ) -> None:
        """Initializes the View to the given root and board dimensions.

        Sets title of the given root window, and instantiates all child 
        components. The buttons on the instantiated ControlBar receive the given
        callbacks as their respective commands.

        Parameters:
            root (tk.Tk): the tk main window root of the view 
            board_dims (tuple[int, int]): the dimensions of the board in the
                form (number of rows, number of columns)
            save_callback: the function invoked on the click of the save button
            load_callback: the function invoked on the click of the load button
            turn_callback: the function invoked on the click of end turn button
        """
        self._root = root
        self._root.title(BANNER_TEXT)

        self._banner = tk.Label(self._root, text=BANNER_TEXT, font=BANNER_FONT)

        self._gameFrame = tk.Frame()  # contains the grid & sidebar
        self._gameGrid = GameGrid(self._gameFrame,
                                  board_dims, (GRID_SIZE, GRID_SIZE))
        self._sideBar = SideBar(self._gameFrame,
                                (4, 1), (SIDEBAR_WIDTH, GRID_SIZE))

        self._controlBar = ControlBar(self._root, save_callback,
                                      load_callback, turn_callback,
                                      height=CONTROL_BAR_HEIGHT)

    def bind_click_callback(self,
                            click_callback: Callable[[tuple[int, int]],
                                                     None]) -> None:
        """Binds a click event handler to the instantiated GameGrid.

        Paramaters:
            click_callback: the event handler to be binded to the GameGrid
        """
        self._gameGrid.bind_click_callback(click_callback)

    def redraw(self, board: 'Board', entities: list['Entity'],
               highlighted: list[tuple[int, int]] = None,
               movement: bool = False) -> None:
        """Redraws the instantiated GameGrid and SideBar based on the game state

        Paramaters:
            board (Board): the current models game board object
            entities (list[Entity]): a list of entities in priority order
            highlighted (list[tuple[int, int]]): a list of positions that willl
                be highlighted on the game grid.
            movement (bool): passed into GameGrid Redraw to determine if the
                highlighted positions are coloured for movment positions or
                target positions.
        """
        # Redraw the GameGrid and Render the sideBar as these change
        self._gameGrid.redraw(board, entities,
                              highlighted=highlighted, movement=movement)
        self._sideBar.display(entities)

        # Now pack everying in order:
        # Banner goes to the top
        self._banner.pack(side=tk.TOP, fill=tk.X, expand=True)

        # Pack the GameGrid and Sidebar inside their joined Frame
        # then pack this whole frame to the top (under the banner)
        self._gameGrid.pack(side=tk.LEFT)
        self._sideBar.pack(side=tk.RIGHT)
        # expand the gameFrame so on window expansion it remains in the middle
        self._gameFrame.pack(side=tk.TOP, expand=True)

        # finally pack control bar to the top (under these) and fill to use X
        self._controlBar.pack(side=tk.TOP, fill=tk.X, expand=True)

# ( Game Frame Classes )


class GameGrid(AbstractGrid):
    """GameGrid is a view component that displays the game board, with entities 
    overlaid on top.

    Tiles are represented by certain colored  squares, and entities are
    displayed by annotating special Unicode symbols on top of these squares

    Methods:
        redraw
        bind_click_callback

    Note that GameGrid inherits the predefined AbstractGrid and its properties.
    """

    def _handle_click(self, click, click_callback: Callable) -> None:
        """Calls the given click_callback with the grid position at click x,y"""
        click_callback(self.pixel_to_cell(
            click.x, click.y))  # from x, y -> r, c

    def redraw(self, board: 'Board', entities: list['Entity'],
               highlighted: list[tuple[int, int]] = None,
               movement: bool = False) -> None:
        """Clears the game grid, then redraws it according to the provided info

        The gameGrid will draw tiles onto itself, the AbstractGrid, and will
        color cells as determined in a2_support. Highlighted cells will take
        priority and will be coloured determined if movement is true or not.

        The health of every non-destroyed building will then be displayed over
        top. For normal entities their DISPLAY unicode character from a2_support
        will be used.

        Paramaters:
            board (Board): The board being displayed
            entities: the list of entities to be displayed
            highlighted: a list of positions in order that will be highlighted
            movement (bool): determines the highlight color, on True will use
                MOVMENT_COLOR else ATTACK_COLOR
         """
        self.clear()  # Start by clearing the board for a fresh start

        # Reset the board dimensions
        self.set_dimensions(board.get_dimensions())
        # (This shouldn't change every redraw but on load level etc it could)
        # It would be preferred to have a separate public function to reset
        # the viewer dimensions on load/save but would break the CSSE rules gave

        # Color each of the squares/Tiles their colors
        for row_num, row in enumerate(board.get_board()):
            for col_num, tile in enumerate(row):
                pos = (row_num, col_num)
                tile_name = tile.get_tile_name()
                annotation = None  # used to determine if we annotate anything

                if highlighted and pos in highlighted:  # use highlighted color
                    color = MOVE_COLOR if movement else ATTACK_COLOR
                else:  # Otherwise get normal color depending on tile
                    if tile_name == MOUNTAIN_NAME:
                        color = MOUNTAIN_COLOR
                    elif tile_name == BUILDING_NAME:
                        if tile.is_destroyed():
                            color = DESTROYED_COLOR
                        else:
                            color = BUILDING_COLOR
                            annotation = tile.get_health()
                    elif tile_name == GROUND_NAME:
                        color = GROUND_COLOR
                # Color and annotate with the found values
                self.color_cell(pos, color)
                if annotation:
                    self.annotate_position(pos, annotation, ENTITY_FONT)

        # Draw/Annotate entities.
        for entity in entities:
            pos, name = entity.get_position(), entity.get_name()
            character = name_to_unicode(name)  # gets the unicode character
            if character:  # It should be one of them but just for future cases
                self.annotate_position(pos, character, ENTITY_FONT)

    def bind_click_callback(self, click_callback: Callable[[tuple[int, int]],
                            None]) -> None:
        """Binds <button 1> and <button 2> events to to use the given callback.

        Paramaters:
            click_callback: The click callback that will be ran on Tk's events
                of <Button 1> and <Button 2> -> the click callback will be ran
                with the passing of the grid (row, col) rather than the event
                itself.
        """
        def handler(event): return self._handle_click(event, click_callback)
        self.bind("<Button 1>", handler)
        self.bind("<Button 2>", handler)


class SideBar(AbstractGrid):
    """SideBar is a view component that displays properties of each entity. 

    Entities appear in descending priority order, with the highest priority
    entity appearing at the top of the sidebar, and the lowest priority entity
    appearing at the bottom of the sidebar.

    Additional Methods:
        display

    Note that SideBar inherits the predefined AbstractGrid and its properties.
    """

    def _annotate_row(self, row_text: list[str], row_num: int,
                      font: tuple = SIDEBAR_FONT):
        """Annotates a whole row of a grid with the list of text.

        Paramaters:
            row_text (list[str]): A list of each string for each column in that
                row. Has the same number of items as columns in grid.
            row_num (int): The row number of the row being annotated.

        Example:
            grid: C1 | C2 | C3 | C4
            >>> view._annotate_row(['a, b, c, d'], 2, NORM_FONT)
            grid: C1 | C2 | C3 | C4
                   a | b  | c  | d
        """
        for col_num, col_text in enumerate(row_text):
            self.annotate_position((row_num, col_num), col_text, font)

    def display(self, entities: list['Entity']) -> None:
        """Clears the side bar then redraws header row and entities present.

        Presently, the sidebar has the Symbol, position, health and damage of
        the entity displayed.

        Paramaters:
            entities: this is a list of entities that are in descending priority
                order. The lowest (last) entity will therefore appear on the
                last row of the sidebar.
            """
        self.clear()  # Start by clearing the sidebar
        rows = len(entities) + 1  # account for the 1 heading row
        self.set_dimensions((rows, len(SIDEBAR_HEADINGS))
                            )  # incase entities die
        # Start by drawing the headings row
        self._annotate_row(SIDEBAR_HEADINGS, 0)
        # Go through each entity and draw one row at a time
        for entity_num, entity in enumerate(entities):
            row = [name_to_unicode(entity.get_name()),  # unicode character,
                   str(entity.get_position()),  # position tuple
                   str(entity.get_health()),  # HP
                   str(entity.get_strength())]  # strength
            # now annote the row contents onto the sidebar
            # +1 accounts for heading row
            self._annotate_row(row, entity_num+1)

# ( Control Bar Class )


class ControlBar(tk.Frame):
    """ControlBar is a view component that contains three buttons that allow the
    user to perform administration actions.

    In order from left to right, the ControlBar contains the buttons:
        - save, load, and end turn
    """

    def __init__(self, master: tk.Widget,
                 save_callback: Optional[Callable[[], None]] = None,
                 load_callback: Optional[Callable[[], None]] = None,
                 turn_callback: Optional[Callable[[], None]] = None,
                 **kwargs) -> None:
        """Initializes control bar with given callbacks.

        Paramaters:
            master: the tk widget the frame runs on
            save_callback: the function invoked on the click of the save button
            load_callback: the function invoked on the click of the load button
            turn_callback: the function invoked on the click of end turn button
        """
        # initialize tk.Frame
        super().__init__(master, **kwargs)
        # add the 3 main buttons with their respective callbacks
        self._add_btn(SAVE_TEXT, save_callback)
        self._add_btn(LOAD_TEXT, load_callback)
        self._add_btn(TURN_TEXT, turn_callback)

    def _add_btn(self, text, command: Callable = None) -> None:
        """creates a button to the control bar with the given text and command.

        This function will pack the button to tk.LEFT and use expand to ensure
        all buttons are evenly spaced.

        Paramaters:
            command: The callable that will be ran when the button is clicked
        """
        btn = tk.Button(self, text=text, command=command)
        btn.pack(side=tk.LEFT, expand=True)


# --- CONTROLLER ---
class IntoTheBreach(object):
    """IntoTheBreach is the controller class for the overall game.

    The controller is responsible for creating and maintaining instances of the
    model and view classes, event handling, and facilitating communication
    between the model and view classes. 

    The controller will track which entity occupied the tile last clicked on by
    the user in order to correctly highlight tiles on the board.

    Attributes:
        _root: the main tk.Tk root
        _game_file: the file path of the current level
        _highlighted_entity: the last clicked entity (highlighted)
        _viewer: The BreachView object
        _model: The BreachModel object

    Methods:
        redraw
        set_focussed_entity
        make_move
        load_model
        """

    def __init__(self, root: tk.Tk, game_file: str) -> None:
        """Instantiates the controller. 

        Creates instances of BreachModel and BreachView, and redraws
        display to show the initial game state.

        Paramaters:
            root: the tk root used for display
            game_file: a valid game file/path of the level to be loaded

        Preconditions:
            No IO_ERRORS will occur when loading the initialboard.
        """
        self._root = root
        self._game_file = game_file
        self._highlighted_entitiy = None
        self._move = False

        # Loads Model
        self.load_model(self._game_file)

        # Loads & sets up viewer (binding main click callback)
        self._viewer = BreachView(self._root,
                                  self._model.get_board().get_dimensions(),
                                  self._save_game, self._load_game,
                                  self._end_turn)
        self._viewer.bind_click_callback(self._handle_click)

        self.redraw()  # Initial render

    def _get_highlighted_squares(self) -> list[tuple[int, int]]:
        """Returns all highlighted positions.

        This function uses the currently highlighted entity and either gets
        their targets or valid movement positions depending on the move state
        of the game.

        Returns this as a list of positions (row, col).
        """
        entity = self._highlighted_entitiy
        if not entity:
            return []  # No valid positions
        elif entity.is_friendly() and self._move:
            return self._model.get_valid_movement_positions(entity)
        else:
            return entity.get_targets()

    def _save_game(self) -> None:
        """Saves the current gamestate to a userequested location.

        Will only save if the user has made no moves since the last time they
        clicked the end turn button. Will display error message box if this is
        the case.

        The file will be writen as the str of the model (ie board then entities)
        """
        self.set_focussed_entity()  # button clicked so unhighlight anything
        if not self._model.ready_to_save():
            # Show error message box because unable to save
            messagebox.showerror(title=INVALID_SAVE_TITLE,
                                 message=INVALID_SAVE_MESSAGE)
        else:
            file_path = filedialog.asksaveasfilename()  # gets the file loc.
            with open(file_path, 'w') as f:
                f.write(str(self._model))  # opens file and writes the string

    def _load_game(self) -> None:
        """Loads the game/model from a file of their selection.

        If an IOError occurs trying to load this a message box will be shown.
        """
        self.set_focussed_entity()  # button clicked -> unhighlight anything
        self.load_model(filedialog.askopenfilename())  # load their file
        self.redraw()  # redraw for the new contents of the model

    def _end_turn(self) -> None:
        self.set_focussed_entity()  # unhighlight the entity
        self._model.end_turn()  # run the models end turn method
        self.redraw()  # redraw to show any changes to the model

        # Win Condition checking
        if self._model.has_won():
            text = WIN_TEXT
        elif self._model.has_lost():
            text = LOSE_TEXT
        else:
            return  # There was no win or lose, more moves can be made.

        self._root.update()  # Update manually to display board changes
        play_again = messagebox.askquestion(title=text,
                                            message=f"{text} {PLAY_AGAIN_TEXT}")
        if play_again == 'no':
            self._root.destroy() # Destroy the root window and exit 'peacefully'
        else:
            # they want to play again: re_loads model and viewer again
            self.load_model(self._game_file)
            self.redraw()  # redraw the viewer to new model conditions

    def _handle_click(self, position: tuple[int, int]) -> None:
        entity_pos = self._model.entity_positions()
        highlighted_squares = self._get_highlighted_squares()
        if position in entity_pos:  # if the pos clicked has an entity on it
            entity = entity_pos[position]  # get the entity object
            self._move = entity.is_friendly() and entity.is_active()
            # The move is only valid if its an active Mech
            # highlight/focus it since it was clicked
            self.set_focussed_entity(entity)
        elif highlighted_squares and position in highlighted_squares:
            # They have clicked on a highlighted square
            self.make_move(position)  # we will try and move them
            # make_move will not work if they clicked on a target anyway, and
            # automatically clears the highlighted entity.
        else:
            # clicking on a random square should cancel highlight
            self.set_focussed_entity()

        self.redraw()  # redraw on click incase entities moved/other changes

    def bind_click_callback(self,
                            click_callback: Callable[[tuple[int, int]],
                            None]) -> None:
        """Binds the given callback to the main <button 1> & <button 2>"""
        self._viewer.bind_click_callback(click_callback)

    def load_model(self, file_path: str) -> None:
        """Replaces the current game state with a new state based on the
        provided file.

        Paramaters:
            file_path (str): The file name/file path of the model to be loaded.

        Preconditions:
            file_path could be invalid in which case an error would be shown,
                but on error will only raise IO_ERROR's
            if file_path is valid its contents are in a valid format.
        """
        try:  # Try to open it to see if they gave a real file_path
            with open(file_path) as f:
                file_contents = f.readlines()
                # we shouldn't process anything with the file open (grab & go)
        except IOError as ioe: # only except on the io error as specified in doc
            messagebox.showerror(title=IO_ERROR_TITLE,
                                 message=f"{IO_ERROR_MESSAGE}{ioe}")
            return
        # File contents were retrieved and are now a valid state
        file_board = []
        file_entities = []
        board_generated = False # Used to know when we have reached a blank line
        for line in file_contents:
            line = line.rstrip()  # Remove the \n & any accidental whitespace
            # Depending on if we have the board or not yet do one of two things
            # either keep adding the row as a list to the board being generated,
            # and when the blank line is reached generate the actual object
            # OR the board is generated in which case each row represents an
            # entity -> instanciate an antity of the given type.
            if not board_generated:
                if not line:
                    # If we have reached the blank, board is done
                    # turn into object
                    board_obj = Board(file_board)
                    board_generated = True
                else:
                    file_board.append(list(line))  # add it to the board
            else:
                # Must be generating entities
                symbol, *info = line.split(',')
                args = [(int(info[0]), int(info[1]))] \
                    + [int(x) for x in info[2:]]
                # the arguments will be valid but any length so have it be
                # the position first then whatever is left (2:)
                if symbol == TANK_SYMBOL:
                    file_entities.append(TankMech(*args))
                elif symbol == HEAL_SYMBOL:
                    file_entities.append(HealMech(*args))
                elif symbol == FIREFLY_SYMBOL:
                    file_entities.append(Firefly(*args))
                elif symbol == SCORPION_SYMBOL:
                    file_entities.append(Scorpion(*args))
                # Else should not occur- it would indicate an invalid model
                # state involving entities not implemented yet.

        self._model = BreachModel(board_obj, file_entities)  # create the model
        self._game_file = file_path  # save the file path
        self.set_focussed_entity()  # reset focused entity to None

    def redraw(self) -> None:
        """Redraws the view based on the state of the model and the current 
        focussed entity."""
        self._viewer.redraw(self._model.get_board(),
                            self._model.get_entities(),
                            self._get_highlighted_squares(), self._move)

    def set_focussed_entity(self, entity: Optional['Entity'] = None) -> None:
        """Sets the highlighted/focussed entity to one given otherwise None."""
        self._highlighted_entitiy = entity

    def make_move(self, position: tuple[int, int]) -> None:
        """Attempts to move the focussed entity to the given position
        and then clears the focussed entity."""
        self._model.attempt_move(self._highlighted_entitiy, position)
        self.set_focussed_entity()

# <-- End of Object Definitions -->


def play_game(root: tk.Tk, file_path: str) -> None:
    """Plays the given game.

    Constructs the controller instance using the given file path and the root
    tk.Tk parameter.

    Ensures the root window stays opening listening for events (using mainloop).

    Paramaters:
        root (tk.Tk): the root object to run the game with
        file_path (str): the file path to the games first level file

    Preconditions:
        the initial file_path has to be valid.
    """
    gameController = IntoTheBreach(root, file_path)  # init contrller from file
    root.mainloop()  # start the mainloop for event listening etc


def main() -> None:
    """The main function is used for developer testing.

    It calls play game for any custom conditions of root and file_path.
    """
    root = tk.Tk()
    play_game(root, './levels/level3.txt')


if __name__ == "__main__":
    main()  # allows file to work as standalone script (for testing etc.s)
