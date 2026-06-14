# Combat System Reference

Source: [Combat System - Heroes of Might and Magic: Olden Era Official Wiki](https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Combat_System)

License: CC BY-SA 4.0 unless otherwise noted on the source page.

Retrieved: 2026-06-08. Source page last edited: 2026-05-24 03:16.

This file is a Markdown conversion of the external wiki reference. It is
reference material for combat-action planning; committed simulator behavior
belongs in `doc/requirements.md`.

## Overview

Battles in Heroes of Might and Magic take place on rectangular battlefields,
with individual hex spaces representing spaces a unit can occupy. Your army is
positioned on one side, with the enemy army on the opposite. Most battles will
have various objects strewn about which represent hex spaces that may not be
occupied by unit stacks. These obstacles can act as choke points to funnel enemy
units though, or as natural walls for ranged units to position to protect
themselves from enemy melee units.

When besieging an enemy city, roughly half of the battlefield will be taken up
by the defender's city walls which must be destroyed before becoming passable by
ground troops.

## Turn Order And Movement Speed

Combat is divided into rounds. During each round, unit stacks take turns moving
across the battlefield and attacking enemy units. A round ends once all units
from both sides have acted or used their abilities.

Across the top of the battlefield interface, there will be a row of icons
representing every creature stack in the battle and the order in which they will
be taking their turns during the current round. This order is mostly determined
by a creature's initiative and speed values.

Initiative determines how soon a creature can act during battle, while speed
indicates how far a creature is able to move during its turn. Most units will
have their initiative and speed values be fairly close to each other, but there
are some examples of creatures who are able to act very soon in combat but
cannot move very far, and creatures with low initiative but very high speed.

If there is a tie in initiative, turn priority will go to creatures with the
higher speed value. If multiple creature stacks have equal initiative and speed
values, the turn order will shift back and forth between either side. With
regard to allied troops that are first to act, the move order will additionally
be sorted by how they appear in the order they appear in the hero's army slots,
from left to right. This applies even if units are arranged differently on the
battlefield during the Tactics phase.

After all unit stacks on both sides have had an opportunity to move, attack, or
take another action, the battle will move on the next round.

Note: In the first round of battle, if both sides have creatures with identical
initiative and speed values, the tie break for moving first will go to the
attacker. It appears that odd numbered rounds will give initiative priority to
the attacker, while defenders are given priority on even-numbered rounds.

Considering the previous example, if the attacker also had another creature with
higher initiative, that creature would take the first action, and then the next
action would go to the defending side, and then back to the attacker, and so on.
It appears that the game tries to give equal opportunity to act to both sides as
much as possible. If the stack of Griffins were to die, then the round order
would change to have the attacker's Guard Captains take the first action.

## Waiting And Skipping Turns

Other than attacking or using abilities, unit stacks also have two additional
options to take when it is their turn.

* Wait: The Wait option will push that unit's action to the end of the turn
  order. Once a unit has taken this option, their initiative will essentially be
  flipped, with the highest Initiative units taking their turn after everything
  else has acted. Having your units wait during battles can be very
  advantageous, as you can force lower initiative to take their turn first,
  either having to stay in place or move towards you, allowing you to take the
  first attack.
* Skip Turn: This option will simply end your unit's turn without them having
  taken an action or moving. While it is generally a good idea to always be
  maneuvering your units into better position or attacking your enemy's units,
  it is sometimes the best move to do nothing.

Sometimes you will want your weaker units to not attack a powerful enemy stack
because the retaliation will greatly hurt or kill them, or perhaps you have a
small stack of a weak unit positioned next to an enemy ranged unit to prevent
them from shooting at your more powerful stack of creatures.

Other times you may be blocking your ranged units from being attacked by having
small stacks of weaker creatures standing in the way of the enemy, and you want
them to waste their actions killing off them instead of attacking the ranged
units behind them.

## Attacking

Units can use one of three basic attack types on the battlefield:

* Melee Attacks: Used against units in adjacent hexes. Will trigger a
  counterattack, in most cases.
* Long Reach Attacks: Target enemy units exactly one hex away. These attacks do
  not provoke a counterattack. Units with Long Reach attacks can often also
  engage in melee if needed.
* Ranged Attacks: Can target any enemy on the battlefield, except when an enemy
  is in an adjacent hex; in that case, the unit may only move or perform a melee
  attack. Ranged attacks deal reduced damage if the target is more than three
  hexes away: damage decreases by 10% per additional hex, up to a maximum of 50%
  reduction.

## Damage

When a creature attacks another, the damage inflicted is increased by the
attacker's Attack value and reduced by the defender's Defense value.

The Attack and Defense of the hero is added to the Attack and Defense of the
creatures under their command.

The damage is multiplied by `(1 + 5% * attacker's ATK)`, then divided by
`(1 + 5% * defender's DEF)`. Another equivalent formula is:

```text
(20 + ATK) / (20 + DEF)
```

For example, if a Swordsman with 4 Attack and 4 Defense were to attack a
Skeleton with 4 Attack and 1 Defense, the modifier would be `(20 + 4) / (20 +
1)`, for a result of `1.14`. This means that when the Swordsman attacks the
Skeleton, it will deal `2-3` damage, multiplied by `1.14`. This results in a
final damage calculation of `2.28-3.42`. Damage is rounded up to next whole
number if over `.5`, and rounded down if under `.5`.

Damage modifier formula:

```text
((1 + 5% * ATK) / (1 + 5% * DEF)) - 1
```

| DEF \ ATK | 0 | 1 | 2 | 3 | 4 | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0% | +5% | +10% | +15% | +20% | +25% | +50% | +75% | +100% | +125% | +150% | +175% | +200% |
| 1 | -5% | 0% | +5% | +10% | +14% | +19% | +43% | +67% | +90% | +114% | +138% | +162% | +186% |
| 2 | -9% | -5% | 0% | +5% | +9% | +14% | +36% | +59% | +82% | +105% | +127% | +150% | +173% |
| 3 | -13% | -9% | -4% | 0% | +4% | +9% | +30% | +52% | +74% | +96% | +117% | +139% | +161% |
| 4 | -17% | -12% | -8% | -4% | 0% | +4% | +25% | +46% | +67% | +88% | +108% | +129% | +150% |
| 5 | -20% | -16% | -12% | -8% | -4% | 0% | +20% | +40% | +60% | +80% | +100% | +120% | +140% |
| 10 | -33% | -30% | -27% | -23% | -20% | -17% | 0% | +17% | +33% | +50% | +67% | +83% | +100% |
| 15 | -43% | -40% | -37% | -34% | -31% | -29% | -14% | 0% | +14% | +29% | +43% | +57% | +71% |
| 20 | -50% | -48% | -45% | -43% | -40% | -38% | -25% | -12% | 0% | +12% | +25% | +38% | +50% |
| 25 | -56% | -53% | -51% | -49% | -47% | -44% | -33% | -22% | -11% | 0% | +11% | +22% | +33% |
| 30 | -60% | -58% | -56% | -54% | -52% | -50% | -40% | -30% | -20% | -10% | 0% | +10% | +20% |
| 35 | -64% | -62% | -60% | -58% | -56% | -55% | -45% | -36% | -27% | -18% | -9% | 0% | +9% |
| 40 | -67% | -65% | -63% | -62% | -60% | -58% | -50% | -42% | -33% | -25% | -17% | -8% | 0% |

Below is a table showing common Attack modifiers and how they impact the
resulting damage.

| Damage Modifiers | Damage Formula |
| --- | --- |
| Basic Modifier | `(20 + ATK) / (20 + DEF)` = `(1 + 5% * ATK) / (1 + 5% * DEF)` |
| Basic Modifier + Offense skill | `BASIC MODIFIER * [1.15; 1.20; 1.25]` for 15%, 20%, or 25% damage bonus |
| Basic Modifier + defending creature has Defense skill | `BASIC MODIFIER * [0.85; 0.80; 0.75]` for 15%, 20%, or 25% damage reduction |
| Overall Formula for Damage Calculations | `(20 + ATK) / (20 + DEF) * Bonus1 * Bonus2 * ... * BonusN * Crit` = `((1 + 5% * ATK) * Bonus1 * Bonus2 * ... * BonusN * Crit) / (1 + 5% * DEF)` |

As more and more modifiers get added into the mix, however, calculating damage
can be more complicated, as bonuses to specific kinds of damage, known as
tag-based damage, are grouped differently than bonuses that affect all types of
damage, known as all-type damage.

The full formula is:

```text
(Unit Count)
* (Unit Damage)
* (Attack / Defense Modifier)
* (All-type Damage Modifiers)
* (Tag-based Damage Modifiers)
* (Other independent Modifiers)
* (Luck Modifier)
= Damage Range
```

* All-Type Damage Modifiers: The parameters are `inAllDmgMod` or `outAllDmgMod`
  in the data files.
* Examples of All-Type Damage Modifiers: Radiant Armor, Naira's Way, Adaptation:
  Attack / Defense, and the Scorpion ability.
* Tag-Based Damage: The parameters are `inDmgMods` or `outDmgMods` in the data
  files.
* Examples of Tag-Based Damage: Offense / Defense skills, Blessing spell,
  Favorable Wind / Optical Illusion.
* If the spell, effect, or skill calls out specific kinds of damage, then it is
  tag-based. If it does not specify a particular source, then it should fall
  under the all-type category.
* Other independent Modifiers: Other parameters, such as range penalty, walls
  reducing ranged damage taken, and extra damage against summoned units, Apex
  Predator, Jousting Bonus, and Luck.

Other notes:

* The Attack / Defense Modifier has no upper limit, with a lower limit of `0`.
* Damage Reduction from the All-type Damage Reduction category has no upper
  limit.
* Tag-based damage bonuses/reductions categorized by tags are added within the
  same category and then multiplied across different categories, with the
  minimum result being at least `10%`.
* Tag-based modifiers for attackers and defenders are calculated separately.
* Regardless of damage adjustments, the final result will deal at least `1`
  point of damage.

### Calculation Examples

Example 1:

| Unit count | Unit Damage | A/D Modifier | All-type Modifiers | Attacker Tag-based | Defender Tag-based | Other independent Modifiers |
| --- | --- | --- | --- | --- | --- | --- |
| `100` | `3~4` | `(9 + 20) / (8 + 20)` | `(1 + 0.1) * (1 - 0.1)` | `(1 + 0.2) * (1 + 0.15)` | `(1 - 0.25) * (1 - 0.2 - 0.3)` | `0.5 * 0.7` |
| - | - | `1.035714` | Fields of Serenity: `+10% / -10%` | Basic Damage: `+20%` (Advanced Offense); Ranged Damage: `+15%` (Archery) | Basic Damage: `-25%` (Expert Defense); Ranged Damage: `-20%` (Cover); `-30%` (Ranged Defense I) | Wall: `-50%`; Attack range: `-30%` at 7 tiles |

```text
100 * (3 ~ 4) * (9 + 20) / (8 + 20)
* ((1 + 0.1) * (1 - 0.1))
* ((1 + 0.2) * (1 + 0.15))
* ((1 - 0.25) * (1 - 0.2 - 0.3))
* 0.7 * 0.5
= 55.71532838 ~ 74.28710451 -> 56 ~ 74
```

Example 2:

| Unit count | Unit Damage | A/D Modifier | All-type Modifiers | Attacker Tag-based | Defender Tag-based | Other independent Modifiers |
| --- | --- | --- | --- | --- | --- | --- |
| `100` | `4` | `(9 + 20) / (8 + 20)` | `(1 + 0.1) * (1 - 0.1 - 0.3)` | `(1 + 0.20) * (1 + 0.35) * (1 + 0.15 + 0.5)` | `(1 - 0.25) * (1 - 0.2 - 0.3 - 0.25)` | `0.5 * 0.7` |
| - | Masterful Blessing | `1.035714` | Fields of Serenity: `-10% / -10%`; Radiant Armor: `-30%` | Basic Damage: `+20%` (Advanced Offense); Normal Damage: `+35%` (Blessing); Ranged Damage: `+15%` (Archery); `+50%` (Favorable Wind) | Basic Damage: `-25%` (Expert Defense); Ranged Damage: `-20%` (Cover); `-30%` (Ranged Defense I); `-25%` (Optical Illusion) | Wall: `-50%`; Attack range: `-30%` at 7 tiles |

```text
100 * 4 * (9 + 20) / (8 + 20)
* ((1 + 0.1) * (1 - 0.1 - 0.3))
* ((1 + 0.20) * (1 + 0.35) * (1 + 0.15 + 0.5))
* ((1 - 0.25) * (1 - 0.2 - 0.3 - 0.25))
* 0.7 * 0.5
= 47.96364375 -> 48
```

An edge case that triggers the tag-based damage cap:

Initial Attack / Defense Damage modifier:

```text
(36 + 20) / (12 + 20) = 56 / 32 = 1.75
```

Tag-Based Damage Modifiers:

* Ranged Mastery: Friendly creatures deal `+10%` and take `-10%` ranged and long
  reach damage.
* Cover (Defense Subskill): Friendly creatures take `-20%` damage from ranged
  and long reach attacks.
* Expert Defense: Friendly creatures take `-25%` damage from basic attacks.
* Aegis: This creature and adjacent friendly creatures take `-30%` ranged
  damage.
* Ranged Defense III (Creature Passive): Takes `-60%` ranged damage.
* Optical Illusion: `-50%` ranged damage taken.

Tag-Based Damage Modifier total:

```text
(1 - 25%) * (1 - 10% - 20% - 30% - 60% - 50%)
= -52.5% -> 10%
```

This means `-90%` damage, because the result has to be `10%` at minimum.

All-Type Damage Modifiers:

* Radiant Armor: Takes `-40%` damage from all sources.

So, with 100 Archangels attacking the Animated Armor:

* Archangel attack / defense modifier against Animated Armor is `1.75`.
  Archangel damage range is `50-75`.
* Multiplied with damage modifier, the damage range becomes `8,750-13,125`.
* Next comes all-type damage modifiers. All modifiers get added together and
  then multiplied with the damage range. There are no all-type damage bonuses,
  with one all-type damage reduction of `40%`, from Radiant Armor, so that
  becomes `5,250-7,875`.
* Next is the tag-based bonuses and reductions. There are no tag-based bonuses,
  and a combined `-180%` from tag-based damage reductions, which gets capped at
  `90%` damage reduction. Multiplying by `.10` gives `525-787.5`, which becomes
  `788`, matching the final damage result on the screen.

Full formula written out with numbers from the example:

```text
(100) * (50 - 75) * (1.75) * (0.6) * (0.1)
= 525 - 787.5
```

## Spells And Hero Abilities

Moving and attacking with your units is not the only thing you can do while in
Combat. Your Heroes are also able to cast powerful spells which can alter the
flow of battle in your favor. Spells can damage enemy units directly, bestow
positive effects on your units and negative effects on enemies, create obstacles
on the battlefield itself, and more. Spells require spell points in order to
cast them, which are determined based on your Hero's Knowledge stat.

Spells can range in tiers from `1-5`, and each tier of magic has increasingly
more effective spells belonging to it. As spells rise in tier, their cost in
spell points also rises, meaning that unless you have a very knowledgeable Hero,
you are going to have to weigh your choices in combat. Individual spells also
have their own levels of effectiveness that cause them to become more powerful
depending on how skilled your hero is at magic. A full breakdown of spellcasting
may be found on the wiki Spellcasting page.

## Creature Abilities

Aside from Spellcasting, Heroes and Creatures may also have access to several
different Abilities they may use during battle. An Ability is similar to a Spell
in that it is another way to interact with the battlefield, directly or
indirectly, but they are powered by something called Focus Points instead. Focus
is generated through the course of a battle by attacking and being attacked by
enemy creatures, by certain Sub-Skills heroes can learn, and through certain
kinds of Spells.

## Morale

Morale is a combat modifier from your hero that can impact how effective your
creatures are on the battlefield. Positive Morale will give your units a chance
to act twice in combat, while creatures with negative Morale may lose their
chance to act at all that round. Each point of positive Morale will grant a `4%`
chance to act twice during their turn, while each point of negative Morale will
have a `4%` chance for that creature to lose their action.

There are many different Creature Types in the game. Each one will have its own
potential range of Morale, with some types being completely unaffected by it,
while others can never go below zero. While you can theoretically stack up
Morale bonuses from many different sources, the effective cap for any creature
is limited by its type. These extra bonuses are not necessarily wasted, however.

Enemy heroes can have negative effects from Artifacts and other sources that
reduce the Morale of your army, and having extra sources of Morale can help to
counteract these effects.

Another thing that can influence creature morale is the number of different
factions in your army. Having all of your creatures belong to one faction will
give you `+1` to their morale, while each additional faction present in your army
will reduce morale by `-1`.

## Luck

Luck is the potential for a unit to deal extra damage, or reduced damage for bad
luck, during combat. Each point of luck will give a `6%` chance to get a Lucky
or Unlucky strike during battle. Creatures deal `50%` more damage on a Lucky
strike, and `50%` less damage on an unlucky strike. For a full description of
the combat formula, visit the Combat System page.

There are many different Creature Types in the game. Each one will have its own
potential range of Luck, with some types being completely unaffected by it, while
others can never go below zero. While you can theoretically stack up Luck
bonuses from many different sources, the effective cap for any creature is
limited by its type. These extra bonuses are not necessarily wasted, however.

Enemy heroes can have negative effects from Artifacts and other sources that
reduce the Luck of your army, and having extra sources of Luck can help to
counteract these effects.

There are many gameplay modifiers that can influence Morale and Luck, such as
Hero Skills, Faction Laws, and Artifacts. You may also receive temporary effects
from Map Objects that can increase or decrease these stats.

## See Also

* [Spellcasting](https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Spellcasting)
