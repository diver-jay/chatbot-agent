# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a prompts repository containing AI chatbot system prompts and instructions. The repository focuses on storing and organizing various prompt templates for different AI applications, including entity detection, persona extraction, tone selection, and conversational AI responses.

## Structure

### `/prompts/` - Core prompt templates
- `entity_detection_prompt.md` - Detects and extracts entities from user input
- `persona_extraction_prompt.md` - Extracts persona characteristics from conversations
- `split_response_prompt.md` - Splits AI responses into structured components
- `tone_selection_prompt.md` - Selects appropriate conversational tone based on context
- `tone_celebrity_20s.md` - 20대 셀럽 스타일 톤 가이드
- `tone_influencer_20s.md` - 20대 인플루언서 스타일 톤 가이드
- `tone_mentor.md` - 멘토 스타일 톤 가이드

### Additional Directories
- `/src/` - Source code implementation
- `/images/` - Image resources
- `/rules/` - Rule definitions
- `main.py` - Main application script
- `requirements.txt` - Python dependencies

## Working with Prompts

When editing or creating new prompt files:
- Maintain language consistency (Korean or English) within each prompt file
- Follow the established structure with clear sections for role definition, persona, tone guidelines, and constraints
- Preserve the conversational and friendly tone specifications where applicable
- Keep prompt instructions clear and actionable for AI systems
- For tone prompts, include detailed examples and use cases

## File Conventions

- Use `.md` format for prompt documentation
- Include clear headers and section organization
- Maintain language consistency within each prompt file