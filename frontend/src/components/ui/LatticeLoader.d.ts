import type { CSSProperties, ReactNode } from "react";

export interface LatticeCustomPattern {
  cells: Array<number | null>;
  loop?: number;
  scale?: number;
  lit?: 0.25 | 0.35 | 0.45 | 0.62;
}

export type LatticePatternName =
  | "arrow"
  | "dots"
  | "orbit"
  | "ripple"
  | "snake"
  | "spiral"
  | "sweep"
  | "spin"
  | "rain"
  | "pulse";

export interface LatticeLoaderProps {
  label?: string;
  doneLabel?: string;
  errorLabel?: string;
  status?: "working" | "done" | "error";
  pattern?: LatticePatternName | LatticeCustomPattern;
  grid?: 3 | 4;
  shape?: "square" | "round";
  color?: string;
  doneColor?: string;
  errorColor?: string;
  cellSize?: number;
  gap?: number;
  fontSize?: number;
  step?: number;
  idleOpacity?: number;
  glow?: boolean;
  glowColor?: string;
  showTimer?: boolean;
  elapsed?: number;
  className?: string;
  style?: CSSProperties;
}

export default function LatticeLoader(props: LatticeLoaderProps): ReactNode;
