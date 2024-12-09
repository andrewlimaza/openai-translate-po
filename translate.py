import argparse
import os
import polib
import openai
import time

# Run the command below to translate a .PO file using the OpenAI API:
#  python translate.py <path_to_your_file.po> --lang <language_code> --model <model_name>
# --model (optional) Set the GPT model you want to use, defaults to gpt-4o-mini
# --lang (required) Set the target language code for translation (e.g., 'fr', 'it')


# OpenAI API configuration
openai.api_key = "your_openai_api_key"

# Batch size for API requests
BATCH_SIZE = 10

def translate_batch(batch, target_language, model):
    """Translate a batch of text entries."""
    try:
        # Build a list of translation prompts
        messages = [
            {"role": "system", "content": f"You are a helpful assistant who translates text into {target_language}."}
        ]
        for text in batch:
            messages.append({"role": "user", "content": f"Translate to {target_language}: {text}"})

        # Call the OpenAI API with ChatCompletion
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )

        # Extract the response for each translation
        result = response['choices'][0]['message']['content']
        # Split the response into translations
        translations = result.split("\n")
        return [translation.strip() for translation in translations]
    except Exception as e:
        print(f"Error translating batch: {batch}. Error: {e}")
        return batch  # Return the original batch if there's an error

def translate_po_file(input_file, target_language, model):
    """Translate all untranslated entries in a .PO file."""
    try:
        # Load the .PO file
        po_file = polib.pofile(input_file)
    except Exception as e:
        print(f"Error reading .PO file: {e}")
        return

    print(f"Translating {len(po_file)} entries to {target_language} using model {model}...")

    # Collect untranslated entries
    entries_to_translate = [entry for entry in po_file if entry.msgid and not entry.msgstr]
    total_entries = len(entries_to_translate)
    print(f"Found {total_entries} untranslated entries.")

    # Process entries in batches
    for i in range(0, total_entries, BATCH_SIZE):
        batch = entries_to_translate[i:i + BATCH_SIZE]
        batch_texts = [entry.msgid for entry in batch]
        print(f"Translating batch {i // BATCH_SIZE + 1} of {((total_entries - 1) // BATCH_SIZE) + 1}...")

        # Translate the batch
        translated_texts = translate_batch(batch_texts, target_language, model)

        # Assign translations to entries
        for entry, translation in zip(batch, translated_texts):
            entry.msgstr = translation

        # Save progress to the file after each batch
        po_file.save(input_file)
        print(f"Batch {i // BATCH_SIZE + 1} saved to file.")

        # Delay to prevent hitting API rate limits
        time.sleep(1)

    print(f"Translation completed and saved to {input_file}.")

def main():
    """Main function to handle command-line arguments and run the script."""
    parser = argparse.ArgumentParser(description="Translate a .PO file using OpenAI API.")
    parser.add_argument("input_file", help="Path to the input .PO file")
    parser.add_argument("--lang", required=True, help="Target language code (e.g., 'fr', 'it')")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use (default: gpt-4o-mini")
    args = parser.parse_args()

    input_file = args.input_file
    target_language = args.lang
    model = args.model

    # Validate input file
    if not input_file.endswith(".po"):
        print("Error: Only .PO files are supported. Please provide a valid .PO file.")
        exit(1)

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        exit(1)

    # Translate the file
    translate_po_file(input_file, target_language, model)

if __name__ == "__main__":
    main()