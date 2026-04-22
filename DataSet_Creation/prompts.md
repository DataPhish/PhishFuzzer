# Prompting Strategy

This document provides the exact prompting strategy used in the PhishFuzzer dataset creation pipeline.  
All prompts are designed to enforce structural consistency, realism, and reproducibility across labeling, enrichment, and generation stages.

---

# 1. Intent Labeling Prompt

```
You are an email security analyst.

This dataset contains phishing, spam, and legitimate emails.

Your task is to classify the PRIMARY explicitly requested user action.

The "motivation" field MUST be exactly ONE of:
- "Follow the link"
- "Open attachment"
- "Reply"
- "Unknown"

DEFINITION:
Classify based on the main action the sender explicitly wants the recipient to perform.

DECISION RULES (apply in order):

1. If the email explicitly instructs the recipient to open, download, review, or access an attached file 
   OR if an attachment is present and clearly referenced: "Open attachment"

2. If the email explicitly instructs the recipient to click, visit, confirm, verify, log in, submit, view, 
   or access something via a link: "Follow the link"

IMPORTANT:
- The mere presence of a URL is NOT sufficient.
- Passive reference links (citations, footer links, unsubscribe links, sponsor banners) do NOT count unless clearly emphasized as the main action.

3. If the email explicitly asks the recipient to reply, respond, send information, 
   or submit content via email: "Reply"

4. If no clear action is requested: "Unknown"

Respond ONLY in strict JSON format:
{{"motivation": "Follow the link"}}

Email:
Subject: {subject}
Body: {body}

URL Field:
{url_str}

Attachment Field:
{file_str}
```

---

# 2. Populating the Dataset Prompt (Structural Augmentation)

## BASE RULES

```
RULES:
1. If the Body contains explicit URL(s), extract and return those exact URL(s).
2. If the Body explicitly mentions attachment filename(s), extract and return those exact filename(s).
3. If the Body does NOT explicitly contain the URL or filename, but the email context clearly implies one,
   generate a realistic URL or filename consistent with the email content and Type.
4. Structural Enforcement by Motivation:
   - If Motivation = "Follow the link", a URL MUST NOT be null.
   - If Motivation = "Open attachment", a File MUST NOT be null.
   - If Motivation = "Reply" or "Unknown", structure must be inferred strictly from Body only.
5. If Motivation requires structure but none exists explicitly in the Body,
   generate a realistic artifact consistent with the email content and Type.
6. Do NOT generate both URL and File unless clearly implied.
7. Return null only when:
   - Motivation does not require structure
   - AND the Body does not imply structure.
8. Return strictly structured JSON only.

```

## PHISHING PROMPT

```
You are completing missing URL and File fields for phishing emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic phishing email would include:A URL, An attachment file

URL RULE:
- Emails MUST NEVER use official domains.
- URLs should appear deceptive or impersonation-style.
- Avoid placeholder domains.

FILE RULE:
- Only add a File if clearly implied.
- Use realistic phishing-style names (e.g., invoice.pdf, secure_document.html, form.docx).

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}

```

## SPAM PROMPT
```
You are completing missing URL and File fields for spam emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic spam email would include: A URL, An attachment file

URL RULE:
- URLs must use real, official company domains.
- Only add a URL if promotional action is implied.

FILE RULE:
- Only add a File if implied.
- Use realistic marketing names (e.g., brochure.pdf, catalog.pdf).
- Do NOT generate malicious-looking file types.

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}
```

## VALID PROMPT
```
You are completing missing URL and File fields for legitimate emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic legitimate email would include: A URL, An attachment file

URL RULE:
- URLs must be official and realistic.
- Only add a URL if clearly implied.

FILE RULE:
- Only add a File if explicitly referenced.
- Use professional filenames (e.g., agenda.pdf, report.docx, summary.xlsx).
- Do NOT invent attachments.

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}
```

---

# 3. Rephrasing / Dataset Expansion


## GLOBAL RULES
```
You are generating synthetic email variants for a cybersecurity dataset.
1. Generate EXACTLY 3 variants.
2. Preserve the original Motivation exactly.
3. Preserve the core communicative intent and requested action.
4. Do NOT reuse the original entity name if one exists.
5. If the original email does NOT contain a clear brand, organization, platform, or institutional entity:
   - Introduce a realistic and context-appropriate organization, theme or topic naturally.
   - The introduced entity must match the theme of the email (e.g., mailing list → technical community; academic → journal; discussion thread → forum platform; digest → newsletter provider).
   - Do NOT force an entity where it would break realism. Maintain natural structure.
6. Do NOT translate the language unless explicitly instructed.
   - If the input email is non-English, the output MUST remain in that language.
7. If the original email is a personal message, mailing list thread, digest, or technical discussion:
   - Preserve conversational or discussion structure.
   - You may introduce a platform or community context if needed.
   - Do NOT convert it into a corporate marketing email unless the theme supports it.
8. Update entity references consistently when applicable:
   - Subject
   - Body
   - Sender display name
   - From address
   - URLs
9. Structural diversity is mandatory:
   - 1 short
   - 1 medium
   - 1 long
   For narrative or conversational emails:
       • short (4–8 sentences)
       • medium (10–16 sentences)
       • long (25–40 sentences)
   For newsletters, editorial digests, structured marketing emails, 
   or multi-section content feeds:
       • Vary overall length naturally.
       • Preserve section-based formatting.
       • Do NOT force strict sentence-count targets.
       • Do NOT rewrite entire newsletter issues verbatim.
       • Condense or reorganize content while maintaining theme and structure.
10. Return STRICTLY a JSON array of 3 objects.
11. Each object MUST contain EXACTLY:
   - Subject
   - Body
   - From
   - URL(s)
   - File
12. Do NOT include explanations, markdown, comments, or extra keys.
13. Structural enforcement by Motivation:
   - If Motivation = "Follow the link" → URL(s) MUST NOT be null.
   - If Motivation = "Open attachment" → File MUST NOT be null.
   - If Motivation = "Reply" → URL(s) and File optional unless implied.
   - If Motivation = "Unknown" → Do NOT introduce artificial URLs or Files unless logically appropriate.
14. URL and File count consistency:
   - If the original email contains multiple URLs, maintain approximately the same number (±1 maximum).
   - If the original email contains a File, maintain one File.
15. Replacement entities must match the email theme (e.g., academic → journal/platform; technical thread → developer community; mailing list → forum provider; finance → bank/payment provider; SaaS login → cloud provider).
16. Do NOT use bracketed or descriptive placeholders such as:
   - [Link]
   - [Insert URL]
   - <URL>
   - [Malicious Link]
   - Any bracketed link descriptions.
   Links must either:
   • be explicit full URLs (e.g., https://secure-platform-login.com/verify)
   • OR referenced naturally (e.g., "click here", "use the link below"),
     but never inside brackets.
17. If the email is a newsletter, digest, headline list, score summary, 
or structured content feed (e.g., multiple headlines, stats tables, bullet-style listings):
   - Preserve structured formatting.
   - Do NOT force conversational rewriting.
   - Sentence-count targets (Rule 9) may be approximate rather than strict.
   - Maintain headline-style structure if present.
18. If the email is a transactional document (e.g., booking confirmation, invoice, ticket, travel document, receipt):
   - Preserve document-style structure.
   - Do NOT aggressively summarize critical booking or attachment information.
   - Length variation should be applied naturally without removing essential travel or document details.
   
INPUT EMAIL:
<INSERT ORIGINAL EMAIL JSON HERE>
```

## PHISHING — WELL-KNOWN
```
TASK:
Generate EXACTLY 3 phishing variants.

All variants MUST:
- Impersonate DIFFERENT real, well-known globally recognized entities 
(e.g., organization, platform, institution, service provider, or brand appropriate to the theme).
- Use GOOD grammar (professional tone).

Do NOT invent entity names in this prompt. No generic names, just REAl WORLD WLL/KNOWN entities.

Do NOT mention the words "phishing", "malicious", or "fraudulent" inside the email body.

PHISHING DOMAIN RULES:

1. From address:
   - Must appear brand-aligned.
   - Must use a deceptive or look-alike domain.
   - Never use official brand domain.

2. URLs:
   - Must be deceptive, look-alike, or attacker-controlled domains.
   - Use realistic phishing patterns such as:
       • brand-secure-login.com
       • verify-brand-account.net
       • brand-support-auth.co
       • account.brand-security.info
   - Do NOT use official domains.
   - Maintain approximately the same number of URLs as the original email (±1).

3. Attachments (if required by Motivation):
   - Use realistic phishing file names:
       • invoice.pdf
       • secure_document.html
       • account_update.docx
       • verification_form.xlsx
   - Allowed extensions: .pdf, .html, .docx, .xlsx
   - Do NOT generate executable files.

4. Persuasion:
   - Maintain realistic phishing persuasion (urgency, authority, reward, or account threat).
   - Do NOT include warnings or reduce attacker realism.
```


## PHISHING — FAKE
```
TASK:
Generate EXACTLY 3 phishing variants.

All variants MUST:
- Use DIFFERENT fabricated but realistic entity names 
- (e.g., organization, platform, service provider, institution, or brand appropriate to the theme of the email).
- The fabricated entities MUST NOT be real (no real brands, universities, journals, platforms, government agencies, or services).

Do NOT mention the words "phishing", "malicious", or "fraudulent" inside the email body.

PHISHING DOMAIN RULES:

1. From address:
   - Use a deceptive or attacker-controlled domain.
   - Domain must not look overly generic.
   - Example pattern:
       • support@secure-payments-alert.com
       • billing@account-verification-center.net

2. URLs:
   - Must be deceptive or attacker-controlled domains.
   - Use realistic phishing structures:
       • login-secure-update.com
       • verify-account-now.net
       • account-authentication-center.org
   - Maintain approximately the same number of URLs as the original email (±1).

3. Attachments (if required by Motivation):
   - Use realistic phishing-style file names:
       • invoice_details.pdf
       • account_verification.html
       • payment_form.docx
   - Allowed extensions: .pdf, .html, .docx, .xlsx

4. Persuasion:
   - Maintain realistic phishing persuasion (urgency, authority, account threat).
   - Do NOT include warnings or reduce attacker realism.
```

## SPAM — WELL-KNOWN
```

TASK:
Generate EXACTLY 3 spam variants.

All variants MUST:
- Impersonate DIFFERENT real, well-known globally recognized entities 
(e.g., organization, platform, institution, service provider, or brand appropriate to the theme).
- Use GOOD grammar (professional tone).

RULES:
- Email must be clearly unsolicited or promotional
- From address MUST use official or plausible marketing domains owned by the entity
- No impersonation of security alerts or account warnings
""".strip()


# ==========================
# SPAM — FAKE
# ==========================

SPAM_FAKE_PROMPT = """
TASK:
Generate EXACTLY 3 spam variants.

All variants MUST:
- Use DIFFERENT fabricated but realistic entity names 
(e.g., organization, platform, service provider, institution, or brand appropriate to the theme of the email).
- The fabricated entities MUST NOT be real (no real brands, universities, journals, platforms, government agencies, or services).

RULES:
- Use a realistic domain that matches the fabricated entity name.
- From sender MUST use the fabricated entity's domain.
- Email must clearly be promotional or unsolicited.
- No impersonation of security alerts or account warnings
```

## VALID — WELL-KNOWN
```
TASK:
Generate EXACTLY 3 legitimate email variants.

All variants MUST:
- Impersonate DIFFERENT real, well-known globally recognized entities 
(e.g., organization, platform, institution, service provider, or brand appropriate to the theme).
- Use GOOD grammar (professional tone).


RULES:
- Use ONLY official sender domains owned by the entity
- URLs MUST be official entity domains
- From sender MUST use official domain or legitimate ESP
- Include appropriate compliance, help, or security language
- No deception or urgency abuse
```

## VALID — FAKE
```
TASK:
Generate EXACTLY 3 legitimate email variants.

All variants MUST:
- Use DIFFERENT fabricated but realistic entity names 
(e.g., organization, platform, service provider, institution, or brand appropriate to the theme of the email).
- The fabricated entities MUST NOT be real (no real brands, universities, journals, platforms, government agencies, or services).

RULES:
- Use a realistic domain that matches the fabricated entity name.
- From sender MUST use the fabricated antity's domain.
- Include appropriate compliance, help, or security language
- No impersonation of security alerts or account warnings
```

---

# 4. Classification Prompt

```
You are a cybersecurity email classifier.

Classify the email into ONE of these categories:
- phishing
- spam
- valid

Respond with ONLY ONE WORD.
Do not explain.
```