import os
import json
import csv
import openai
import re
import random
from prompt_gen import generate_prompts
# Configuration
openai.api_key   # Replace with your OpenAI API key
prompts_output_folder = "prompt_gen"  # Replace with the actual path
labels_folder = "labels_with_ids"  # Replace with the actual path
elements_folder = "elements"  # Replace with the actual path
output_folder = "expression"  # Replace with the actual path

def main():
    # Generate prompts using generate_prompts function
    prompt_file_paths = generate_prompts(elements_folder, prompts_output_folder)
    # Process each generated prompt file
    for prompt_file_path in prompt_file_paths:

        match = re.search(r'_(\d+)_prompts\.txt$', prompt_file_path)
        if match:
            subfolder_name = match.group(1)  # Get the extracted number
        else:
            subfolder_name = "0000"
        subfolder_path = os.path.join(output_folder, subfolder_name)
        
        os.makedirs(subfolder_path, exist_ok=True)

        # Read raw sentences from the generated prompt file
        with open(prompt_file_path, 'r') as file:
            raw_sentences = [line.strip() for line in file.readlines()]

        # Parse elements from CSV files
        element_data = parse_elements(elements_folder, subfolder_name)

        # Process each raw sentence
        for raw_sentence in raw_sentences:
            matching_ids = find_matching_ids(raw_sentence, element_data)
            frame_data = filter_frames(matching_ids, subfolder_name)
            generate_json_files(raw_sentence, frame_data, subfolder_path)

def find_matching_ids(prompt, element_data):
    prompt_lower = prompt.lower()  # Convert prompt to lowercase
    prompt_tokens = prompt_lower.split()  # Split prompt into words

    CONNECTING_WORDS = ['in', 'on', 'with', 'at', 'of', 'for', 'to']

    # Remove connecting words from prompt tokens
    prompt_tokens = [token for token in prompt_tokens if token not in CONNECTING_WORDS]

    matching_ids = set()  # Set to store unique matching IDs

    # Regex pattern for "male" and "female"
    pattern_male = r'\bmale\b'
    pattern_female = r'\bfemale\b'

    # Iterate over each element in element_data
    for element in element_data:
        cls_id = element['class_id']
        matches = 0  # Number of matching conditions
        total_conditions = len(prompt_tokens)  # Total number of conditions in the prompt
        is_valid = True  # To check if the element matches all conditions

        # Iterate over each key-value pair in the element
        for key, value in element.items():
            if key == 'class_id' or key == 'frame_id':  # Skip fields we don't need to check
                continue

            value_lower = str(value).lower()

            # Check gender with regex for "male" and "female"
            if key == 'gender':
                if re.search(pattern_male, prompt_lower) and value_lower == 'male':
                    matches += 1
                elif re.search(pattern_female, prompt_lower) and value_lower == 'female':
                    matches += 1
                total_conditions += 'male' in prompt_lower or 'female' in prompt_lower

            # Check numeric conditions (e.g., "age 30", "height 180")
            num_match = re.search(rf'{key} (\d+)', prompt_lower)  # Find numeric conditions
            if num_match:
                num_value = num_match.group(1)
                if str(value) == num_value:  # Compare prompt number with element number
                    matches += 1
                else:
                    is_valid = False

            # Check if each token in the prompt matches the value
            for token in prompt_tokens:
                if token in value_lower:
                    matches += 1

        # If all conditions match and no conditions failed, add class_id to results
        if matches == total_conditions and is_valid:
            matching_ids.add(cls_id)

    return list(matching_ids)

def parse_elements(elements_folder,subfolder_name):
    """Parse the elements CSV files to collect the data."""
    element_data = []
    for file in os.listdir(elements_folder):
        if file.endswith(f"{subfolder_name}.csv"):
            file_path = os.path.join(elements_folder, file)
            with open(file_path, mode='r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # Strip and convert to lowercase
                    color = row['color'].strip().lower() if row['color'] else ''
                    type = row['type'].strip().lower() if row['type'] else ''
                    gender = row['gender'].strip().lower() if row['gender'] else ''
                    
                    # Only include rows where both color and type are not empty
                    if color and type and gender:
                        element_data.append({
                            'frame_id': int(row['frame_id']),
                            'class_id': int(row['class_id']),
                            'color': color,
                            'type': type,
                            'gender': gender
                        })
    return element_data

def filter_frames( matching_ids, subfolder_name):
    """Filter frames to find all IDs matching the attributes."""
    frame_data = {}
    # Iterate through each CSV file in the elements folder
    for file in os.listdir(elements_folder):
        if file.endswith(f"{subfolder_name}.csv"):
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

    while len(generated_sentences) < 3:
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
    """Paraphrase the sentence or replace gender-specific words with predefined alternatives."""
    gender_replacements = {
        "male": ["man","male", "boy", "gentlemale", "person", "individual", "humale", "adult", "guy"],
        "female": ["woman","female", "girl", "lady", "person", "individual", "humale", "adult", "gal"]
    }
    
    # Kiểm tra nếu câu chỉ chứa từ giới tính "male" hoặc "female"
    words = sentence.lower().strip().split()
    if len(words) == 1 and words[0] in gender_replacements:
        # Chọn ngẫu nhiên một từ thay thế
        return random.choice(gender_replacements[words[0]])
    
    # Nếu không phải câu giới tính, tiếp tục sử dụng OpenAI để paraphrase
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that paraphrases sentences."},
                {"role": "user", "content": f"Paraphrase the following sentence, making sure there are no periods at the end and no capital letters: '{sentence}'"}
            ],
            max_tokens=60,
            temperature=0.7,
        )
        paraphrased_sentence = response['choices'][0]['message']['content'].strip()
        return paraphrased_sentence
    except Exception as e:
        print(f"Error during paraphrasing: {e}")
        return sentence  # Trả về câu gốc nếu xảy ra lỗi

def sanitize_filename(prompt):
    """Sanitize the prompt to create a valid filename."""
    sanitized_prompt = re.sub(r'[<>:"/\\|?*\n]', '', prompt)  # Remove invalid characters
    sanitized_prompt = sanitized_prompt.replace(' ', '_')  # Replace spaces with underscores
    sanitized_prompt = sanitized_prompt[:150]  # Optionally truncate to prevent overly long filenames
    return sanitized_prompt

if __name__ == "__main__":
    main()

