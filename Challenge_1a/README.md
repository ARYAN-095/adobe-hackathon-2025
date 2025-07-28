PDF Outline Extractor
This solution extracts a structured outline, including a title and hierarchical headings (H1, H2, etc.), from PDF documents. It uses a rule-based approach to identify structural elements based on formatting cues like font size, style, and numbering conventions.

Approach
The script processes PDFs in a multi-step pipeline to ensure accurate and structured output.

Repetitive Content Filtering: To avoid including page headers or footers in the outline, the script first scans the document to identify text lines that repeat across many pages. These repetitive lines are stored in a set and are ignored during the main extraction process.

Title Detection: The title is assumed to be on the first page and is identified by finding the text with the largest font size. All text fragments sharing this maximum font size are concatenated to form the final title.

Heading Identification: The core of the solution is a rule-based engine that iterates through every line of the PDF to identify headings:

Rule 1: Numbered Headings: The primary rule looks for lines that start with a numerical pattern (e.g., 1., 2.1, 3.1.4). The hierarchy level (H1, H2, H3) is determined by the number of periods in the numbering (e.g., 2.1 is H2).

Rule 2: Non-Numbered Headings: For headings that are not numbered (like "Acknowledgements" or "Table of Contents"), the script looks for a combination of formatting cues: a significantly larger font size than the body text, a bold font style, and a short line length (typically fewer than 5 words). These are generally classified as H1.

Outline Structuring & Output: All identified headings are collected along with their level and page number. The script performs a final post-processing step to remove any duplicate headings that might appear on the same page. The final output is a single JSON file for each processed PDF, containing the document's title and a structured list of outline items.

Models or Libraries Used
This solution does not use any AI or machine learning models. It relies on the following Python libraries:

PyMuPDF (fitz): The core library for parsing PDF files. It provides access to low-level details like text, fonts, and bounding boxes for every element in the document.

Standard Libraries:

os: For interacting with the file system.

json: For creating the final JSON output file.

re: For using regular expressions to detect numbered headings.

argparse: For handling command-line arguments, allowing the input and output directories to be configurable.

collections.defaultdict: For efficiently counting font sizes and repetitive lines.

statistics: Used in previous versions for heuristic analysis.

How to Build and Run Your Solution
The solution is designed to be run inside a Docker container to ensure a consistent and clean environment.

1. Project Structure
Ensure your project files are organized as follows:
```
.
├── Challenge_1a/
│   ├── input/
│   │   └── your_document.pdf
│   ├── output/
│   │   └── (this will be generated)
│   ├── main.py          # The Python script
│   └── requirements.txt
└── Dockerfile
```

2. requirements.txt
Your Challenge_1a/requirements.txt file should contain:
```
PyMuPDF==1.24.1
```

3. Dockerfile
Use the following Dockerfile:

```
# Use a specific architecture to avoid cross-platform issues
FROM --platform=linux/amd64 python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only requirements and install early for layer caching
COPY Challenge_1a/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main app code
COPY Challenge_1a/main.py .

# Set default command
CMD ["python", "main.py"]
```

4. Build the Docker Image
Open a terminal in the root directory of your project (the one containing the Dockerfile) and run the build command:
```
docker build -t solution1a .
```

5. Run the Container
To process the PDFs, run the container with the input and output directories mounted as volumes. This command maps the input folder on your local machine to the /app/input folder inside the container, and does the same for the output folder.

```
docker run --rm -v "$(pwd)/Challenge_1a/input:/app/input" -v "$(pwd)/Challenge_1a/output:/app/output" --network none solution1a
```


After the command finishes, the extracted JSON outline will be available in your Challenge_1a/output directory.