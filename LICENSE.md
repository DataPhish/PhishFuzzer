PhishFuzzer — The Machine Wars Email Dataset
Copyright (c) 2026 Rebeka Toth, Nils Gruschka, Tamas Bisztray

Unless otherwise noted, all material in this repository is licensed under
the Creative Commons Attribution-NonCommercial 4.0 International License
(CC BY-NC 4.0). This covers:

  - the source code and scripts (dataset creation, labeling, metadata
    population, normalization, rephrasing, classification and analysis);
  - the email datasets (seed set and generated variants), annotations,
    labels and metadata;
  - the raw classification outputs (JSONL), figures and documentation.

Third-party source material is subject to its own terms (see "Third-party
source material" below).

===============================================================================
CC BY-NC 4.0 — SUMMARY
===============================================================================

You are free to:
  - Share — copy and redistribute the material in any medium or format.
  - Adapt — remix, transform, and build upon the material.

Under the following terms:
  - Attribution — You must give appropriate credit, provide a link to the
    license, and indicate if changes were made. You may do so in any
    reasonable manner, but not in any way that suggests the licensor
    endorses you or your use.
  - NonCommercial — You may not use the material for commercial purposes,
    i.e. for any use primarily intended for or directed towards commercial
    advantage or monetary compensation. The authors consider this to
    include using the code or data to train, evaluate, or benchmark models
    or products that are offered commercially.
  - No additional restrictions — You may not apply legal terms or
    technological measures that legally restrict others from doing anything
    the license permits.

The full legal code is available at:
  https://creativecommons.org/licenses/by-nc/4.0/legalcode

The material is provided "as is", without warranty of any kind. To the
extent possible, the licensor is not liable for any damages arising from its
use, as set out in Section 5 of the CC BY-NC 4.0 legal code.

===============================================================================
REQUIRED ATTRIBUTION
===============================================================================

As permitted by Section 3(a)(1) of the CC BY-NC 4.0 legal code, the
licensor requests that attribution be given by citing the accompanying
paper:

  Rebeka Toth, Nils Gruschka and Tamas Bisztray. "The Phish, The Spam,
  and The Valid: Generating Feature-Rich Emails for Benchmarking LLMs".
  In: CYBERSEC 2026: The First International Conference on Security and
  Cybersecurity in the AI and Digital Context. Accepted for publication,
  forthcoming. Porto, Portugal: Digital Transformation Research Society,
  2026. ISBN: 978-1-68558-449-8.
  URL: https://www.dtrsociety.org/library/contribution/cybersec2026_20040

BibTeX is given in the README and in CITATION.cff.
This applies to any part of the repository — code, data, results or
figures — that you share, adapt, or build upon. Please also cite the paper
in any publication, report, or presentation that uses this material.

===============================================================================
COMMERCIAL USE
===============================================================================

Commercial use requires a separate license from the authors. Please contact
the authors (see the README) to request one.

===============================================================================
THIRD-PARTY SOURCE MATERIAL
===============================================================================

Part of the seed set (3,000 of 3,300 seed emails) is derived from publicly
available corpora, including the Kaggle Phishing Dataset and the Apache
SpamAssassin public corpus. The remaining 300 seed emails come from a private
collection and were de-identified and sanitized before release.

Content derived from third-party sources remains subject to the terms of its
original license, which take precedence over this license for that content.
Users are responsible for checking and complying with those terms,
particularly for redistribution. The CC BY-NC 4.0 license covers the
authors' own contributions: the code, generated variants, labels, motivation
annotations, metadata, normalization, and results.

===============================================================================
RESPONSIBLE USE NOTICE
===============================================================================

This dataset contains phishing and spam emails, including LLM-generated
variants, released to support research on detecting malicious email and on
benchmarking language models. All emails underwent manual de-identification,
content sanitization, and metadata validation.

Users are asked to:
  - use the material for research, education, and defensive security
    purposes;
  - not use it to craft, send, or improve phishing or spam campaigns against
    real people or organizations;
  - not try to re-identify any individual or organization referred to in
    the data.

This notice states the authors' intent and is not an additional licence
condition. The research was conducted in accordance with the ethics
guidelines of the University of Oslo.
