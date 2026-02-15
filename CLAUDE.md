# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CrossRiver** is a 2D boat navigation game built with Pygame where players steer a boat across a river while avoiding obstacles within a 60-second time limit. The project demonstrates iterative game development with multiple physics implementations.

**Technology Stack:**
- Python 3.x
- Pygame (core game engine)
- pytmx (optional, for tilemap support in maps.py)

## Common Development Commands

### Running the Game

**Latest Version (Recommended):**
```bash
cd C:\Users\AMINE\Desktop\CrossRiver
python week2.py
```

**Other Versions:**
```bash
python CrossRiver.py    # Original prototype
python update1.py       # Early physics
python update1.2.py     # Refined physics
python week1.py         # Week 1 iteration
python level1.0.py      # Level-based approach
python maps.py          # TMX tilemap version (requires pytmx)
```

### Installing Dependencies

**Core Dependency:**
```bash
pip install pygame
```

**For Tilemap Support (maps.py only):**
```bash
pip install pytmx
```

### Creating a Requirements File
```bash
pip freeze > requirements.txt
```

## Architecture

### File Progression and Purpose

The codebase shows iterative development with multiple versions. Understanding the progression helps when working with the code:

| File | Status | Key Features | Purpose |
|------|--------|--------------|---------|
| `CrossRiver.py` | Prototype | Simple impulse-based movement | Initial concept |
| `update1.py` | Early | Basic 2D velocity physics | First physics iteration |
| `update1.2.py` | Mid-dev | Added smooth rotation, momentum | Refined controls |
| `week1.py` | Mid-dev | Tuned physics constants | Physics refinement |
| `level1.0.py` | Mid-dev | Simplified without rotation states | Level system attempt |
| `week2.py` | **Current** | 60-second timer, shake effect, polished physics | Latest stable version |
| `maps.py` | Advanced | TMX tilemap integration, collision layers | Alternative approach with Tiled maps |

**When making changes:** Work primarily on `week2.py` as it's the most recent and polished version.

### Core Game Loop Structure

All versions follow this pattern (60 FPS):

```
Input Handling
    └── Arrow keys control rotation and acceleration

Physics Engine
    ├── Momentum system with input buffer
    ├── Smooth rotation toward target angle
    ├── 2D velocity with forward direction
    ├── Friction and sideways drift
    └── Speed limiting

Collision Detection
    ├── Circle collision (boat radius = 15px)
    └── AABB collision vs rectangular obstacles

Rendering
    ├── Blue river background
    ├── Green obstacle rectangles
    ├── Brown boat polygon (rotated)
    └── Timer display (white/red with shake)
```

### Physics System (week2.py)

**Critical Constants - Modify These to Tune Gameplay:**

```python
MAX_SPEED = 10                    # Maximum velocity magnitude
ROTATION_SPEED = 450             # Degrees per second for smooth rotation
ROTATION_STEP = 25               # Degrees added per key press
BASE_ACCEL = 0.6                 # Base acceleration multiplier
ACCEL_PER_PRESS = 0.35          # Extra accel per buffered input
BASE_FRICTION = 0.99             # Forward friction (1% per frame)
SIDEWAYS_FRICTION = 0.985        # Sideways drift friction
SIDEWAYS_DRIFT_MULT = 0.75       # Global sideways effect reduction
SINGLE_KEY_ACCEL_MULT = 0.8      # Accel reduction when one key held
SINGLE_KEY_SIDEWAYS_MULT = 0.55  # Sideways reduction for single key
```

**How Physics Work:**

1. **Input Buffer System:**
   - Each key press adds to `input_buffer`
   - Buffer decays exponentially over 0.25 seconds
   - More buffered presses = higher acceleration
   - Allows "tapping" for burst speed

2. **Rotation Mechanics:**
   - Each arrow key press rotates boat by 25° (discrete steps)
   - Rotation animates smoothly at 450°/second
   - Opposite key press cancels current rotation
   - Boat always rotates to `target_angle`

3. **Velocity System:**
   - Forward direction computed from `boat_angle`
   - Acceleration applied in forward direction
   - Friction applied based on alignment:
     - Low friction when moving forward
     - High friction when moving sideways
   - Single key press reduces both acceleration and sideways effect

4. **Collision Response:**
   - Circle-rect collision detection
   - Collision resets boat to spawn position
   - Velocity and rotation also reset

### Boat Rendering

The boat is a brown polygon defined by 4 vertices:
```python
boat_shape = [
    pygame.Vector2(5, -9),   # front right
    pygame.Vector2(5, 9),    # back right
    pygame.Vector2(-5, 9),   # back left
    pygame.Vector2(-5, -9)   # front left
]
```

Each vertex is rotated by `boat_angle` and drawn at `boat_pos`.

### Collision Detection

**Simple Version (week2.py, week1.py, level1.0.py):**
- Hardcoded obstacle rectangles in `cubes` list
- Format: `(x, y, width, height)`
- Boat has 15px collision radius
- Circle-AABB collision algorithm

**Tilemap Version (maps.py):**
- Loads TMX files from `maps/` directory
- Blocking layers: "Trees", "Puie"
- Builds collision rectangles from tile grid
- Supports Tiled map editor workflow
- Requires `maps/crossRiver_Map_Level1.tmx` and associated tilesets

### Game Mechanics

**Controls:**
- LEFT arrow: Rotate 25° left, accelerate forward
- RIGHT arrow: Rotate 25° right, accelerate forward
- DOWN arrow: Rotate 25° left (alternative)

**Timer System:**
- 60-second countdown
- Turns red at ≤10 seconds
- Shakes when critical (random ±2px offset)
- Game auto-restarts when timer expires

**Collision Behavior:**
- Resets boat to `INITIAL_BOAT_POS = (WIDTH // 2, 600)`
- Clears velocity and rotation
- Timer continues running (no penalty)

## Collision Rectangle Reference (week2.py)

Current obstacles in the game (modify these to change level layout):

```python
cubes = [
    (0, 0, 200, HEIGHT),                  # Left wall
    (WIDTH - 200, 0, 200, HEIGHT),        # Right wall
    (200, 450, 380, 200),                 # Obstacle 1
    (200, 330, 750, 150),                 # Obstacle 2
    (670, 570, 500, 300),                 # Obstacle 3
    (330, 0, 720, 230),                   # Obstacle 4
]
```

**To modify the level:**
1. Edit the `cubes` list (lines 218-225)
2. Update the corresponding `pygame.draw.rect()` calls (lines 253-257)
3. Adjust obstacle positions to create new challenges

## Working with Tilemaps (maps.py)

**Setup Requirements:**
1. Create `maps/` subdirectory in project root
2. Place TMX file: `maps/crossRiver_Map_Level1.tmx`
3. Ensure tileset images are in the same directory
4. Install pytmx: `pip install pytmx`

**Tilemap Configuration:**
- Map loads from `MAP_PATH` variable (line 28)
- Blocking layers defined in `BLOCKING_LAYER_NAMES` (line 89)
- Collision rects auto-generated from blocking layers
- Supports fullscreen mode: `pygame.FULLSCREEN | pygame.SCALED`

**Spawn Point:**
- Determined by "Water" layer in TMX
- Searches for tile with property `isEntrance=true`
- Falls back to center if not found

## Code Structure Guidelines

**Current State:**
- All code is procedural (no classes)
- Game loop is monolithic
- Variables are module-level globals
- Physics and rendering are mixed

**When Making Changes:**

1. **Modifying Physics:**
   - Adjust constants at top of file (lines 31-42 in week2.py)
   - Test changes by running the game
   - Constants affect: speed, rotation, friction, drift

2. **Adding New Features:**
   - Follow existing patterns in week2.py
   - Use `pygame.Vector2` for positions/velocities
   - Maintain 60 FPS with `clock.tick(60)`
   - Use `dt` (delta time) for frame-rate independence

3. **Collision Detection:**
   - Boat collision radius is hardcoded at 15px
   - Add new obstacles to both `cubes` list and drawing code
   - Keep collision checks simple (circle vs AABB)

4. **Visual Changes:**
   - Screen size: `WIDTH = 1250, HEIGHT = 650` (week2.py)
   - Colors: River (100, 120, 230), Obstacles (34, 139, 34), Boat (139, 69, 19)
   - Font size: 72px for timer

## Development Patterns

**Iterative Approach:**
- Multiple versions exist for physics experimentation
- Each version represents a design decision
- Compare versions to understand tradeoffs
- Keep old versions for reference

**Testing:**
- No formal test suite
- Manual playtesting by running scripts
- Physics tuning through iteration
- Use different files for A/B testing features

**Version Control:**
- File naming indicates progression (update1 → update1.2 → week1 → week2)
- Each file is self-contained (no imports between versions)
- Easy to roll back by running older files

## Important Notes

**Window Size:**
- week2.py: 1250 x 650
- maps.py: 1440 x 810 (fullscreen)
- Adjust `WIDTH, HEIGHT` constants to change resolution

**Performance:**
- Game runs at 60 FPS
- All calculations use `dt` (delta time in seconds)
- Frame-rate independent physics

**Boat Position:**
- Origin is top-left (0, 0)
- Initial spawn: center-bottom (WIDTH // 2, 600)
- Y-axis points downward (standard Pygame coordinate system)

**Rotation:**
- Angle in degrees (not radians)
- 0° = pointing up (negative Y direction)
- Increases clockwise
- Kept in range [0, 360) with modulo

## Future Enhancement Ideas

Based on the codebase structure, consider:

1. **Object-Oriented Refactoring:**
   - Create `Boat` class with position, velocity, angle
   - Create `Obstacle` class for collision objects
   - Create `Game` class to manage state

2. **Level System:**
   - Load obstacle layouts from files
   - Progressive difficulty
   - Multiple levels with different layouts

3. **Asset Management:**
   - External sprite images for boat
   - Tileset graphics for obstacles
   - Background textures

4. **Configuration:**
   - `config.py` for physics constants
   - `settings.json` for game options
   - Easy tuning without code changes

5. **Polish:**
   - Sound effects (engine, collision)
   - Particle effects (water splash)
   - Smooth camera following boat
   - Win condition when reaching opposite shore
