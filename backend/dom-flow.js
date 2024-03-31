const fs = require('fs').promises; // Using promises version of fs
const { execSync } = require('child_process');
const express = require('express');
const bodyParser = require('body-parser');
const openai = require('openai');
require('dotenv').config();

const app = express();
const PORT = 3050;

app.use(bodyParser.json());

const openaiApiKey = process.env.OPENAI_API_KEY;
const openaiInstance = new openai.OpenAI(openaiApiKey);

async function generateGraphvizDot(prompt) {
    try {
        console.log('Sending request to OpenAI GPT-3.5 Turbo API...');
        const response = await openaiInstance.chat.completions.create({
            model: "gpt-3.5-turbo", // Changed the model to text-davinci-002
            temperature: 0.7,
            max_tokens: 1000,
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

function convertDotToPng(dotContent, outputImagePath) {
    const dotFilePath = 'dom-flow.dot';
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
        const url = 'https://www.hello.com'; // Replace 'http://example.com' with your URL
        const prompt = `Given a URL pointing to an HTML document, create a Graphviz DOT file that represents its Document Object Model (DOM). Filter out unnecessary HTML elements like meta. The DOT file should illustrate the hierarchical structure of HTML elements, with each element represented as a node. Parent-child relationships should be shown through edges connecting nodes. Label each node with the HTML element tag, and include id or class attributes if present. Here is the URL:\n\n"${url}"\n\nGenerate the Graphviz DOT representation. Make this string of dot file having digraph use id Node Appearance:

        Original: node [shape=box, style="filled", fontname="Arial"];
        Replace with: node [shape=ellipse, style="filled", fontname="Arial", fontsize=12];
        Edge Style:
        
        Original: edge [fontname="Arial"];
        Replace with: edge [fontname="Arial", color=gray, penwidth=1.5];
        Label Formatting:
        
        Original: ""
        Replace with: "" [label="", shape=box, fillcolor="#90EE90", fontsize=10];

        Highlighting:
        
        Original: fillcolor 
        Replace with: fillcolor based on tags for each tag each color

       
        
        Overall Layout:
    
        
        Rearrange nodes for better flow and spacing 
        Make this string of dot file having digraph use id,class,type Node connect them according to DOM Appearance include id,class color them according  node apperaces Remove extra string and GIVE ONLY AS STRING remove extra characters other than DOMFlowchart{add this at lastline before "}" label: "DOM of your ${url}"; } and give as just string`;

        const dotContent = await generateGraphvizDot(prompt);
        console.log('Generated DOT content:', dotContent);
        const outputImagePath = 'dom-flow.png';
        convertDotToPng(dotContent, outputImagePath);
        res.json({ message: 'Test Graphviz PNG generated successfully.', imagePath: outputImagePath });
    } catch (error) {
        console.error('Error generating Graphviz PNG:', error);
        res.status(500).send('Failed to generate Graphviz content or PNG image for test.');
    }
});





app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});