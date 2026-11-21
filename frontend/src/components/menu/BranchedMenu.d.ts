import type { ReactNode } from "react";
import type { IconSvgElement } from "@hugeicons/react";

export interface BranchedMenuChildItem {
  value: string;
  label: string;
  icon?: IconSvgElement | ReactNode;
}

export interface BranchedMenuSectionItem {
  label: string;
  value?: string;
  children?: BranchedMenuChildItem[];
}

export interface BranchedMenuProps {
  items?: BranchedMenuSectionItem[];
  defaultOpen?: number | number[];
  defaultActive?: string;
  onSelect?: (
    value: string,
    item: BranchedMenuChildItem | BranchedMenuSectionItem,
  ) => void;
  onToggle?: (index: number, isOpen: boolean) => void;
  color?: string;
  accentColor?: string;
  lineColor?: string;
  width?: number;
  rowHeight?: number;
  indent?: number;
  trunk?: number;
  radius?: number;
  lineWidth?: number;
  fontSize?: number;
  drawDuration?: number;
  foldDuration?: number;
  className?: string;
}

export default function BranchedMenu(props: BranchedMenuProps): ReactNode;
