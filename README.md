# Raising a Family in Europe — which policies actually help

**Live:** https://alexjungaalto.github.io/family-policy-europe/

An interactive Europe map. Click a country and get the **5–9 government policies** that make the
largest material difference to one clearly defined household:

> Two working parents around 30 on ordinary (median) wages, **renting**, with **no inheritance**
> and no family money, and **1–2 children under 6**.

Each policy is ranked by value to that household, quantified in one line ("≈ €470/month for
2 kids"), tagged with who qualifies and what the catch is, and linked to an official source.
A **Compare** view puts the at-a-glance line (child cash, paid leave, childcare, tax relief, taxes on
wages, work rights) of all countries side by side. Sister project of [Fight the Academic Bullies](https://fightacademicbullies.org).

Coverage: EU-27 + United Kingdom, Switzerland, Norway, Iceland (31 countries).

Eight colour-coded categories:

- 💶 **Cash benefits for children** — universal child benefit, birth grants, under-3 allowances
- 👶 **Paid parental leave** — maternity/paternity/parental leave, replacement rate, daddy quota
- 🧸 **Childcare & early education** — entitlement age, typical parent fee at median income, place availability
- 🧾 **Tax relief for families** — splitting/quotient, child tax credits
- 🏠 **Housing support** — rent allowance reachable at median wage, family priority in social housing
- 🩺 **Free health, meals & schooling** — free child healthcare, school meals, free preschool
- 💼 **Lower taxes on wages** — earned-income credits, employee contribution cuts, targeted wage-tax exemptions, bracket indexation
- ⏰ **Work rights & in-kind benefits** — statutory paid leave, right to part-time/flexible work while children are small, job protection, sick-child days, meal vouchers, commuting subsidies

## What it deliberately leaves out

Schemes aimed only at households well below the median wage, and schemes that assume family
capital (large deposits, property purchase). Countries are not scored: wages, rents and taxes
differ too much for a single number to be honest.

## Layout

```
docs/
  index.html            static Leaflet app (no build step)
  data/europe.geojson   Natural Earth admin-0, Europe + neighbours, ISO2 in properties.iso
  data/policies.json    per-country entries keyed by ISO2 (see schema below)
merge_research.py       merge per-country <ISO2>.json research files into policies.json
merge_ext.py            insert labourtax/workrights extension files into the ranked lists
check_links.py          sweeps every URL in policies.json + index.html; dead links block deploy
deploy.sh               link-check → stamp DATA_V → commit → push (GitHub Pages serves docs/)
```

### `policies.json` schema (per country)

```json
{
  "country": "Austria", "iso": "AT", "checked": "2026-09-17",
  "note": "Honest 2–3 sentence big picture.",
  "headline": {"cash": "…", "leave": "…", "childcare": "…", "tax": "…", "labourtax": "…", "workrights": "…"},
  "policies": [
    {"rank": 1, "cat": "cash|leave|childcare|tax|housing|healthedu|labourtax|workrights",
     "name": "…", "what": "…", "value": "one quantified line for the household",
     "eligibility": "…", "url": "official page", "url_label": "…", "caveat": "the catch"}
  ],
  "resources": {"official": {"label","url"}, "calculator": {…}, "guide": {…}}
}
```

Deep links: `#DE` opens Germany, `#compare` and `#about` open those panels.

## Method & caveats

Entries were compiled (AI-assisted, human-reviewed) from official government sources and
EU/OECD overviews at 2025/2026 rates; every URL is checked before deploy. Rates change every
budget year — confirm on the linked page before planning around a number. Corrections and pull
requests welcome: alexjung235@gmail.com.
