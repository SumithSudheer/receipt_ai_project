import spacy
import re
from datetime import datetime

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    print("Downloading spaCy model 'en_core_web_lg'...")
    from spacy.cli import download
    download("en_core_web_lg")
    nlp = spacy.load("en_core_web_lg")

def normalize_date(date_str):
    """Convert various formats to YYYY-MM-DD."""
    # Prioritize more specific formats first
    date_formats = [
        "%m/%d/%Y %H:%M",  # e.g., 05/08/2019 21:15 (Safeway example)
        "%m/%d/%y %H:%M",  # e.g., 05/08/19 21:15 (Safeway example)
        "%m/%d/%Y %I:%M:%S %p", # e.g., 5/10/2019 1:46:00 PM
        "%m/%d/%Y",        # e.g., 11/25/2018
        "%m/%d/%y",        # e.g., 11/25/18
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d %B %Y",        # e.g., 25 November 2018
        "%d %b %Y",        # e.g., 25 Nov 2018
        "%B %d, %Y",       # e.g., November 25, 2018
        "%b %d, %Y",       # e.g., Nov 25, 2018
    ]
    for fmt in date_formats:
        try:
            cleaned_date_str = date_str.replace('O', '0').replace('o', '0')
            return datetime.strptime(cleaned_date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def extract_amounts(text: str,amounts):
    lines = text.split("\n")
    candidate_amounts = []
    candidate_amounts_test = []
    ignore_keywords = ["gift", "survey", "win", "reward", "promo", "coupon", "expires", "discount", "off", "save", "now value"]
    priority_keywords = ["total", "amount", "due", "balance", "paid"]

    for line in lines:
        line_lower = line.lower()

        # Ignore ad/promo lines
        if any(word in line_lower for word in ignore_keywords):
            continue

        # Find amounts
        matches = re.findall(r"(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)", line)
        for amt in matches:
            
            amt_clean = amt.replace(",", "")
            if float(amt_clean) not in amounts:
                continue
            print(amt_clean)
            try:
                value = float(amt_clean)
            except:
                # Fix missing decimal, e.g., "1500" -> 15.00 if reasonable
                if len(amt_clean) >= 3:
                    value = float(amt_clean[:-2] + "." + amt_clean[-2:])
                else:
                    continue

            # If priority keyword in line, return immediately
            if any(k in line_lower for k in priority_keywords):
                return value
            candidate_amounts_test.append({"key":line_lower,"value":value})
            candidate_amounts.append(value)
    # print(candidate_amounts_test)
    # print(max(candidate_amounts) )
    # Filter out unrealistic values (e.g., < 1 or > 10,000)
    candidate_amounts = [amt for amt in candidate_amounts if 1 < amt < 10000]

    # Fallback: largest amount
    return max(candidate_amounts) if candidate_amounts else None

def extract_entities(text: str):
    doc = nlp(text)

    merchant_name = None
    amounts = []
    all_dates = []

    # Extract merchant name and money using spaCy
    for ent in doc.ents:
        # print(ent,"lllllllllllllll",ent.label_)
        if ent.label_ == "ORG" and merchant_name is None:
            merchant_name = ent.text
        elif ent.label_ == "MONEY":
            val = ent.text.replace("$", "").replace(",", "").strip()
            try:
                amounts.append(float(val))
            except:
                pass

    # Regex for amounts with commas
    regex_amounts = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2})", text)
    for amt in regex_amounts:
        amt_clean = amt.replace(",", "")
        try:
            amounts.append(float(amt_clean))
        except:
            pass
    print(amounts)
    # total_amount = max(amounts) if amounts else None
    total_amount = extract_amounts(text,amounts)
    print(total_amount)
    # Regex patterns for different date formats including time
    date_patterns = [
        # Allows for 'O' or 'o' for digits 0-9 for month/day/year components
        r"\b[0-9Oo]{1,2}[/-][0-9Oo]{1,2}[/-][0-9Oo]{2,4}(?: \d{1,2}:\d{2}(?::\d{2})?(?: [APMapm]{2})?)?\b",
        r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
    ]
    print(text)
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        print(matches)
        for m in matches:
            normalized = normalize_date(m)
            if normalized:
                all_dates.append(normalized)

    purchased_at = min(all_dates) if all_dates else None

    return {
        "merchant_name": merchant_name if merchant_name else "Unknown",
        "total_amount": total_amount if total_amount else 0,
        "purchased_at": purchased_at,
        "all_dates": sorted(list(set(all_dates)))  # Unique and sorted
    }
