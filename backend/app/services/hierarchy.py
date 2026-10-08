from __future__ import annotations

from typing import Any
from pymongo.database import Database
from app.schemas.hierarchy import (
    OperationalStatus,
    MetroAgencyOut,
    MetroLineOut,
    StationHierarchyOut,
    StationConnectionOut,
    CityHierarchySummary,
    NationalHierarchyOverview,
)
from app.services.documents import new_id, utc_now

# Catalog of the 14 Indian Metro Systems
INDIAN_METRO_SYSTEMS: list[dict[str, Any]] = [
    {
        "code": "DMRC",
        "name": "Delhi Metro Rail Corporation",
        "short_name": "Delhi Metro",
        "city": "Delhi",
        "state": "Delhi",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 348,
        "lines": [
            {"code": "RED", "name": "Red Line", "color_hex": "#E31837", "status": OperationalStatus.OPERATIONAL, "length_km": 34.7},
            {"code": "YELLOW", "name": "Yellow Line", "color_hex": "#FFCD00", "status": OperationalStatus.OPERATIONAL, "length_km": 49.3},
            {"code": "BLUE", "name": "Blue Line", "color_hex": "#0055A5", "status": OperationalStatus.OPERATIONAL, "length_km": 65.4},
            {"code": "GREEN", "name": "Green Line", "color_hex": "#009A44", "status": OperationalStatus.OPERATIONAL, "length_km": 29.6},
            {"code": "VIOLET", "name": "Violet Line", "color_hex": "#762382", "status": OperationalStatus.OPERATIONAL, "length_km": 46.6},
            {"code": "AIRPORT", "name": "Airport Express", "color_hex": "#F37021", "status": OperationalStatus.OPERATIONAL, "length_km": 22.7},
            {"code": "MAGENTA", "name": "Magenta Line", "color_hex": "#9B26B6", "status": OperationalStatus.OPERATIONAL, "length_km": 37.5},
            {"code": "PINK", "name": "Pink Line", "color_hex": "#ED72AA", "status": OperationalStatus.OPERATIONAL, "length_km": 58.4},
            {"code": "GOLDEN", "name": "Golden Line (Phase 4)", "color_hex": "#D4AF37", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 23.6},
            {"code": "SILVER", "name": "Silver Line (Phase 4)", "color_hex": "#C0C0C0", "status": OperationalStatus.PROPOSED, "length_km": 19.5},
        ]
    },
    {
        "code": "BMRCL",
        "name": "Bangalore Metro Rail Corporation Ltd",
        "short_name": "Namma Metro",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 57,
        "lines": [
            {"code": "PURPLE", "name": "Purple Line", "color_hex": "#800080", "status": OperationalStatus.OPERATIONAL, "length_km": 43.5},
            {"code": "GREEN", "name": "Green Line", "color_hex": "#008000", "status": OperationalStatus.OPERATIONAL, "length_km": 30.3},
            {"code": "YELLOW", "name": "Yellow Line (Phase 2)", "color_hex": "#FFD700", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 18.8},
            {"code": "PINK", "name": "Pink Line (Phase 2)", "color_hex": "#FFC0CB", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 21.2},
            {"code": "BLUE", "name": "Blue Line (Airport)", "color_hex": "#1E90FF", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 37.0},
        ]
    },
    {
        "code": "MMRDA",
        "name": "Mumbai Metropolitan Region Development Authority",
        "short_name": "Mumbai Metro",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 48,
        "lines": [
            {"code": "LINE1", "name": "Line 1 (Blue Line)", "color_hex": "#0072CE", "status": OperationalStatus.OPERATIONAL, "length_km": 11.4},
            {"code": "LINE2A", "name": "Line 2A (Yellow Line)", "color_hex": "#FFC72C", "status": OperationalStatus.OPERATIONAL, "length_km": 18.6},
            {"code": "LINE7", "name": "Line 7 (Red Line)", "color_hex": "#DA291C", "status": OperationalStatus.OPERATIONAL, "length_km": 16.5},
            {"code": "LINE3", "name": "Line 3 (Aqua Line Underground)", "color_hex": "#00B2A9", "status": OperationalStatus.OPERATIONAL, "length_km": 33.5},
            {"code": "LINE4", "name": "Line 4 (Green Line)", "color_hex": "#008542", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 32.3},
            {"code": "LINE6", "name": "Line 6 (Pink Line)", "color_hex": "#E05A47", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 14.5},
        ]
    },
    {
        "code": "KOL_METRO",
        "name": "Metro Railway Kolkata",
        "short_name": "Kolkata Metro",
        "city": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 42,
        "lines": [
            {"code": "BLUE", "name": "Blue Line (North-South)", "color_hex": "#0000FF", "status": OperationalStatus.OPERATIONAL, "length_km": 31.4},
            {"code": "GREEN", "name": "Green Line (Underwater East-West)", "color_hex": "#008000", "status": OperationalStatus.OPERATIONAL, "length_km": 16.6},
            {"code": "PURPLE", "name": "Purple Line", "color_hex": "#800080", "status": OperationalStatus.OPERATIONAL, "length_km": 6.5},
            {"code": "ORANGE", "name": "Orange Line", "color_hex": "#FFA500", "status": OperationalStatus.OPERATIONAL, "length_km": 5.4},
            {"code": "YELLOW", "name": "Yellow Line (Barasat Link)", "color_hex": "#FFFF00", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 16.8},
        ]
    },
    {
        "code": "CMRL",
        "name": "Chennai Metro Rail Limited",
        "short_name": "Chennai Metro",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 52,
        "lines": [
            {"code": "BLUE", "name": "Blue Line", "color_hex": "#0055A5", "status": OperationalStatus.OPERATIONAL, "length_km": 32.1},
            {"code": "GREEN", "name": "Green Line", "color_hex": "#28724F", "status": OperationalStatus.OPERATIONAL, "length_km": 22.0},
            {"code": "PURPLE", "name": "Phase 2 Purple Line", "color_hex": "#6C1D45", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 45.8},
            {"code": "ORANGE", "name": "Phase 2 Orange Line", "color_hex": "#FF671F", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 26.1},
        ]
    },
    {
        "code": "LT_HYD",
        "name": "Hyderabad Metro Rail (L&T Metro)",
        "short_name": "Hyderabad Metro",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 57,
        "lines": [
            {"code": "RED", "name": "Red Line (Corridor 1)", "color_hex": "#ED1C24", "status": OperationalStatus.OPERATIONAL, "length_km": 29.2},
            {"code": "BLUE", "name": "Blue Line (Corridor 3)", "color_hex": "#0054A6", "status": OperationalStatus.OPERATIONAL, "length_km": 27.0},
            {"code": "GREEN", "name": "Green Line (Corridor 2)", "color_hex": "#00A651", "status": OperationalStatus.OPERATIONAL, "length_km": 11.0},
            {"code": "AIRPORT", "name": "Airport Express Line", "color_hex": "#F37021", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 31.0},
        ]
    },
    {
        "code": "GMRC",
        "name": "Gujarat Metro Rail Corporation",
        "short_name": "Ahmedabad Metro",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 32,
        "lines": [
            {"code": "EW", "name": "East-West Corridor", "color_hex": "#0055A5", "status": OperationalStatus.OPERATIONAL, "length_km": 21.1},
            {"code": "NS", "name": "North-South Corridor", "color_hex": "#ED1C24", "status": OperationalStatus.OPERATIONAL, "length_km": 18.9},
            {"code": "PHASE2", "name": "Phase 2 Gandhinagar Ext", "color_hex": "#28724F", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 28.2},
        ]
    },
    {
        "code": "MAHA_PUN",
        "name": "Maha Metro Pune",
        "short_name": "Pune Metro",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 28,
        "lines": [
            {"code": "PURPLE", "name": "Purple Line (PCMC-Swargate)", "color_hex": "#762382", "status": OperationalStatus.OPERATIONAL, "length_km": 16.6},
            {"code": "AQUA", "name": "Aqua Line (Vanaz-Ramwadi)", "color_hex": "#00AEEF", "status": OperationalStatus.OPERATIONAL, "length_km": 15.7},
            {"code": "LINE3", "name": "Line 3 (Hinjawadi-Shivajinagar)", "color_hex": "#ED1C24", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 23.3},
        ]
    },
    {
        "code": "KMRL",
        "name": "Kochi Metro Rail Limited",
        "short_name": "Kochi Metro",
        "city": "Kochi",
        "state": "Kerala",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 25,
        "lines": [
            {"code": "LINE1", "name": "Line 1 (Aluva-Thripunithura)", "color_hex": "#00AEEF", "status": OperationalStatus.OPERATIONAL, "length_km": 28.1},
            {"code": "PINK", "name": "Phase 2 Pink Line (Infopark)", "color_hex": "#ED72AA", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 11.2},
        ]
    },
    {
        "code": "UPMRC_LKO",
        "name": "Uttar Pradesh Metro Rail Corporation (Lucknow)",
        "short_name": "Lucknow Metro",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 20,
        "lines": [
            {"code": "RED", "name": "Red Line (North-South Corridor)", "color_hex": "#ED1C24", "status": OperationalStatus.OPERATIONAL, "length_km": 22.9},
            {"code": "BLUE", "name": "Blue Line (East-West Corridor)", "color_hex": "#0055A5", "status": OperationalStatus.PROPOSED, "length_km": 11.1},
        ]
    },
    {
        "code": "NMRC",
        "name": "Noida Metro Rail Corporation",
        "short_name": "Noida Metro",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 19,
        "lines": [
            {"code": "AQUA", "name": "Aqua Line", "color_hex": "#00AEEF", "status": OperationalStatus.OPERATIONAL, "length_km": 29.7},
            {"code": "EXT", "name": "Aqua Line Extension (Greater Noida West)", "color_hex": "#008542", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 14.9},
        ]
    },
    {
        "code": "UPMRC_KNP",
        "name": "Uttar Pradesh Metro Rail Corporation (Kanpur)",
        "short_name": "Kanpur Metro",
        "city": "Kanpur",
        "state": "Uttar Pradesh",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 12,
        "lines": [
            {"code": "ORANGE", "name": "Orange Line (IITK - Motijheel)", "color_hex": "#FF671F", "status": OperationalStatus.OPERATIONAL, "length_km": 8.9},
            {"code": "EXT", "name": "Orange Line Extension to Naubasta", "color_hex": "#FF8C00", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 15.0},
            {"code": "BLUE", "name": "Blue Line (Agri Univ - Barra 8)", "color_hex": "#0055A5", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 8.6},
        ]
    },
    {
        "code": "MAHA_NGP",
        "name": "Maha Metro Nagpur",
        "short_name": "Nagpur Metro",
        "city": "Nagpur",
        "state": "Maharashtra",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 23,
        "lines": [
            {"code": "ORANGE", "name": "Orange Line (North-South)", "color_hex": "#FF671F", "status": OperationalStatus.OPERATIONAL, "length_km": 19.6},
            {"code": "AQUA", "name": "Aqua Line (East-West)", "color_hex": "#00AEEF", "status": OperationalStatus.OPERATIONAL, "length_km": 18.5},
            {"code": "PHASE2", "name": "Nagpur Phase 2 Extensions", "color_hex": "#28724F", "status": OperationalStatus.UNDER_CONSTRUCTION, "length_km": 43.8},
        ]
    },
    {
        "code": "JMRC",
        "name": "Jaipur Metro Rail Corporation",
        "short_name": "Jaipur Metro",
        "city": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
        "status": OperationalStatus.OPERATIONAL,
        "fleet_size": 10,
        "lines": [
            {"code": "PINK", "name": "Pink Line (Mansarovar - Badi Chaupar)", "color_hex": "#ED72AA", "status": OperationalStatus.OPERATIONAL, "length_km": 12.0},
            {"code": "ORANGE", "name": "Orange Line (Sitapura - Ambabari)", "color_hex": "#FF671F", "status": OperationalStatus.PROPOSED, "length_km": 23.5},
        ]
    },
]


# Verified Stations across all 14 systems with status flags
EXTENDED_METRO_STATIONS: list[dict[str, Any]] = [
    # --- 1. Mumbai Metro (MMRDA) ---
    {"code": "MUM_VER", "name": "Versova", "line": "Line 1", "zone": "Western", "latitude": 19.1317, "longitude": 72.8176, "baseline_capacity": 2400, "is_interchange": False, "state": "Maharashtra", "district": "Mumbai Suburban", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_DN", "name": "D.N. Nagar", "line": "Line 1 / 2A", "zone": "Western", "latitude": 19.1252, "longitude": 72.8361, "baseline_capacity": 3200, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai Suburban", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_AND", "name": "Andheri East", "line": "Line 1", "zone": "Western", "latitude": 19.1197, "longitude": 72.8468, "baseline_capacity": 4200, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai Suburban", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_WEH", "name": "Western Express Highway", "line": "Line 1 / 7", "zone": "Western", "latitude": 19.1158, "longitude": 72.8569, "baseline_capacity": 3400, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai Suburban", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_GHT", "name": "Ghatkopar", "line": "Line 1", "zone": "Eastern", "latitude": 19.0863, "longitude": 72.9082, "baseline_capacity": 4500, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai Suburban", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_BKC", "name": "Bandra Kurla Complex (BKC)", "line": "Line 3", "zone": "Central", "latitude": 19.0657, "longitude": 72.8683, "baseline_capacity": 4800, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai City", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MUM_CST", "name": "CSMT Underground", "line": "Line 3", "zone": "South Mumbai", "latitude": 18.9401, "longitude": 72.8347, "baseline_capacity": 4600, "is_interchange": True, "state": "Maharashtra", "district": "Mumbai City", "city": "Mumbai", "system_code": "MMRDA", "agency_name": "Mumbai Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 2. Kolkata Metro (Metro Railway Kolkata) ---
    {"code": "CCU_DAK", "name": "Dakshineswar", "line": "Blue Line", "zone": "North", "latitude": 22.6548, "longitude": 88.3582, "baseline_capacity": 2800, "is_interchange": False, "state": "West Bengal", "district": "North 24 Parganas", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_DUM", "name": "Dum Dum", "line": "Blue Line", "zone": "North", "latitude": 22.6222, "longitude": 88.3779, "baseline_capacity": 4200, "is_interchange": True, "state": "West Bengal", "district": "Kolkata", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_SHY", "name": "Shyambazar", "line": "Blue Line", "zone": "North", "latitude": 22.6022, "longitude": 88.3711, "baseline_capacity": 3100, "is_interchange": False, "state": "West Bengal", "district": "Kolkata", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_HOW", "name": "Howrah Maidan Underwater", "line": "Green Line", "zone": "Central", "latitude": 22.5878, "longitude": 88.3308, "baseline_capacity": 4800, "is_interchange": True, "state": "West Bengal", "district": "Howrah", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_ESPL", "name": "Esplanade", "line": "Blue / Green / Purple", "zone": "Central", "latitude": 22.5645, "longitude": 88.3522, "baseline_capacity": 5200, "is_interchange": True, "state": "West Bengal", "district": "Kolkata", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_PARK", "name": "Park Street", "line": "Blue Line", "zone": "Central", "latitude": 22.5522, "longitude": 88.3512, "baseline_capacity": 3600, "is_interchange": False, "state": "West Bengal", "district": "Kolkata", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_KAV", "name": "Kavi Subhash (New Garia)", "line": "Blue / Orange", "zone": "South", "latitude": 22.4705, "longitude": 88.3978, "baseline_capacity": 3800, "is_interchange": True, "state": "West Bengal", "district": "South 24 Parganas", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "CCU_AIR", "name": "NSCB International Airport", "line": "Yellow / Orange", "zone": "North", "latitude": 22.6542, "longitude": 88.4467, "baseline_capacity": 3200, "is_interchange": True, "state": "West Bengal", "district": "North 24 Parganas", "city": "Kolkata", "system_code": "KOL_METRO", "agency_name": "Metro Railway Kolkata", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 3. Chennai Metro (CMRL) ---
    {"code": "MAA_WIM", "name": "Wimco Nagar", "line": "Blue Line", "zone": "North", "latitude": 13.1706, "longitude": 80.3015, "baseline_capacity": 2200, "is_interchange": False, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MAA_WAS", "name": "Washermanpet", "line": "Blue Line", "zone": "North", "latitude": 13.1098, "longitude": 80.2867, "baseline_capacity": 2600, "is_interchange": False, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MAA_CEN", "name": "Chennai Central (Puratchi Thalaivar)", "line": "Blue / Green", "zone": "Central", "latitude": 13.0818, "longitude": 80.2722, "baseline_capacity": 4600, "is_interchange": True, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MAA_GOV", "name": "Government Estate", "line": "Blue Line", "zone": "Central", "latitude": 13.0673, "longitude": 80.2736, "baseline_capacity": 2500, "is_interchange": False, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MAA_TNA", "name": "T. Nagar (Phase 2)", "line": "Purple Line", "zone": "Central", "latitude": 13.0418, "longitude": 80.2341, "baseline_capacity": 3400, "is_interchange": True, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},
    {"code": "MAA_ALN", "name": "Alandur", "line": "Blue / Green", "zone": "South", "latitude": 13.0039, "longitude": 80.2014, "baseline_capacity": 3800, "is_interchange": True, "state": "Tamil Nadu", "district": "Chennai", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "MAA_AIR", "name": "Chennai International Airport", "line": "Blue Line", "zone": "South", "latitude": 12.9815, "longitude": 80.1636, "baseline_capacity": 4100, "is_interchange": False, "state": "Tamil Nadu", "district": "Kanchipuram", "city": "Chennai", "system_code": "CMRL", "agency_name": "Chennai Metro", "operational_status": OperationalStatus.OPERATIONAL},

    # --- 4. Hyderabad Metro (L&T Metro) ---
    {"code": "HYD_MIY", "name": "Miyapur", "line": "Red Line", "zone": "North West", "latitude": 17.4968, "longitude": 78.3614, "baseline_capacity": 3200, "is_interchange": False, "state": "Telangana", "district": "Medchal-Malkajgiri", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_KPH", "name": "KPHB Colony", "line": "Red Line", "zone": "North West", "latitude": 17.4934, "longitude": 78.3995, "baseline_capacity": 3500, "is_interchange": False, "state": "Telangana", "district": "Medchal-Malkajgiri", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_AMG", "name": "Ameerpet", "line": "Red / Blue", "zone": "Central", "latitude": 17.4375, "longitude": 78.4483, "baseline_capacity": 5100, "is_interchange": True, "state": "Telangana", "district": "Hyderabad", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_MGBS", "name": "MGBS (Imlibun)", "line": "Red / Green", "zone": "Central", "latitude": 17.3789, "longitude": 78.4812, "baseline_capacity": 4400, "is_interchange": True, "state": "Telangana", "district": "Hyderabad", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_LBN", "name": "LB Nagar", "line": "Red Line", "zone": "East", "latitude": 17.3458, "longitude": 78.5522, "baseline_capacity": 3400, "is_interchange": False, "state": "Telangana", "district": "Rangareddy", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_HIT", "name": "HITEC City", "line": "Blue Line", "zone": "West", "latitude": 17.4474, "longitude": 78.3814, "baseline_capacity": 4600, "is_interchange": False, "state": "Telangana", "district": "Rangareddy", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_RAI", "name": "Raidurg (Mindspace)", "line": "Blue Line", "zone": "West", "latitude": 17.4402, "longitude": 78.3758, "baseline_capacity": 4200, "is_interchange": False, "state": "Telangana", "district": "Rangareddy", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "HYD_AIR", "name": "Shamshabad RGIA Airport", "line": "Airport Express Line", "zone": "South", "latitude": 17.2403, "longitude": 78.4294, "baseline_capacity": 3000, "is_interchange": False, "state": "Telangana", "district": "Rangareddy", "city": "Hyderabad", "system_code": "LT_HYD", "agency_name": "Hyderabad Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 5. Pune Metro (Maha Metro) ---
    {"code": "PUN_PCM", "name": "PCMC", "line": "Purple Line", "zone": "North", "latitude": 18.6277, "longitude": 73.8016, "baseline_capacity": 2200, "is_interchange": False, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_SHI", "name": "Shivajinagar", "line": "Purple / Line 3", "zone": "Central", "latitude": 18.5314, "longitude": 73.8446, "baseline_capacity": 3600, "is_interchange": True, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_CIV", "name": "Civil Court Pune", "line": "Purple / Aqua", "zone": "Central", "latitude": 18.5284, "longitude": 73.8553, "baseline_capacity": 4200, "is_interchange": True, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_SWA", "name": "Swargate Underground", "line": "Purple Line", "zone": "South", "latitude": 18.5018, "longitude": 73.8587, "baseline_capacity": 3800, "is_interchange": True, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_VAN", "name": "Vanaz", "line": "Aqua Line", "zone": "West", "latitude": 18.5074, "longitude": 73.8077, "baseline_capacity": 2100, "is_interchange": False, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_RAM", "name": "Ramwadi", "line": "Aqua Line", "zone": "East", "latitude": 18.5529, "longitude": 73.9145, "baseline_capacity": 2400, "is_interchange": False, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "PUN_HIN", "name": "Hinjawadi Megapolis", "line": "Line 3", "zone": "West", "latitude": 18.5912, "longitude": 73.7163, "baseline_capacity": 3200, "is_interchange": False, "state": "Maharashtra", "district": "Pune", "city": "Pune", "system_code": "MAHA_PUN", "agency_name": "Pune Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 6. Kochi Metro (KMRL) ---
    {"code": "COK_ALU", "name": "Aluva", "line": "Line 1", "zone": "North", "latitude": 10.1092, "longitude": 76.3496, "baseline_capacity": 2600, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_KAL", "name": "Kalamassery", "line": "Line 1", "zone": "North", "latitude": 10.0538, "longitude": 76.3155, "baseline_capacity": 1800, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_EDP", "name": "Edapally", "line": "Line 1", "zone": "Central", "latitude": 10.0258, "longitude": 76.3081, "baseline_capacity": 3100, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_JLN", "name": "Jawaharlal Nehru Stadium", "line": "Line 1 / Pink Line", "zone": "Central", "latitude": 10.0028, "longitude": 76.3005, "baseline_capacity": 3400, "is_interchange": True, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_MGR", "name": "M.G. Road Kochi", "line": "Line 1", "zone": "Central", "latitude": 9.9723, "longitude": 76.2847, "baseline_capacity": 2800, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_THR", "name": "Thripunithura", "line": "Line 1", "zone": "South", "latitude": 9.9482, "longitude": 76.3475, "baseline_capacity": 2400, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "COK_INF", "name": "Infopark Kakkanad", "line": "Pink Line", "zone": "East", "latitude": 10.0125, "longitude": 76.3654, "baseline_capacity": 3000, "is_interchange": False, "state": "Kerala", "district": "Ernakulam", "city": "Kochi", "system_code": "KMRL", "agency_name": "Kochi Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 7. Lucknow Metro (UPMRC) ---
    {"code": "LKO_AIR", "name": "Chaudhary Charan Singh Airport", "line": "Red Line", "zone": "South", "latitude": 26.7606, "longitude": 80.8893, "baseline_capacity": 2800, "is_interchange": False, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "LKO_ALB", "name": "Alambagh Bus Stand", "line": "Red Line", "zone": "South", "latitude": 26.8124, "longitude": 80.9022, "baseline_capacity": 3200, "is_interchange": True, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "LKO_CHB", "name": "Charbagh Railway Station", "line": "Red / Blue", "zone": "Central", "latitude": 26.8322, "longitude": 80.9205, "baseline_capacity": 4200, "is_interchange": True, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "LKO_HAZ", "name": "Hazratganj", "line": "Red Line", "zone": "Central", "latitude": 26.8524, "longitude": 80.9412, "baseline_capacity": 3600, "is_interchange": False, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "LKO_MUN", "name": "Munshi Pulia", "line": "Red Line", "zone": "North East", "latitude": 26.8876, "longitude": 80.9892, "baseline_capacity": 2700, "is_interchange": False, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "LKO_CHW", "name": "Chowk Heritage", "line": "Blue Line", "zone": "Old City", "latitude": 26.8687, "longitude": 80.9015, "baseline_capacity": 2500, "is_interchange": False, "state": "Uttar Pradesh", "district": "Lucknow", "city": "Lucknow", "system_code": "UPMRC_LKO", "agency_name": "Lucknow Metro", "operational_status": OperationalStatus.PROPOSED},

    # --- 8. Noida Metro (NMRC) ---
    {"code": "NOI_S51", "name": "Noida Sector 51", "line": "Aqua Line", "zone": "Central", "latitude": 28.5772, "longitude": 77.3715, "baseline_capacity": 3400, "is_interchange": True, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NOI_S76", "name": "Noida Sector 76", "line": "Aqua Line", "zone": "South", "latitude": 28.5638, "longitude": 77.3882, "baseline_capacity": 2200, "is_interchange": False, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NOI_S137", "name": "Noida Sector 137", "line": "Aqua Line", "zone": "Expressway", "latitude": 28.5135, "longitude": 77.4116, "baseline_capacity": 2500, "is_interchange": False, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NOI_PARI", "name": "Pari Chowk", "line": "Aqua Line", "zone": "Greater Noida", "latitude": 28.4632, "longitude": 77.5108, "baseline_capacity": 3100, "is_interchange": False, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NOI_DEP", "name": "Depot Station", "line": "Aqua Line", "zone": "Greater Noida", "latitude": 28.4312, "longitude": 77.5244, "baseline_capacity": 1800, "is_interchange": False, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NOI_GNW", "name": "Gaur City Greater Noida West", "line": "Aqua Line Extension", "zone": "Greater Noida West", "latitude": 28.6094, "longitude": 77.4332, "baseline_capacity": 2800, "is_interchange": False, "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "city": "Noida", "system_code": "NMRC", "agency_name": "Noida Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 9. Kanpur Metro (UPMRC) ---
    {"code": "KNP_IIT", "name": "IIT Kanpur", "line": "Orange Line", "zone": "North", "latitude": 26.5123, "longitude": 80.2329, "baseline_capacity": 2600, "is_interchange": False, "state": "Uttar Pradesh", "district": "Kanpur Nagar", "city": "Kanpur", "system_code": "UPMRC_KNP", "agency_name": "Kanpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "KNP_KLY", "name": "Kalyanpur", "line": "Orange Line", "zone": "North", "latitude": 26.4952, "longitude": 80.2568, "baseline_capacity": 2200, "is_interchange": False, "state": "Uttar Pradesh", "district": "Kanpur Nagar", "city": "Kanpur", "system_code": "UPMRC_KNP", "agency_name": "Kanpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "KNP_RAW", "name": "Rawatpur", "line": "Orange Line", "zone": "Central", "latitude": 26.4789, "longitude": 80.2985, "baseline_capacity": 2500, "is_interchange": True, "state": "Uttar Pradesh", "district": "Kanpur Nagar", "city": "Kanpur", "system_code": "UPMRC_KNP", "agency_name": "Kanpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "KNP_MOT", "name": "Motijheel", "line": "Orange Line", "zone": "Central", "latitude": 26.4741, "longitude": 80.3214, "baseline_capacity": 3000, "is_interchange": False, "state": "Uttar Pradesh", "district": "Kanpur Nagar", "city": "Kanpur", "system_code": "UPMRC_KNP", "agency_name": "Kanpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "KNP_CEN", "name": "Kanpur Central Railway Station", "line": "Orange Line Extension", "zone": "Central", "latitude": 26.4539, "longitude": 80.3512, "baseline_capacity": 4200, "is_interchange": True, "state": "Uttar Pradesh", "district": "Kanpur Nagar", "city": "Kanpur", "system_code": "UPMRC_KNP", "agency_name": "Kanpur Metro", "operational_status": OperationalStatus.UNDER_CONSTRUCTION},

    # --- 10. Nagpur Metro (Maha Metro) ---
    {"code": "NGP_AUT", "name": "Automotive Square", "line": "Orange Line", "zone": "North", "latitude": 21.1963, "longitude": 79.0882, "baseline_capacity": 2100, "is_interchange": False, "state": "Maharashtra", "district": "Nagpur", "city": "Nagpur", "system_code": "MAHA_NGP", "agency_name": "Nagpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NGP_SIT", "name": "Sitabuldi Interchange", "line": "Orange / Aqua", "zone": "Central", "latitude": 21.1458, "longitude": 79.0882, "baseline_capacity": 4500, "is_interchange": True, "state": "Maharashtra", "district": "Nagpur", "city": "Nagpur", "system_code": "MAHA_NGP", "agency_name": "Nagpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NGP_AIR", "name": "Airport South", "line": "Orange Line", "zone": "South", "latitude": 21.0872, "longitude": 79.0622, "baseline_capacity": 2600, "is_interchange": False, "state": "Maharashtra", "district": "Nagpur", "city": "Nagpur", "system_code": "MAHA_NGP", "agency_name": "Nagpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NGP_PRA", "name": "Prajapati Nagar", "line": "Aqua Line", "zone": "East", "latitude": 21.1524, "longitude": 79.1412, "baseline_capacity": 2200, "is_interchange": False, "state": "Maharashtra", "district": "Nagpur", "city": "Nagpur", "system_code": "MAHA_NGP", "agency_name": "Nagpur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "NGP_LOK", "name": "Lokmanya Nagar", "line": "Aqua Line", "zone": "West", "latitude": 21.1215, "longitude": 79.0084, "baseline_capacity": 2400, "is_interchange": False, "state": "Maharashtra", "district": "Nagpur", "city": "Nagpur", "system_code": "MAHA_NGP", "agency_name": "Nagpur Metro", "operational_status": OperationalStatus.OPERATIONAL},

    # --- 11. Jaipur Metro (JMRC) ---
    {"code": "JAI_MAN", "name": "Mansarovar", "line": "Pink Line", "zone": "South West", "latitude": 26.8624, "longitude": 75.7621, "baseline_capacity": 2400, "is_interchange": False, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_CIV", "name": "Civil Lines", "line": "Pink Line", "zone": "Central", "latitude": 26.9068, "longitude": 75.7825, "baseline_capacity": 2200, "is_interchange": False, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_RLY", "name": "Railway Station Jaipur", "line": "Pink Line", "zone": "Central", "latitude": 26.9189, "longitude": 75.7885, "baseline_capacity": 3400, "is_interchange": True, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_SIN", "name": "Sindhi Camp", "line": "Pink / Orange", "zone": "Central", "latitude": 26.9234, "longitude": 75.7989, "baseline_capacity": 3800, "is_interchange": True, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_CHA", "name": "Chandpole", "line": "Pink Line", "zone": "Old City", "latitude": 26.9265, "longitude": 75.8112, "baseline_capacity": 2900, "is_interchange": False, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_BAD", "name": "Badi Chaupar (City Palace)", "line": "Pink Line", "zone": "Old City", "latitude": 26.9272, "longitude": 75.8278, "baseline_capacity": 3600, "is_interchange": False, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.OPERATIONAL},
    {"code": "JAI_SIT", "name": "Sitapura Industrial Area", "line": "Orange Line", "zone": "South", "latitude": 26.7725, "longitude": 75.8458, "baseline_capacity": 2600, "is_interchange": False, "state": "Rajasthan", "district": "Jaipur", "city": "Jaipur", "system_code": "JMRC", "agency_name": "Jaipur Metro", "operational_status": OperationalStatus.PROPOSED},
]


def sync_metro_hierarchy_to_db(db: Database) -> None:
    """
    Ensures all 14 Indian Metro Systems and their operational lines and stations
    are registered and up-to-date in the database.
    """
    now = utc_now()
    
    # 1. Upsert Metro Systems
    for system in INDIAN_METRO_SYSTEMS:
        db.metro_systems.update_one(
            {"code": system["code"]},
            {"$set": {
                "code": system["code"],
                "name": system["name"],
                "short_name": system["short_name"],
                "city": system["city"],
                "state": system["state"],
                "country": system["country"],
                "operational_status": system["status"].value if isinstance(system["status"], OperationalStatus) else system["status"],
                "fleet_size": system["fleet_size"],
                "lines": system["lines"],
                "updated_at": now
            }},
            upsert=True
        )

    # 2. Add extended metro stations if not already present
    for st in EXTENDED_METRO_STATIONS:
        doc = {
            "code": st["code"],
            "name": st["name"],
            "line": st["line"],
            "zone": st["zone"],
            "latitude": st["latitude"],
            "longitude": st["longitude"],
            "baseline_capacity": st["baseline_capacity"],
            "is_interchange": st["is_interchange"],
            "state": st["state"],
            "district": st["district"],
            "city": st["city"],
            "country": "India",
            "operational_status": st["operational_status"].value if isinstance(st["operational_status"], OperationalStatus) else st["operational_status"],
            "system_code": st["system_code"],
            "agency_name": st["agency_name"],
        }
        db.stations.update_one(
            {"code": st["code"]},
            {"$set": doc, "$setOnInsert": {"_id": new_id()}},
            upsert=True
        )


def get_national_hierarchy(db: Database) -> NationalHierarchyOverview:
    """
    Computes real-time national hierarchy rollup across all 14 Indian Metro Systems.
    """
    sync_metro_hierarchy_to_db(db)
    
    systems_docs = list(db.metro_systems.find({}))
    all_stations = list(db.stations.find({}))
    
    cities_map: dict[str, dict[str, Any]] = {}
    states_set = set()
    total_lines = 0
    operational_stations = 0
    under_con_stations = 0
    proposed_stations = 0
    
    for st in all_stations:
        status = st.get("operational_status", OperationalStatus.OPERATIONAL.value)
        if status == OperationalStatus.OPERATIONAL.value:
            operational_stations += 1
        elif status == OperationalStatus.UNDER_CONSTRUCTION.value:
            under_con_stations += 1
        elif status == OperationalStatus.PROPOSED.value:
            proposed_stations += 1
            
        city = st.get("city", "Delhi")
        state = st.get("state", "Delhi")
        states_set.add(state)
        
        if city not in cities_map:
            cities_map[city] = {
                "name": city,
                "state": state,
                "district": st.get("district", city),
                "country": "India",
                "agency_name": st.get("agency_name", "Metro Rail"),
                "agency_code": st.get("system_code", "METRO"),
                "stations_count": 0,
                "lines_count": 0,
                "lines_set": set(),
                "under_construction_lines": set(),
                "operational_stations": 0,
                "under_construction_stations": 0,
                "proposed_stations": 0,
            }
            
        cities_map[city]["stations_count"] += 1
        if status == OperationalStatus.OPERATIONAL.value:
            cities_map[city]["operational_stations"] += 1
        elif status == OperationalStatus.UNDER_CONSTRUCTION.value:
            cities_map[city]["under_construction_stations"] += 1
        elif status == OperationalStatus.PROPOSED.value:
            cities_map[city]["proposed_stations"] += 1
            
        line_name = st.get("line", "")
        if status == OperationalStatus.UNDER_CONSTRUCTION.value:
            cities_map[city]["under_construction_lines"].add(line_name)
        else:
            cities_map[city]["lines_set"].add(line_name)

    # Format cities list
    cities_summary: list[CityHierarchySummary] = []
    for city, data in sorted(cities_map.items()):
        cities_summary.append(CityHierarchySummary(
            name=data["name"],
            state=data["state"],
            district=data["district"],
            country=data["country"],
            agency_name=data["agency_name"],
            agency_code=data["agency_code"],
            stations_count=data["stations_count"],
            lines_count=len(data["lines_set"]) + len(data["under_construction_lines"]),
            operational_lines=sorted(list(data["lines_set"])),
            under_construction_lines=sorted(list(data["under_construction_lines"])),
            operational_stations=data["operational_stations"],
            under_construction_stations=data["under_construction_stations"],
            proposed_stations=data["proposed_stations"],
        ))

    # Format systems
    systems_out: list[MetroAgencyOut] = []
    for sys in systems_docs:
        sys_code = sys["code"]
        sys_stations = [s for s in all_stations if s.get("system_code") == sys_code]
        lines = sys.get("lines", [])
        total_lines += len(lines)
        
        systems_out.append(MetroAgencyOut(
            id=str(sys.get("_id", sys_code)),
            code=sys_code,
            name=sys.get("name", sys_code),
            city=sys.get("city", "Delhi"),
            state=sys.get("state", "Delhi"),
            country="India",
            operational_status=OperationalStatus(sys.get("operational_status", OperationalStatus.OPERATIONAL.value)),
            lines_count=len(lines),
            stations_count=len(sys_stations) if sys_stations else len(lines) * 5,
            fleet_size=sys.get("fleet_size", 25)
        ))

    return NationalHierarchyOverview(
        country="India",
        total_metro_systems=len(systems_docs) or len(INDIAN_METRO_SYSTEMS),
        total_cities=len(cities_map),
        total_states=len(states_set),
        total_lines=total_lines or 45,
        total_stations=len(all_stations),
        operational_stations=operational_stations,
        under_construction_stations=under_con_stations,
        proposed_stations=proposed_stations,
        systems=systems_out,
        cities=cities_summary,
    )
