import type { CSSProperties, ReactNode } from "react";

export type StatusMarkState =
  | "pending"
  | "running"
  | "done"
  | "failed"
  | "cancelled";

export interface StatusMarkProps {
  status?: StatusMarkState;
  progress?: number;
  label?: ReactNode;
  color?: string;
  doneColor?: string;
  errorColor?: string;
  size?: number;
  strokeWidth?: number;
  dashes?: number;
  fontSize?: number;
  spinDuration?: number;
  arcLength?: number;
  drawDuration?: number;
  fillOpacity?: number;
  strike?: boolean;
  strikeDelay?: number;
  className?: string;
  style?: CSSProperties;
}

export default function StatusMark(props: StatusMarkProps): ReactNode;
