"""Licence step: runs inside fetch, before anything is chosen. The verdict decides whether a source may be
flattened (copied into the compiled skill) or only referenced.

  flatten     MIT, BSD, ISC, Apache-2.0, CC-BY-4.0, CC0, Unlicense, 0BSD, MIT-0: copy with the duties met
  reference   no licence, an unknown or proprietary licence, NonCommercial or NoDerivatives terms: never copied,
              only named, so the user installs the original themselves
  copyleft    GPL, AGPL, LGPL, MPL, CC-BY-SA: copying would put the whole compiled skill under those terms,
              so it is referenced by default (see references/licences.md)
  own         a local source the user says they wrote (--own); recorded as such in the lock
"""
import re

FINGERPRINTS = [
    ("AGPL-3.0", [r"GNU AFFERO GENERAL PUBLIC LICENSE"]),
    ("LGPL-3.0", [r"GNU LESSER GENERAL PUBLIC LICENSE", r"Version 3"]),
    ("LGPL-2.1", [r"GNU LESSER GENERAL PUBLIC LICENSE", r"Version 2\.1"]),
    ("GPL-3.0", [r"GNU GENERAL PUBLIC LICENSE", r"Version 3"]),
    ("GPL-2.0", [r"GNU GENERAL PUBLIC LICENSE", r"Version 2"]),
    ("MPL-2.0", [r"Mozilla Public License,? (Version|v\.?) ?2\.0"]),
    ("Apache-2.0", [r"Apache License", r"Version 2\.0"]),
    ("CC-BY-NC-SA-4.0", [r"Attribution-NonCommercial-ShareAlike 4\.0"]),
    ("CC-BY-NC-ND-4.0", [r"Attribution-NonCommercial-NoDerivatives 4\.0"]),
    ("CC-BY-NC-4.0", [r"Attribution-NonCommercial 4\.0"]),
    ("CC-BY-ND-4.0", [r"Attribution-NoDerivatives 4\.0"]),
    ("CC-BY-SA-4.0", [r"Attribution-ShareAlike 4\.0"]),
    ("CC-BY-4.0", [r"Attribution 4\.0 International"]),
    ("CC0-1.0", [r"CC0 1\.0 Universal|Creative Commons Zero"]),
    ("Unlicense", [r"This is free and unencumbered software released into the public domain"]),
    ("BSD-3-Clause", [r"Redistribution and use in source and binary forms", r"Neither the name"]),
    ("BSD-2-Clause", [r"Redistribution and use in source and binary forms"]),
    ("MIT", [r"Permission is hereby granted, free of charge", r"above copyright notice and this permission notice shall be\s+included"]),
    ("MIT-0", [r"Permission is hereby granted, free of charge"]),
    ("0BSD", [r"Permission to use, copy, modify, and/or distribute this software for any\s+purpose with or without fee is hereby granted\.\s+THE SOFTWARE"]),
    ("ISC", [r"Permission to use, copy, modify, and(/or)? distribute this software for any\s+purpose with or without fee is hereby granted, provided that the above\s+copyright notice"]),
]

SPDX_ALIASES = {
    "mit": "MIT", "mit license": "MIT", "apache-2.0": "Apache-2.0", "apache 2.0": "Apache-2.0", "apache2": "Apache-2.0",
    "apache license 2.0": "Apache-2.0", "bsd-3-clause": "BSD-3-Clause", "bsd-2-clause": "BSD-2-Clause", "isc": "ISC",
    "cc-by-4.0": "CC-BY-4.0", "cc by 4.0": "CC-BY-4.0", "cc0-1.0": "CC0-1.0", "cc0": "CC0-1.0", "unlicense": "Unlicense",
    "0bsd": "0BSD", "mit-0": "MIT-0", "mpl-2.0": "MPL-2.0", "gpl-3.0": "GPL-3.0", "gpl-2.0": "GPL-2.0", "agpl-3.0": "AGPL-3.0",
    "cc-by-sa-4.0": "CC-BY-SA-4.0", "lgpl-3.0": "LGPL-3.0", "lgpl-2.1": "LGPL-2.1",
}

FLATTEN = {"MIT", "MIT-0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Apache-2.0", "CC-BY-4.0", "CC0-1.0", "Unlicense"}
COPYLEFT = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "MPL-2.0", "CC-BY-SA-4.0"}
RESTRICTIVENESS = ["CC0-1.0", "Unlicense", "0BSD", "MIT-0", "MIT", "ISC", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0",
                   "CC-BY-4.0", "MPL-2.0", "LGPL-2.1", "LGPL-3.0", "CC-BY-SA-4.0", "GPL-2.0", "GPL-3.0", "AGPL-3.0"]

DUTIES = {
    "MIT": "Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.",
    "MIT-0": "No duties. Credited anyway.",
    "ISC": "Keep the copyright and permission notice: LICENSE travels in the source folder.",
    "BSD-2-Clause": "Keep the copyright notice, the conditions and the disclaimer: LICENSE travels in the source folder.",
    "BSD-3-Clause": "Keep the notice, conditions and disclaimer; never use the authors' names to endorse: LICENSE travels in the source folder.",
    "0BSD": "No duties. Credited anyway.",
    "Unlicense": "Public domain. Credited anyway.",
    "CC0-1.0": "Public domain dedication. Credited anyway.",
    "Apache-2.0": "Give a copy of the licence, mark every changed file with a notice that it was changed, keep the copyright and attribution notices, and carry the NOTICE file's contents.",
    "CC-BY-4.0": "Credit the author, link the licence, and say what was changed.",
}


def identify(text):
    """Best SPDX id for a licence text, or None."""
    t = re.sub(r"[ \t]+", " ", text)
    for spdx, pats in FINGERPRINTS:
        if all(re.search(p, t, re.I | re.M) for p in pats):
            return spdx
    if re.search(r"all rights reserved", t, re.I) and not re.search(r"permission is hereby granted", t, re.I):
        return "LicenseRef-AllRightsReserved"
    return None


def _from_frontmatter(value):
    if not value:
        return None
    v = str(value).strip().lower().rstrip(".")
    if v in SPDX_ALIASES:
        return SPDX_ALIASES[v]
    for key, spdx in SPDX_ALIASES.items():
        if re.match(rf"^{re.escape(key)}\b", v):
            return spdx
    if re.search(r"proprietary|all rights reserved|commercial", v):
        return "LicenseRef-Proprietary"
    return None


def copyright_lines(text):
    return [l.strip() for l in text.splitlines() if re.match(r"^\s*(copyright|\(c\)|" + chr(0xA9) + r")\s", l.strip(), re.I)][:6]


def verdict_for(spdx):
    if spdx in FLATTEN:
        return "flatten"
    if spdx in COPYLEFT:
        return "copyleft"
    return "reference"


def assess(rec, own=False):
    """Decide the licence of one read source record. Returns a dict written to the lock and the README."""
    if own and rec.get("type") == "local":
        return {"spdx": "LicenseRef-Own", "verdict": "own", "file": None, "copyright": [],
                "notice": None, "duties": "Your own text. Nothing to carry.", "problems": [],
                "evidence": "declared with --own"}
    files = rec.get("licence_files", [])
    problems = []
    found = []
    for f in files:
        spdx = identify(f["text"])
        found.append((f, spdx))
        if spdx is None:
            problems.append(f"{f['path']}: licence text not recognised")
    fm_spdx = _from_frontmatter((rec.get("frontmatter") or {}).get("license"))
    nearest = next(((f, s) for f, s in found if s), None)
    spdx = nearest[1] if nearest else None
    evidence = f"{nearest[0]['path']}" if nearest else None
    if fm_spdx and spdx and fm_spdx != spdx and not fm_spdx.startswith("LicenseRef"):
        problems.append(f"SKILL.md says {fm_spdx}, {evidence} says {spdx}; the stricter one is used")
        spdx = max(spdx, fm_spdx, key=lambda s: RESTRICTIVENESS.index(s) if s in RESTRICTIVENESS else 99)
    elif fm_spdx and fm_spdx.startswith("LicenseRef"):
        problems.append(f"SKILL.md licence field: {(rec.get('frontmatter') or {}).get('license')!r}")
        spdx = fm_spdx
    elif fm_spdx and not spdx:
        problems.append(f"only the SKILL.md frontmatter names a licence ({fm_spdx}); no licence file was found")
        spdx = None if not files else spdx
    if not files and not fm_spdx:
        problems.append("no licence file: all rights reserved by default")
    lic_text = nearest[0]["text"] if nearest else ""
    notice = "\n\n".join(n["text"].strip() for n in rec.get("notice_files", [])) or None
    v = verdict_for(spdx) if spdx else "reference"
    return {
        "spdx": spdx or "NOASSERTION",
        "verdict": v,
        "file": nearest[0]["path"] if nearest else None,
        "file_text": lic_text,
        "copyright": copyright_lines(lic_text),
        "notice": notice,
        "duties": DUTIES.get(spdx, "Not copied. Referenced only." if v != "flatten" else ""),
        "problems": problems,
        "evidence": evidence or ("frontmatter" if fm_spdx else "none"),
    }


def output_licence(assessments, own_licence=None):
    """The frontmatter licence line for a compiled skill that carries several sources."""
    ids = sorted({a["spdx"] for a in assessments if a["verdict"] == "flatten"})
    parts = []
    if own_licence:
        parts.append(own_licence)
    parts += [i for i in ids if i not in parts]
    if not parts:
        return "See connect-anything.lock.json"
    return " AND ".join(parts) + ". Each source folder holds its own LICENSE"
