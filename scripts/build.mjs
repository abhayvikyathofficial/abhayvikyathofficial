// Builds everything in /assets (header, footer, tech chips, GB Nodes card) in dark + light,
// then rewrites the stack block in README.md between the <!-- stack --> markers.
// Text is converted to outlines (Geist, same typeface as phoenixdev.online) so it
// renders identically for every visitor instead of falling back to a system font.
//
//   npm install
//   npm run build
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import opentype from 'opentype.js'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const font = (file) => opentype.loadSync(path.join(root, 'scripts/fonts', file))

const FONTS = {
  bold: font('Geist-Bold.ttf'),
  semibold: font('Geist-SemiBold.ttf'),
  medium: font('Geist-Medium.ttf'),
  mono: font('GeistMono-Regular.ttf'),
}

// ---- edit these -----------------------------------------------------------
const COPY = {
  initials: 'AV',
  name: 'Abhay Vikyath',
  site: 'abhayvikyath.in',
  headline: ['I turn ideas into', 'content and [brands]', 'people remember.'],
  ticker: ['Content strategy', 'Creative direction', 'Brand storytelling', 'Multimedia and social', 'UI/UX and web design', 'Community', 'Events'],
  tickerSeconds: 46,
}

// [label, icon] per group. Icons are simple-icons slugs from scripts/icons.json,
// or one of the hand-drawn glyphs in CUSTOM further down.
const STACK = [
  ['Content and strategy', [['Claude', 'claude'], ['Notion', 'notion'], ['Google Analytics', 'googleanalytics'], ['Meta', 'meta'], ['YouTube', 'youtube'], ['Instagram', 'instagram']]],
  ['Design and video', [['Figma', 'figma'], ['Canva', 'canva'], ['Photoshop', 'photoshop'], ['Premiere Pro', 'premiere'], ['After Effects', 'aftereffects'], ['Framer', 'framer'], ['Blender', 'blender']]],
  ['Web', [['HTML5', 'html5'], ['CSS', 'css'], ['JavaScript', 'javascript'], ['TypeScript', 'typescript'], ['React', 'react'], ['Next.js', 'nextdotjs'], ['Tailwind CSS', 'tailwindcss'], ['Vite', 'vite'], ['GSAP', 'greensock'], ['WordPress', 'wordpress']]],
  ['Backend and data', [['Node.js', 'nodedotjs'], ['Express', 'express'], ['Bun', 'bun'], ['Payload CMS', 'payloadcms'], ['PostgreSQL', 'postgresql'], ['Python', 'python'], ['C#', 'dotnet']]],
  ['Shipping', [['Vercel', 'vercel'], ['Cloudflare', 'cloudflare'], ['GitHub', 'github'], ['Git', 'git'], ['Playwright', 'playwright'], ['Vitest', 'vitest']]],
]


const THEMES = {
  dark: { bg: '#0a0a0a', border: '#262626', text: '#fafafa', soft: '#8f8f8f', line: '#232323', chip: '#0a0a0a', chipBorder: '#2e2e2e', chipText: '#ededed' },
  light: { bg: '#fafafa', border: '#e4e4e4', text: '#0a0a0a', soft: '#757575', line: '#e7e7e7', chip: '#ffffff', chipBorder: '#dcdcdc', chipText: '#171717' },
}
// ---------------------------------------------------------------------------

const W = 1280
const PAD = 72
const n = (v) => Number(v.toFixed(1))

const width = (str, f, size, tracking = 0) => f.getAdvanceWidth(str, size, { kerning: true, letterSpacing: tracking })
const outline = (str, f, size, x, y, tracking = 0) => f.getPath(str, x, y, size, { kerning: true, letterSpacing: tracking }).toPathData(1)

function text(str, { font, size, x, y, fill, tracking = 0, align = 'left' }) {
  const w = width(str, font, size, tracking)
  const left = align === 'right' ? x - w : align === 'center' ? x - w / 2 : x
  return `<path fill="${fill}" d="${outline(str, font, size, left, y, tracking)}"/>`
}

/* ----------------------------------------------------------------- header */

// One headline line; [bracketed] words become stroke-only.
function line(str, { size, x, y, color, tracking }) {
  let out = ''
  let cx = x
  for (const part of str.split(/(\[[^\]]+\])/).filter(Boolean)) {
    const hollow = part.startsWith('[')
    const word = hollow ? part.slice(1, -1) : part
    const d = outline(word, FONTS.bold, size, cx, y, tracking)
    out += hollow
      ? `<path fill="none" stroke="${color}" stroke-width="2.4" stroke-linejoin="round" d="${d}"/>`
      : `<path fill="${color}" d="${d}"/>`
    cx += width(word, FONTS.bold, size, tracking)
  }
  return out
}

function header(theme) {
  const c = THEMES[theme]
  const H = 580
  const BAND = 62 // ticker strip along the bottom edge
  const TRACK = -0.05
  const plain = COPY.headline.map((l) => l.replace(/[[\]]/g, ''))
  // size the headline so its widest line spans the card
  const size = Math.min(124, ...plain.map((l) => (124 * (W - PAD * 2)) / width(l, FONTS.bold, 124, TRACK)))
  const lead = size * 0.98
  const first = 134 + size * 0.86

  // ticker: one cycle of the phrase list, repeated and slid left by one cycle
  const TS = 17
  const TT = 0.16
  let tx = 0
  let cycle = ''
  for (const item of COPY.ticker) {
    const label = item.toUpperCase()
    cycle += outline(label, FONTS.mono, TS, tx, 0, TT)
    tx += width(label, FONTS.mono, TS, TT) + 30
    cycle += `M${n(tx)} -6.2a3 3 0 1 0 6 0a3 3 0 1 0 -6 0z` // separator dot
    tx += 6 + 30
  }
  const span = n(tx)
  const copies = Math.ceil(W / span) + 2

  const label = `${COPY.name}. ${plain.join(' ')}`
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${label}">
<defs>
<clipPath id="card"><rect x="2" y="2" width="${W - 4}" height="${H - 4}" rx="23"/></clipPath>
<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".09" stop-color="#fff"/><stop offset=".91" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="fade"><rect y="${H - BAND}" width="${W}" height="${BAND}" fill="url(#edge)"/></mask>
<path id="t" d="${cycle}"/>
</defs>
<style>
.run{animation:run ${COPY.tickerSeconds}s linear infinite}
@keyframes run{to{transform:translateX(-${span}px)}}
@media (prefers-reduced-motion:reduce){.run{animation:none}}
</style>
<rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="24" fill="${c.bg}" stroke="${c.border}" stroke-width="2"/>
<circle cx="${PAD + 24}" cy="78" r="24" fill="${c.text}"/>
${text(COPY.initials, { font: FONTS.bold, size: 17, x: PAD + 24, y: 84, fill: c.bg, tracking: -0.02, align: 'center' })}
${text(COPY.name, { font: FONTS.semibold, size: 24, x: PAD + 64, y: 86.5, fill: c.text, tracking: -0.03 })}
${text(COPY.site, { font: FONTS.mono, size: 18, x: W - PAD, y: 84.5, fill: c.soft, align: 'right' })}
${COPY.headline.map((l, i) => line(l, { size, x: PAD - 5, y: n(first + i * lead), color: c.text, tracking: TRACK })).join('\n')}
<g clip-path="url(#card)">
<rect x="0" y="${H - BAND}" width="${W}" height="1.5" fill="${c.line}"/>
<g mask="url(#fade)"><g class="run" fill="${c.soft}">
${Array.from({ length: copies }, (_, i) => `<use href="#t" x="${n(PAD + (i - 1) * span)}" y="${H - BAND / 2 + 6}"/>`).join('')}
</g></g>
</g>
</svg>
`
}

/* ----------------------------------------------------------------- footer */

// Closing mark: the name set huge and hollow, fading out toward the bottom edge.
function footer(theme) {
  const c = THEMES[theme]
  const TRACK = -0.055
  const size = (300 * (W - 40)) / width(COPY.name, FONTS.bold, 300, TRACK)
  const H = Math.round(size * 0.78) // baseline sits just above the bottom edge, descenders are cut
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${COPY.name}">
<defs>
<linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".45" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity=".06"/></linearGradient>
<mask id="m"><rect width="${W}" height="${H}" fill="url(#g)"/></mask>
</defs>
<path mask="url(#m)" fill="none" stroke="${c.soft}" stroke-width="1.8" stroke-linejoin="round" d="${outline(COPY.name, FONTS.bold, size, 8, n(size * 0.74), TRACK)}"/>
</svg>
`
}

/* ------------------------------------------------------------------ chips */

const icons = JSON.parse(fs.readFileSync(path.join(root, 'scripts/icons.json'), 'utf8'))
const CUSTOM = {
  tebex: { hex: null, svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 8h15l-1.2 12.5h-12.6z"/><path d="M8.5 8V6.5a3.5 3.5 0 0 1 7 0V8"/></g>` },
  remotion: { hex: '0B84F3', svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><rect x="2.5" y="4.5" width="19" height="15" rx="3"/><path d="M10 9v6l5-3z" fill="currentColor"/></g>` },
}
CUSTOM.photoshop = { hex: '31A8FF', svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3.5" width="18" height="17" rx="3"/><circle cx="9" cy="9.5" r="1.6"/><path d="M4 18l5-5 4 4 3-3 5 5"/></g>` }
CUSTOM.premiere = { hex: '9999FF', svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18M3 15h18M8 4v16M16 4v16"/></g>` }
CUSTOM.aftereffects = { hex: '9999FF', svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/></g>` }
CUSTOM.canva = { hex: '00C4CC', svg: `<g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M15.5 9.5a4.5 4.5 0 1 0 0 5"/></g>` }
CUSTOM.playwright = { hex: '2EAD33', svg: `<g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18l6-13 3 6 7-4"/><circle cx="18" cy="17" r="3"/></g>` }
const FALLBACK_HEX = { playwright: '2EAD33' }

const rgb = (hex) => [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16))
const lum = (hex) => {
  const [r, g, b] = rgb(hex).map((v) => ((v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
const mix = (hex, to, t) => rgb(hex).map((v, i) => Math.round(v + (rgb(to)[i] - v) * t).toString(16).padStart(2, '0')).join('')

// Brand colour, nudged until it is readable on the chip background.
function tint(hex, theme, c) {
  if (!hex) return c.chipText
  let h = hex.toLowerCase()
  if (theme === 'dark') {
    if (lum(h) < 0.02) return c.chipText
    for (let i = 0; i < 12 && lum(h) < 0.17; i++) h = mix(h, 'ffffff', 0.14)
    return '#' + h
  }
  if (lum(h) > 0.82) return c.chipText
  for (let i = 0; i < 12 && lum(h) > 0.52; i++) h = mix(h, '000000', 0.1)
  return '#' + h
}

const slug = (s) => s.toLowerCase().replace(/#/g, 'sharp').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

function chip(label, icon, theme) {
  const c = THEMES[theme]
  const H = 30
  const SIZE = 12.5
  const IS = 14
  const ix = 10
  const tx = ix + IS + 7
  const tw = width(label, FONTS.medium, SIZE, 0.005)
  const CW = Math.ceil(tx + tw + 11)
  const src = CUSTOM[icon] ?? icons[icon]
  if (!src) throw new Error(`missing icon: ${icon}`)
  const color = tint(src.hex ?? FALLBACK_HEX[icon], theme, c)
  const glyph = src.svg ?? `<path fill="currentColor" d="${src.path}"/>`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${CW}" height="${H}" viewBox="0 0 ${CW} ${H}" role="img" aria-label="${label.replace(/&/g, '&amp;')}">
<rect x=".5" y=".5" width="${CW - 1}" height="${H - 1}" rx="8" fill="${c.chip}" stroke="${c.chipBorder}"/>
<g transform="translate(${ix} ${(H - IS) / 2}) scale(${(IS / 24).toFixed(4)})" color="${color}">${glyph}</g>
<path fill="${c.chipText}" d="${outline(label, FONTS.medium, SIZE, tx, 19.4, 0.005)}"/>
</svg>
`
}

/* ------------------------------------------------------------------- emit */

const write = (rel, svg) => {
  const file = path.join(root, 'assets', rel)
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, svg)
  return fs.statSync(file).size
}

for (const theme of Object.keys(THEMES)) {
  for (const [name, svg] of [['header', header(theme)], ['footer', footer(theme)]]) {
    console.log(`assets/${name}-${theme}.svg`, (write(`${name}-${theme}.svg`, svg) / 1024).toFixed(1) + ' KB')
  }
}

fs.rmSync(path.join(root, 'assets/chips'), { recursive: true, force: true })
let rows = ''
let count = 0
for (const [group, items] of STACK) {
  rows += `<tr>\n<td width="150" valign="top"><b>${group}</b></td>\n<td>\n`
  for (const [label, icon] of items) {
    const file = `${slug(label)}.svg`
    for (const theme of Object.keys(THEMES)) write(`chips/${theme}/${file}`, chip(label, icon, theme))
    rows += `<picture><source media="(prefers-color-scheme: dark)" srcset="assets/chips/dark/${file}"><img src="assets/chips/light/${file}" height="30" alt="${label}"></picture>\n`
    count++
  }
  rows += `</td>\n</tr>\n`
}
console.log(`assets/chips: ${count} chips x 2 themes`)

const readme = path.join(root, 'README.md')
const md = fs.readFileSync(readme, 'utf8')
const START = '<!-- stack:start -->'
const END = '<!-- stack:end -->'
if (!md.includes(START) || !md.includes(END)) throw new Error('README.md is missing the stack markers')
fs.writeFileSync(readme, md.slice(0, md.indexOf(START) + START.length) + `\n<table>\n${rows}</table>\n` + md.slice(md.indexOf(END)))
console.log('README.md stack block updated')
