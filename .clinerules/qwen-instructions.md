# AI Light Show - Qwen Token Optimization Instructions

## Core Principle
Minimize token consumption while maintaining accuracy and system functionality.

## Prompt Engineering
- **Be Specific and Concise**: Use clear, direct language without unnecessary elaboration
- **Use Bullet Points**: Structure information in bullet points rather than paragraphs
- **Prioritize Key Information**: Include only the most relevant details in prompts
- **Use Abbreviations**: Where clear, use standard abbreviations (e.g., "sec" for seconds)

## Context Management
- **Limit Context Length**: Only include essential context in prompts
- **Use Templates**: Leverage Jinja2 templates to structure information efficiently
- **Dynamic Context Loading**: Load only the fixture information that's relevant to the current task
- **Cache Reusable Information**: Store frequently used data to avoid repeated inclusion in prompts

## Data Representation
- **JSON Formatting**: Use compact JSON formatting without unnecessary whitespace
- **Key-Value Pairs**: Represent information as key-value pairs when possible
- **Numeric Precision**: Use appropriate precision (e.g., 2 decimal places for time values)
- **Standardized Units**: Always specify units clearly (s for seconds, b for beats)

## Response Handling
- **Structured Outputs**: Request JSON responses for easier parsing
- **Limit Response Length**: Specify maximum response lengths when appropriate
- **Avoid Redundancy**: Don't repeat information that's already in the context
- **Use References**: Refer to previously mentioned items by name or ID rather than re-describing them

## System-Level Optimizations
- **Chunked Processing**: Process large tasks in smaller chunks to reduce context size
- **Incremental Updates**: Only send changed information in subsequent requests
- **Efficient Templates**: Use Jinja2 includes to reuse common prompt sections without duplicating content
- **Selective Information Loading**: Load only the information needed for the current operation

## Specific Techniques for This System
- **Fixture Information**: Only include fixture details that are relevant to the current action
- **Time Values**: Use precise numeric values rather than verbose descriptions
- **Action Specifications**: Use standardized action formats (#action fixture at time for duration)
- **Beat Alignment**: Reference beat times directly rather than describing musical positions

## Template Optimization
- **Modular Templates**: Break templates into reusable components
- **Conditional Includes**: Only include sections that are relevant to the current task
- **Compact Formatting**: Remove unnecessary whitespace and formatting in templates
- **Preprocessing**: Format data efficiently before including in templates

## Communication Protocols
- **Minimal Status Updates**: Send only essential progress information
- **Batched Responses**: Combine multiple pieces of information in single responses when possible
- **Error Handling**: Use concise error messages with specific error codes
- **Acknowledgement Messages**: Use brief acknowledgements rather than verbose confirmations

## Agent-Specific Guidelines
- **Context Builder**: Focus on musical features and emotional context, avoid verbose descriptions
- **Lighting Planner**: Generate concise action lists with precise timing
- **Effect Translator**: Convert actions to DMX commands with minimal explanation

## Implementation Patterns
- **Token Counting**: Be aware of context window limits (128K tokens)
- **Efficient Parsing**: Use regex and structured data parsing rather than natural language processing when possible
- **Caching**: Cache template renders and frequently used prompts
- **Streaming**: Use streaming responses for long-running operations

## Testing & Debug
- Monitor token usage in logs
- Optimize prompts based on actual usage patterns
- Use compact logging formats
- Profile token consumption during development

---
**Edit this file to update token optimization instructions. For questions, see README and docs/.**
