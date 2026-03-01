#!/usr/bin/env python3
"""
Biblical Text Processor V2 - Multi-Section Generator
Automatically breaks large biblical text into multiple 1000-word sections for video generation.
KJV-Preserving: Keeps thou/thee/ye/unto/shalt grammar while fixing OCR/narration issues.
Optional AI: Sentence restructuring for optimal ElevenLabs narration (10-22 words per sentence).

Usage: Run the script to process text from 'Input' file into multiple video-ready sections.
Output: All processed sections saved in 'Output' file with clear separators.
Version: 1.4.0 - KJV Narration Mode + AI Polish + Comprehensive 1611 Normalization (95+ patterns)
"""

import re
import sys
import os
import json
from typing import Optional

# AI Processing (OpenAI API)
try:
    import openai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# KJV Narration Editor Prompt for AI
KJV_NARRATION_PROMPT = """You are a KJV narration editor preparing Bible passages for ElevenLabs text-to-speech (audiobook-style).
Make the text easy to speak and easy for captions while keeping the King James feel.

DO NOT CHANGE these KJV words: thou, thee, thy, thine, ye, unto, shalt, hast, didst, art. Keep them exactly.

Critical fixes (must):
1) Never output "vs". If the input contains "vs", replace it with "us" (deliver us, upon us, done to us).
2) Remove verse numbers and number/word glue (example: "2Blessed" → "Blessed").
3) Keep all names and places unchanged (Azarias, Ananias, Misael, Jerusalem, Cherubims, Chaldeans, etc.).

ElevenLabs narration rules:
4) Break long sentences into shorter sentences (target 10–22 words).
5) Prefer periods over colons/semicolons. Use commas lightly.
6) Keep meaning EXACTLY the same—no added commentary or explanation.
7) Fix OCR spellings that hurt narration, but keep KJV vocabulary and reverence. Make only these kinds of fixes:
   - vp → up
   - vpon → upon
   - deliuer → deliver
   - iudgement(s) → judgment(s)
   - heauen → heaven
   - aboue → above
   - vnto → unto
   (Do not modernize thou/thee/ye/thy/thine/shalt/hast/didst/art.)

Optional pause control (use sparingly): Insert <break time="0.3s" /> only where a speaker would naturally pause between major thoughts.

Output format: clean paragraphs only. No headings. No bullets. No verse numbers."""

def ai_polish_narration(text: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Use AI to polish KJV text for ElevenLabs narration.
    Returns polished text or None if AI unavailable/fails.
    """
    if not AI_AVAILABLE:
        print("OpenAI library not installed. Skipping AI polish. Install: pip install openai")
        return None
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("No OpenAI API key found. Set OPENAI_API_KEY environment variable or skip AI polish.")
        return None
    
    try:
        print("Calling AI for KJV narration polish...")
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective
            messages=[
                {"role": "system", "content": KJV_NARRATION_PROMPT},
                {"role": "user", "content": f"Polish this KJV passage for narration:\n\n{text}"}
            ],
            temperature=0.3,  # Low temp for consistency
            max_tokens=4000
        )
        
        polished = response.choices[0].message.content.strip()
        print("AI polish complete!")
        return polished
        
    except Exception as e:
        print(f"AI polish failed: {e}")
        print("Continuing with regex-cleaned version...")
        return None

def clean_text(text):
    """Clean and normalize the input text."""
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\n+', ' ', text)  # Replace multiple newlines with spaces
    text = re.sub(r'\s+', ' ', text.strip())  # Replace multiple spaces with single space
    
    # NEW: Script formatting cleaning
    print("🎬 Cleaning script formatting...")
    
    # Remove stage directions like [Scene: ...] and [Opening Scene - ...]
    text = re.sub(r'\*\*\[.*?\]\*\*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **text** → text
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *text* → text
    
    # Remove scene separators and dashes
    text = re.sub(r'---+', '', text)
    text = re.sub(r'_{3,}', '', text)
    text = re.sub(r'={3,}', '', text)
    
    # Remove stage directions in parentheses (but preserve biblical content in parentheses)
    # Only remove if it contains video production terms
    text = re.sub(r'\(.*?[Vv]oiceover.*?\)', '', text)
    text = re.sub(r'\(.*?[Ss]cene.*?\)', '', text)
    text = re.sub(r'\(.*?[Cc]inematic.*?\)', '', text)
    text = re.sub(r'\(.*?[Ii]nstrumental.*?\)', '', text)
    
    # Remove common video production terms
    text = re.sub(r'\*\*Narrator \(Voiceover\)\*\*', '', text)
    text = re.sub(r'Narrator \(Voiceover\)', '', text)
    text = re.sub(r'\*\*Title\*\*:', '', text)
    text = re.sub(r'Title:', '', text)
    text = re.sub(r'\*\*\[Final Scene.*?\]\*\*', '', text)
    text = re.sub(r'\*\*\[Opening Scene.*?\]\*\*', '', text)
    
    # EXISTING: Biblical formatting cleaning
    print("📖 Cleaning biblical formatting...")
    
    # Remove verse references like "Deuteronomy 4:7-8" but keep the actual text
    text = re.sub(r'\b[A-Za-z]+\s+\d+:\d+(-\d+)?\s+', '', text)

    # Remove standalone verse numbers (common KJV formatting)
    text = re.sub(r'(?m)^\s*[1-9]\d{0,2}[:.)]?\s+', '', text)       # line-leading
    text = re.sub(r'\s+[1-9]\d{0,2}[:.)]?\s+(?=[A-Za-z])', ' ', text)  # inline
    # Remove verse numbers stuck to the start of words (e.g., "1And", "49O")
    text = re.sub(r'\b[1-9]\d{0,2}[:.)]?\s*(?=[A-Za-z])', '', text)
    # Remove verse numbers with paragraph symbol (e.g., "3¶ ", "16¶ ")
    text = re.sub(r'\b[1-9]\d{0,2}¶\s*', '', text)
    # Remove verse numbers with opening parentheses (e.g., "15(For" → "For")
    text = re.sub(r'\b[1-9]\d{0,2}\(', '(', text)
    # Clean up multiple opening parentheses that may result
    text = re.sub(r'\(\(+', '(', text)
    
    # Clean up punctuation spacing
    text = re.sub(r'([.!?])\s*', r'\1 ', text)
    
    # Remove multiple spaces again
    text = re.sub(r'\s+', ' ', text)
    
    # Remove section headers and precept references (but keep main content)
    text = re.sub(r'Precepts to [^:]+:', '', text)
    text = re.sub(r'How special and Holy they are', '', text)
    text = re.sub(r'THE MOST HIGH CHOSEN PEOPLE', '', text)
    text = re.sub(r'Conclusion', '', text)
    
    # Final cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive line breaks
    text = re.sub(r'\s{2,}', ' ', text)     # Remove excessive spaces
    
    # Remove empty lines
    text = '\n'.join(line for line in text.split('\n') if line.strip())
    
    return text.strip()

def kjv_narration_fix(text: str) -> str:
    """
    Fix KJV text for narration/captions while KEEPING archaic pronouns/grammar.
    - Fixes 1611 spellings (v→u, iudgement→judgment, Ierusalem→Jerusalem, etc.)
    - PRESERVES: thou/thee/thy/thine/ye/unto/shalt/hast/didst/art/wilt/doth/saith
    - Keeps KJV grammar intact
    - Narration-ready (no broken transcription)
    """
    
    # Fix standalone "vs" → "us" (people reference, not "versus")
    text = re.sub(r'\bvs\b', 'us', text, flags=re.IGNORECASE)
    
    # CRITICAL: Fix common u→v and other core 1611 patterns FIRST (highest priority)
    text = re.sub(r'\bgiue\b', 'give', text, flags=re.IGNORECASE)
    text = re.sub(r'\bloue\b', 'love', text, flags=re.IGNORECASE)
    text = re.sub(r'\bliue\b', 'live', text, flags=re.IGNORECASE)
    text = re.sub(r'\baliue\b', 'alive', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpreserue\b', 'preserve', text, flags=re.IGNORECASE)
    text = re.sub(r'\bserue\b', 'serve', text, flags=re.IGNORECASE)
    text = re.sub(r'\bobserue\b', 'observe', text, flags=re.IGNORECASE)
    
    # Critical v→u substitutions (1611 print conventions - comprehensive)
    text = re.sub(r'\bvp\b', 'up', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvpon\b', 'upon', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnto\b', 'unto', text, flags=re.IGNORECASE)  # Keep 'unto' (KJV word) but fix spelling
    text = re.sub(r'\bvnder\b', 'under', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvniust\b', 'unjust', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvniquitie\b', 'iniquity', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvncircumcised\b', 'uncircumcised', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnstable\b', 'unstable', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnrighteous\b', 'unrighteous', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnmeasurable\b', 'unmeasurable', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnsearchable\b', 'unsearchable', text, flags=re.IGNORECASE)
    text = re.sub(r'\bvnworthy\b', 'unworthy', text, flags=re.IGNORECASE)
    text = re.sub(r'\bouer\b', 'over', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmids\b', 'midst', text, flags=re.IGNORECASE)
    text = re.sub(r'\bouen\b', 'oven', text, flags=re.IGNORECASE)
    
    # Names and places (critical for accuracy)
    text = re.sub(r'\bIerusalem\b', 'Jerusalem', text)
    text = re.sub(r'\bIacob\b', 'Jacob', text)
    text = re.sub(r'\bIuda\b', 'Judah', text)
    
    # CRITICAL pronunciation-breaking spellings (ElevenLabs priority)
    text = re.sub(r'\biudgement', 'judgment', text, flags=re.IGNORECASE)  # judgement/judgements
    text = re.sub(r'\bIudgement', 'Judgment', text)  # Capital version
    text = re.sub(r'\bdeliuer', 'deliver', text, flags=re.IGNORECASE)     # deliver/delivered/deliverance
    text = re.sub(r'\bheauen', 'heaven', text, flags=re.IGNORECASE)       # heaven/heavens/heavenly
    text = re.sub(r'\biniquitie\b', 'iniquity', text, flags=re.IGNORECASE)  # Over-pronounced -tie
    text = re.sub(r'\baboue\b', 'above', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuen\b', 'even', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuer\b', 'ever', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmoue\b', 'move', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmooue\b', 'move', text, flags=re.IGNORECASE)
    text = re.sub(r'\blouing\b', 'loving', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsaued\b', 'saved', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhaue\b', 'have', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwholy\b', 'wholly', text, flags=re.IGNORECASE)  # CRITICAL: read as "holy"
    
    # Common -e endings that break pronunciation
    text = re.sub(r'\bsoule\b', 'soul', text, flags=re.IGNORECASE)
    text = re.sub(r'\boliue\b', 'olive', text, flags=re.IGNORECASE)
    text = re.sub(r'\bpossesse\b', 'possess', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkeepe\b', 'keep', text, flags=re.IGNORECASE)
    text = re.sub(r'\btalke\b', 'talk', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbinde\b', 'bind', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbetweene\b', 'between', text, flags=re.IGNORECASE)
    text = re.sub(r'\balwayes\b', 'always', text, flags=re.IGNORECASE)
    
    # Double consonants and variant spellings
    text = re.sub(r'\bshalbe\b', 'shall be', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsonne\b', 'son', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwelles\b', 'wells', text, flags=re.IGNORECASE)
    text = re.sub(r'\bielous\b', 'jealous', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmilke\b', 'milk', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhony\b', 'honey', text, flags=re.IGNORECASE)
    
    # Commandments variations (critical for this text)
    text = re.sub(r'\bCommaundements\b', 'Commandments', text)
    text = re.sub(r'\bcommaundements\b', 'commandments', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCommandements\b', 'Commandments', text)
    text = re.sub(r'\bcommandements\b', 'commandments', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcommaundement\b', 'commandment', text, flags=re.IGNORECASE)
    
    # Past tense -dst endings (buildedst, filledst, etc.) → modern forms
    text = re.sub(r'\bbuildedst\b', 'built', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfilledst\b', 'filled', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdiggedst\b', 'dug', text, flags=re.IGNORECASE)
    text = re.sub(r'\bplantedst\b', 'planted', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdigged\b', 'dug', text, flags=re.IGNORECASE)
    
    # Additional verb forms
    text = re.sub(r'\bsware\b', 'swore', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshewed\b', 'showed', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsweare\b', 'swear', text, flags=re.IGNORECASE)
    text = re.sub(r'\bHeare\b', 'Hear', text)  # Capital H only
    text = re.sub(r'\bheare\b', 'hear', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsonnes\b', 'sons', text, flags=re.IGNORECASE)
    
    # Righteousness variants
    text = re.sub(r'\brighteousnes\b', 'righteousness', text, flags=re.IGNORECASE)
    
    # OCR artifacts and archaic forms that hurt narration
    text = re.sub(r'\bfornace\b', 'furnace', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshewre\b', 'shower', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshowre\b', 'shower', text, flags=re.IGNORECASE)
    text = re.sub(r'\bholden\b', 'held', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcaptiue\b', 'captive', text, flags=re.IGNORECASE)
    text = re.sub(r'\bAlmightie\b', 'Almighty', text)
    text = re.sub(r'\bdeepe\b', 'deep', text, flags=re.IGNORECASE)
    text = re.sub(r'\bMaiestie\b', 'Majesty', text)
    text = re.sub(r'\bmercifull\b', 'merciful', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuils\b', 'evils', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuill\b', 'evil', text, flags=re.IGNORECASE)
    text = re.sub(r'\bgoodnesse\b', 'goodness', text, flags=re.IGNORECASE)
    text = re.sub(r'\bforgiuenesse\b', 'forgiveness', text, flags=re.IGNORECASE)
    text = re.sub(r'\bforgiue\b', 'forgive', text, flags=re.IGNORECASE)
    text = re.sub(r'\biust\b', 'just', text, flags=re.IGNORECASE)
    text = re.sub(r'\byron\b', 'iron', text, flags=re.IGNORECASE)
    text = re.sub(r'\bprouoked\b', 'provoked', text, flags=re.IGNORECASE)
    text = re.sub(r'\breseruing\b', 'reserving', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsaue\b', 'save', text, flags=re.IGNORECASE)
    
    # Common word endings (plural/verb forms) - comprehensive
    text = re.sub(r'\bmercie', 'mercy', text, flags=re.IGNORECASE)  # mercie/mercies
    text = re.sub(r'\bmercys\b', 'mercies', text, flags=re.IGNORECASE)  # mercys → mercies
    text = re.sub(r'\bsinnes\b', 'sins', text, flags=re.IGNORECASE)
    text = re.sub(r'\bworkes\b', 'works', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwayes\b', 'ways', text, flags=re.IGNORECASE)
    text = re.sub(r'\btrueth\b', 'truth', text, flags=re.IGNORECASE)
    text = re.sub(r'\bseruant', 'servant', text, flags=re.IGNORECASE)    # servant/servants
    text = re.sub(r'\bbeloued\b', 'beloved', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmarueilous\b', 'marvelous', text, flags=re.IGNORECASE)
    text = re.sub(r'\bkindenesse\b', 'kindness', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwindes\b', 'winds', text, flags=re.IGNORECASE)
    text = re.sub(r'\bheate\b', 'heat', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsoules\b', 'souls', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwhome\b', 'whom', text, flags=re.IGNORECASE)
    text = re.sub(r'\bthreatnin', 'threatenin', text, flags=re.IGNORECASE)  # threatning → threatening
    text = re.sub(r'\boffences\b', 'offenses', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcondemne\b', 'condemn', text, flags=re.IGNORECASE)
    
    # Double-e contractions (normalize to modern single) - EXPANDED
    text = re.sub(r'\byee\b', 'ye', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwee\b', 'we', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbee\b', 'be', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhee\b', 'he', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshee\b', 'she', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmee\b', 'me', text, flags=re.IGNORECASE)
    text = re.sub(r'\bgoe\b', 'go', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdoe\b', 'do', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshew\b', 'show', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshall bee\b', 'shall be', text, flags=re.IGNORECASE)
    
    # Additional -e word endings
    text = re.sub(r'\bmeane\b', 'mean', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwhither\b', 'where', text, flags=re.IGNORECASE)  # archaic "whither" → "where"
    text = re.sub(r'\bfeare\b', 'fear', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfrontlets\b', 'frontlets', text, flags=re.IGNORECASE)  # Already correct
    text = re.sub(r'\bsigne\b', 'sign', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsignes\b', 'signs', text, flags=re.IGNORECASE)
    text = re.sub(r'\bwel\b', 'well', text, flags=re.IGNORECASE)
    
    # Additional nature/animal terms
    text = re.sub(r'\bfoules\b', 'fowls', text, flags=re.IGNORECASE)
    text = re.sub(r'\briuers\b', 'rivers', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcattell\b', 'cattle', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmountaines\b', 'mountains', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfountaines\b', 'fountains', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuermore\b', 'evermore', text, flags=re.IGNORECASE)
    text = re.sub(r'\beuery\b', 'every', text, flags=re.IGNORECASE)
    
    # Comprehensive 1611 spellings (extra syllables, stress issues, pronunciation errors)
    text = re.sub(r'\bCouenant\b', 'Covenant', text)
    text = re.sub(r'\bdisanull\b', 'disannul', text, flags=re.IGNORECASE)
    text = re.sub(r'\bNeuerthelesse\b', 'Nevertheless', text)
    text = re.sub(r'\breproch\b', 'reproach', text, flags=re.IGNORECASE)
    text = re.sub(r'\blesse\b', 'less', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfinde\b', 'find', text, flags=re.IGNORECASE)
    text = re.sub(r'\brammes\b', 'rams', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbullockes\b', 'bullocks', text, flags=re.IGNORECASE)
    text = re.sub(r'\blambes\b', 'lambs', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfeare\b', 'fear', text, flags=re.IGNORECASE)
    text = re.sub(r'\bseeke\b', 'seek', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdeale\b', 'deal', text, flags=re.IGNORECASE)
    text = re.sub(r'\bgiue\b', 'give', text, flags=re.IGNORECASE)  # "gee-ve" issue
    text = re.sub(r'\bdoe\b', 'do', text, flags=re.IGNORECASE)
    text = re.sub(r'\bonely\b', 'only', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhote\b', 'hot', text, flags=re.IGNORECASE)
    text = re.sub(r'\btowe\b', 'tow', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfourtie\b', 'forty', text, flags=re.IGNORECASE)
    text = re.sub(r'\bcubites\b', 'cubits', text, flags=re.IGNORECASE)
    text = re.sub(r'\bCaldeans\b', 'Chaldeans', text)
    text = re.sub(r'\bdowne\b', 'down', text, flags=re.IGNORECASE)
    text = re.sub(r'\bfellowes\b', 'fellows', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbene\b', 'been', text, flags=re.IGNORECASE)  # "ben-eh" issue
    text = re.sub(r'\bkingdome\b', 'kingdom', text, flags=re.IGNORECASE)
    text = re.sub(r'\bLorde\b', 'Lord', text)
    text = re.sub(r'\bSunne\b', 'Sun', text)  # "sun-nuh" issue
    text = re.sub(r'\bMoone\b', 'Moon', text)  # "moon-eh" issue
    text = re.sub(r'\bstarres\b', 'stars', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdewes\b', 'dews', text, flags=re.IGNORECASE)
    text = re.sub(r'\bstormes\b', 'storms', text, flags=re.IGNORECASE)  # NEW
    text = re.sub(r'\bdayes\b', 'days', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdarkenesse\b', 'darkness', text, flags=re.IGNORECASE)  # "ness-uh" artifact
    text = re.sub(r'\byce\b', 'ice', text, flags=re.IGNORECASE)  # NEW - ElevenLabs stumbles
    text = re.sub(r'\bcolde\b', 'cold', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhils\b', 'hills', text, flags=re.IGNORECASE)  # Missing L
    text = re.sub(r'\baire\b', 'air', text, flags=re.IGNORECASE)  # Ghost syllable
    text = re.sub(r'\bthankes\b', 'thanks', text, flags=re.IGNORECASE)
    text = re.sub(r'\blyeth\b', 'lieth', text, flags=re.IGNORECASE)
    text = re.sub(r'\bmouthes\b', 'mouths', text, flags=re.IGNORECASE)  # "mouth-es" awkward
    text = re.sub(r'\bCommandement', 'Commandment', text)  # Commandment/Commandments
    text = re.sub(r'\blawlesse\b', 'lawless', text, flags=re.IGNORECASE)  # Double-s cadence
    text = re.sub(r'\bhatefull\b', 'hateful', text, flags=re.IGNORECASE)  # Same issue
    text = re.sub(r'\bwhales\b', 'whales', text, flags=re.IGNORECASE)
    text = re.sub(r'\bspirits\b', 'spirits', text, flags=re.IGNORECASE)
    
    # Fix "&" → "and" for narration
    text = re.sub(r'\s+&\s+', ' and ', text)
    
    return text

def split_into_words(text):
    """Split text into individual words."""
    return text.split()

def create_sections(words, max_words=1000):
    """Break words into multiple sections - handles both small and large texts."""
    sections = []
    
    # If text is small enough (less than 1.5x max_words), treat as single section
    if len(words) <= max_words * 1.5:
        print(f"📝 Text is {len(words)} words - processing as single section")
        sections.append(words)
        return sections
    
    # For larger texts, break into multiple sections
    print(f"📚 Text is {len(words)} words - breaking into multiple sections")
    current_section = []
    
    i = 0
    while i < len(words):
        # Add words to current section until we reach max_words
        while len(current_section) < max_words and i < len(words):
            current_section.append(words[i])
            i += 1
        
        # If we have a full section, try to end at a complete sentence
        if len(current_section) == max_words and i < len(words):
            section_text = ' '.join(current_section)
            
            # Find last complete sentence
            last_period = section_text.rfind('.')
            last_exclamation = section_text.rfind('!')
            last_question = section_text.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            if last_sentence_end > len(section_text) * 0.7:  # Only if we don't cut too much
                clean_section_text = section_text[:last_sentence_end + 1]
                sections.append(clean_section_text.split())
                
                # Move remaining words to next section
                remaining_text = section_text[last_sentence_end + 1:].strip()
                current_section = remaining_text.split() if remaining_text else []
            else:
                # If no good sentence break, just use the full section
                sections.append(current_section[:])
                current_section = []
        else:
            # Add remaining words as final section
            if current_section:
                sections.append(current_section[:])
                current_section = []
    
    return sections

def format_section(words, section_num):
    """Format a single section with proper structure."""
    text = ' '.join(words)
    sentences = re.split(r'([.!?])', text)
    formatted_sentences = []
    sentence_count = 0
    
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            if sentence.strip():  # Only add non-empty sentences
                formatted_sentences.append(sentence.strip())
                sentence_count += 1
                
                # Add line break every 2 sentences for readability
                if sentence_count % 2 == 0:
                    formatted_sentences.append('\n')
    
    formatted_text = ''.join(formatted_sentences).strip()
    
    # Ensure sentences are spaced correctly: add a space after terminal punctuation
    # when it is immediately followed by a non-whitespace character (e.g., "Bible.Around" → "Bible. Around").
    formatted_text = re.sub(r'([.!?])(?=\S)', r'\1 ', formatted_text)
    
    # Add section header
    word_count = len(words)
    expected_minutes = word_count / 214  # Updated: 1000 words = 4:40 minutes
    expected_scenes = word_count // 40
    
    section_header = f"""
=== SECTION {section_num} ===
Words: {word_count} | Est. Video: {expected_minutes:.1f} min | Scenes: {expected_scenes}
Ready for Biblical Video Generator

"""
    
    return section_header + formatted_text

def read_input_file():
    """Read content from the Input file."""
    input_file = "Input"
    
    if not os.path.exists(input_file):
        print(f"❌ Error: '{input_file}' file not found!")
        print("   Please make sure the 'Input' file exists in the current directory.")
        return None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"❌ Error reading '{input_file}': {e}")
        return None

def save_output(sections_text):
    """Save all processed sections to Output file."""
    output_file = "Output"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sections_text)
        print(f"All sections saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving to '{output_file}': {e}")
        return False

def main():
    print("=" * 70)
    print("BIBLICAL TEXT PROCESSOR V2 - MULTI-SECTION GENERATOR")
    print("=" * 70)
    print("Processes biblical text - single section OR multiple 1000-word sections")
    print("Each section optimized for Biblical Video Generator") 
    print("Generates ~4-5 minute videos per 1000 words at 214 WPM")
    print("Auto-cleans script formatting (stage directions, markdown, etc.)")
    print("-" * 70)
    
    print("\nReading biblical text from 'Input' file...")
    
    # Read from Input file
    raw_text = read_input_file()
    if raw_text is None:
        return
    
    print("Successfully loaded text from Input file")
    print(f"Raw text length: {len(raw_text)} characters")
    
    # Check if script formatting is present
    has_script_formatting = (
        '[' in raw_text or '**[' in raw_text or '---' in raw_text or 
        'Narrator (Voiceover)' in raw_text or '**(' in raw_text
    )
    
    if has_script_formatting:
        print("Script formatting detected - will be automatically cleaned")
    
    print("\nProcessing text...")
    
    # Clean and process the text
    cleaned_text = clean_text(raw_text)
    print("Fixing KJV text for narration (keeping thou/thee/ye/unto/shalt)...")
    narration_ready = kjv_narration_fix(cleaned_text)
    
    # Optional AI polish for sentence restructuring
    ai_polished = ai_polish_narration(narration_ready)
    if ai_polished:
        final_text = ai_polished
        print("Using AI-polished version (sentence restructuring applied)")
    else:
        final_text = narration_ready
        print("Using regex-cleaned version (AI polish skipped)")
    
    words = final_text.split()
    
    print(f"Total word count after cleaning: {len(words)} words")
    
    # Show cleaning results
    if has_script_formatting:
        print("Script formatting cleaned (stage directions, markdown, etc.)")
    
    if len(words) == 0:
        print("No words found after cleaning. The text may need manual review.")
        return
    
    # Create sections
    sections = create_sections(words, max_words=1000)
    
    if len(sections) == 1:
        print(f"Text processed as single section (ready for one video)")
    else:
        print(f"Text divided into {len(sections)} sections")
    
    # Format all sections
    all_sections_text = ""
    total_words = 0
    
    print("\nSECTION BREAKDOWN:")
    print("-" * 50)
    
    for i, section_words in enumerate(sections, 1):
        word_count = len(section_words)
        expected_minutes = word_count / 214  # Updated: Actual ElevenLabs timing
        total_words += word_count
        
        print(f"Section {i}: {word_count} words → {expected_minutes:.1f} min video")
        
        # Format this section
        formatted_section = format_section(section_words, i)
        all_sections_text += formatted_section
        
        # Add separator between sections (except for last section)
        if i < len(sections):
            all_sections_text += "\n\n" + "="*70 + "\n\n"
    
    print("-" * 50)
    print(f"TOTAL: {total_words} words across {len(sections)} section{'s' if len(sections) > 1 else ''}")
    print(f"Total video time: {(total_words / 214):.1f} minutes")
    if len(sections) == 1:
        print(f"Ready for single video generation")
    else:
        print(f"Ready for {len(sections)} separate video generations")
    
    # Save to Output file
    print(f"\nSaving all sections to 'Output' file...")
    
    # Add header to the output file
    output_header = f"""BIBLICAL TEXT PROCESSOR V2 - PROCESSED SECTIONS
Generated: Multiple sections from large biblical text
Total Sections: {len(sections)}
Total Words: {total_words}
Total Video Time: {(total_words / 214):.1f} minutes

Instructions:
- Each section below is optimized for Biblical Video Generator
- Copy individual sections for separate video generation
- Each section generates ~4-5 minutes of professional biblical video per 1000 words

{'='*70}

"""
    
    final_output = output_header + all_sections_text
    
    if save_output(final_output):
        print("SUCCESS! All sections processed and saved.")
        print(f"\nNext Steps:")
        print(f"   1. Open the 'Output' file")
        if len(sections) == 1:
            print(f"   2. Copy the processed text for your video")
            print(f"   3. Paste into Biblical Video Generator")
            print(f"\nYou now have 1 video-ready biblical section!")
        else:
            print(f"   2. Copy Section 1 for your first video")
            print(f"   3. Paste into Biblical Video Generator")
            print(f"   4. Repeat for remaining {len(sections)-1} sections")
            print(f"\nYou now have {len(sections)} video-ready biblical sections!")
    else:
        print("Error occurred while saving. Please check file permissions.")

if __name__ == "__main__":
    main()