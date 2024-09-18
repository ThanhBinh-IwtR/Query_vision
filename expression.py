import os
import json
import csv
import openai
import re
from prompt_gen import generate_prompts
# Configuration
#openai.api_key   # Replace with your OpenAI API key
prompts_output_folder = "prompt_gen"  # Replace with the actual path
labels_folder = "labels_with_ids"  # Replace with the actual path
elements_folder = "elements"  # Replace with the actual path
output_folder = "expression"  # Replace with the actual path

def main():
    # Generate prompts using generate_prompts function
    prompt_file_paths = generate_prompts(elements_folder, prompts_output_folder)

    # Process each generated prompt file
    for i, prompt_file_path in enumerate(prompt_file_paths):
        # Determine the subfolder name for each elements file
        subfolder_name = f"{i:04d}"
        subfolder_path = os.path.join(output_folder, subfolder_name)
        num_path = os.path.basename(subfolder_path)
        os.makedirs(subfolder_path, exist_ok=True)

        # Read raw sentences from the generated prompt file
        with open(prompt_file_path, 'r') as file:
            raw_sentences = [line.strip() for line in file.readlines()]

        # Parse elements from CSV files
        element_data = parse_elements(elements_folder, num_path)

        # Process each raw sentence
        for raw_sentence in raw_sentences:
            matching_ids = find_matching_ids(raw_sentence, element_data)
            frame_data = filter_frames(matching_ids, num_path)
            generate_json_files(raw_sentence, frame_data, subfolder_path)

def find_matching_ids(prompt, element_data):
    """Find unique IDs that match the given prompt based on the element data."""
    prompt_lower = prompt.lower()  # Convert the prompt to lowercase for case-insensitive matching
    matching_ids = set()  # Use a set to store unique IDs
    for element in element_data:
        cls_id = element['class_id']
        color = element.get('color') or ''
        action = element.get('action') or ''
        gender = element.get('gender') or ''
        # Check if both color and action are in the prompt (case-insensitive)
        if (color in prompt_lower or not color) and (action in prompt_lower or not action) and (gender in prompt_lower or not gender):
            matching_ids.add(cls_id)  # Add to set for uniqueness
    
    return list(matching_ids)  # Convert to list before returning

def parse_elements(elements_folder,num_path):
    """Parse the elements CSV files to collect the data."""
    element_data = []
    for file in os.listdir(elements_folder):
        if file.endswith(f"{num_path}.csv"):
            file_path = os.path.join(elements_folder, file)
            with open(file_path, mode='r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # Strip and convert to lowercase
                    color = row['color'].strip().lower() if row['color'] else ''
                    action = row['action'].strip().lower() if row['action'] else ''
                    gender = row['gender'].strip().lower() if row['gender'] else ''
                    
                    # Only include rows where both color and action are not empty
                    if color and action and gender:
                        element_data.append({
                            'frame_id': int(row['frame_id']),
                            'class_id': int(row['class_id']),
                            'color': color,
                            'action': action,
                            'gender': gender
                        })
    return element_data

def filter_frames( matching_ids, num_path):
    """Filter frames to find all IDs matching the attributes."""
    frame_data = {}
    # Iterate through each CSV file in the elements folder
    for file in os.listdir(elements_folder):
        if file.endswith(f"{num_path}.csv"):
            file_path = os.path.join(elements_folder, file)
            
            with open(file_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    frame_number = int(row['frame_id'])
                    class_id = int(row['class_id'])

                    # Check if the class_id is in matching_ids
                    if class_id in matching_ids:
                        if frame_number not in frame_data:
                            frame_data[frame_number] = []
                        frame_data[frame_number].append(class_id)

    # Sort class_ids for each frame_number
    for frame_number in frame_data:
        frame_data[frame_number] = sorted(frame_data[frame_number])
    return frame_data

def generate_json_files(raw_sentence, frame_data, subfolder_path):
    """Generate JSON files with paraphrased sentences."""
    generated_sentences = set()  # Store sentences to avoid repetition
    counter = 0

    while len(generated_sentences) < 2:
        paraphrased_sentence = paraphrase(raw_sentence)
        if paraphrased_sentence not in generated_sentences:
            generated_sentences.add(paraphrased_sentence)
            
            # Prepare JSON data
            json_data = {
                "label": frame_data,
                "ignore": [],
                "video_name": os.path.basename(subfolder_path),  # Use the subfolder name as the video name
                "sentence": paraphrased_sentence,
                "raw_sentence": raw_sentence
            }

            # Sanitize filename by removing invalid characters
            sanitized_prompt = sanitize_filename(paraphrased_sentence)

            # Save JSON file
            json_filename = f"{sanitized_prompt}.json"
            json_path = os.path.join(subfolder_path, json_filename)  # Save in the subfolder path
            with open(json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            counter += 1


def paraphrase(sentence):
    """Use OpenAI API to paraphrase the sentence."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that paraphrases sentences."},
                {"role": "user", "content": f"Paraphrase the following sentence: '{sentence}'"}
            ],
            max_tokens=60,
            temperature=0.7,
        )
        paraphrased_sentence = response['choices'][0]['message']['content'].strip()
        return paraphrased_sentence
    except Exception as e:
        print(f"Error during paraphrasing: {e}")
        return sentence  # Return the original sentence if paraphrasing fails

def sanitize_filename(prompt):
    """Sanitize the prompt to create a valid filename."""
    sanitized_prompt = re.sub(r'[<>:"/\\|?*\n]', '', prompt)  # Remove invalid characters
    sanitized_prompt = sanitized_prompt.replace(' ', '_')  # Replace spaces with underscores
    sanitized_prompt = sanitized_prompt[:150]  # Optionally truncate to prevent overly long filenames
    return sanitized_prompt

if __name__ == "__main__":
    main()

