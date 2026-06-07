# Combat system reference

This is a planning reference based on the official wiki page for the Heroes of
Might and Magic: Olden Era combat system. It is not a canonical project
requirements document. Promote behavior into `doc/requirements.md` only when it
is committed enough to test.

Source: https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Combat_System

Reviewed: 2026-06-06

Wiki page revision noted during review: oldid `19877`, last edited
2026-05-24 03:16.

## Scope notes

The page describes combat at a gameplay-guide level. Several mechanics are
clear enough to guide future model boundaries, but many details still need
confirmation before they become simulator behavior.

One wording mismatch is worth preserving: the wiki describes battles as taking
place on rectangular battlefields. This project already treats the canonical
battlefield as flat-top staggered rows with row lengths
`[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`. Keep the project requirement as
authoritative unless later evidence changes the battlefield model.

## Battlefield and battle state

* Battles use hex spaces, and unit stacks occupy battlefield hexes.
* Armies start on opposing sides of the battlefield.
* Obstacles block unit occupancy and can shape tactical routes.
* Siege battles may replace a large part of the battlefield with city walls.
* Walls appear to be destructible and may become passable after destruction.

Planning implications:

* The current split between `Battlefield`, obstacles, deployment zones, and
  occupancy still fits the source.
* Siege walls should probably be modeled as field configuration with mutable
  state later, because walls begin as blockers but can be destroyed.
* Do not fold walls into the current obstacle model until siege behavior is in
  scope.

## Rounds and turn order

* Combat proceeds in rounds.
* Each unit stack can act once per round unless modified by morale, waiting, or
  other effects.
* A round ends after all unit stacks from both sides have acted or used an
  ability.
* Turn order is primarily driven by initiative.
* Speed is a tie-breaker and separately controls movement distance.
* If initiative and speed tie, priority alternates between sides rather than
  sorting all units from one side first.
* The first round appears to favor the attacker for exact initiative and speed
  ties.
* Odd-numbered rounds may favor the attacker and even-numbered rounds may favor
  the defender, but the page phrases this as observed behavior rather than a
  settled rule.
* Allied stack ordering can depend on army-slot order when units are otherwise
  tied.

Planning implications:

* Unit definitions need both initiative and speed eventually, but Milestone 2
  only needs speed per the roadmap.
* A future turn-order model will need attacker and defender battle roles.
* Army-slot order is a separate input from battlefield placement.
* Tie-breaking should be delayed until turn-order work; do not bake it into the
  Unit model.

Open questions:

* Is the observed odd/even round tie-breaker stable game behavior?
* Does waiting affect only the current round or also later initiative ordering?

## Waiting and skipping

* Waiting moves a stack's action later in the same round.
* Waiting appears to reverse initiative order among waiting units, making high
  initiative units act after lower initiative units in the wait phase.
* Skipping ends the stack's current turn without movement or action.

Planning implications:

* Waiting and skipping belong to future battle/turn state, not unit
  definitions.
* Waiting likely needs an explicit action state so a stack cannot wait more than
  once in the same round unless the real rules allow it.

## Attack types

The page identifies three basic attack categories:

* Melee attacks target adjacent opposing units and usually provoke counterattacks.
* Long-reach attacks target enemies exactly one hex away and do not provoke
  counterattacks.
* Ranged attacks can target enemies across the battlefield, but adjacent enemies
  suppress ranged attacking and force movement or melee instead.

Ranged damage falls off after range 3. Each extra hex reduces damage by 10%,
with a maximum 50% reduction.

Planning implications:

* Attack category is unit-definition data.
* Counterattack behavior belongs to combat-action resolution.
* Ranged adjacency lockout needs occupancy and neighbor lookup.
* Ranged falloff needs distance math, so it belongs after range and movement
  math.

Open questions:

* Does "exactly one hex away" for long-reach mean one empty hex between units or
  a target at hex distance 2? The wiki wording is ambiguous because melee
  adjacency is also one hex away in ordinary hex-distance language.
* Do large or multi-hex units change adjacency and long-reach targeting?

## Damage model

Base damage is affected by attacker attack and defender defense. The page gives
the attack/defense modifier as:

```text
(20 + ATK) / (20 + DEF)
```

The broader damage range formula is:

```text
unit count
* unit damage
* attack/defense modifier
* all-type damage modifiers
* tag-based damage modifiers
* other independent modifiers
* luck modifier
```

Additional notes from the page:

* Hero attack and defense are added to creature attack and defense.
* Attack/defense modifier has no upper limit and a lower limit of zero.
* Final damage always deals at least 1 point.
* All-type modifiers and tag-based modifiers are grouped differently.
* Tag-based modifiers are additive within the same category and multiplicative
  across categories.
* Tag-based damage reduction has a minimum resulting multiplier of 10%.
* Attacker-side and defender-side tag modifiers are calculated separately.
* Damage rounding examples suggest normal nearest-integer behavior, but this
  needs executable confirmation before implementation.

Planning implications:

* Unit definitions eventually need attack, defense, damage range, and attack
  tags.
* Damage resolution should be its own focused module when Milestone 5 begins.
* Damage modifiers need typed categories rather than an unstructured list of
  percentages.
* The simulator should avoid implementing partial damage math until target
  examples are available as tests.

Open questions:

* What exact rounding rule is used for `.5` values?
* Is the 10% tag-based floor applied per tag group, per attacker/defender side,
  or after all tag-based reduction categories are combined?
* Which modifier category should range penalty use in code: independent
  modifier, ranged tag modifier, or a dedicated range modifier?

## Spells, hero abilities, and creature abilities

* Heroes can cast spells that damage units, apply positive or negative effects,
  create battlefield obstacles, or otherwise alter battle state.
* Spell points come from hero knowledge.
* Spells have tiers from 1 to 5.
* Spell effectiveness can vary by hero magic skill.
* Creature and hero abilities can also affect the battlefield.
* Abilities use focus points rather than spell points.
* Focus is generated through battle events such as attacking or being attacked,
  with additional sources from skills and spells.

Planning implications:

* Spells and abilities should remain deferred until actions and battle state
  exist.
* Created obstacles imply obstacle state may eventually be dynamic, not only
  static field configuration.
* Focus and spell points belong to battle resources, not unit definitions.

## Morale

* Positive morale can let a unit act twice.
* Negative morale can make a unit lose its action for the round.
* Each point of positive morale gives a 4% chance of an extra action.
* Each point of negative morale gives a 4% chance of losing the action.
* Creature types constrain morale ranges.
* Mixed-faction armies affect morale: a single-faction army gains morale, while
  each additional faction reduces morale.
* Extra morale bonuses can still matter when counteracting opposing morale
  penalties, even if the effective creature range is capped.

Planning implications:

* Unit definitions eventually need creature type and faction.
* Army composition matters, so morale calculation depends on army-level state.
* Morale effects belong to turn-order/action scheduling, not raw unit data.

## Luck

* Each point of luck gives a 6% chance of a lucky or unlucky strike.
* Lucky strikes deal 50% more damage.
* Unlucky strikes deal 50% less damage.
* Creature types constrain luck ranges.
* Skills, laws, artifacts, map objects, and other effects can modify luck.

Planning implications:

* Luck affects damage resolution.
* Luck should be modeled as an input to damage calculation, not embedded into
  base damage.
* Creature type and effect systems are prerequisites for faithful luck caps.

## Milestone impact

### Milestone 2: Unit model

Useful now:

* Unit identity.
* Unit side through battle stack state.
* Unit stack count.
* Speed.
* Future-facing fields should leave room for initiative, faction, creature type,
  attack category, attack, defense, and damage range.

Avoid now:

* Damage resolution.
* Morale and luck probability.
* Turn-order tie-breaking.
* Ability and spell effects.
* Siege walls.

### Milestone 3: Range and movement math

Relevant later:

* Speed determines movement distance.
* Ranged attacks need distance for range penalty.
* Ranged adjacency lockout needs neighbor adjacency checks.
* Long-reach targeting needs a clarified distance rule.

### Milestone 5: Combat actions

Relevant later:

* Attack category and counterattack rules.
* Damage formula and modifier grouping.
* Luck-based damage changes.
* Morale-based extra or lost actions.
* Ability resources and action alternatives.

## Candidate terms for glossary

These terms appear likely to become recurring domain vocabulary:

* Ability
* Attack category
* Attacker
* Counterattack
* Creature type
* Defender
* Focus point
* Initiative
* Luck
* Morale
* Round
* Spell point
* Turn order
* Unit definition
* Unit stack
