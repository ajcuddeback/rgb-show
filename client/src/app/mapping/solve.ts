/**
 * Pure math for camera mapping. No Angular, no DOM - unit-testable in Node.
 *
 * Camera convention: angle index k sits at azimuth phi_k around the tree.
 * Angle 0 is "front" (camera on -Y looking at +Y). The camera's image-right
 * direction in world XY is r = (cos phi, sin phi); image-up is world +Z.
 * Walking to your right (as you face the tree) increases phi.
 */

export interface Blob2D { x: number; y: number; peak: number; }
export type Observation = Blob2D | null;
export type Point3 = [number, number, number];

/** Luma (0..255) of an RGBA buffer. */
export function luma(rgba: Uint8ClampedArray, w: number, h: number): Float32Array {
  const out = new Float32Array(w * h);
  for (let i = 0, j = 0; i < out.length; i++, j += 4) {
    out[i] = 0.299 * rgba[j] + 0.587 * rgba[j + 1] + 0.114 * rgba[j + 2];
  }
  return out;
}

/**
 * Find the single lit LED in `cur` relative to `dark` (both luma). Returns the
 * weighted centroid of the brightest spot, or null when nothing stands out.
 */
export function detectBlob(cur: Float32Array, dark: Float32Array, w: number, h: number, threshold = 35): Observation {
  const n = w * h;
  let sum = 0;
  let max = -1, maxI = 0;
  const diff = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const d = cur[i] - dark[i];
    const v = d > 0 ? d : 0;
    diff[i] = v;
    sum += v;
    if (v > max) { max = v; maxI = i; }
  }
  const mean = sum / n;               // global drift (auto-exposure, someone turned a lamp on)
  if (max - mean < threshold) { return null; }
  const mx = maxI % w, my = Math.floor(maxI / w);
  const r = Math.max(4, Math.round(Math.min(w, h) * 0.03));
  const cut = mean + (max - mean) * 0.4;
  let sx = 0, sy = 0, sw = 0;
  for (let y = Math.max(0, my - r); y <= Math.min(h - 1, my + r); y++) {
    for (let x = Math.max(0, mx - r); x <= Math.min(w - 1, mx + r); x++) {
      const v = diff[y * w + x] - cut;
      if (v > 0) { sx += x * v; sy += y * v; sw += v; }
    }
  }
  if (sw <= 0) { return { x: mx, y: my, peak: Math.min(1, (max - mean) / 255) }; }
  return { x: sx / sw, y: sy / sw, peak: Math.min(1, (max - mean) / 255) };
}

function percentile(vals: number[], p: number): number {
  if (!vals.length) { return 0; }
  const s = [...vals].sort((a, b) => a - b);
  const i = Math.min(s.length - 1, Math.max(0, Math.round((s.length - 1) * p)));
  return s[i];
}

export interface SolveResult {
  points: (Point3 | null)[];
  located: number;        // solved from >= 2 angles
  partial: number;        // solved from a single angle (depth guessed)
  missing: number;        // not seen at all - interpolated by the server
  outliers: number;       // rejected as reflections / noise
}

/**
 * Combine per-angle 2D observations into 3D points.
 * `views[k][i]` is the blob for LED i seen from angle k (or null), in pixel
 * coordinates of an image `w` x `h`. `azimuths[k]` is in degrees.
 */
export function solvePoints(views: Observation[][], azimuths: number[], w: number, h: number): SolveResult {
  const n = views[0]?.length ?? 0;
  const K = views.length;

  // Normalize each view independently: center horizontally on the median LED,
  // scale by the tree's apparent height so views taken at different distances agree.
  const norm: ({ u: number; v: number; wgt: number } | null)[][] = [];
  for (let k = 0; k < K; k++) {
    const obs = views[k];
    const us: number[] = [], vs: number[] = [];
    for (const o of obs) { if (o) { us.push((o.x - w / 2) / h); vs.push((h / 2 - o.y) / h); } }
    const cu = percentile(us, 0.5);
    const v0 = percentile(vs, 0.03), v1 = percentile(vs, 0.97);
    const scale = Math.max(1e-3, v1 - v0);
    norm.push(obs.map(o => o ? { u: ((o.x - w / 2) / h - cu) / scale, v: ((h / 2 - o.y) / h - v0) / scale, wgt: Math.max(0.05, o.peak) } : null));
  }

  const points: (Point3 | null)[] = new Array(n).fill(null);
  const views_used: number[] = new Array(n).fill(0);
  let located = 0, partial = 0, missing = 0;
  const lambda = 0.02;    // ridge term: keeps single-view solutions finite
  for (let i = 0; i < n; i++) {
    let a11 = lambda, a12 = 0, a22 = lambda, b1 = 0, b2 = 0, zs = 0, zw = 0, used = 0;
    for (let k = 0; k < K; k++) {
      const o = norm[k][i];
      if (!o) { continue; }
      const phi = (azimuths[k] * Math.PI) / 180;
      const c = Math.cos(phi), s = Math.sin(phi);
      a11 += o.wgt * c * c; a12 += o.wgt * c * s; a22 += o.wgt * s * s;
      b1 += o.wgt * c * o.u; b2 += o.wgt * s * o.u;
      zs += o.wgt * o.v; zw += o.wgt;
      used++;
    }
    if (used === 0) { missing++; continue; }
    const det = a11 * a22 - a12 * a12;
    const x = (a22 * b1 - a12 * b2) / det;
    const y = (a11 * b2 - a12 * b1) / det;
    points[i] = [x, y, zs / zw];
    views_used[i] = used;
    if (used >= 2) { located++; } else { partial++; }
  }

  // Lights seen from a single angle: the camera fixes their position along its
  // image-right axis but says nothing about depth. Adjacent lights on the wire
  // are inches apart, so take the depth from the nearest fully-located neighbors.
  for (let i = 0; i < n; i++) {
    if (views_used[i] !== 1 || !points[i]) { continue; }
    let k = -1;
    for (let kk = 0; kk < K; kk++) { if (norm[kk][i]) { k = kk; break; } }
    const phi = (azimuths[k] * Math.PI) / 180;
    const rx = Math.cos(phi), ry = Math.sin(phi);          // observed direction
    const px = -ry, py = rx;                                // unobserved (depth) direction
    let lo = i - 1; while (lo >= 0 && views_used[lo] < 2) { lo--; }
    let hi = i + 1; while (hi < n && views_used[hi] < 2) { hi++; }
    const a = lo >= 0 ? points[lo] : null, b = hi < n ? points[hi] : null;
    if (!a && !b) { continue; }
    let prior: Point3;
    if (a && b) { const t = (i - lo) / (hi - lo); prior = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
    else { prior = (a ?? b) as Point3; }
    const u = norm[k][i]!.u;                                // measured along r
    const depth = prior[0] * px + prior[1] * py;            // neighbors' component along r-perp
    points[i] = [u * rx + depth * px, u * ry + depth * py, points[i]![2]];
  }

  // Reject reflections: a light far from both wire-neighbors (which are inches away) is noise.
  const dists: number[] = [];
  for (let i = 1; i < n; i++) {
    const a = points[i - 1], b = points[i];
    if (a && b) { dists.push(Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2])); }
  }
  const med = percentile(dists, 0.5) || 0.05;
  let outliers = 0;
  for (let i = 0; i < n; i++) {
    const p = points[i];
    if (!p) { continue; }
    const neigh = [points[i - 1], points[i + 1]].filter((q): q is Point3 => !!q);
    if (!neigh.length) { continue; }
    const far = neigh.every(q => Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]) > med * 5);
    if (far) {
      points[i] = null;
      outliers++;
      if (views_used[i] >= 2) { located--; } else { partial--; }
    }
  }
  return { points, located, partial, missing: missing + outliers, outliers };
}

/** Rough reconstruction error against known positions (for tests / the simulator). */
export function rmsError(a: (Point3 | null)[], b: Point3[]): number {
  let s = 0, c = 0;
  for (let i = 0; i < b.length; i++) {
    const p = a[i];
    if (!p) { continue; }
    s += (p[0] - b[i][0]) ** 2 + (p[1] - b[i][1]) ** 2 + (p[2] - b[i][2]) ** 2;
    c++;
  }
  return c ? Math.sqrt(s / c) : Infinity;
}
