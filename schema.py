"""
JSON schema used to constrain Ollama's job-posting output.

extractor.py independently validates each response against this schema.
Structural validity does not guarantee factual accuracy. Optional fields may
be omitted when information is absent; callers should use safe defaults.
"""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {
            "type": "string",
            "description": "Company or organization name. Empty string if not stated.",
        },
        "job_title": {
            "type": "string",
            "description": "The job title as written in the posting.",
        },
        "seniority_level": {
            "type": "string",
            "enum": [
                "Internship",
                "Entry-level/Junior",
                "Mid-level",
                "Senior",
                "Lead/Staff",
                "Manager/Director",
                "Unknown",
            ],
            "description": "Best judgement of seniority from title, years required, and responsibilities.",
        },
        "required_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills, tools or qualifications explicitly described as required or essential.",
        },
        "nice_to_have_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Skills explicitly described as preferred, a bonus, or nice-to-have.",
        },
        "tech_stack": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Named languages, frameworks, platforms or tools (e.g. Python, SQL, Power BI, AWS).",
        },
        "years_experience_required": {
            "type": "string",
            "description": "Years of experience required, as stated (e.g. '2+ years'). Empty string if not stated.",
        },
        "employment_type": {
            "type": "string",
            "enum": ["Full-time", "Part-time", "Contract", "Internship", "Not specified"],
        },
        "remote_policy": {
            "type": "string",
            "enum": ["Remote", "Hybrid", "Onsite", "Not specified"],
        },
        "location": {
            "type": "string",
            "description": "City/country if stated. Empty string if not stated.",
        },
        "salary_range": {
            "type": "string",
            "description": "Salary or pay range exactly as written. Empty string if not stated.",
        },
        "sponsorship_signal": {
            "type": "string",
            "enum": [
                "Sponsorship offered",
                "No sponsorship / must have right to work",
                "Not mentioned",
            ],
            "description": (
                "Whether the posting explicitly says it can or cannot sponsor a visa, "
                "or requires existing right to work. Use 'Not mentioned' if the posting "
                "is silent on this — never guess."
            ),
        },
        "sponsorship_evidence_quote": {
            "type": "string",
            "description": (
                "The exact sentence from the posting that the sponsorship_signal decision "
                "is based on. Empty string if sponsorship_signal is 'Not mentioned'."
            ),
        },
        "visa_keywords_found": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Any visa/right-to-work related phrases found verbatim in the posting "
                "(e.g. 'sponsor a visa', 'right to work in the UK', 'Skilled Worker visa'). "
                "Empty array if none."
            ),
        },
    },
    "required": [
        "company",
        "job_title",
        "seniority_level",
        "required_skills",
        "tech_stack",
        "employment_type",
        "remote_policy",
        "sponsorship_signal",
        "visa_keywords_found",
    ],
    "additionalProperties": False,
}
