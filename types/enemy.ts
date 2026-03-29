export type EnemyType = "boss" | "elite" | "normal";
export type EncounterPool = "weak" | "normal";
export type ActKey = "act1a" | "act1b" | "act2" | "act3";

export interface BiomeMeta {
  label: string;
  weakPoolCount: number;
  normalPoolFrom: number;
}

export interface Move {
  turn: string;
  action: string;
  effect: string;
  damage: string;
}

export interface Phase {
  name: string;
  moves: Move[];
}

export interface Ability {
  name: string;
  description: string;
}

export interface Enemy {
  id: string;
  name: string;
  nameEn: string;
  act: ActKey;
  biome: string;
  biomeEn: string;
  type: EnemyType;
  encounterPool?: EncounterPool;
  hp: string;
  imageUrl: string;
  abilities: Ability[];
  phases: Phase[];
  tips: string;
}

export interface EnemiesData {
  biomeMeta: Record<ActKey, BiomeMeta>;
  enemies: Enemy[];
}
