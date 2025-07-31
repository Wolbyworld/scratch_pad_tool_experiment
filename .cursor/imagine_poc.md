# Imagine PoC

Thu, 31 Jul 25

### Description

- Goal: Create a comprehensive specification for implementing image handling capabilities within Luzia chat interface
- Primary objective: Enable Luzia to recognize when images are generated and provide two core functionalities
  - Answer questions about generated images
  - Perform “fake editing” (generate new images based on edit requests rather than true image editing)
- Target environment: Staging/prototype environment (feature already exists in production)

### Specific Requirements

- **Image Generation Trigger**
  - Function calling triggered when LLM identifies image generation request
  - The function calling returns the media file path stored in the media folder in the local project
- **Prompt Enhancement System**
  - Create prompt improver function accepting two parameters:
    - Original user prompt
    - Additional instructions (could be empty)
  - Integration with GPT-4.1-mini for prompt optimization. You create the first version of the prompt, keep it simple, it’s not the point of the PoC
  - Output: Enhanced prompt for image generation
- **Image Generation Integration**
  - Implement DALL-E integration for proof of concept
  - Use low-quality, cost-effective settings for testing
  - Store generated images with reference system similar to vision feature. Add them in the media folder, and put a reference into the scratchpad. This si part of the process
  - This should be the first step for testing and stop afterwards. Have the function working
  - Add the improved prompt as part of the llm conversation context (i think it comes out of the box by calling the function of image generation)
- **Scratch Pad Integration**
  - Archive media file references in scratch pad system
  - Store improved prompt as image description
  - Enable context retention for follow-up interactions
- **Question Answering Capability (user can ask questions about the image)**
  - The working should be out of the box the same of the other media types. User ask, the scratchpad is triggered, the scratchpad defines whether we have enough info to respond, or we need to call a vision model
  - should also work out of the box, but if there is a vision call, update the scratchpad
- **Fake Editing Functionality**
  - use the image generation function calling
  - Aggregate information from scratch pad (improved prompt + follow-up context) and send it to the funciton calling
  - add to the context and scratch pad

### Design Considerations

- **Context Window Management**
  - Assumption that multiple edit requests will work within context window
  - Uncertainty about handling sequential edits beyond context limits
  - Need for implementation strategy validation
- **Data Flow Architecture**
  - User request → Function calling detection → Prompt improvement → Image generation → Scratch pad storage
- **Storage Strategy**
  - Mirror vision feature’s media reference system
  - Maintain conversation context with generation metadata
  - Scratch pad serves as primary data store for image context

### Plan (but happy to change)

- **Phase 1: Core Infrastructure**
  - Create prompt improver function with GPT-4o mini integration
  - Implement DALL-E integration for proof of concept
  - Set up function calling mechanism for image generation detection
- **Phase 2: Storage and Context**
  - Integrate scratch pad system for image reference storage
  - Implement context injection into conversation system prompt
  - Test question answering capability using stored prompts
- **Phase 3: Edit Functionality**
  - Implement edit detection through function calling
  - Create context aggregation system for edit requests
  - Test sequential editing workflow and context window limitations
- **Validation Requirements**
  - Test sequential edit handling beyond initial implementation
  - Verify context window behavior with multiple edit iterations
  - Confirm scratch pad integration maintains data integrity

