We need a very simple experiment. We need to create a simple chat experience where the LLM GPT-4.1-mini has available an image generation tool (you can re-use the tool from the overall project). I want the code to remain very simple, as the goal is mostly to test, how the model handles the tool calling and how the model handles the context. 

- You can use the .env api key of the bigger project
- I want you to connect to openAI models (inference: gpt-4.1-mini; image dall-e)
- I don't care about the image quality, so make dall-e to use the lowest and fastest config
- store the files in a media file inside this folder

The important part is that the things that influence the experience (IMO: system prompt <with or without the mention of the tool, this i want to test>), tool description, parameters of the tool, and its description, are easily editable so that I can quickly iterate on them