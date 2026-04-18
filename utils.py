import pandas as pd
import json

CSV_PATH = "traffic_stops_2024_03_stop_level.csv"
GEOJSON_PATH = "texas_counties.geojson"

CUSTOM_REGIONS = {
    "High Plains": [
        "Lubbock", "Randall", "Potter", "Hale", "Moore", "Hockley", "Gray",
        "Hutchinson", "Deaf Smith", "Lamb", "Terry", "Ochiltree", "Parmer",
        "Yoakum", "Dallam", "Castro", "Bailey", "Swisher", "Childress", "Lynn",
        "Carson", "Floyd", "Crosby", "Hansford", "Hartley", "Wheeler", "Garza",
        "Donley", "Hemphill", "Lipscomb", "Hall", "Sherman", "Collingsworth",
        "Cochran", "Oldham", "Armstrong", "Dickens", "Briscoe", "Motley",
        "Roberts", "King"
    ],
    "Northwest": [
        "Taylor", "Wichita", "Brown", "Montague", "Jones", "Eastland", "Young",
        "Scurry", "Callahan", "Comanche", "Nolan", "Wilbarger", "Clay",
        "Runnels", "Stephens", "Jack", "Archer", "Mitchell", "Coleman",
        "Haskell", "Fisher", "Baylor", "Hardeman", "Knox", "Shackelford",
        "Throckmorton", "Cottle", "Stonewall", "Foard", "Kent"
    ],
    "Metroplex": [
        "Dallas", "Tarrant", "Collin", "Denton", "Ellis", "Johnson", "Kaufman",
        "Parker", "Grayson", "Rockwall", "Hunt", "Wise", "Hood", "Navarro",
        "Erath", "Cooke", "Fannin", "Palo Pinto", "Somervell"
    ],
    "Upper East": [
        "Smith", "Gregg", "Bowie", "Henderson", "Harrison", "Van Zandt", "Anderson",
        "Rusk", "Cherokee", "Lamar", "Wood", "Upshur", "Hopkins", "Titus",
        "Cass", "Panola", "Rains", "Camp", "Morris", "Red River", "Franklin",
        "Marion", "Delta"
    ],
    "Southeast": [
        "Jefferson", "Angelina", "Orange", "Nacogdoches", "Hardin", "Polk",
        "Jasper", "San Jacinto", "Shelby", "Houston", "Tyler", "Trinity",
        "Newton", "Sabine", "San Augustine"
    ],
    "Central": [
        "Bell", "McLennan", "Brazos", "Coryell", "Hill", "Washington", "Grimes",
        "Milam", "Lampasas", "Limestone", "Freestone", "Burleson", "Bosque",
        "Falls", "Robertson", "Leon", "Madison", "Hamilton", "San Saba", "Mills"
    ],
    "Gulf Coast": [
        "Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston", "Liberty",
        "Walker", "Waller", "Chambers", "Wharton", "Matagorda", "Austin", "Colorado"
    ],
    "Capital": [
        "Travis", "Williamson", "Hays", "Bastrop", "Burnet", "Caldwell",
        "Fayette", "Llano", "Lee", "Blanco"
    ],
    "Alamo": [
        "Bexar", "Comal", "Guadalupe", "Medina", "Wilson", "Kerr", "Atascosa",
        "Kendall", "Gillespie", "Bandera", "Frio", "Karnes"
    ],
    "West Texas": [
        "Midland", "Ector", "Tom Green", "Howard", "Gaines", "Andrews", "Pecos",
        "Reeves", "Dawson", "Ward", "McCulloch", "Winkler", "Martin", "Crane",
        "Kimble", "Mason", "Coke", "Concho", "Sutton", "Reagan", "Upton",
        "Crockett", "Schleicher", "Menard", "Irion", "Sterling", "Glasscock",
        "Terrell", "Borden", "Loving"
    ],
    "Coastal Bend": [
        "Nueces", "Victoria", "San Patricio", "Jim Wells", "Bee", "Kleberg",
        "Aransas", "Lavaca", "De Witt", "Gonzales", "Calhoun", "Jackson",
        "Live Oak", "Duval", "Goliad", "Brooks", "Refugio", "McMullen", "Kenedy"
    ],
    "South Texas Border": [
        "Hidalgo", "Cameron", "Webb", "Starr", "Maverick", "Val Verde", "Uvalde",
        "Willacy", "Zapata", "Zavala", "Dimmit", "La Salle", "Jim Hogg",
        "Kinney", "Real", "Edwards"
    ],
    "Upper Rio Grande": [
        "El Paso", "Brewster", "Presidio", "Hudspeth", "Culberson", "Jeff Davis"
    ]
}


def build_county_region_map():
    county_to_region = {}
    for region, counties in CUSTOM_REGIONS.items():
        for county in counties:
            county_to_region[county] = region
    return county_to_region


def load_data():
    df = pd.read_csv(CSV_PATH, low_memory=False)

    if "County" in df.columns:
        df["County"] = df["County"].astype(str).str.strip().str.title()

        county_name_fixes = {
            "Dewitt": "De Witt",
            "Dewit": "De Witt",
            "De Witt": "De Witt",
            "Dewitt County": "De Witt",
            "DeWitt": "De Witt",
            "Mcculloch": "McCulloch",
            "Mclennan": "McLennan",
            "Mcmullen": "McMullen"
        }

        df["County"] = df["County"].replace(county_name_fixes)

    if "Datetime" in df.columns:
        df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")

    if "Searched" in df.columns:
        df["Searched"] = df["Searched"].astype(str).str.strip().str.title()

    if "Contraband_Found" in df.columns:
        df["Contraband_Found"] = df["Contraband_Found"].astype(str).str.strip().str.title()

    df["searched_flag"] = (df["Searched"] == "Yes").astype(int) if "Searched" in df.columns else 0
    df["contraband_flag"] = (df["Contraband_Found"] == "Yes").astype(int) if "Contraband_Found" in df.columns else 0

    if "Datetime" in df.columns:
        df["Stop_Date"] = df["Datetime"].dt.date
        df["Hour"] = df["Datetime"].dt.hour

    county_to_region = build_county_region_map()
    if "County" in df.columns:
        df["Region_Label"] = df["County"].map(county_to_region).fillna("Unknown")

    return df


def load_geojson():
    with open(GEOJSON_PATH, "r") as f:
        counties_geojson = json.load(f)
    return counties_geojson


def build_county_summary(df):
    county_summary = (
        df.groupby("County", dropna=False)
        .agg(
            total_stops=("County", "size"),
            searched_count=("searched_flag", "sum"),
            contraband_count=("contraband_flag", "sum")
        )
        .reset_index()
    )

    county_summary["search_rate"] = (
        county_summary["searched_count"] / county_summary["total_stops"]
    )

    county_summary["contraband_rate"] = (
        county_summary["contraband_count"] / county_summary["total_stops"]
    )

    return county_summary