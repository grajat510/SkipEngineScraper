# SkipEngine Scraper

A tool to skip trace contact information from SkipEngine.com for foreclosure records.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure your foreclosures_processed.csv file is in the same directory as the script.

## Usage

Run the script:
```
python skip_trace.py
```

The script will:
1. Read contact details from foreclosures_processed.csv
2. Skip trace each contact using SkipEngine API
3. Add the retrieved Mobile Phone, Landline, and Email information to the CSV
4. Save the updated information back to the same file

Alternatively, you can use the property-based lookup:
```
python property_trace.py
```

## Configuration

The API key is configured in the script. If you need to use a different API key, edit the `API_KEY` variable in skip_trace.py.

## API Details

This script uses SkipEngine's Base Complete API (`/v1/service` endpoint) to retrieve contact information. According to the documentation, this API requires:

- Address fields (Address1, City, State, Zip) - required
- Name fields (FName, LName) - optional, but recommended

The script will send these fields to the API and parse the response to extract:
- Mobile phone numbers
- Landline phone numbers
- Email addresses

### Authentication

The SkipEngine API requires the API key to be sent in the `x-api-key` header, not in the standard Authorization header. The scripts have been configured to use this authentication method.

### Data Format Requirements

- **ZIP Code**: The API requires a 5-digit ZIP code without the ZIP+4 extension (e.g., "49548" not "49548-2203"). The script automatically extracts just the first 5 digits from any ZIP code in your CSV file.
- **State**: Must be a 2-character state code (e.g., "MI" not "Michigan").

## Troubleshooting

Common errors:

1. **404 Not Found Error**: Check that the API endpoint URL is correct. Currently using `/v1/service` for the base API and `/v1/property` for the property API.

2. **401 Authorization Error**: Verify your API key is valid and make sure it's being passed in the `x-api-key` header.

3. **400 Bad Request**: This often occurs when the data format doesn't match what the API expects:
   - ZIP codes must be 5 digits without the extension (the script now handles this automatically)
   - Make sure state codes are 2 characters (e.g., "MI" not "Michigan")

4. **No Data Returned**: The API might not have information for the provided contact. Try providing more accurate or complete information.

5. **Test Mode**: To avoid charges during testing, you can use the test API key by changing the headers to use `TEST_API_KEY` instead of `API_KEY`. 