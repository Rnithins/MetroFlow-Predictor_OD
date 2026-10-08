from __future__ import annotations

from datetime import UTC, timedelta

from pymongo.database import Database

from app.core.security import get_password_hash
from app.services.documents import new_id, utc_now
from app.services.hierarchy import sync_metro_hierarchy_to_db


def ensure_indexes(database: Database) -> None:
    database.users.create_index("email", unique=True)
    database.stations.create_index("code", unique=True)
    database.passenger_flows.create_index([("station_id", 1), ("timestamp", -1)])
    database.predictions.create_index([("station_id", 1), ("target_timestamp", -1)])
    database.od_matrices.create_index([("city", 1), ("timestamp", -1)])
    database.trains.create_index("code", unique=True)
    database.metro_systems.create_index("code", unique=True)


def _sample_stations() -> list[dict]:
    stations_data = []

    # 1. Gujarat -> Ahmedabad (MEGA / GMRC)
    ahmedabad_stations = [
        ("AMD_VG", "Vastral Gam", "East-West Corridor", "East", 23.0012, 72.6580, 1800, False),
        ("AMD_NCR", "Nirant Cross Road", "East-West Corridor", "East", 23.0035, 72.6480, 1500, False),
        ("AMD_VAS", "Vastral", "East-West Corridor", "East", 23.0062, 72.6390, 1600, False),
        ("AMD_RC", "Rabari Colony", "East-West Corridor", "East", 23.0089, 72.6280, 1700, False),
        ("AMD_AMR", "Amraiwadi", "East-West Corridor", "East", 23.0115, 72.6180, 1900, False),
        ("AMD_AP", "Apparel Park", "East-West Corridor", "East", 23.0150, 72.6070, 2400, True),
    ]
    for code, name, line, zone, lat, lng, cap, is_ic in ahmedabad_stations:
        stations_data.append({
            "_id": new_id(),
            "code": code,
            "name": name,
            "line": line,
            "zone": zone,
            "latitude": lat,
            "longitude": lng,
            "baseline_capacity": cap,
            "is_interchange": is_ic,
            "state": "Gujarat",
            "district": "Ahmedabad",
            "city": "Ahmedabad",
        })

    # 2. Karnataka -> Bengaluru (Namma Metro)
    bengaluru_stations = [
        ("BLR_BYP", "Baiyappanahalli", "Purple Line", "East", 12.9912, 77.6521, 2600, False),
        ("BLR_SVR", "Swami Vivekananda Road", "Purple Line", "East", 12.9860, 77.6440, 1800, False),
        ("BLR_IND", "Indiranagar", "Purple Line", "East", 12.9783, 77.6403, 2400, False),
        ("BLR_HAL", "Halasuru", "Purple Line", "Central", 12.9754, 77.6272, 1700, False),
        ("BLR_TRI", "Trinity", "Purple Line", "Central", 12.9727, 77.6169, 1900, False),
        ("BLR_MGR", "Mahatma Gandhi Road", "Purple Line", "Central", 12.9756, 77.6066, 3200, True),
        ("BLR_CUB", "Cubbon Park", "Purple Line", "Central", 12.9810, 77.5973, 2200, False),
        ("BLR_VID", "Vidhana Soudha", "Purple Line", "Central", 12.9797, 77.5925, 2500, False),
        ("BLR_SMV", "Sir M. Visveshwaraya", "Purple Line", "Central", 12.9740, 77.5835, 2700, False),
        ("BLR_MAJ", "Majestic (Kempegowda)", "Purple / Green", "Central", 12.9756, 77.5728, 4500, True),
        ("BLR_SBC", "City Railway Station", "Purple Line", "Central", 12.9772, 77.5670, 3100, True),
        ("BLR_MGD", "Magadi Road", "Purple Line", "West", 12.9755, 77.5552, 1800, False),
        ("BLR_HOS", "Hosahalli", "Purple Line", "West", 12.9748, 77.5450, 1600, False),
        ("BLR_VIJ", "Vijayanagar", "Purple Line", "West", 12.9696, 77.5375, 2200, False),
        ("BLR_ATT", "Attiguppe", "Purple Line", "West", 12.9622, 77.5332, 1700, False),
        ("BLR_DPN", "Deepanjali Nagar", "Purple Line", "West", 12.9525, 77.5370, 1600, False),
        ("BLR_MYS", "Mysore Road", "Purple Line", "West", 12.9463, 77.5298, 2800, False),
        ("BLR_NAG", "Nagasandra", "Green Line", "North", 13.0483, 77.4995, 2000, False),
        ("BLR_DAS", "Dasarahalli", "Green Line", "North", 13.0441, 77.5130, 1700, False),
        ("BLR_JAL", "Jalahalli", "Green Line", "North", 13.0392, 77.5198, 1900, False),
        ("BLR_PI", "Peenya Industry", "Green Line", "North", 13.0350, 77.5255, 1800, False),
        ("BLR_PEE", "Peenya", "Green Line", "North", 13.0329, 77.5273, 2100, False),
        ("BLR_YPI", "Yeshwanthpur Industry", "Green Line", "North", 13.0280, 77.5390, 1600, False),
        ("BLR_YES", "Yeshwanthpur", "Green Line", "North", 13.0232, 77.5501, 3100, True),
        ("BLR_SSF", "Sandal Soap Factory", "Green Line", "North", 13.0147, 77.5544, 1800, False),
        ("BLR_MHL", "Mahalakshmi", "Green Line", "North", 13.0080, 77.5492, 1700, False),
        ("BLR_RAJ", "Rajajinagar", "Green Line", "West", 12.9987, 77.5557, 2100, False),
        ("BLR_KUV", "Kuvempu Road", "Green Line", "West", 12.9945, 77.5580, 1600, False),
        ("BLR_SRI", "Srirampura", "Green Line", "Central", 12.9962, 77.5637, 1800, False),
        ("BLR_SMP", "Sampige Road", "Green Line", "Central", 12.9908, 77.5710, 2000, False),
        ("BLR_CKP", "Chickpet", "Green Line", "Central", 12.9667, 77.5746, 2400, False),
        ("BLR_KRM", "Krishna Rajendra Market", "Green Line", "Central", 12.9609, 77.5748, 2900, False),
        ("BLR_NC", "National College", "Green Line", "South", 12.9504, 77.5732, 1900, False),
        ("BLR_LAL", "Lalbagh", "Green Line", "South", 12.9461, 77.5800, 2200, False),
        ("BLR_SEC", "Southend Circle", "Green Line", "South", 12.9377, 77.5801, 1800, False),
        ("BLR_JAY", "Jayanagar", "Green Line", "South", 12.9279, 77.5802, 2300, False),
        ("BLR_RVR", "Rashtreeya Vidyalaya Road", "Green Line", "South", 12.9216, 77.5801, 2000, False),
        ("BLR_BSK", "Banashankari", "Green Line", "South", 12.9155, 77.5736, 2800, True),
        ("BLR_JPN", "Jayaprakash Nagar", "Green Line", "South", 12.9074, 77.5729, 2100, False),
        ("BLR_YEL", "Yelachenahalli", "Green Line", "South", 12.8958, 77.5702, 2200, False),
    ]
    for code, name, line, zone, lat, lng, cap, is_ic in bengaluru_stations:
        stations_data.append({
            "_id": new_id(),
            "code": code,
            "name": name,
            "line": line,
            "zone": zone,
            "latitude": lat,
            "longitude": lng,
            "baseline_capacity": cap,
            "is_interchange": is_ic,
            "state": "Karnataka",
            "district": "Bengaluru Urban",
            "city": "Bengaluru",
        })

    # 3. Delhi / NCR -> Delhi (DMRC)
    delhi_stations = [
        ("DEL_RIT", "Rithala", "Red Line", "North West", 28.7208, 77.1072, 2200, False),
        ("DEL_ROW", "Rohini West", "Red Line", "North West", 28.7148, 77.1147, 2000, False),
        ("DEL_ROE", "Rohini East", "Red Line", "North West", 28.7093, 77.1245, 1900, False),
        ("DEL_PIT", "Pitam Pura", "Red Line", "North West", 28.7032, 77.1325, 2100, False),
        ("DEL_KOH", "Kohat Enclave", "Red Line", "North West", 28.6978, 77.1398, 2000, False),
        ("DEL_NSP", "Netaji Subhash Place", "Red / Pink", "North West", 28.6958, 77.1528, 3600, True),
        ("DEL_KP", "Keshav Puram", "Red Line", "North", 28.6890, 77.1610, 1800, False),
        ("DEL_KN", "Kanhiya Nagar", "Red Line", "North", 28.6830, 77.1680, 1700, False),
        ("DEL_IND", "Inderlok", "Red / Green", "North", 28.6730, 77.1700, 3400, True),
        ("DEL_SN", "Shastri Nagar", "Red Line", "North", 28.6690, 77.1810, 1900, False),
        ("DEL_PN", "Pratap Nagar", "Red Line", "North", 28.6670, 77.1920, 1800, False),
        ("DEL_PB", "Pul Bangash", "Red Line", "North", 28.6660, 77.2020, 1900, False),
        ("DEL_TH", "Tis Hazari", "Red Line", "North", 28.6670, 77.2150, 2200, False),
        ("DEL_KAS", "Kashmere Gate", "Red / Yellow / Violet", "North", 28.6675, 77.2282, 4500, True),
        ("DEL_SP", "Shastri Park", "Red Line", "North East", 28.6700, 77.2500, 2100, False),
        ("DEL_SEE", "Seelampur", "Red Line", "North East", 28.6700, 77.2650, 2200, False),
        ("DEL_WEL", "Welcome", "Red / Pink", "North East", 28.6710, 77.2770, 3200, True),
        ("DEL_SHA", "Shahdara", "Red Line", "East", 28.6730, 77.2890, 2600, False),
        ("DEL_MP", "Mansarovar Park", "Red Line", "East", 28.6780, 77.3020, 1900, False),
        ("DEL_JHI", "Jhilmil", "Red Line", "East", 28.6790, 77.3130, 1800, False),
        ("DEL_DG", "Dilshad Garden", "Red Line", "East", 28.6810, 77.3220, 2500, False),
        ("DEL_SB", "Samaypur Badli", "Yellow Line", "North", 28.7450, 77.1350, 2300, False),
        ("DEL_R18", "Rohini Sector 18", "Yellow Line", "North", 28.7360, 77.1420, 1900, False),
        ("DEL_HAI", "Haiderpur", "Yellow Line", "North", 28.7230, 77.1510, 2000, False),
        ("DEL_JAH", "Jahangirpuri", "Yellow Line", "North", 28.7160, 77.1620, 2400, False),
        ("DEL_AN", "Adarsh Nagar", "Yellow Line", "North", 28.7050, 77.1720, 2100, False),
        ("DEL_AZA", "Azadpur", "Yellow / Pink", "North", 28.6990, 77.1810, 3500, True),
        ("DEL_MT", "Model Town", "Yellow Line", "North", 28.6940, 77.1930, 2200, False),
        ("DEL_GTB", "GTB Nagar", "Yellow Line", "North", 28.6980, 77.2070, 3100, False),
        ("DEL_VV", "Vishwa Vidyalaya", "Yellow Line", "North", 28.6900, 77.2140, 3300, False),
        ("DEL_VS", "Vidhan Sabha", "Yellow Line", "North", 28.6810, 77.2200, 2100, False),
        ("DEL_CL", "Delhi Civil Lines", "Yellow Line", "North", 28.6740, 77.2250, 2300, False),
        ("DEL_CC", "Chandni Chowk", "Yellow Line", "Central", 28.6570, 77.2300, 3800, False),
        ("DEL_CB", "Chawri Bazar", "Yellow Line", "Central", 28.6500, 77.2270, 3200, False),
        ("DEL_ND03", "New Delhi", "Yellow / Airport Express", "Central", 28.6430, 77.2220, 4200, True),
        ("DEL_RAJ", "Rajiv Chowk", "Blue / Yellow", "Central", 28.6304, 77.2177, 4800, True),
        ("DEL_PAT", "Patel Chowk", "Yellow Line", "Central", 28.6230, 77.2130, 2600, False),
        ("DEL_CS", "Central Secretariat", "Yellow / Violet", "Central", 28.6150, 77.2120, 3800, True),
        ("DEL_UB", "Udyog Bhawan", "Yellow Line", "Central", 28.6110, 77.2120, 2400, False),
        ("DEL_RC", "Race Course", "Yellow Line", "Central", 28.6000, 77.2160, 2100, False),
        ("DEL_JB", "Jor Bagh", "Yellow Line", "South", 28.5880, 77.2180, 2300, False),
        ("DEL_INA", "INA", "Yellow / Pink", "South", 28.5750, 77.2090, 3700, True),
        ("DEL_AIIMS", "AIIMS", "Yellow Line", "South", 28.5680, 77.2080, 3400, False),
        ("DEL_GP", "Green Park", "Yellow Line", "South", 28.5580, 77.2060, 2800, False),
        ("DEL_HOU", "Hauz Khas", "Yellow / Magenta", "South", 28.5433, 77.2065, 4100, True),
        ("DEL_MN", "Malviya Nagar", "Yellow Line", "South", 28.5300, 77.2070, 2700, False),
        ("DEL_SAK", "Saket", "Yellow Line", "South", 28.5200, 77.2030, 2900, False),
        ("DEL_QM", "Qutab Minar", "Yellow Line", "South", 28.5130, 77.1860, 2400, False),
        ("DEL_CP", "Chhatarpur", "Yellow Line", "South", 28.5060, 77.1740, 2800, False),
        ("DEL_SUL", "Sultanpur", "Yellow Line", "South", 28.4980, 77.1620, 2200, False),
        ("DEL_GHI", "Ghitorni", "Yellow Line", "South", 28.4900, 77.1490, 2100, False),
        ("DEL_AG", "Arjan Garh", "Yellow Line", "South", 28.4810, 77.1260, 2000, False),
        ("DEL_GD", "Guru Dronacharya", "Yellow Line", "South", 28.4820, 77.1030, 2600, False),
        ("DEL_SIK", "Sikanderpur", "Yellow / Rapid Metro", "South", 28.4819, 77.0926, 3900, True),
        ("DEL_MG", "MG Road", "Yellow Line", "South", 28.4800, 77.0800, 3200, False),
        ("DEL_IFF", "IFFCO Chowk", "Yellow Line", "South", 28.4720, 77.0720, 3400, False),
        ("DEL_HCC", "HUDA City Centre", "Yellow Line", "South", 28.4590, 77.0720, 3800, False),
        ("DEL_NCC", "Noida City Centre", "Blue Line", "East", 28.5740, 77.3560, 2800, False),
        ("DEL_NGC", "Noida Golf Course", "Blue Line", "East", 28.5670, 77.3460, 2100, False),
        ("DEL_BG", "Botanical Garden", "Blue / Magenta", "East", 28.5640, 77.3340, 4200, True),
        ("DEL_N18", "Noida Sector 18", "Blue Line", "East", 28.5700, 77.3230, 3600, False),
        ("DEL_N16", "Noida Sector 16", "Blue Line", "East", 28.5780, 77.3160, 2600, False),
        ("DEL_N15", "Noida Sector 15", "Blue Line", "East", 28.5850, 77.3110, 2400, False),
        ("DEL_NAN", "New Ashok Nagar", "Blue Line", "East", 28.5910, 77.3050, 2200, False),
        ("DEL_MVE", "Mayur Vihar Extension", "Blue Line", "East", 28.5940, 77.2940, 2300, False),
        ("DEL_MV1", "Mayur Vihar-I", "Blue / Pink", "East", 28.6050, 77.2910, 3700, True),
        ("DEL_AKS", "Akshardham", "Blue Line", "East", 28.6180, 77.2790, 3100, False),
        ("DEL_YB", "Yamuna Bank", "Blue Line", "East", 28.6230, 77.2660, 3900, True),
        ("DEL_INDRA", "Indraprastha", "Blue Line", "Central", 28.6200, 77.2510, 2400, False),
        ("DEL_PRAG", "Pragati Maidan", "Blue Line", "Central", 28.6230, 77.2430, 3000, False),
        ("DEL_MH", "Mandi House", "Blue / Violet", "Central", 28.6250, 77.2340, 3800, True),
        ("DEL_BK", "Barakhamba Road", "Blue Line", "Central", 28.6300, 77.2270, 2900, False),
        ("DEL_RK", "Ramakrishna Ashram Marg", "Blue Line", "Central", 28.6380, 77.2090, 2600, False),
        ("DEL_JHA", "Jhandewalan", "Blue Line", "Central", 28.6440, 77.1990, 2700, False),
        ("DEL_KB", "Karol Bagh", "Blue Line", "Central", 28.6440, 77.1900, 3500, False),
        ("DEL_RP", "Rajendra Place", "Blue Line", "Central", 28.6430, 77.1780, 2800, False),
        ("DEL_PNAR", "Patel Nagar", "Blue Line", "West", 28.6530, 77.1680, 2500, False),
        ("DEL_SHAD", "Shadipur", "Blue Line", "West", 28.6520, 77.1580, 2400, False),
        ("DEL_KNAR", "Kirti Nagar", "Blue / Green", "West", 28.6550, 77.1470, 3600, True),
        ("DEL_MNAR", "Moti Nagar", "Blue Line", "West", 28.6580, 77.1390, 2300, False),
        ("DEL_RN", "Ramesh Nagar", "Blue Line", "West", 28.6530, 77.1310, 2200, False),
        ("DEL_RG", "Rajouri Garden", "Blue / Pink", "West", 28.6490, 77.1230, 3800, True),
        ("DEL_TG", "Tagore Garden", "Blue Line", "West", 28.6440, 77.1120, 2400, False),
        ("DEL_SUBN", "Subhash Nagar", "Blue Line", "West", 28.6390, 77.1040, 2600, False),
        ("DEL_TN", "Tilak Nagar", "Blue Line", "West", 28.6360, 77.0960, 2800, False),
        ("DEL_JPE", "Janakpuri East", "Blue Line", "West", 28.6290, 77.0870, 2900, False),
        ("DEL_JPW", "Janakpuri West", "Blue / Magenta", "West", 28.6294, 77.0777, 4200, True),
        ("DEL_UNE", "Uttam Nagar East", "Blue Line", "West", 28.6240, 77.0650, 3100, False),
        ("DEL_UNW", "Uttam Nagar West", "Blue Line", "West", 28.6220, 77.0560, 3000, False),
        ("DEL_NAW", "Nawada", "Blue Line", "West", 28.6200, 77.0420, 2500, False),
        ("DEL_DM", "Dwarka Mor", "Blue Line", "West", 28.6190, 77.0330, 2700, False),
        ("DEL_DWK", "Dwarka", "Blue / Grey", "West", 28.6150, 77.0210, 3200, True),
        ("DEL_D14", "Dwarka Sector 14", "Blue Line", "West", 28.6020, 77.0260, 2000, False),
        ("DEL_D13", "Dwarka Sector 13", "Blue Line", "West", 28.5950, 77.0320, 1900, False),
        ("DEL_D12", "Dwarka Sector 12", "Blue Line", "West", 28.5920, 77.0400, 2100, False),
        ("DEL_D11", "Dwarka Sector 11", "Blue Line", "West", 28.5880, 77.0490, 2000, False),
        ("DEL_D10", "Dwarka Sector 10", "Blue Line", "West", 28.5810, 77.0580, 2200, False),
        ("DEL_D9", "Dwarka Sector 9", "Blue Line", "West", 28.5740, 77.0640, 2300, False),
        ("DEL_D8", "Dwarka Sector 8", "Blue Line", "West", 28.5650, 77.0670, 2100, False),
        ("DEL_D21", "Dwarka Sector 21", "Blue / Airport Express", "West", 28.5520, 77.0580, 3600, True),
        ("DEL_LN", "Laxmi Nagar", "Blue Line", "East", 28.6300, 77.2770, 3400, False),
        ("DEL_NV", "Nirman Vihar", "Blue Line", "East", 28.6370, 77.2870, 2900, False),
        ("DEL_PV", "Preet Vihar", "Blue Line", "East", 28.6410, 77.2960, 2600, False),
        ("DEL_KKD", "Karkarduma", "Blue / Pink", "East", 28.6490, 77.3060, 3400, True),
        ("DEL_AV", "Anand Vihar", "Blue / Pink", "East", 28.6470, 77.3160, 4400, True),
        ("DEL_KAU", "Kaushambi", "Blue Line", "East", 28.6450, 77.3240, 2300, False),
        ("DEL_VAI", "Vaishali", "Blue Line", "East", 28.6490, 77.3390, 2800, False),
        ("DEL_APM", "Ashok Park Main", "Green Line", "West", 28.6720, 77.1550, 2300, True),
        ("DEL_PBE", "Punjabi Bagh East", "Green Line", "West", 28.6700, 77.1420, 2200, False),
        ("DEL_SHIV", "Shivaji Park", "Green Line", "West", 28.6690, 77.1310, 1900, False),
        ("DEL_MAD", "Madipur", "Green Line", "West", 28.6710, 77.1210, 1800, False),
        ("DEL_PVE", "Paschim Vihar East", "Green Line", "West", 28.6730, 77.1120, 2100, False),
        ("DEL_PVW", "Paschim Vihar West", "Green Line", "West", 28.6750, 77.1010, 2000, False),
        ("DEL_PG", "Peera Garhi", "Green Line", "West", 28.6790, 77.0920, 2600, False),
        ("DEL_UN", "Udyog Nagar", "Green Line", "West", 28.6810, 77.0810, 2200, False),
        ("DEL_SMS", "Surajmal Stadium", "Green Line", "West", 28.6830, 77.0690, 2100, False),
        ("DEL_NANGL", "Nangloi", "Green Line", "West", 28.6820, 77.0580, 2500, False),
        ("DEL_NRS", "Nangloi Railway Station", "Green Line", "West", 28.6830, 77.0470, 2200, False),
        ("DEL_RDP", "Rajdhani Park", "Green Line", "West", 28.6850, 77.0340, 1800, False),
        ("DEL_MUN", "Mundka", "Green Line", "West", 28.6830, 77.0220, 2400, False),
        ("DEL_MIA", "Mundka Industrial Area", "Green Line", "West", 28.6840, 77.0080, 1900, False),
        ("DEL_GHE", "Ghevra", "Green Line", "West", 28.6880, 76.9930, 1800, False),
        ("DEL_TK", "Tikri Kalan", "Green Line", "West", 28.6910, 76.9770, 1700, False),
        ("DEL_TB", "Tikri Border", "Green Line", "West", 28.6940, 76.9630, 2000, False),
        ("DEL_MIE", "Modern Industrial Estate", "Green Line", "West", 28.6920, 76.9450, 1800, False),
        ("DEL_BS", "Bus Stand", "Green Line", "West", 28.6910, 76.9320, 2100, False),
        ("DEL_CPK", "City Park", "Green Line", "West", 28.6920, 76.9210, 2300, False),
        ("DEL_ITO", "ITO", "Violet Line", "Central", 28.6290, 77.2410, 3100, False),
        ("DEL_JAN", "Janpath", "Violet Line", "Central", 28.6240, 77.2190, 2700, False),
        ("DEL_KM", "Khan Market", "Violet Line", "Central", 28.6000, 77.2270, 2800, False),
        ("DEL_JLN", "Jawaharlal Nehru Stadium", "Violet Line", "South", 28.5870, 77.2340, 3200, False),
        ("DEL_JANP", "Jangpura", "Violet Line", "South", 28.5810, 77.2390, 2400, False),
        ("DEL_LNAG", "Lajpat Nagar", "Violet / Pink", "South", 28.5700, 77.2370, 4100, True),
        ("DEL_MOO", "Moolchand", "Violet Line", "South", 28.5650, 77.2340, 2500, False),
        ("DEL_KC", "Kailash Colony", "Violet Line", "South", 28.5550, 77.2420, 2600, False),
        ("DEL_NP", "Nehru Place", "Violet Line", "South", 28.5510, 77.2510, 3700, False),
        ("DEL_KMAND", "Kalkaji Mandir", "Violet / Magenta", "South", 28.5490, 77.2590, 4200, True),
        ("DEL_GPURI", "Govind Puri", "Violet Line", "South", 28.5360, 77.2640, 2700, False),
        ("DEL_OKH", "Okhla", "Violet Line", "South", 28.5290, 77.2730, 2400, False),
        ("DEL_JAS", "Jasola Apollo", "Violet Line", "South", 28.5370, 77.2830, 2600, False),
        ("DEL_SV", "Sarita Vihar", "Violet Line", "South", 28.5290, 77.2910, 2500, False),
        ("DEL_ME", "Mohan Estate", "Violet Line", "South", 28.5190, 77.2970, 2300, False),
        ("DEL_TUG", "Tughlakabad", "Violet Line", "South", 28.5090, 77.3010, 2600, False),
        ("DEL_BAD", "Badarpur", "Violet Line", "South", 28.4970, 77.3030, 3100, False),
        ("DEL_SARAI", "Sarai", "Violet Line", "South", 28.4780, 77.3090, 2100, False),
        ("DEL_NHPC", "NHPC Chowk", "Violet Line", "South", 28.4620, 77.3110, 2200, False),
        ("DEL_MM", "Mewla Maharajpur", "Violet Line", "South", 28.4480, 77.3130, 2000, False),
        ("DEL_S28", "Sector 28", "Violet Line", "South", 28.4350, 77.3140, 2100, False),
        ("DEL_BM", "Badkhal Mor", "Violet Line", "South", 28.4190, 77.3160, 2200, False),
        ("DEL_FO", "Faridabad Old", "Violet Line", "South", 28.4060, 77.3160, 2400, False),
        ("DEL_NCA", "Neelam Chowk Ajronda", "Violet Line", "South", 28.3900, 77.3170, 2300, False),
        ("DEL_BC", "Bata Chowk", "Violet Line", "South", 28.3790, 77.3160, 2500, False),
        ("DEL_EM", "Escorts Mujesar", "Violet Line", "South", 28.3680, 77.3140, 2600, False),
        ("DEL_SS", "Shivaji Stadium", "Airport Express", "Central", 28.6290, 77.2140, 2500, False),
        ("DEL_DK", "Dhaula Kuan", "Airport Express", "South West", 28.5910, 77.1610, 2900, True),
        ("DEL_AERO", "Delhi Aerocity", "Airport Express", "South West", 28.5490, 77.1210, 3100, False),
        ("DEL_AIRP", "Airport (T3)", "Airport Express", "South West", 28.5560, 77.0860, 3600, False),
        ("DEL_DMOR", "Dabri Mor", "Magenta Line", "West", 28.6140, 77.0890, 2400, False),
        ("DEL_DPURI", "Dashrath Puri", "Magenta Line", "West", 28.6030, 77.0910, 2200, False),
        ("DEL_PAL", "Palam", "Magenta Line", "South West", 28.5890, 77.0840, 2300, False),
        ("DEL_SBC", "Sadar Bazaar Cantonment", "Magenta Line", "South West", 28.5810, 77.1180, 2000, False),
        ("DEL_T1", "Terminal 1 IGI Airport", "Magenta Line", "South West", 28.5690, 77.1190, 3400, False),
        ("DEL_SHV", "Shankar Vihar", "Magenta Line", "South West", 28.5630, 77.1400, 1900, False),
        ("DEL_VASV", "Vasant Vihar", "Magenta Line", "South West", 28.5610, 77.1610, 2600, False),
        ("DEL_MUNR", "Munirka", "Magenta Line", "South", 28.5580, 77.1740, 2800, False),
        ("DEL_RKP", "R.K. Puram", "Magenta Line", "South", 28.5490, 77.1820, 2700, False),
        ("DEL_IIT", "IIT Delhi", "Magenta Line", "South", 28.5450, 77.1950, 3000, False),
        ("DEL_PP", "Panchsheel Park", "Magenta Line", "South", 28.5420, 77.2180, 2500, False),
        ("DEL_CD", "Chirag Delhi", "Magenta Line", "South", 28.5410, 77.2280, 2700, False),
        ("DEL_GK", "Greater Kailash", "Magenta Line", "South", 28.5410, 77.2390, 2800, False),
        ("DEL_NE", "Nehru Enclave", "Magenta Line", "South", 28.5450, 77.2510, 2600, False),
        ("DEL_ONSIC", "Okhla NSIC", "Magenta Line", "South", 28.5530, 77.2660, 2300, False),
        ("DEL_SUKH", "Sukhdev Vihar", "Magenta Line", "South", 28.5610, 77.2760, 2400, False),
        ("DEL_JMI", "Jamia Millia Islamia", "Magenta Line", "South", 28.5630, 77.2840, 2900, False),
        ("DEL_OV", "Okhla Vihar", "Magenta Line", "South", 28.5590, 77.2940, 2200, False),
        ("DEL_JV", "Jasola Vihar Shaheen Bagh", "Magenta Line", "South", 28.5460, 77.3030, 2400, False),
        ("DEL_KK", "Kalindi Kunj", "Magenta Line", "South", 28.5420, 77.3110, 2500, False),
        ("DEL_OBS", "Okhla Bird Sanctuary", "Magenta Line", "East", 28.5460, 77.3230, 2600, False),
        ("DEL_NOI", "Noida Sector 62", "Blue Line", "East", 28.6219, 77.3639, 2800, False),
    ]
    for code, name, line, zone, lat, lng, cap, is_ic in delhi_stations:
        stations_data.append({
            "_id": new_id(),
            "code": code,
            "name": name,
            "line": line,
            "zone": zone,
            "latitude": lat,
            "longitude": lng,
            "baseline_capacity": cap,
            "is_interchange": is_ic,
            "state": "Delhi",
            "district": "New Delhi" if "Central" in zone else "South Delhi" if "South" in zone else "North Delhi",
            "city": "Delhi",
        })

    # 4. Haryana -> Gurugram (Rapid Metro)
    gurugram_stations = [
        ("GUR_S55", "Sector 55-56", "Rapid Metro", "South", 28.4190, 77.1030, 1600, False),
        ("GUR_S54", "Sector 54 Chowk", "Rapid Metro", "South", 28.4280, 77.1000, 1500, False),
        ("GUR_S53", "Sector 53-54", "Rapid Metro", "South", 28.4410, 77.0980, 1600, False),
        ("GUR_S42", "Sector 42-43", "Rapid Metro", "Central", 28.4550, 77.0940, 1700, False),
        ("GUR_P1", "Phase 1", "Rapid Metro", "Central", 28.4720, 77.0930, 1800, False),
        ("GUR_SIK", "Sikanderpur Gurugram", "Rapid Metro / Yellow Line", "Central", 28.4819, 77.0926, 3400, True),
        ("GUR_P2", "Phase 2", "Rapid Metro", "North", 28.4900, 77.0890, 1900, False),
        ("GUR_P3", "Phase 3", "Rapid Metro", "North", 28.4960, 77.0940, 2000, False),
        ("GUR_MA", "Micromax Moulsari Avenue", "Rapid Metro", "North", 28.5020, 77.0920, 2100, False),
        ("GUR_CC", "IndusInd Bank Cyber City", "Rapid Metro", "North", 28.4950, 77.0880, 3100, False),
        ("GUR_BT", "Vodafone Belvedere Towers", "Rapid Metro", "North", 28.4890, 77.0860, 2200, False),
    ]
    for code, name, line, zone, lat, lng, cap, is_ic in gurugram_stations:
        stations_data.append({
            "_id": new_id(),
            "code": code,
            "name": name,
            "line": line,
            "zone": zone,
            "latitude": lat,
            "longitude": lng,
            "baseline_capacity": cap,
            "is_interchange": is_ic,
            "state": "Haryana",
            "district": "Gurugram",
            "city": "Gurugram",
        })

    # 5. Other Major Hubs (Mumbai, Hyderabad, Chennai, Kolkata, Kochi, Pune, Srinagar)
    other_stations = [
        ("MUM_AND", "Andheri East", "Line 1", "Suburban", 19.1197, 72.8468, 3200, True, "Maharashtra", "Mumbai Suburban", "Mumbai"),
        ("MUM_DN", "D.N. Nagar", "Line 1 / 2A", "Suburban", 19.1252, 72.8361, 2500, True, "Maharashtra", "Mumbai Suburban", "Mumbai"),
        ("HYD_AMG", "Ameerpet", "Red / Blue", "Central", 17.4375, 78.4483, 3000, True, "Telangana", "Hyderabad", "Hyderabad"),
        ("HYD_HIT", "HITEC City", "Blue Line", "West", 17.4474, 78.3814, 2800, False, "Telangana", "K.V. Rangareddy", "Hyderabad"),
        ("MAA_CEN", "Chennai Central", "Blue / Green", "Central", 13.0818, 80.2722, 3100, True, "Tamil Nadu", "Chennai", "Chennai"),
        ("CCU_ESPL", "Esplanade", "Blue / Green / Purple", "Central", 22.5645, 88.3522, 3800, True, "West Bengal", "Kolkata", "Kolkata"),
        ("COK_ALU", "Aluva Kochi", "Line 1", "North", 10.1092, 76.3496, 1400, False, "Kerala", "Ernakulam", "Kochi"),
        ("PUN_CIV", "Civil Court Pune", "Purple / Aqua", "Central", 18.5284, 73.8553, 1800, True, "Maharashtra", "Pune", "Pune"),
        ("SXR_LAL", "Lal Chowk", "Line 1 (Upcoming)", "Central", 34.0722, 74.8085, 1200, False, "Jammu and Kashmir", "Srinagar", "Srinagar"),
    ]
    for code, name, line, zone, lat, lng, cap, is_ic, state, district, city in other_stations:
        stations_data.append({
            "_id": new_id(),
            "code": code,
            "name": name,
            "line": line,
            "zone": zone,
            "latitude": lat,
            "longitude": lng,
            "baseline_capacity": cap,
            "is_interchange": is_ic,
            "state": state,
            "district": district,
            "city": city,
        })

    return stations_data



def _weather_for(hour_offset: int, station_index: int) -> str:
    if (hour_offset + station_index) % 23 == 0:
        return "monsoon heavy rain"
    if (hour_offset + station_index) % 11 == 0:
        return "cloudy"
    if (hour_offset + station_index) % 17 == 0:
        return "heatwave"
    return "clear"


def seed_database(database: Database) -> None:
    sync_metro_hierarchy_to_db(database)
    if database.stations.count_documents({}) >= 100 and database.users.count_documents({}) > 0:
        return

    # Clear old incomplete seeds if refreshing
    database.users.delete_many({})
    database.stations.delete_many({})
    database.passenger_flows.delete_many({})
    database.trains.delete_many({})
    database.od_matrices.delete_many({})
    database.predictions.delete_many({})

    now = utc_now().astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    stations = _sample_stations()

    users = [
        {
            "_id": "user_admin_001",
            "email": "admin@metroflow.ai",
            "full_name": "Metro Admin",
            "password_hash": get_password_hash("admin12345"),
            "role": "admin",
            "is_active": True,
            "job_title": "Operations Director",
            "organization": "MetroFlow Transit",
            "commute_line": "Blue / Yellow",
            "theme_preference": "system",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": "user_analyst_001",
            "email": "user@metroflow.ai",
            "full_name": "Transit Analyst",
            "password_hash": get_password_hash("User@12345"),
            "role": "user",
            "is_active": True,
            "job_title": "Demand Analyst",
            "organization": "MetroFlow Transit",
            "commute_line": "Purple / Green",
            "theme_preference": "system",
            "created_at": now,
            "updated_at": now,
        },
    ]

    flows: list[dict] = []
    start = (now - timedelta(days=13)).replace(hour=0)
    
    # 1. Seed Passenger Flows
    for day_offset in range(14):
        day_start = start + timedelta(days=day_offset)
        weekend_factor = 0.75 if day_start.weekday() >= 5 else 1.0

        for hour in range(24):
            timestamp = day_start + timedelta(hours=hour)
            # Indian commuter peak hours: 8:30-10:30 AM and 5:30-8:30 PM
            peak_factor = 1.95 if hour in {8, 9, 17, 18, 19} else 1.35 if hour in {7, 10, 16, 20} else 0.45 if hour < 5 else 1.0

            for index, station in enumerate(stations):
                weather_code = _weather_for(day_offset * 24 + hour, index)
                # Heavy rains reduce passenger inflow slightly, but increase dwell time
                weather_factor = 0.88 if weather_code == "monsoon heavy rain" else 1.05 if weather_code == "heatwave" else 1.0
                
                # Introduce major Indian festivals (Diwali / Durga Puja spikes)
                is_festival = day_offset % 7 == 0 and hour in {16, 17, 18, 19, 20}
                event_multiplier = 1.45 if is_festival else 1.0
                
                daily_variation = 0.92 + ((day_offset + index) % 7) * 0.02
                base = station["baseline_capacity"] * 0.38
                passenger_count = int(base * peak_factor * weekend_factor * weather_factor * event_multiplier * daily_variation)
                passenger_count = max(passenger_count, 30 + index * 10)

                flows.append(
                    {
                        "_id": new_id(),
                        "station_id": station["_id"],
                        "timestamp": timestamp,
                        "passenger_count": passenger_count,
                        "avg_dwell_minutes": round(2.0 + (peak_factor - 1) * 1.5 + (1.2 if weather_code == "monsoon heavy rain" else 0.0), 2),
                        "weather_code": weather_code,
                        "event_flag": is_festival,
                        "event_name": "Festival Shopping Rush" if is_festival else None,
                        "source": "seed",
                    }
                )

    # 2. Seed Trains
    trains = [
        {"_id": new_id(), "code": "DEL_T1", "name": "Delhi Blue Express", "city": "Delhi", "line": "Blue / Yellow", "capacity": 1500, "status": "active", "speed_kmh": 45, "current_station_code": "DEL_RAJ"},
        {"_id": new_id(), "code": "DEL_T2", "name": "Kashmere Link", "city": "Delhi", "line": "Red / Yellow / Violet", "capacity": 1500, "status": "active", "speed_kmh": 40, "current_station_code": "DEL_KAS"},
        {"_id": new_id(), "code": "BLR_T1", "name": "Namma Purple", "city": "Bengaluru", "line": "Purple / Green", "capacity": 1200, "status": "active", "speed_kmh": 38, "current_station_code": "BLR_MAJ"},
        {"_id": new_id(), "code": "MUM_T1", "name": "Mumbai Wave 1", "city": "Mumbai", "line": "Line 1", "capacity": 1800, "status": "active", "speed_kmh": 35, "current_station_code": "MUM_AND"},
        {"_id": new_id(), "code": "HYD_T1", "name": "Hyderabad Blue Star", "city": "Hyderabad", "line": "Red / Blue", "capacity": 1200, "status": "active", "speed_kmh": 42, "current_station_code": "HYD_AMG"},
    ]

    # 3. Seed OD Matrices (Origin-Destination matrices for major cities)
    od_matrices = []
    cities_with_multiple_stations = ["Delhi", "Bengaluru", "Mumbai", "Hyderabad"]
    for city in cities_with_multiple_stations:
        city_stations = [s for s in stations if s["city"] == city]
        if len(city_stations) < 2:
            continue
        # Seed matrices for the past 24 hours (hourly)
        for h_offset in range(24):
            matrix_time = now - timedelta(hours=h_offset)
            matrix_list = []
            for origin in city_stations:
                for dest in city_stations:
                    if origin["code"] == dest["code"]:
                        continue
                    # Dynamic flow based on peak hours
                    is_peak = matrix_time.hour in {8, 9, 17, 18, 19}
                    flow = int((300 if is_peak else 80) * (0.8 + (h_offset % 3) * 0.1))
                    matrix_list.append({
                        "origin_station_code": origin["code"],
                        "origin_station_name": origin["name"],
                        "destination_station_code": dest["code"],
                        "destination_station_name": dest["name"],
                        "passenger_flow": flow
                    })
            od_matrices.append({
                "_id": new_id(),
                "city": city,
                "timestamp": matrix_time,
                "matrix": matrix_list
            })

    # 4. Seed Predictions
    latest_flow_per_station = {flow["station_id"]: flow for flow in flows}
    predictions = [
        {
            "_id": new_id(),
            "station_id": station["_id"],
            "target_timestamp": latest_flow_per_station[station["_id"]]["timestamp"] + timedelta(hours=1),
            "predicted_count": round(latest_flow_per_station[station["_id"]]["passenger_count"] * 1.09, 2),
            "baseline_count": round(latest_flow_per_station[station["_id"]]["passenger_count"] * 0.97, 2),
            "confidence_score": 0.89,
            "anomaly_score": 0.11,
            "recommended_action": "Heavy traffic. Position standby trains and stager announcements.",
            "model_version": "metroflow-adaptive-fusion-v1",
            "generated_at": now,
            "created_by": "system",
        }
        for station in stations
    ]

    database.users.insert_many(users)
    database.stations.insert_many(stations)
    database.passenger_flows.insert_many(flows)
    database.trains.insert_many(trains)
    database.od_matrices.insert_many(od_matrices)
    database.predictions.insert_many(predictions)
