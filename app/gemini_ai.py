import google.generativeai as genai
import os # To access environment variables
import json # To parse the JSON response
import unicodedata

API_KEY = "AIzaSyDH1w-yDSmkAiCk-bgxSoi-flKlLEkzvHI"
genai.configure(api_key=API_KEY)

# Recommended way: load from environment variable
# try:
    # genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# except KeyError:
#     print("Error: GOOGLE_API_KEY environment variable not set.")
#     print("Please set the GOOGLE_API_KEY environment variable with your Gemini API key.")
#     # Exit or handle the error appropriately
#     exit(1)

# Initialize the Generative Model
# 'gemini-pro' is a good general-purpose model for text tasks.
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- Example of how you would use it (as in the previous response) ---
def extract_entities_with_gemini(raw_text: str):
    prompt = f"""
    From the following receipt text (extracted from pdf), please extract the following information:
    1. Merchant Name
    2. Total Amount
    3. Billed Date (in YYYY-MM-DD format) (if time also add time) (maybe in different format or then convert it )

    If a piece of information is not found, state "Not Found".

    Receipt Text:
    {raw_text}

    Format your response as a JSON object:
    {{
      "merchant_name": "...",
      "total_amount": ...,
      "purchased_at": "..."
    }}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        extracted_data_json = response.text

        # --- THE KEY FIX: Remove markdown code block syntax ---
        # First, strip leading/trailing whitespace including newlines
        cleaned_json_string = extracted_data_json.strip()

        # Check if it starts and ends with the markdown code block indicators
        if cleaned_json_string.startswith('```json') and cleaned_json_string.endswith('```'):
            # Remove the '```json\n' from the start and '\n```' from the end
            # We add 1 for the newline character after ```json
            cleaned_json_string = cleaned_json_string[len('```json\n'):-len('\n```')]
            cleaned_json_string = cleaned_json_string.strip() # Strip again in case of extra newlines within the block


        # Optional: More robust cleaning for non-breaking spaces and other unicode whitespace
        cleaned_json_string = cleaned_json_string.replace('\u00A0', ' ')
        cleaned_json_string = unicodedata.normalize('NFKC', cleaned_json_string)


        # --- CRITICAL DEBUG PRINTS ---
        print("\n--- Gemini API Cleaned Response Text (Type and Raw) ---")
        print(f"Type: {type(cleaned_json_string)}")
        print(f"Length: {len(cleaned_json_string)}")
        print(f"Content (repr): {repr(cleaned_json_string)}") # Shows raw string with escaped chars
        print(f"Content (Normal): [{cleaned_json_string}]") # With brackets to spot invisible leading/trailing chars
        print("----------------------------------------------------\n")
        # --- END DEBUG ADDITIONS ---

        entities = json.loads(cleaned_json_string) # Use the cleaned string
        print("\n--- Successfully Parsed Entities ---")
        print(entities)
        print("------------------------------------\n")
        return entities
    except json.JSONDecodeError as json_e:
        print(f"JSON Decoding Error: {json_e}")
        print(f"String that caused error (for debug): '{cleaned_json_string}'") # Print the cleaned string for final check
        return {"merchant_name": "Unknown", "total_amount": 0, "purchased_at": None}
    except Exception as e:
        print(f"General Error calling Gemini API: {e}")
        return {"merchant_name": "Unknown", "total_amount": 0, "purchased_at": None}



    # try:
    #     response = gemini_model.generate_content(prompt)
    #     # Assuming the response text is the JSON string
    #     extracted_data_json = response.text
    #     cleaned_json_string = extracted_data_json.replace('\u00A0', ' ').replace('\u200B', '')
    #     cleaned_json_string = unicodedata.normalize('NFKC', cleaned_json_string)
    #     cleaned_json_string = cleaned_json_string.strip()
    #     if isinstance(cleaned_json_string, bytes):
    #         cleaned_json_string = cleaned_json_string.decode('utf-8')
    #     print(cleaned_json_string)
    #     # --- CRITICAL DEBUG PRINTS ---
    #     print("\n--- Gemini API Cleaned Response Text (Type and Raw) ---")
    #     print(f"Type: {type(cleaned_json_string)}")
    #     print(f"Length: {len(cleaned_json_string)}")
    #     print(f"Content (repr): {repr(cleaned_json_string)}") # Shows raw string with escaped chars
    #     print(f"Content (Normal): [{cleaned_json_string}]") # With brackets to spot invisible leading/trailing chars
    #     print("----------------------------------------------------\n")
    #     # --- END DEBUG ADDITIONS ---
    #     entities = json.loads(cleaned_json_string)
    #     print(entities)
    #     return entities
    # except Exception as e:
    #     print(f"Error calling Gemini API: {e}")
    #     # Return a default or error state if API call fails
    #     return {"merchant_name": "Unknown", "total_amount": 0, "purchased_at": None}

