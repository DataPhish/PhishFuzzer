# ==========================
# GLOBAL RULES
# ==========================

GLOBAL_RULES = """
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

""".strip()


# ==========================
# PHISHING — WELL-KNOWN
# ==========================

PHISHING_WELL_PROMPT = """
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

""".strip()


# ==========================
# PHISHING — FAKE
# ==========================

PHISHING_FAKE_PROMPT = """
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

""".strip()


# ==========================
# SPAM — WELL-KNOWN
# ==========================

SPAM_WELL_PROMPT = """
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
""".strip()


# ==========================
# VALID — WELL-KNOWN
# ==========================

VALID_WELL_PROMPT = """
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
""".strip()


# ==========================
# VALID — FAKE
# ==========================

VALID_FAKE_PROMPT = """
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
""".strip()
