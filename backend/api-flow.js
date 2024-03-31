// Ensure to import required modules and set up environment variables

const fs = require('fs').promises; // Using promises version of fs
const { execSync } = require('child_process');
const express = require('express');
const bodyParser = require('body-parser');
const openai = require('openai');
require('dotenv').config();

const app = express();
const PORT = 3040;

app.use(bodyParser.json());

const openaiApiKey = process.env.OPENAI_API_KEY;
const openaiInstance = new openai.OpenAI(openaiApiKey);

async function generateGraphvizDotFromCsv(prompt) {
    try {
        console.log('Sending request to OpenAI GPT-3.5 Turbo API...');
        const response = await openaiInstance.chat.completions.create({
            model: "gpt-3.5-turbo-16k", // Changed the model to text-davinci-002
            temperature: 0.7,
            max_tokens: 5000,
            top_p: 1,
            frequency_penalty: 0,
            presence_penalty: 0,
            messages: [{ role: 'user', content: prompt }]
        });
        console.log(response.choices[0].message);
        return response.choices[0].message.content;
    } catch (error) {
        console.error('Error generating text from OpenAI GPT-3.5 Turbo:', error);
        throw error;
    }
}

async function harToCsv(inputFile) {
    try {
        const data = await fs.readFile(inputFile, 'utf8');
        const harData = JSON.parse(data);
        const entries = harData.log.entries.filter(entry => {
            const status = entry.response.status;
            const mimeType = entry.response.content.mimeType || '';
            return ![304, 101].includes(status) ;
        });
        const headers = ['URL', 'Method', 'Status','Status Text', 'Mime Type', 'Content Size (bytes)', 'Time (ms)'];
        const rows = entries.map(entry => [
            entry.request.url,
            entry.request.method,
            entry.response.status,
            entry.response.statusText,
            entry.response.content.mimeType || '',
            entry.response.content.size || 0,
            entry.time
        ]);
        const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
        return csv;
    } catch (error) {
        console.error('Error parsing HAR data:', error);
        throw error;
    }
}

function convertDotToPng(dotContent, outputImagePath) {
    const dotFilePath = 'api-flow.dot';
    fs.writeFile(dotFilePath, dotContent)
        .then(() => {
            execSync(`dot -Tpng ${dotFilePath} -o ${outputImagePath}`);
        })
        .catch(error => {
            console.error('Error writing DOT file:', error);
            throw error;
        });
}

app.get('/test-convert-har', async (req, res) => {
    try {
        const testHarFilePath = 'export.har';
        const csvData = await harToCsv(testHarFilePath);
        console.log(csvData.length)
        if(csvData.length>70){
        const prompt = `digraph APIFlowchart {
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
        

       
        csvData: ${csvData}

        make this string of dot file having digraph APIFlowchart {} having csvData replaced from above
        `;
        const dotContent = await generateGraphvizDotFromCsv(prompt);
        console.log('Generated DOT content:', dotContent);
        const outputImagePath = 'api-flow.png';
        convertDotToPng(dotContent, outputImagePath);
        res.json({ message: 'Test Graphviz PNG generated successfully.', imagePath: outputImagePath });
    }
    else{
        res.json({ message: 'Nothing in HAR to generate'});
    }
    } catch (error) {
        console.error('Error generating Graphviz PNG:', error);
        res.status(500).send('Failed to generate Graphviz content or PNG image for test.');
    }
});





app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
