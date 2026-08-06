# Architecture

Reunion Companion is divided into four layers.

## 1. Binary reader

Reads bytes and package contents without interpreting genealogy semantics.

## 2. Decoder

Converts known binary structures into typed intermediate records.

## 3. Object model

Represents people, families, events, places, notes, media, and sources independently of Reunion's storage format.

## 4. Consumers

Exports, publishing, validation, search, and AI features consume the object model.

## Safety boundary

No component writes to a Reunion family file.
