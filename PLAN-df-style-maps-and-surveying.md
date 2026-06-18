# PLAN — DF-style nested maps and optional surveying avatar

Status: PROPOSED / EXPLORATORY
Scope: map structure, unit movement, surveying, negotiation, and player embodiment for a graph-first infrastructure/proc-gen game.

## Context

The project direction is drifting toward a hybrid of:

- graph-first world generation
- Dwarf Fortress-style nested maps
- infrastructure/logistics simulation
- Workers & Resources-style physical construction loops
- PowerHouse-style utility/network constraints
- Godot as a visualization/editor shell

This note captures a map/movement model and evaluates whether the player should have a physical representative for surveying and negotiations.

## Core map direction

Use **DF-style nested maps**, but not necessarily DF-style ASCII presentation.

The useful idea is the map model:

```text
world map
  -> region map
    -> local infrastructure map
      -> facility/site map
        -> building/interior/subsystem map
```

The game should not simulate every unit at every scale. Each map scale should expose the level of detail relevant to that layer.

## Map scale model

### 1. World / regional map

Purpose:

- strategic infrastructure planning
- town/facility placement
- road/rail/power corridors
- regional supply chains
- town growth pressure
- high-level unit routing

Representation:

- graph nodes for towns, facilities, substations, mines, depots, river crossings, industrial areas, and road/rail junctions
- graph edges for road segments, rail segments, power corridors, pipelines, and service routes
- stylized terrain/cell background for readability

Units:

- graph-routed trucks, buses, trains, crews, survey parties, and service units
- no fine-grained pedestrian simulation

### 2. Local infrastructure map

Purpose:

- construction placement
- material delivery
- staging areas
- service access
- utility layout
- road/rail geometry

Representation:

- DF-like cell/tile map or isometric cell map
- terrain cells with semantic tags: road, staging, storage, slope, riverbank, corridor, district block
- graph overlay for routes and infrastructure

Units:

- local construction crews, trucks, machines, inspectors
- units still follow graph/path routes, but cells make construction and placement legible

### 3. Town/city map

Purpose:

- inspect demand/supply
- model residential/commercial/industrial districts
- show growth drivers and failures
- optionally negotiate with town administration

Representation:

- nested district graph
- optional cell blocks for visible town layout
- district nodes for residential, commercial, industrial, civic, logistics, utility, and expansion areas

Units:

- mostly abstracted population and demand
- visible service vehicles or inspectors only when useful

### 4. Facility/site map

Purpose:

- warehouse yards
- loading bays
- substations
- power plants
- mines
- construction staging

Representation:

- small DF-like cell map
- rooms/zones/equipment nodes
- throughput nodes and internal edges

Units:

- mostly state-machine animation: loading, unloading, inspection, maintenance
- local free movement can be visual flavor only

## Movement model

Use a hybrid:

> High-level logistics move on graph routes. Local interaction happens on DF-like cell maps. Visual flavor can use local free movement.

### Regional movement

Graph-routed.

Units ask:

```text
What route through the built infrastructure gets me from origin node to destination node?
```

They do not generally cross arbitrary terrain unless explicitly allowed by a route type such as survey path, dirt track, or construction access.

### Local movement

Cell/path-based.

Use cells for:

- construction site access
- staging area layout
- facility internals
- loading/unloading positions
- utility corridors

Cells should be semantic, not just visual pixels.

### Visual movement

Free movement is allowed when it does not affect simulation correctness.

Examples:

- workers wandering inside a construction site
- forklifts animating in a warehouse
- inspectors walking around a town hall
- survey avatar moving within a selected local map

Rule:

```text
If movement affects logistics or construction, it must resolve against the graph/cell path model.
If it is only flavor, it may be free/local animation.
```

## DF-style features to borrow

### Nested maps

Do not represent the world at one uniform simulation resolution. Open more detail only when needed.

### Z/layer thinking

Use layers for infrastructure, not just height:

```text
surface roads
buried water/sewer/pipeline
power transmission
elevated rail/bridges
terrain/slope
administrative/service overlays
```

### Semantic cells

Cells should represent meaningful infrastructure state:

```text
road_segment
warehouse_yard
loading_bay
construction_site
utility_corridor
residential_block
commercial_service_node
industrial_demand_node
river_crossing
resource_deposit
```

### Legends/provenance mode

DF's world feels alive because places have history. This project should use provenance as game-facing history.

Examples:

```text
This town grew because power reliability exceeded 90% for 30 days.
This warehouse became a bottleneck after the quarry opened.
This road segment failed because construction crews could not reach the staging node.
This commercial district declined because delivery reliability fell below threshold.
```

## Physical player representative

Question:

> Would it be too much to make the user have a physical representation to do surveying and negotiations?

Answer:

Not inherently, but it should be an **optional embodiment layer**, not the main control model.

The risk is turning an infrastructure/logistics sim into a walking simulator. The benefit is that surveying and negotiation can make the world feel grounded and give the player a human-scale relationship with the graph.

### Recommended framing

The player is not a god cursor only. The player can dispatch or inhabit a **field representative**.

Possible titles:

- surveyor
- project manager
- field engineer
- municipal liaison
- company rep
- utility planner
- construction superintendent

The representative is a unit with limited abilities that unlocks or improves information, approvals, and local trust.

## Surveying mechanic

### Purpose

Surveying should reveal or validate information that is otherwise uncertain.

Examples:

```text
terrain slope accuracy
soil/rock quality
river crossing feasibility
utility corridor difficulty
land ownership constraints
environmental/community concerns
road access quality
hidden resource quality
construction risk
```

### Representation

A survey can be a graph action:

```text
SurveyTask
  starts at access node
  follows road/path/survey route
  visits target cells/features
  produces SurveyReport node
  updates confidence/provenance on terrain/features
```

### Gameplay output

Surveying does not need twitch movement. It can produce better planning data:

```text
Before survey:
  bridge cost estimate: $80k-$240k
  soil confidence: low
  crossing risk: unknown

After survey:
  bridge cost estimate: $145k-$170k
  soil confidence: high
  crossing risk: moderate
```

### Why this fits the graph model

Surveying creates provenance:

```text
Feature -> SURVEYED_BY -> SurveyTask
SurveyReport -> VALIDATES -> TerrainClaim
SurveyReport -> GENERATED_BY -> FieldRepresentative
TerrainClaim -> CONFIDENCE -> 0.88
```

This is strongly aligned with the broader Archolith-style theme: generated/known facts should have provenance and confidence.

## Negotiation mechanic

### Purpose

Negotiation should control permissions, costs, deadlines, and relationships.

Possible negotiation targets:

- town council
- landowner
- utility authority
- district manager
- industrial customer
- neighborhood group
- environmental regulator
- construction contractor
- rail/road authority

### Negotiation outputs

```text
right_of_way granted
construction window approved
temporary road access granted
subsidy offered
rate agreement signed
community opposition reduced
required mitigation added
inspection delay imposed
```

### Representation

Negotiation can be modeled as graph constraints, not RPG dialogue trees only.

```text
NegotiationTask
  actor: field representative
  target: town council / landowner / authority
  issue: right_of_way / permit / subsidy / service agreement
  inputs: reputation, reliability history, local impact, prior promises
  outputs: agreement node, constraint changes, relationship changes
```

Example graph changes:

```text
Agreement -> GRANTS -> RightOfWay
Agreement -> APPLIES_TO -> RoadCorridor42
Town -> TRUSTS -> Company
Constraint -> REQUIRES -> NoiseMitigation
```

### UI style

Keep negotiation mostly panel-driven:

- show stakeholder demands
- show likely outcomes
- show tradeoffs
- let the player choose offer terms
- optionally show the representative visiting the location

Avoid making negotiation depend on walking to every NPC unless that is a deliberate genre shift.

## Embodiment levels

Use this as a design dial.

### Level 0 — god cursor only

No representative.

Pros:

- simplest
- clean sim focus
- best for infrastructure planning

Cons:

- less grounded
- fewer human-scale interactions

### Level 1 — dispatchable representative

The player assigns a representative to survey/negotiation tasks. The unit appears on the graph and consumes time.

Pros:

- grounded without derailing the sim
- supports travel time and access constraints
- easy to integrate into graph movement

Cons:

- less personal than direct control

Recommended baseline.

### Level 2 — inspectable/controllable representative

The player can click into a local map and directly move the representative for inspections, meetings, or site walks.

Pros:

- immersive
- makes local maps feel real
- good for special events

Cons:

- risks slowing gameplay
- needs more UI/animation/content

Use sparingly.

### Level 3 — avatar-first gameplay

The player must physically travel to survey and negotiate.

Pros:

- strong identity and immersion

Cons:

- likely too much for this project
- turns the game into a different genre
- adds pathing, animation, interaction, and pacing burden

Not recommended for MVP.

## Recommended decision

Use **Level 1 as default**:

> The player has one or more dispatchable field representatives who move through the graph to perform surveys, inspections, and negotiations. Direct physical control is optional and reserved for special local-map interactions later.

This keeps the infrastructure sim central while adding grounded friction.

## Why a representative helps

A field representative gives a human-scale reason for incomplete information.

Without surveying:

```text
The player sees all terrain truth immediately.
```

With surveying:

```text
The player sees estimates and confidence levels until someone physically validates them.
```

That creates good gameplay:

- do you build quickly with bad data?
- do you pay/time-cost to survey first?
- do you negotiate right-of-way before designing the corridor?
- do you dispatch the rep to the town or the construction site?
- do you risk a cost overrun from unknown terrain?

## MVP version

Implement only this:

### FieldRepresentative node

```text
FieldRepresentative
  id
  name
  location_node
  availability
  skills: surveying, negotiation, inspection
```

### SurveyTask node

```text
SurveyTask
  target_feature
  route_required
  duration
  output_confidence_delta
  status
```

### NegotiationTask node

```text
NegotiationTask
  target_stakeholder
  issue
  duration
  terms
  outcome
  status
```

### UI

- assign representative to task
- show route/time
- show current task
- show produced report/agreement
- no direct movement control yet

## Example gameplay loop

```text
Player wants to build a transmission corridor to a town.

1. Draw proposed corridor.
2. Game marks unknowns: slope confidence low, land access unknown, river crossing uncertain.
3. Player dispatches surveyor.
4. Surveyor travels on existing road graph, then walks/surveys proposed segment.
5. Survey report narrows cost and reveals one difficult crossing.
6. Player dispatches representative to town council / landowner.
7. Negotiation grants right-of-way but adds mitigation requirement.
8. Construction plan updates with known constraints.
```

This is a strong fit for the graph/provenance direction.

## Open questions

- Is the representative a single player avatar or a staff/team resource?
- Can multiple reps exist later?
- Does the player ever directly control a rep, or only dispatch them?
- Can failed negotiations create long-term political/community constraints?
- Do surveys expire or become stale after terrain/work changes?
- Can contractors perform surveys/negotiations instead of the player company?

## Recommendation for project plan

Add this as an optional design pillar:

```text
Survey and negotiation are represented as graph tasks performed by dispatchable field representatives. These tasks generate provenance-bearing reports, agreements, and constraints that affect infrastructure planning.
```

Keep it out of the MVP renderer until the graph/world scaffold works.
