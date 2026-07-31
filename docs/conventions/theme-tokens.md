# Theme styling tokens

How the site's styling relates to the WP theme (Twenty Twenty-Five), learned while
tuning the list_browser count readout on 2026-07-26.

**`gettinglost.cst` uses ZERO theme variables** — `var(--…)` count is 0. Every
color is a hardcoded hex or inherited; the only font rule is `font-family: inherit`
on the control surface. So the house style of that file is hardcode/inherit, not
tokens.

**Colors — there is NO brown in the theme palette.** The `--wp--preset--color--*`
tokens are: `contrast` #111111, `base` #FFFFFF, `accent-1` #FFEE58 (yellow),
`accent-2` #F6CFF4 (pink), `accent-3` #503AA8 (purple), `accent-4` #686868 (gray),
`accent-5` #FBFAF3 (off-white), `accent-6` color-mix, plus WP's stock vivid-* set.
The **site text brown `#4a3828` (rgb 74,56,40) is the theme body foreground**, NOT
exposed as a named preset token — so there is no `var()` to point at for "the site
brown." To make an element wear the theme brown, **set no `color` and let it
inherit** (this is exactly how the grid card titles get #4a3828). The list_browser
controls instead use a **bespoke `#5e442c` (rgb 94,68,44)** — a slightly stronger
brown, used ~7× in the file. (The count was switched from #5e442c → inherit so it
matches the card titles.)

**Fonts — inheritance already lands on theme fonts.** Body font is
`--wp--preset--font-family--source-sans-3` (`"Source Sans 3", sans-serif`);
**headings (h1–h6) render in `Lora, serif`** (`--wp--preset--font-family--lora`).
A plain `<div>` inherits the sans body font; a heading element gets Lora serif.
So: an element is "on a theme font" by default via inheritance — to get the serif
heading font you use a heading element, not a font declaration. (~60 font-family
tokens are registered on `:root`, but the site only really uses these two.)

Practical recipe to make something "belong to the page": inherit color (→ #4a3828),
don't set font-family (→ Source Sans 3), use a heading element if you want Lora.
Verifying live CSS after a sync has a cache trap — see `.claude/toolchain.md`.
Related: [docs/rendering/blocks.md](../rendering/blocks.md) (list_browser renderer), [docs/rendering/wp-templates.md](../rendering/wp-templates.md).
