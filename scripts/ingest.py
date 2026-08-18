from datetime import datetime

from sqlalchemy import text

from database import get_db_engine

import os
import re
import requests

from dotenv import load_dotenv
from pprint import pprint


import pandas as pd
import pgeocode

GERMAN_POSTCODES = pgeocode.Nominatim("de")
GERMAN_STATES = [
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
]


def get_state_from_address(address_line):

    if not address_line:
        return None

    for state in GERMAN_STATES:

        if state.lower() in address_line.lower():
            return state

    return None
def get_location_from_postcode(postcode):
    """
    Resolve a German postcode into:
    - state
    - region / municipality

    Returns (None, None) if the postcode cannot be resolved.
    """

    if not postcode:
        return None, None

    result = GERMAN_POSTCODES.query_postal_code(
        str(postcode)
    )

    if result is None:
        return None, None

    state = result.get("state_name")
    region = result.get("place_name")

    if pd.isna(state):
        state = None

    if pd.isna(region):
        region = None

    return state, region

load_dotenv()

# --------------------------------------------------
# Search configuration
# --------------------------------------------------

#SEARCH_LOCATION = "Berlin"
#SEARCH_LOCATION = [
#    "Düsseldorf"
    
#]

SEARCH_LOCATION = "Düsseldorf"
SEARCH_STATE = "Nordrhein_Westfalen"
MAX_LISTINGS = 5

SEARCH_LOCATION_STATE = {
    "Berlin": "Berlin",
    "Hamburg": "Hamburg",
    "München": "Bayern",
    "Düsseldorf": "Nordrhein_Westfalen",
    "Köln": "Nordrhein_Westfalen",
    "Frankfurt": "Hessen",
    "Stuttgart": "Baden_Württemberg",
    "Leipzig": "Sachsen",
    "Dresden": "Sachsen",
    "Hannover": "Niedersachsen",
}
MAX_LISTINGS = 5


# --------------------------------------------------
# Fetch listings from external source
# --------------------------------------------------

def fetch_listings():

    print(
        f"Fetching housing listings for "
        f"{SEARCH_LOCATION} from Apify..."
    )

    token = os.getenv("APIFY_TOKEN")

    if not token:
        raise ValueError(
            "APIFY_TOKEN is missing from the .env file."
        )

    actor_id = "igolaizola~immobilienscout24-scraper"

    url = (
        f"https://api.apify.com/v2/acts/"
        f"{actor_id}/run-sync-get-dataset-items"
    )

    payload = {
        "maxItems": 5,
        "location": SEARCH_LOCATION,
        "operation": "buy",
        "propertyType": "house",
        "fetchDetails": True
    }

    response = requests.post(
        url,
        params={
            "token": token
        },
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    listings = response.json()

    print(
        f"Fetched {len(listings)} real listing(s)."
        f"for {SEARCH_LOCATION}."
    )

    return listings

# --------------------------------------------------
# Normalize external listing
# --------------------------------------------------

def extract_detail_attributes(raw_listing):
    """
    Collect label -> text/value pairs from all ATTRIBUTE_LIST
    sections in the listing details.
    """

    details = raw_listing.get("_details") or {}
    sections = details.get("sections", [])

    extracted = {}

    for section in sections:

        if section.get("type") != "ATTRIBUTE_LIST":
            continue

        for attribute in section.get("attributes", []):

            label = attribute.get("label")

            if not label:
                continue

            value = (
                attribute.get("text")
                or attribute.get("value")
            )

            # CHECK fields may not have text
            if value is None and attribute.get("type") == "CHECK":
                value = True

            extracted[label.strip()] = value

    return extracted

def parse_number(value):
    """
    Convert strings such as:
    '€1,050,000' -> 1050000.0
    '233 m²'     -> 233.0
    '7 rms'      -> 7.0
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value)

    # Remove non-breaking spaces
    value = value.replace("\xa0", " ")

    # Keep digits, commas, dots and minus signs
    cleaned = re.sub(
        r"[^\d,.\-]",
        "",
        value
    )

    if not cleaned:
        return None

    # Handle values like €1,050,000
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", "")

    # Handle German-style decimals such as 233,5
    elif "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)

    except ValueError:
        return None
  
BUILDING_TYPE_MAP = {
    "Detached house": "single_family_house",
    "Semi-detached house": "semidetached_house",
    "End-terrace house": "end_terrace_house",
    "Mid-terrace house": "mid_terrace_house",
    "Bungalow": "bungalow",
    "Villa": "villa",
    "Farmhouse": "farmhouse",
    "Multi-family house": "multi_family_house",
    "Castle / manor house": "castle_manor_house",
}

CONDITION_MAP = {
    "In mint condition": "mint_condition",
    "Well kept": "well_kept",
    "Modernized": "modernized",
    "Fully renovated": "fully_renovated",
    "Refurbished": "refurbished",
    "Needs renovation": "need_of_renovation",
    "First occupancy": "first_time_use",
    "First occupancy after refurbishment": "first_time_use_after_refurbishment",
    "Negotiable": "negotiable",
    "Ready for demolition": "ripe_for_demolition",
} 

STATE_MAP = {
    "Baden-Württemberg": "Baden_Württemberg",
    "Bayern": "Bayern",
    "Berlin": "Berlin",
    "Brandenburg": "Brandenburg",
    "Bremen": "Bremen",
    "Hamburg": "Hamburg",
    "Hessen": "Hessen",
    "Mecklenburg-Vorpommern": "Mecklenburg_Vorpommern",
    "Niedersachsen": "Niedersachsen",
    "Nordrhein-Westfalen": "Nordrhein_Westfalen",
    "Rheinland-Pfalz": "Rheinland_Pfalz",
    "Saarland": "Saarland",
    "Sachsen": "Sachsen",
    "Sachsen-Anhalt": "Sachsen_Anhalt",
    "Schleswig-Holstein": "Schleswig_Holstein",
    "Thüringen": "Thüringen",
}        
        
def normalize_listing(raw_listing):

    
    address = raw_listing.get("address") or {}

    postcode = address.get("postcode")
    address_line = address.get("line", "")

    detail_attributes = extract_detail_attributes(
        raw_listing
    )

    # --------------------------------------------------
    # Location
    # --------------------------------------------------

    state, region = get_location_from_postcode(
        postcode
    )
    
    if state:
        state = STATE_MAP.get(
             state,
             state
    )
    
    if state is None:
        state = SEARCH_STATE

    if region is None:
        region = SEARCH_LOCATION
    
    

    # -----------------------------------------
    # Main property values
    # -----------------------------------------

    price = parse_number(
        raw_listing.get("price")
    )

    if price is None:
        price = parse_number(
            detail_attributes.get("Purchase price:")
        )

    living_space = parse_number(
        raw_listing.get("livingSpace")
    )

    if living_space is None:
        living_space = parse_number(
            detail_attributes.get(
                "Living space approx.:"
            )
        )

    rooms = parse_number(
        raw_listing.get("rooms")
    )

    lot_area = parse_number(
        detail_attributes.get(
            "Plot space approx.:"
        )
    )

    year_built = parse_number(
        detail_attributes.get(
            "Construction year:"
        )
    )

    if year_built is not None:
        year_built = int(year_built)

#    condition = detail_attributes.get(
#        "Object state:"
#    )

#    building_type = (
#        detail_attributes.get("House type:")
#        or raw_listing.get("realEstateType")
#    )
    
    raw_condition = detail_attributes.get(
         "Object state:"
    )

    raw_building_type = (
         detail_attributes.get("House type:")
         or raw_listing.get("realEstateType")
    )


    condition = CONDITION_MAP.get(
         raw_condition,
         "no_information"
    )

    building_type = BUILDING_TYPE_MAP.get(
         raw_building_type,
         "other_real_estate"
    )
    print(
       f"Building type: {raw_building_type} "
       f"-> {building_type}"
    )

    print(
       f"Condition: {raw_condition} "
       f"-> {condition}"
    )
    
    # -----------------------------------------
    # Return normalized listing
    # -----------------------------------------

    return {
        "source_listing_id": str(
            raw_listing.get("id")
        ),

        "state": state,
        "region": region,

        "living_space": living_space,
        "rooms": rooms,
        "year_built": year_built,
        "lot_area": lot_area,

        "condition": condition,
        "building_type": building_type,

        "asking_price": price,

        "source": "apify_immoscout24",
    }

# --------------------------------------------------
# Validate listing
# --------------------------------------------------

def validate_listing(listing):
    """
    Basic validation before inserting into PostgreSQL.
    """

    required_fields = [
        "source_listing_id",
        "state",
        "region",
        "living_space",
        "rooms",
        "asking_price",
    ]

    for field in required_fields:

        if listing.get(field) is None:

            print(
                f"Skipping listing "
                f"{listing.get('source_listing_id', 'unknown')} "
                f"because '{field}' is missing."
            )

            return False

    # Basic price validation
    if listing["asking_price"] <= 0:
        print(
            f"Skipping listing "
            f"{listing['source_listing_id']} "
            f"because asking price is invalid."
        )

        return False

    # Basic living-space validation
    if listing["living_space"] <= 0:
        print(
            f"Skipping listing "
            f"{listing['source_listing_id']} "
            f"because living space is invalid."
        )

        return False

    return True


# --------------------------------------------------
# Upsert listings into PostgreSQL
# --------------------------------------------------

def save_listings(listings):
    """
    Insert new listings.

    If a listing already exists and relevant property
    information changes, update it and clear its old
    prediction so score_listings.py can score it again.
    """

    engine = get_db_engine()

    query = text("""
        INSERT INTO listings (
            source_listing_id,
            state,
            region,
            living_space,
            rooms,
            year_built,
            lot_area,
            condition,
            building_type,
            asking_price,
            source,
            first_seen_at,
            last_seen_at
        )

        VALUES (
            :source_listing_id,
            :state,
            :region,
            :living_space,
            :rooms,
            :year_built,
            :lot_area,
            :condition,
            :building_type,
            :asking_price,
            :source,
            :first_seen_at,
            :last_seen_at
        )

        ON CONFLICT (source_listing_id)

        DO UPDATE SET
            state = EXCLUDED.state,
            region = EXCLUDED.region,
            living_space = EXCLUDED.living_space,
            rooms = EXCLUDED.rooms,
            year_built = EXCLUDED.year_built,
            lot_area = EXCLUDED.lot_area,
            condition = EXCLUDED.condition,
            building_type = EXCLUDED.building_type,
            asking_price = EXCLUDED.asking_price,
            source = EXCLUDED.source,
            last_seen_at = EXCLUDED.last_seen_at,

            predicted_price = NULL,
            valuation_delta = NULL,
            valuation_delta_pct = NULL,
            predicted_at = NULL

        WHERE
            listings.state
                IS DISTINCT FROM EXCLUDED.state

            OR listings.region
                IS DISTINCT FROM EXCLUDED.region

            OR listings.living_space
                IS DISTINCT FROM EXCLUDED.living_space

            OR listings.rooms
                IS DISTINCT FROM EXCLUDED.rooms

            OR listings.year_built
                IS DISTINCT FROM EXCLUDED.year_built

            OR listings.lot_area
                IS DISTINCT FROM EXCLUDED.lot_area

            OR listings.condition
                IS DISTINCT FROM EXCLUDED.condition

            OR listings.building_type
                IS DISTINCT FROM EXCLUDED.building_type

            OR listings.asking_price
                IS DISTINCT FROM EXCLUDED.asking_price;
    """)

    now = datetime.now()

    inserted_or_updated = 0

    with engine.begin() as conn:

        for listing in listings:

            listing["first_seen_at"] = now
            listing["last_seen_at"] = now

            conn.execute(
                query,
                listing
            )

            inserted_or_updated += 1

    print(
        f"Processed {inserted_or_updated} listing(s) "
        "in PostgreSQL."
    )


# --------------------------------------------------
# Main ingestion pipeline
# --------------------------------------------------

def run_ingestion():

    print("=" * 60)
    print("HOUSING LISTING INGESTION PIPELINE")
    print("=" * 60)

    # -----------------------------------------
    # 1. Fetch raw listings
    # -----------------------------------------

    raw_listings = fetch_listings()
    first_listing = raw_listings[0]
    
    attrs = extract_detail_attributes(
    first_listing
    )

    print("\nEXTRACTED DETAIL ATTRIBUTES:")

    for key, value in attrs.items():
        print(f"{key} -> {value}")
    
    print("\nADDRESS:")
    pprint(first_listing.get("address"))

    print("\nATTRIBUTES:")
    pprint(first_listing.get("attributes"))
    
    print("\nPRICE:")
    print(first_listing.get("price"))

    print("\nLIVING SPACE:")
    print(first_listing.get("livingSpace"))

    print("\nROOMS:")
    print(first_listing.get("rooms"))
    
    print("\nREAL ESTATE TYPE:")
    print(first_listing.get("realEstateType"))
    
    if first_listing:
       print("\nTOP LEVEL KEYS:")
       print(first_listing.keys())    
       
       
       print("\nDETAIL KEYS:")
       print(
            first_listing.get("_details", {}).keys()
       )    
       print("\nSECTION TYPES:")
       details = first_listing.get("_details", {})
       for section in details.get("sections", []):
            if section.get("type") == "ATTRIBUTE_LIST":
               print("\nATTRIBUTE_LIST SECTION:")
               pprint(section)
               break 
               
#       print("\nFIRST RAW LISTING:")
#       pprint(
#           raw_listings[0],
#           sort_dicts=False,
#           width=120
#       )

    if not first_listing:

        print("No listings returned from source.")
        return


    # -----------------------------------------
    # 2. Normalize listings
    # -----------------------------------------

    normalized_listings = []

    for raw_listing in raw_listings:

        try:

            listing = normalize_listing(
                raw_listing
            )

            normalized_listings.append(
                listing
            )

        except Exception as error:

            print(
                "Failed to normalize listing:",
                error
            )


    # -----------------------------------------
    # 3. Validate listings
    # -----------------------------------------

    valid_listings = []

    for listing in normalized_listings:

        if validate_listing(listing):

            valid_listings.append(
                listing
            )


    print(
        f"{len(valid_listings)} valid listing(s) "
        "ready for database ingestion."
    )


    if not valid_listings:

        print("No valid listings to save.")
        return


    # -----------------------------------------
    # 4. Save to PostgreSQL
    # -----------------------------------------

    save_listings(
        valid_listings
    )


    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)


# --------------------------------------------------
# Run script
# --------------------------------------------------

if __name__ == "__main__":

    listings = fetch_listings()

    if listings:

        print("\nFIRST LISTING:")
        print(listings[0])
    run_ingestion()
