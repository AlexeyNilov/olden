# User stories

## User story format

Write each story in the form:

> **As a** `<user_type>`, **I want** `<goal>` **so that** `<benefit>`.

This captures:

* **Who** the user is
* **What** they want to achieve
* **Why** it matters

## Glossary

* **Battlefield:** The combat field made of flat-top hexes arranged in 11 staggered rows.
* **Hex coordinate:** A zero-based `(column, row)` address for one battlefield hex.
* **Field configuration:** Static battlefield data such as obstacles, and deployment zones.
* **Battle state:** Dynamic combat data such as unit occupancy.

## Actual stories

* **As a** combat simulator developer, **I want** a deterministic battlefield model **so that** movement, targeting, placement, and combat-state rules can be tested against a stable field topology.
