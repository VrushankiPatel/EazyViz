from flask import Flask, request, render_template,jsonify,send_file
import subprocess
import json
import os
from openai import OpenAI

open_client = OpenAI()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')


def generate_graphviz_dot(prompt):
    try:
        openai_api_key = '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'
        print(openai_api_key)
        if not openai_api_key:
            raise Exception("OpenAI API key not found in environment variables")

        # Call OpenAI API to generate completion
        completion = open_client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # Extract the generated text from the completion
        completion_text = completion.choices[0].message.content

        return completion_text
    except Exception as e:
        raise Exception(f"Error generating text from OpenAI GPT-3.5 Turbo: {str(e)}")


# Route to test HAR conversion
@app.route('/test-convert-dom', methods=['POST'])
def test_convert_dom():
    try:
        url = request.form.get('URL')  # Get URL from the form
        uploaded_file = request.files.get('htmlFile') 
        html_content = ""
        if uploaded_file and uploaded_file.filename != '':
            html_content = uploaded_file.read().decode('utf-8')
        print(url)
        print(html_content)
        if not url and not html_content:
            return jsonify({'error': 'URL and file is missing in the form data.'}), 400
        
        prompt = f"""Given the HTML code or URL to a HTML document, create a Graphviz DOT file that represents its complete Document Object Model (DOM). 
        Here is the HTML code: {html_content}
        Here is the URL: {url}
        
        The output should only be a string starting with "digraph" and ending with a curly brace.
        No other extra characters.
        """

        print(prompt)
        dot_content = generate_graphviz_dot(prompt)
        output_image_path = 'dom-flow.png'  # Output image path
        dotFilePath = 'dom-flow.dot'
        convertDotToPng(dot_content, dotFilePath, output_image_path)
        # Render HTML template with image
        # Assuming the image is in the same directory as the Flask app
        return render_template('home.html', showSection(harSection), dom_image_url=output_image_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def har_to_csv(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            har_data = json.load(file)
            entries = har_data['log']['entries']
            filtered_entries = [entry for entry in entries if entry['response']['status'] not in [304, 101]]
            headers = ['URL', 'Method', 'Status', 'Status Text', 'Mime Type', 'Content Size (bytes)', 'Time (ms)']
            rows = [[entry['request']['url'],
                     entry['request']['method'],
                     entry['response']['status'],
                     entry['response']['statusText'],
                     entry['response']['content']['mimeType'] if 'mimeType' in entry['response']['content'] else '',
                     entry['response']['content']['size'] if 'size' in entry['response']['content'] else 0,
                     entry['time']] for entry in filtered_entries]
            csv_data = '\n'.join([','.join(map(str, row)) for row in [headers] + rows])
            return csv_data
    except Exception as error:
        print('Error parsing HAR data:', error)
        raise error


def convertDotToPng(dotContent,dotFilePath, outputImagePath):
    with open(dotFilePath, 'w') as dotFile:
        dotFile.write(dotContent)
    subprocess.run(['dot', '-Tpng', dotFilePath, '-o', outputImagePath])


# Define route for uploading HAR file and converting it
@app.route('/test-convert-har', methods=['POST'])
def test_convert_har():
    try:
        # Check if a file was uploaded
        if 'fileUpload' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Get the uploaded file
        uploaded_file = request.files['fileUpload']
        
        # Check if the file is empty
        if uploaded_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save the uploaded file
        testHarFilePath = 'uploaded_har.har'
        uploaded_file.save(testHarFilePath)
        
        # Perform conversion
        csvData = har_to_csv(testHarFilePath)
        
        # Check if there is data in the CSV
        if len(csvData) > 70:
            # Generate DOT content
            prompt =  """digraph APIFlowchart {
            // Global settings for appearance
            node [shape=box, style="filled", fontname="Arial"];
            edge [fontname="Arial"];
            // Start of the API flow
            start [label="Start", shape=oval, fillcolor="#D3D3D3"];
        
            // API Call Nodes
            {% for row in csvData %}
            "{{ row.Method }} {{ row.URL }}" [label="{{ row.Method }} {{ row.URL }}\n{{ row.statusText }}", shape=box, fillcolor="{% if row.Status == '200' %}#90EE90{% else %}#FF6347{% endif %}"];
            {% endfor %}
        
        
            // Outcome Status Nodes
            success [label="Success", shape=ellipse, fillcolor="#98FB98"];
            failure [label="Failure", shape=ellipse, fillcolor="#FF6347"];
        
            // Flow and Decisions
            start -> "{{ csvData[0].Method }} {{ csvData[0].URL }}"
            {% for i in range(0, csvData|length-1) %}
            "{{ csvData[i].Method }} {{ csvData[i].URL }}" -> "{{ csvData[i+1].Method }} {{ csvData[i+1].URL }}" [color="{% if row.Status == '200' %}blue{% else %}red{% endif %}"];
            {% endfor %}
            
        
            // Actual Outcomes as per CSV data (highlighted path)
            {% for row in csvData %}
            {% if loop.index0 != csvData|length-1 %}
            "{{ row.Method }} {{ row.URL }}"  ;
            {% endif %}
            {% endfor %}
        
            // Customizing the appearance
            label="API Call Flowchart:";
            fontsize=20;
            labelloc="t";
        }
        

       
        use this csvData: ${csvData} and dot give in response show status code

        make this string of dot file having digraph APIFlowchart {} having csvData replaced from above
        """
            dotContent = generate_graphviz_dot(prompt)
            
            # Convert DOT to PNG
            outputImagePath = 'api-flow.png'
            dotFilePath = "api-flow.dot"
            convertDotToPng(dotContent, dotFilePath, outputImagePath)
            
            # Render HTML template with image
            image_url = '/' + outputImagePath  # Assuming the image is in the same directory as the Flask app
            return render_template('home.html', api_image_url="image_url")
        else:
            # Return message if there is no data in the HAR file
            return jsonify({'message': 'Nothing in HAR to generate'})
    except Exception as error:
        # Return error response if an exception occurs
        return jsonify({'error': str(error)}), 500

# Function to convert DOT to PNG
def convert_dot_to_png(dot_content, output_image_path):
    try:
        with open('dom-flow.dot', 'w') as dot_file:
            dot_file.write(dot_content)
        subprocess.run(['dot', '-Tpng', 'dom-flow.dot', '-o', output_image_path])
    except Exception as e:
        raise Exception(f"Error converting DOT to PNG: {str(e)}")

@app.route('/get-api-image')
def get_generated_image():
    try:
        # Generate the image here
        # For example, you might have generated the image and saved it as 'api-flow.png'
        image_path = 'api-flow.png'
        # Return the image file using send_file
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        print('Error:', e)
        return 'Error generating or retrieving the image', 500
    
@app.route('/get-dom-image')
def get_generated_dom_image():
    try:
        # Generate the image here
        # For example, you might have generated the image and saved it as 'api-flow.png'
        image_path = 'dom-flow.png'
        # Return the image file using send_file
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        print('Error:', e)
        return 'Error generating or retrieving the image', 500

if __name__ == '__main__':
    app.run(debug=True, port=5051)