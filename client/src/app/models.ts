export type RGB = [number, number, number];
export type Params = Record<string, unknown>;

export type ParamType = 'color' | 'colors' | 'number' | 'select' | 'boolean';

export interface ParamSchema {
  key: string;
  type: ParamType;
  label: string;
  default: unknown;
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
  min_items?: number;
  max_items?: number;
  help?: string;
}

export interface AnimationDef {
  name: string;
  label: string;
  description: string;
  category: string;
  params: ParamSchema[];
  preview: RGB[];
}

export interface TreeConfig {
  numPixels: number;
  pin: string;
  pixelOrder: string;
  gamma: number;
  fps: number;
  layout: string;
  rings: number[];
  simulated: boolean;
}

export interface RgbState {
  power: boolean;
  animation: string | null;
  params: Params;
  speed: number;
  brightness: number;
  running: boolean;
  config: TreeConfig;
}

export interface Preset {
  id: string;
  name: string;
  animation: string;
  params: Params;
  speed?: number;
  brightness?: number;
}

export interface Palette {
  name: string;
  colors: string[];
}

export const PALETTES: Palette[] = [
  { name: 'Classic', colors: ['#ff0000', '#00ff00', '#f500f5', '#ffff00', '#0078ff'] },
  { name: 'Red & Green', colors: ['#ff0000', '#00c800'] },
  { name: 'Candy Cane', colors: ['#ff0000', '#ffffff'] },
  { name: 'Warm & Gold', colors: ['#ffa046', '#ffffff', '#ffaa00'] },
  { name: 'Winter', colors: ['#005aff', '#78c8ff', '#ffffff'] },
  { name: 'Aurora', colors: ['#00ff78', '#00a0ff', '#8c00ff', '#00ffc8'] },
  { name: 'Hanukkah', colors: ['#0038a8', '#ffffff', '#8cb4ff'] },
  { name: 'Ember', colors: ['#ff3c00', '#ffaa00', '#ff0000'] },
  { name: 'Rainbow', colors: ['#ff0000', '#ffaa00', '#ffff00', '#00ff00', '#0066ff', '#aa00ff'] },
  { name: 'Pastel', colors: ['#ffb3ba', '#baffc9', '#bae1ff', '#ffffba'] },
];

export function rgbToHex(rgb: unknown): string {
  if (typeof rgb === 'string') { return rgb; }
  const [r, g, b] = (Array.isArray(rgb) ? rgb : [0, 0, 0]).map(v => Math.max(0, Math.min(255, Math.round(Number(v) || 0))));
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

export function hexToRgb(hex: string): RGB {
  const s = hex.replace('#', '');
  const full = s.length === 3 ? s.split('').map(c => c + c).join('') : s;
  return [parseInt(full.slice(0, 2), 16) || 0, parseInt(full.slice(2, 4), 16) || 0, parseInt(full.slice(4, 6), 16) || 0];
}

export function randomHex(): string {
  // Bright, saturated random color (random hue, full saturation).
  const h = Math.random();
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const q = 1 - f;
  const [r, g, b] = [[1, f, 0], [q, 1, 0], [0, 1, f], [0, q, 1], [f, 0, 1], [1, 0, q]][i % 6];
  return rgbToHex([r * 255, g * 255, b * 255]);
}
