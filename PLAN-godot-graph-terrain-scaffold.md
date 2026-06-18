# PLAN — Godot scaffold for graph-first procedural terrain

Status: PROPOSED / EXPLORATORY
Scope: Godot project scaffold for graph-first procedural terrain/world generation.

## Goal

Capture a practical Godot scaffold for exploring graph-first procedural generation.

The core direction:

> Use graphs to generate and validate world structure, then materialize terrain chunks from that graph.

This is not intended to replace dense terrain storage. The graph should own semantic structure, dependencies, constraints, and provenance. Heightmaps, tile maps, voxel densities, and chunk meshes should remain dense data generated from the graph.

## Design thesis

Godot should be a thin visualization/editor shell around a pure generation core.

Use Godot scenes for:

- display
- input
- debug UI
- editor tools
- materialized chunks

Use a project-owned graph model for:

- regions
- biomes
- rivers
- roads
- settlements
- resources
- dependencies
- constraints
- generation provenance

Do not make Godot's scene tree the world graph.

## Recommended project layout

```text
graph_terrain_godot/
  project.godot

  scenes/
    main/
      main.tscn
      main.gd
    debug/
      world_debug_view.tscn
      graph_debug_panel.tscn
    terrain/
      terrain_root.tscn
      terrain_chunk_2d.tscn
      terrain_chunk_3d.tscn

  scripts/
    app/
      app.gd
      generation_runner.gd
    graph/
      world_graph.gd
      world_node.gd
      world_edge.gd
      graph_query.gd
    generation/
      generation_pass.gd
      region_pass.gd
      biome_pass.gd
      elevation_pass.gd
      hydrology_pass.gd
      settlement_pass.gd
      road_pass.gd
      validation_pass.gd
    terrain/
      chunk_manager.gd
      chunk_materializer.gd
      heightfield.gd
      tile_materializer.gd
      mesh_materializer.gd
    debug/
      world_debug_draw.gd
      constraint_report_view.gd

  resources/
    generation/
      world_seed_config.gd
      biome_rule_set.gd
      terrain_material_set.gd
      validation_rule_set.gd
    biomes/
      temperate_forest.tres
      desert.tres
      swamp.tres
    materials/
    tiles/

  data/
    generated/
      .gdignore
    snapshots/
      .gdignore

  addons/
    graph_terrain_tools/
      plugin.cfg
      graph_terrain_plugin.gd
      docks/
        graph_inspector_dock.tscn
        graph_inspector_dock.gd
```

## Godot-specific choices

### Folder naming

Use `snake_case` for folders and files.

Reason: Godot projects are filesystem-backed, and case-sensitivity can become a cross-platform export problem. Keeping names boring and lowercase avoids avoidable import/path issues.

### Resources for configuration, not every runtime node

Use Godot `Resource` objects for stable editable data:

- world seed config
- biome rules
- terrain material sets
- validation rule sets
- optional saved graph snapshots

Avoid storing every generated graph node as a `.tres` resource at runtime. That will become noisy and hard to manage.

Good use:

```gdscript
class_name BiomeRuleSet
extends Resource

@export var allowed_transitions: Dictionary = {}
@export var default_biome: StringName = &"temperate_forest"
```

### Autoloads as small services

Use a small number of autoloads:

- `App`
- `WorldService`
- `DebugBus`

Avoid using autoloads as a global junk drawer.

Example:

```gdscript
# autoloads/world_service.gd
extends Node

signal world_generated(graph)
signal validation_report_ready(report)
signal chunk_materialized(chunk_coord)

var graph: WorldGraph

func generate_world(config: WorldSeedConfig) -> void:
    var runner := GenerationRunner.new()
    graph = runner.run(config)
    world_generated.emit(graph)
```

### Editor plugin later

Do not start with a Godot editor plugin. Start runtime-first.

Once the graph model works, add an editor dock under `addons/graph_terrain_tools/` for:

- generate world
- regenerate selected region
- inspect graph node
- show constraint failures
- highlight dependency chain
- export graph snapshot

### Threading rule

Background thread:

- pure graph generation
- arrays/dictionaries
- no scene-tree mutation

Main thread:

- instantiate scenes
- update TileMap/MeshInstance/Node tree
- draw debug overlays

This keeps generation portable and avoids thread-unsafe scene operations.

## Core data model

Start with plain `RefCounted` classes, not scene nodes.

### WorldGraph

```gdscript
class_name WorldGraph
extends RefCounted

var nodes: Dictionary = {}
var edges_from: Dictionary = {}
var edges_to: Dictionary = {}
var metadata: Dictionary = {}

func add_node(node: WorldNode) -> void:
    nodes[node.id] = node

func add_edge(edge: WorldEdge) -> void:
    if not edges_from.has(edge.from_id):
        edges_from[edge.from_id] = []
    if not edges_to.has(edge.to_id):
        edges_to[edge.to_id] = []
    edges_from[edge.from_id].append(edge)
    edges_to[edge.to_id].append(edge)
```

### WorldNode

```gdscript
class_name WorldNode
extends RefCounted

var id: StringName
var kind: StringName
var props: Dictionary = {}

func _init(p_id: StringName, p_kind: StringName, p_props: Dictionary = {}) -> void:
    id = p_id
    kind = p_kind
    props = p_props
```

### WorldEdge

```gdscript
class_name WorldEdge
extends RefCounted

var from_id: StringName
var to_id: StringName
var kind: StringName
var props: Dictionary = {}

func _init(p_from: StringName, p_to: StringName, p_kind: StringName, p_props: Dictionary = {}) -> void:
    from_id = p_from
    to_id = p_to
    kind = p_kind
    props = p_props
```

## Graph vocabulary

Suggested node kinds:

```text
World
Region
Biome
Watershed
River
RiverSegment
Lake
MountainRange
Peak
Valley
Road
RoadSegment
Trail
Settlement
Dungeon
ResourceDeposit
EncounterZone
Chunk
Constraint
GenerationPass
ValidationReport
```

Suggested edge kinds:

```text
CONTAINS
ADJACENT_TO
TRANSITIONS_TO
DRAINS_TO
FLOWS_TO
MERGES_WITH
CUTS_THROUGH
SUPPLIES_WATER_TO
CONNECTS
BLOCKS
NEAR
IN_BIOME
MATERIALIZES
GENERATED_BY
DEPENDS_ON
APPLIES_TO
FAILED_CONSTRAINT
```

## Generation pipeline

Use composable generation passes.

```gdscript
class_name GenerationPass
extends RefCounted

func run(graph: WorldGraph, ctx: GenerationContext) -> void:
    pass
```

Initial pass sequence:

```text
1. RegionPass
2. BiomePass
3. ElevationPass
4. HydrologyPass
5. SettlementPass
6. RoadPass
7. ValidationPass
8. ChunkIndexPass
```

Each pass should record provenance:

```gdscript
graph.add_edge(WorldEdge.new(feature_id, pass_id, &"GENERATED_BY"))
graph.add_edge(WorldEdge.new(feature_id, input_id, &"DEPENDS_ON"))
```

## Dense data stays dense

Do not store every tile, height sample, or voxel as a graph node.

Use dense structures for:

- heightmap
- moisture map
- temperature map
- slope map
- erosion map
- tile IDs
- voxel density
- nav-cost grids

The graph should store higher-level meaning:

- this chunk belongs to watershed 17
- this region uses the desert biome rule
- this river segment crosses chunks 3, 4, 5
- this road depends on a pass through mountain range 2
- this settlement failed water-access validation

## Materialization layer

Separate graph generation from terrain materialization.

```text
WorldGraph = semantic truth
ChunkMaterializer = converts graph + seed into visible data
TerrainChunk2D / TerrainChunk3D = Godot scene that displays materialized output
```

Early prototype target:

- draw regions as colored polygons or circles
- draw river graph as blue lines
- draw road graph as lines
- draw settlements as points
- list validation failures in a debug panel

Do not start with full mesh terrain or voxel terrain.

## Minimum viable prototype

First prototype:

```text
1. Generate 20 region nodes.
2. Connect neighboring regions.
3. Assign biomes using allowed-transition rules.
4. Generate 3 river paths as graph edges.
5. Place 5 settlements near rivers.
6. Connect settlements with roads.
7. Validate constraints.
8. Draw debug map.
```

Validation rules:

```text
every settlement has water within N units
every settlement connects to the road graph
no desert directly borders swamp unless a transition biome exists
no dungeon inside a lake
spawn has a path to the first settlement
rivers flow from higher elevation toward lower elevation
```

## Storage strategy

Start simple.

Recommended early persistence:

```text
JSON graph snapshot for graph/debug state
Godot Resources for configs
chunk files or SQLite later for generated dense terrain cache
```

Do not start with Neo4j or a heavy graph database unless interactive cross-world queries become the main problem.

Possible later split:

```text
LadybugDB or another local graph store = relationships, provenance, debug queries
chunk files or SQLite = generated terrain/cache data
seeded functions = reproducible detail
```

## Relationship to Archolith ideas

This proc-gen direction mirrors the Archolith context/security work:

| Archolith context security | Graph terrain generation |
|---|---|
| context provenance | feature provenance |
| context validation | world constraint validation |
| memory writes | generated feature persistence |
| tool-call justification | generation-pass justification |
| trace/audit | generation debug graph |
| dependency graph | regeneration dependency graph |

Shared thesis:

> Generate artifacts as graph-backed systems with provenance, validation, and dependency tracking.

## First implementation PR checklist

Create a new Godot project with:

```text
project.godot
scenes/main/main.tscn
scenes/main/main.gd
scripts/graph/world_graph.gd
scripts/graph/world_node.gd
scripts/graph/world_edge.gd
scripts/generation/generation_pass.gd
scripts/generation/generation_runner.gd
scripts/generation/region_pass.gd
scripts/generation/validation_pass.gd
scripts/debug/world_debug_draw.gd
resources/generation/world_seed_config.gd
autoloads/world_service.gd
```

Acceptance criteria:

```text
- project opens in Godot
- main scene calls WorldService.generate_world()
- generator creates a small graph with regions and edges
- debug view draws regions/edges
- validation pass returns at least one report object
- no TileMap/Mesh/Voxel dependency yet
- graph code is portable and not tied to scene nodes
```

## Non-goals

- Do not build a full terrain renderer first.
- Do not store every tile as a graph node.
- Do not make the scene tree the source of truth.
- Do not start with GDExtension.
- Do not start with a graph database unless the prototype proves runtime/in-editor queries need it.

## Next decision

Choose whether this belongs in:

1. a new dedicated Godot repo, or
2. an `experiments/graph-terrain-godot/` folder in an existing repo.

A new repo is probably cleaner once actual Godot files are created.
