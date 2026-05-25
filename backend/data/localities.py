"""
Locality & GMB Category database for hyper-local lead generation.
Covers Mumbai with 50+ localities across 4 regions.
"""
from typing import Dict, List

# ── GMB Category Presets ──────────────────────────────────────────────────────
GMB_CATEGORIES: List[str] = [
    "Dental Clinic", "Dentist", "Orthodontist",
    "Gym", "Fitness Centre", "Yoga Studio", "CrossFit Gym",
    "Restaurant", "Cafe", "Bakery", "Fast Food Restaurant",
    "Hospital", "Clinic", "Physiotherapy Centre",
    "Law Firm", "Advocate", "Legal Services",
    "CA Firm", "Chartered Accountant", "Tax Consultant",
    "Real Estate Agency", "Property Dealer",
    "Interior Designer", "Interior Decorator",
    "Digital Marketing Agency", "IT Company", "Software Company",
    "Beauty Salon", "Hair Salon", "Spa", "Nail Salon",
    "Pharmacy", "Medical Store",
    "Coaching Centre", "Tuition Centre", "School",
    "Hotel", "Guest House", "Homestay",
    "Event Management Company", "Wedding Planner",
    "Photographer", "Photography Studio",
    "Automobile Dealer", "Car Service Centre",
    "Courier Service", "Logistics Company",
    "Packers and Movers",
    "Jewellery Shop", "Gold Shop",
    "Clothing Store", "Boutique",
    "Plumber", "Electrician", "AC Repair",
]

# ── City → Region → Localities ────────────────────────────────────────────────
CITY_LOCALITIES: Dict[str, Dict[str, List[Dict]]] = {
    "Mumbai": {
        "Western Suburbs": [
            {"name": "Andheri East",    "query": "Andheri East, Mumbai"},
            {"name": "Andheri West",    "query": "Andheri West, Mumbai"},
            {"name": "Goregaon East",   "query": "Goregaon East, Mumbai"},
            {"name": "Goregaon West",   "query": "Goregaon West, Mumbai"},
            {"name": "Malad East",      "query": "Malad East, Mumbai"},
            {"name": "Malad West",      "query": "Malad West, Mumbai"},
            {"name": "Borivali East",   "query": "Borivali East, Mumbai"},
            {"name": "Borivali West",   "query": "Borivali West, Mumbai"},
            {"name": "Kandivali East",  "query": "Kandivali East, Mumbai"},
            {"name": "Kandivali West",  "query": "Kandivali West, Mumbai"},
            {"name": "Bandra East",     "query": "Bandra East, Mumbai"},
            {"name": "Bandra West",     "query": "Bandra West, Mumbai"},
            {"name": "Khar",            "query": "Khar, Mumbai"},
            {"name": "Juhu",            "query": "Juhu, Mumbai"},
            {"name": "Vile Parle East", "query": "Vile Parle East, Mumbai"},
            {"name": "Vile Parle West", "query": "Vile Parle West, Mumbai"},
            {"name": "Santacruz East",  "query": "Santacruz East, Mumbai"},
            {"name": "Santacruz West",  "query": "Santacruz West, Mumbai"},
            {"name": "Jogeshwari East", "query": "Jogeshwari East, Mumbai"},
            {"name": "Jogeshwari West", "query": "Jogeshwari West, Mumbai"},
            {"name": "Dahisar East",    "query": "Dahisar East, Mumbai"},
            {"name": "Dahisar West",    "query": "Dahisar West, Mumbai"},
        ],
        "Eastern Suburbs": [
            {"name": "Powai",           "query": "Powai, Mumbai"},
            {"name": "Ghatkopar East",  "query": "Ghatkopar East, Mumbai"},
            {"name": "Ghatkopar West",  "query": "Ghatkopar West, Mumbai"},
            {"name": "Mulund East",     "query": "Mulund East, Mumbai"},
            {"name": "Mulund West",     "query": "Mulund West, Mumbai"},
            {"name": "Kurla East",      "query": "Kurla East, Mumbai"},
            {"name": "Kurla West",      "query": "Kurla West, Mumbai"},
            {"name": "Vikhroli",        "query": "Vikhroli, Mumbai"},
            {"name": "Bhandup",         "query": "Bhandup, Mumbai"},
            {"name": "Kanjurmarg",      "query": "Kanjurmarg, Mumbai"},
            {"name": "Chembur",         "query": "Chembur, Mumbai"},
            {"name": "Govandi",         "query": "Govandi, Mumbai"},
            {"name": "Mankhurd",        "query": "Mankhurd, Mumbai"},
            {"name": "Wadala",          "query": "Wadala, Mumbai"},
            {"name": "Sion",            "query": "Sion, Mumbai"},
        ],
        "South Mumbai": [
            {"name": "Colaba",          "query": "Colaba, Mumbai"},
            {"name": "Nariman Point",   "query": "Nariman Point, Mumbai"},
            {"name": "Marine Lines",    "query": "Marine Lines, Mumbai"},
            {"name": "Churchgate",      "query": "Churchgate, Mumbai"},
            {"name": "Fort",            "query": "Fort, Mumbai"},
            {"name": "Dadar East",      "query": "Dadar East, Mumbai"},
            {"name": "Dadar West",      "query": "Dadar West, Mumbai"},
            {"name": "Parel",           "query": "Parel, Mumbai"},
            {"name": "Lower Parel",     "query": "Lower Parel, Mumbai"},
            {"name": "Worli",           "query": "Worli, Mumbai"},
            {"name": "Mahalaxmi",       "query": "Mahalaxmi, Mumbai"},
            {"name": "Byculla",         "query": "Byculla, Mumbai"},
            {"name": "Grant Road",      "query": "Grant Road, Mumbai"},
            {"name": "Cuffe Parade",    "query": "Cuffe Parade, Mumbai"},
            {"name": "Walkeshwar",      "query": "Walkeshwar, Mumbai"},
        ],
        "Navi Mumbai": [
            {"name": "Vashi",           "query": "Vashi, Navi Mumbai"},
            {"name": "Belapur",         "query": "Belapur, Navi Mumbai"},
            {"name": "Kharghar",        "query": "Kharghar, Navi Mumbai"},
            {"name": "Panvel",          "query": "Panvel, Navi Mumbai"},
            {"name": "Nerul",           "query": "Nerul, Navi Mumbai"},
            {"name": "Airoli",          "query": "Airoli, Navi Mumbai"},
            {"name": "Ghansoli",        "query": "Ghansoli, Navi Mumbai"},
            {"name": "Koparkhairane",   "query": "Koparkhairane, Navi Mumbai"},
            {"name": "Sanpada",         "query": "Sanpada, Navi Mumbai"},
            {"name": "Turbhe",          "query": "Turbhe, Navi Mumbai"},
        ],
    },
    "Delhi": {
        "North Delhi": [
            {"name": "Rohini",          "query": "Rohini, Delhi"},
            {"name": "Pitampura",       "query": "Pitampura, Delhi"},
            {"name": "Shalimar Bagh",   "query": "Shalimar Bagh, Delhi"},
            {"name": "Model Town",      "query": "Model Town, Delhi"},
            {"name": "Burari",          "query": "Burari, Delhi"},
        ],
        "South Delhi": [
            {"name": "Saket",           "query": "Saket, Delhi"},
            {"name": "Hauz Khas",       "query": "Hauz Khas, Delhi"},
            {"name": "Green Park",      "query": "Green Park, Delhi"},
            {"name": "Vasant Kunj",     "query": "Vasant Kunj, Delhi"},
            {"name": "Defence Colony",  "query": "Defence Colony, Delhi"},
            {"name": "Greater Kailash", "query": "Greater Kailash, Delhi"},
            {"name": "Malviya Nagar",   "query": "Malviya Nagar, Delhi"},
        ],
        "West Delhi": [
            {"name": "Janakpuri",       "query": "Janakpuri, Delhi"},
            {"name": "Dwarka",          "query": "Dwarka, Delhi"},
            {"name": "Rajouri Garden",  "query": "Rajouri Garden, Delhi"},
            {"name": "Punjabi Bagh",    "query": "Punjabi Bagh, Delhi"},
        ],
        "East Delhi": [
            {"name": "Laxmi Nagar",     "query": "Laxmi Nagar, Delhi"},
            {"name": "Preet Vihar",     "query": "Preet Vihar, Delhi"},
            {"name": "Mayur Vihar",     "query": "Mayur Vihar, Delhi"},
            {"name": "Patparganj",      "query": "Patparganj, Delhi"},
        ],
    },
    "Bangalore": {
        "North Bangalore": [
            {"name": "Hebbal",          "query": "Hebbal, Bangalore"},
            {"name": "Yelahanka",       "query": "Yelahanka, Bangalore"},
            {"name": "Sahakara Nagar",  "query": "Sahakara Nagar, Bangalore"},
            {"name": "Jalahalli",       "query": "Jalahalli, Bangalore"},
        ],
        "South Bangalore": [
            {"name": "Jayanagar",       "query": "Jayanagar, Bangalore"},
            {"name": "JP Nagar",        "query": "JP Nagar, Bangalore"},
            {"name": "Banashankari",    "query": "Banashankari, Bangalore"},
            {"name": "BTM Layout",      "query": "BTM Layout, Bangalore"},
            {"name": "Koramangala",     "query": "Koramangala, Bangalore"},
        ],
        "East Bangalore": [
            {"name": "Whitefield",      "query": "Whitefield, Bangalore"},
            {"name": "Marathahalli",    "query": "Marathahalli, Bangalore"},
            {"name": "Indiranagar",     "query": "Indiranagar, Bangalore"},
            {"name": "Banaswadi",       "query": "Banaswadi, Bangalore"},
            {"name": "KR Puram",        "query": "KR Puram, Bangalore"},
        ],
        "West Bangalore": [
            {"name": "Rajajinagar",     "query": "Rajajinagar, Bangalore"},
            {"name": "Vijayanagar",     "query": "Vijayanagar, Bangalore"},
            {"name": "Malleshwaram",    "query": "Malleshwaram, Bangalore"},
        ],
    },
    "Hyderabad": {
        "West Hyderabad": [
            {"name": "Gachibowli",      "query": "Gachibowli, Hyderabad"},
            {"name": "Madhapur",        "query": "Madhapur, Hyderabad"},
            {"name": "Kondapur",        "query": "Kondapur, Hyderabad"},
            {"name": "Jubilee Hills",   "query": "Jubilee Hills, Hyderabad"},
            {"name": "Banjara Hills",   "query": "Banjara Hills, Hyderabad"},
            {"name": "Miyapur",         "query": "Miyapur, Hyderabad"},
        ],
        "Central Hyderabad": [
            {"name": "Ameerpet",        "query": "Ameerpet, Hyderabad"},
            {"name": "Begumpet",        "query": "Begumpet, Hyderabad"},
            {"name": "Somajiguda",      "query": "Somajiguda, Hyderabad"},
            {"name": "Mehdipatnam",     "query": "Mehdipatnam, Hyderabad"},
        ],
        "East Hyderabad": [
            {"name": "Secunderabad",    "query": "Secunderabad, Hyderabad"},
            {"name": "Uppal",           "query": "Uppal, Hyderabad"},
            {"name": "LB Nagar",        "query": "LB Nagar, Hyderabad"},
        ],
    },
    "Chennai": {
        "North Chennai": [
            {"name": "Anna Nagar",      "query": "Anna Nagar, Chennai"},
            {"name": "Kolathur",        "query": "Kolathur, Chennai"},
            {"name": "Perambur",        "query": "Perambur, Chennai"},
        ],
        "South Chennai": [
            {"name": "Velachery",       "query": "Velachery, Chennai"},
            {"name": "Tambaram",        "query": "Tambaram, Chennai"},
            {"name": "Adyar",           "query": "Adyar, Chennai"},
            {"name": "Besant Nagar",    "query": "Besant Nagar, Chennai"},
            {"name": "Sholinganallur",  "query": "Sholinganallur, Chennai"},
        ],
        "Central Chennai": [
            {"name": "T Nagar",         "query": "T Nagar, Chennai"},
            {"name": "Nungambakkam",    "query": "Nungambakkam, Chennai"},
            {"name": "Egmore",          "query": "Egmore, Chennai"},
        ],
    },
    "Pune": {
        "Central Pune": [
            {"name": "Shivajinagar",    "query": "Shivajinagar, Pune"},
            {"name": "Deccan",          "query": "Deccan, Pune"},
            {"name": "Camp",            "query": "Camp, Pune"},
            {"name": "Kothrud",         "query": "Kothrud, Pune"},
        ],
        "IT Corridors": [
            {"name": "Hinjewadi",       "query": "Hinjewadi, Pune"},
            {"name": "Baner",           "query": "Baner, Pune"},
            {"name": "Aundh",           "query": "Aundh, Pune"},
            {"name": "Wakad",           "query": "Wakad, Pune"},
            {"name": "Viman Nagar",     "query": "Viman Nagar, Pune"},
        ],
        "East Pune": [
            {"name": "Kharadi",         "query": "Kharadi, Pune"},
            {"name": "Hadapsar",        "query": "Hadapsar, Pune"},
            {"name": "Wagholi",         "query": "Wagholi, Pune"},
        ],
    },
}


def get_localities(city: str) -> Dict[str, List[Dict]]:
    """Return locality map for a given city (empty dict if not found)."""
    return CITY_LOCALITIES.get(city, {})


def get_all_locality_queries(city: str, localities: List[str]) -> List[str]:
    """
    Given a city and a list of locality names, return their query strings.
    If localities is empty, returns just the city name as query.
    """
    if not localities:
        return [city]
    all_locs = {}
    for region_locs in CITY_LOCALITIES.get(city, {}).values():
        for loc in region_locs:
            all_locs[loc["name"]] = loc["query"]
    return [all_locs[l] for l in localities if l in all_locs]


def get_all_queries(city: str) -> List[str]:
    """Return query strings for ALL localities in a city."""
    queries = []
    for region_locs in CITY_LOCALITIES.get(city, {}).values():
        for loc in region_locs:
            queries.append(loc["query"])
    return queries if queries else [city]


SUPPORTED_CITIES = list(CITY_LOCALITIES.keys())
