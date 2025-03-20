import requests
import pandas as pd
import time
import os
import re
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv("API_KEY")
# Use test key to avoid charges during testing
TEST_API_KEY = f"test-{API_KEY}"
# Using the v1/service endpoint based on documentation
ENDPOINT = "https://api.skipengine.com/v1/service"

# Headers for API requests - using x-api-key as required by the API
headers = {
    "x-api-key": API_KEY,  # The API expects x-api-key instead of Authorization
    "Content-Type": "application/json"
}

# Dictionary mapping full state names to 2-character codes
STATE_MAPPING = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    "district of columbia": "DC",
    "american samoa": "AS",
    "guam": "GU",
    "northern mariana islands": "MP",
    "puerto rico": "PR",
    "united states minor outlying islands": "UM",
    "u.s. virgin islands": "VI",
}

def extract_5digit_zip(zip_code):
    """Extract the first 5 digits from a ZIP code that might be in ZIP+4 format"""
    if not zip_code:
        return ""
    # Extract just the first 5 digits
    match = re.match(r'^\d{5}', str(zip_code))
    if match:
        return match.group(0)
    return str(zip_code)

def convert_state_to_code(state):
    """Convert full state name to 2-character state code"""
    if not state:
        return ""
    
    # If it's already a 2-character code, return it
    if len(state) == 2 and state.upper() in STATE_MAPPING.values():
        return state.upper()
    
    # Otherwise, look up the state name in our mapping
    state_lower = state.lower()
    if state_lower in STATE_MAPPING:
        return STATE_MAPPING[state_lower]
    
    # Try to match partial state names (e.g., "New" for "New York")
    for full_name, code in STATE_MAPPING.items():
        if state_lower in full_name:
            return code
    
    # Return the original if we can't find a match
    return state[:2].upper() if len(state) >= 2 else state

def skip_trace_contact(first_name, middle_name, last_name, address, city, state, zip_code):
    """
    Skip trace a single contact using SkipEngine API
    Returns dict with mobile_phone, landline, email if found
    """
    # Extract just the 5-digit ZIP code
    zip_5digit = extract_5digit_zip(zip_code)
    
    # Convert state name to 2-character code
    state_code = convert_state_to_code(state)
    
    # Prepare the payload according to SkipEngine API documentation
    payload = {
        "FName": first_name,
        "LName": last_name,
        "Address1": address,
        "City": city,
        "State": state_code,  # Use the converted state code
        "Zip": zip_5digit
    }
    
    try:
        print(f"Sending request to {ENDPOINT}")
        print(f"Request payload: {payload}")
        response = requests.post(ENDPOINT, json=payload, headers=headers)
        
        # Print response status for debugging
        print(f"Response status: {response.status_code}")
        
        # Handle common error codes
        if response.status_code == 404:
            print("Error: API endpoint not found. Check the documentation for the correct endpoint.")
            return {"Mobile Phone": "", "Landline": "", "Email": ""}
        elif response.status_code == 401:
            print("Error: Authorization failed. Check your API key.")
            return {"Mobile Phone": "", "Landline": "", "Email": ""}
        
        # Print full response for debugging
        try:
            response_data = response.json()
            print("\nFULL RESPONSE:")
            print(json.dumps(response_data, indent=2))
            print("\n")
        except:
            print("Could not print JSON response content")
            print(f"Raw response: {response.text}")
            
        response.raise_for_status()  # Raise exception for other HTTP errors
        
        data = response.json()
        print(f"Response received with {len(str(data))} characters")
        
        # Extract the relevant contact information
        result = {
            "Mobile Phone": "",
            "Landline": "",
            "Email": ""
        }
        
        # Parse the response to extract contact details based on the SkipEngine API structure
        if "Output" in data and "Identity" in data["Output"]:
            identity = data["Output"]["Identity"]
            
            # Extract phone numbers - corrected for nested structure
            if "Phones" in identity:
                phones = identity["Phones"]
                
                # Check each phone entry (Phone, Phone2, Phone3, etc.)
                for phone_key in phones:
                    phone_entry = phones[phone_key]
                    
                    # Skip empty entries
                    if not phone_entry or not phone_entry.get("Phone"):
                        continue
                    
                    phone_number = phone_entry.get("Phone", "")
                    phone_type = phone_entry.get("PhoneType", "")
                    
                    # Format phone number with dashes if it's a 10-digit number
                    if phone_number and len(phone_number) == 10:
                        formatted_phone = f"{phone_number[:3]}-{phone_number[3:6]}-{phone_number[6:]}"
                    else:
                        formatted_phone = phone_number
                    
                    # Determine if mobile or landline based on PhoneType
                    # PhoneType W often indicates a wireless/mobile phone
                    if phone_type == "W" or phone_type == "C" or phone_type == "M":
                        result["Mobile Phone"] = formatted_phone
                    else:
                        result["Landline"] = formatted_phone
            
            # Extract email - corrected for nested structure
            if "Emails" in identity:
                emails = identity["Emails"]
                
                # Check the first email entry
                if "Email" in emails and emails["Email"].get("Email"):
                    result["Email"] = emails["Email"].get("Email", "")
        
        # Print the extracted data for verification
        print("\nExtracted contact information:")
        print(f"Mobile Phone: {result['Mobile Phone']}")
        print(f"Landline: {result['Landline']}")
        print(f"Email: {result['Email']}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error skip tracing {first_name} {last_name}: {str(e)}")
        # Print more details about the error for debugging
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response: {e.response.text}")
        return {"Mobile Phone": "", "Landline": "", "Email": ""}

def main():
    # Check if the CSV file exists
    csv_file = "foreclosures_processed.csv"
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} records from {csv_file}")
        # Print initial data
        print("\nInitial CSV data:")
        print(df)
    except Exception as e:
        print(f"Error reading {csv_file}: {str(e)}")
        return
    
    # Add columns for skip traced data if they don't exist
    for col in ["Mobile Phone", "Landline", "Email"]:
        if col not in df.columns:
            df[col] = ""
    
    # Process each record
    for idx, row in df.iterrows():
        print(f"\nProcessing record {idx+1}/{len(df)}: {row['First Name']} {row['Last Name']}")
        
        # Skip trace the contact
        result = skip_trace_contact(
            first_name=row["First Name"],
            middle_name=row["Middle Name"] if "Middle Name" in row and pd.notna(row["Middle Name"]) else "",
            last_name=row["Last Name"],
            address=row["Street Address"],
            city=row["City"],
            state=row["State"],
            zip_code=row["Zip"]
        )
        
        # Update the DataFrame with the skip traced information
        for col, value in result.items():
            df.at[idx, col] = value
        
        # Add a small delay to avoid hitting API rate limits
        time.sleep(1)
    
    # Show the updated data
    print("\nUpdated DataFrame data:")
    print(df)
    
    # Save the updated data back to the CSV file
    try:
        df.to_csv(csv_file, index=False)
        print(f"\nSuccessfully updated {csv_file} with skip traced information")
        
        # Verify the file has been updated
        print(f"Verifying saved data in {csv_file}:")
        verification_df = pd.read_csv(csv_file)
        print(verification_df[["First Name", "Last Name", "Mobile Phone", "Landline", "Email"]])
    except Exception as e:
        print(f"Error writing to {csv_file}: {str(e)}")

if __name__ == "__main__":
    main() 