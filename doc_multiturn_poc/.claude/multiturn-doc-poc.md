This is a PoC mini project to experiment how well gpt-4.1-mini works with PDF documents in a multi-turn conversation. The code has to be independent from the rest of the repo. You should use the new responses API (check the documentation if needed) and you have openAI api key in the general .env file.

Requirements:
1. There needs to be a normal CLI chat experience. This is a PoC, so use color coding for showing different debugging information in the context of the chat. And to make sure that we have full visibility, in a .logs folder (created) you will continously store a .md file with the context that was sent to the model. I left already one file from another poc as an example

Minimum debugging information, but you consider other
- model called
- whether the model executes a tool calling for the pdf reading
- token consumption breakdown

2. User will upload a pdf from this folder or a subfolder within this folder and a prompt by providing a path --file PATH as part of the conversation, not on chat opening. To simulate a normal experience

3. The model will process the document via a tool calling. Create a tool that receives the document the user sends plus the question and respond the question. Use for that processing another LLM call. My recommendation would be to use the OOTB experience of the new file_search tool in the responses_API of openAI (https://platform.openai.com/docs/guides/tools-file-search). It's important that we don't enable that tool directly in the main agent, we need to wrap it in a custom tool for abstraction (i.e., we want to change how we process the PDF, or the main LLM to gemini)

4. All the variables that could be impacting the tool performance - system prompt of the main LLM with the tool description, the tool description or the param descriptions, should be easy ot edit and stored in a config.json, similar to the below. You do the first pass on prompts and descriptions
{
  "openai": {
    "system_prompt": "You are a helpful assistant that can generate images when requested. When a user asks for an image, use the generate_image tool to create it.",
    "tool_description": "Generate an image based on a text description using DALL-E",
    "parameter_description": "Detailed description of the image to generate"
  },
  
  "gemini": {
    "system_prompt": "You are a helpful assistant that can generate images when requested. When a user asks for an image, use the generate_image tool to create it. Improve the user's prompt for the image (more details, better description, always english)",
    "tool_description": "Generate an image based on a text description using DALL-E.", 
    "parameter_description": "Improved version (more details, better descriptions, always english) of the description sent by the user to generate the image"
  }
}

5. We will inject the PDF tool as required=true (not sure the syntax) when the file is uploaded, then during the following 5 back and forth we will still inject the tool with the flag optional, so the model decides whether the model would benefit from re-using the tool to respond the user question. After 5 messasges the tool is not injected unless a new file is uploaded

6. I left some pdfs in /media so you can test. Add them to the .gitignore just in case

